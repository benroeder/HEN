from auxiliary.timer import GracefulTimer
from hardware.device import Device
import threading
import os
import logging
import commands
import time
import datetime

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# The maximum number of writes held in memory before a flush must be invoked.
MAX_Q_SIZE = 100
# The number of seconds between automatic flushes.
AUTO_FLUSH_TIME = 10
# The maximum number of sensor readings to keep in memory for trend analysis.
MAX_SENSOR_HISTORY = 5

COMPRESS_COMMAND = '/usr/bin/gzip '
MOVE_COMMAND = '/bin/mv '

class MonitorDB:
    HOSTONLINE = 1
    HOSTOFFLINE = 0

    __db_dir = None
    __status_lock = None
    __flush_lock = None
    __update_lock = None
    __writebuf_lock = None
    __open_file_lock = None
    __writes_since_flush = None
    __node_fds = None
    __node_locks = None
    __write_buf = None
    __flush_timer = None
    # history format: {nodeid:{sensorid:[(type, time, val, status),..],..},..}
    # newest data at the front of the list (inserted at index 0)
    __sensor_history = None
    __sensor_max = None
    
    __sensor_check_interval = None

    # host status dictionary. Format: {nodeid:status, ...}
    #        Where status is: 0 = OK, 1 = OFFLINE
    __host_status = None

    def __init__(self):
        self.__writes_since_flush = 0
        self.__status_lock = threading.RLock()
        self.__flush_lock = threading.RLock()
        self.__update_lock = threading.RLock()
        self.__writebuf_lock = threading.RLock()
        self.__open_file_lock = threading.RLock()
        self.__node_fds = {}
        self.__node_locks = {}
        self.__write_buf = {}
        self.__sensor_history = {}
        self.__sensor_max = {}
        self.__host_status = {}

    def getStorageStats(self):
        stats = {}
        stats["__sensor_history length"] = len(self.__sensor_history)
        histCount = 0
        for sensorDict in self.__sensor_history.values():
            histCount += len(sensorDict.keys())
        stats["Total history entries"] = histCount
        stats["__sensor_max length"] = len(self.__sensor_max)
        stats["__write_buf length"] = len(self.__write_buf)
        stats["__host_status length"] = len(self.__host_status)
        stats["__node_locks length"] = len(self.__node_locks)
        stats["__node_fds length"] = len(self.__node_fds)
        stats["__writes_since_flush"] = self.__writes_since_flush
        return stats

    def startTimer(self):
        log.debug("MonitorDB: Starting flush timer")
        self.__flush_timer = GracefulTimer(AUTO_FLUSH_TIME, self.flushWrites)
        self.__flush_timer.start()

    def stopTimer(self):
        """\brief Stop the write flush timer.
        """
        log.debug("MonitorDB: stopping flush timer")
        self.__flush_timer.stop()
        self.flushWrites()

    def setSensorCheckInterval(self, interval):
        log.debug("Setting sensor check interval to %s seconds" % str(interval))
        self.__sensor_check_interval = interval

    def setDBDirectory(self, dbDir):
        if len(dbDir) <= 0:
            log.critical("setDBDirectory(): No directory provided, using \"/\"")
            dbDir = "/"
        if dbDir[len(dbDir) - 1] != "/":
            dbDir = dbDir + "/"
        log.debug("setDBDirectory(): Creating dir [" + dbDir + "]")
        if not os.path.exists(dbDir):
            os.mkdir(dbDir)
        log.info("MonitorDB: Using DB directory [" + dbDir + "]")
        self.__db_dir = dbDir

    def setHostStatus(self, nodeid, status):
        self.__status_lock.acquire()
        self.__host_status[nodeid] = status
        self.__status_lock.release()

    def getHostStatus(self, nodeid):
        if self.__host_status.has_key(nodeid):
            return self.__host_status[nodeid]
        else:
            return -1

    def getHostStatuses(self):
        return self.__host_status

    def getHostHistory(self, nodeid):
        history = {}
        if self.__sensor_history.has_key(nodeid):
            return str(self.__sensor_history[nodeid])

    def getAllCurrentSensorReadings(self):
        """\brief Returns the current/max values of sensors for all nodes.
        The results are in the form:
            {nodeid:{sensorid:(type,time,val,maxval,status),..},..}
        """
        results = {}
        for nodeid in self.__sensor_history.keys():
            results[nodeid] = {}
            for sensorid in self.__sensor_history[nodeid].keys():
                if len(self.__sensor_history[nodeid][sensorid]) < 1:
                    return results
                (htype,htime,hval,hstat) = \
                    self.__sensor_history[nodeid][sensorid][0]
                if (self.__sensor_max[nodeid]).has_key(sensorid):
                    results[nodeid][sensorid] = (htype, htime, hval, \
                         (self.__sensor_max[nodeid])[sensorid], hstat)
                else:
                    results[nodeid][sensorid] = \
                            (htype, htime, hval, -1, hstat)
        return results

    def getLastNumSensorReadings(self, nodeid, sensorid, n_readings):
        """\brief Returns the last 'n_readings' readings for the given sensor of
        the given node
        The results are sorted, most recent first, in the form:
            [(time,value), (time,value), ...]
        """
        results = []
        # Check for node history.
        if self.__sensor_history.has_key(nodeid):
            if self.__sensor_history[nodeid].has_key(sensorid):
                readings = (self.__sensor_history[nodeid])[sensorid]
                # Is the history in memory sufficient for the query ?
                if len(readings) >= n_readings:
                    return self.__historyToTimeValPairs( \
                                        readings[0:n_readings - 1])
        # If not, resort to files
        log.debug("getLastNumSensorReadings(): resorting to file lookup")
        files = self.__getOrderedFileNames(self.__db_dir + nodeid)
        for file in files:
            file_readings = self.__readFromFile(nodeid, file, sensorid)
            if file_readings:
                results += file_readings
                if len(results) >= n_readings:
                    return results[0:n_readings - 1]
        # if we're here, we didn't get enough readings! return what we've got.
        return results

    def getSensorReadingsSinceTime(self, nodeid, sensorid, sinceTime):
        """\brief Returns all the sensor readings since the given time.
        The results are sorted, most recent first, in the form:
            [(time,value), (time,value), ...]
        """
        results = []
        # Check for node history.
        if self.__sensor_history.has_key(nodeid):
            if self.__sensor_history[nodeid].has_key(sensorid):
                readings = (self.__sensor_history[nodeid])[sensorid]
                # Is the history in memory sufficient for the query ?
                if len(readings) > 0:
                    (type,time,val,status) = readings[0]
                    if time < sinceTime:
                        return self.__filterTimePairs( \
                           self.__historyToTimeValPairs(readings), sinceTime)
        # If we're here, we need to read from file.
        log.debug("getSensorReadingsSinceTime(): resorting to file lookup")
        files = self.__getOrderedFileNames(self.__db_dir + nodeid)
        for file in files:
            file_readings = self.__readFromFile(nodeid, file, sensorid)
            if file_readings:
                results += file_readings
                results.sort()
                results.reverse()
                (time,val) = file_readings[len(file_readings) - 1]
                if time < sinceTime:
                    return self.__filterTimePairs(results, sinceTime)
        # if we're here, we didn't get enough readings! return what we've got.
        results.sort()
        results.reverse()
        return self.__filterTimePairs(results, sinceTime)

    def __historyToTimeValPairs(self, readings):
        """\brief Converts a list in history format (type, time, val, status) to
            a list in (time,val) format.
        """
        def map_function(self, (type, time, val, status)):
            return (time, val)
        return map(map_function, readings)

    def __filterTimePairs(self, readings, sinceTime):
        """\brief Filters (time,value) pairs from results with time older than
            that given in sinceTime
        """
        def filter_function((time, val)):
            return (int(time) >= int(sinceTime))
        return filter(filter_function, readings)

    def __getOrderedFileNames(self, nodeDir):
        """\brief Returns an ordered list of filenames within the node directory
            used for reading logged sensor readings
            for chronological reading of data, from newest to oldest.
            \param nodeDir - Node directory containing files (full path)
            \return files - list of filenames, from newest to oldest
        """
        sorted_files = []
        files = None
        try:
            files = os.listdir(nodeDir)
            for file in files:
                if file.startswith("log"):
                    sorted_files.append(file)
            sorted_files.sort()
            sorted_files.append('current')
            sorted_files.reverse()
        except Exception, e:
            log.warning("__getOrderedFileNames(): Exception: %s" % str(e))
        return sorted_files

    def __readFromFile(self, nodeid, fileName, sensorid):
        """\brief Reads sensor readings from specified file, into a list of
            (time,reading) tuples, and returns the list.
            \param nodeid - nodeid being looked up. Used for locking the fds
            \param fileName - name of file to be read (not full path)
                              Note: .gz files are automatically handled.
            \param sensorid - sensorid to parse data for
            \return results - a list of (time,reading) tuples, empty if none
        """
        results = []
        if self.__node_locks.has_key(nodeid):
            (self.__node_locks[nodeid]).acquire()
        nodeDir = self.__db_dir + nodeid + '/'
        (status, output) = (None, None)
        if fileName.endswith('.gz'):
            (status, output) = commands.getstatusoutput('zcat ' \
                                                        + nodeDir + fileName)
        else:
            (status, output) = commands.getstatusoutput('cat ' \
                                                        + nodeDir + fileName)
        if status != 0:
            return results
        for line in output.split('\n'):
            vars = line.split(",")
            if len(vars) < 4:
                continue
            if vars[1] == sensorid:
                results.append((vars[2],vars[3]))
        if self.__node_locks.has_key(nodeid):
            (self.__node_locks[nodeid]).release()
        results.reverse()
        return results

    def writeMonitorValue(self, nodeid, sensorid, sensorType, time, value, \
                          critical_value):
        """\brief Writes a node sensor value to the data file, stores it in temp
        memory for trend analysis, then calls the trend analysis.
        This doesn't actually write immediately, but waits for a the write queue
        size to hit MAX_Q_SIZE, at which point all data is flushed.
        \param nodeid -- Node ID (e.g. computer1)
        \param sensorid -- Sensor ID (e.g. rpm0)
        \param sensorType -- Type of sensor
        \param time -- Time of reading, in seconds since epoch
        \param value -- Actual sensor reading/value
        \param critical_value -- Value at which sensor is deemed to be in
        critical condition
        \return status --   0 = STATUS OK
                            1 = WARNING (APPROACHING CRITICAL VALUE)
                            2 = CRITICAL VALUE REACHED
        """
        self.__update_lock.acquire()
        history_queue_size = 0
        # If its a first time for this node, open the db files.
        if not self.__node_fds.has_key(nodeid):
            self.__open_file_lock.acquire()
            self.__openNodeFile(nodeid)
            self.__open_file_lock.release()
        if not (self.__sensor_history[nodeid]).has_key(sensorid):
            # If this is a first time for the sensor, add a list to the dict.
            (self.__sensor_history[nodeid])[sensorid] = []
        else:
            history_queue_size = len((self.__sensor_history[nodeid])[sensorid])
        # Record the max sensor reading (if applicable)
        # TODO: BUG: doesnt consider boundType
        if not (self.__sensor_max[nodeid]).has_key(sensorid):
            (self.__sensor_max[nodeid])[sensorid] = float(value)
        elif float(value) > (self.__sensor_max[nodeid])[sensorid]:
            (self.__sensor_max[nodeid])[sensorid] = float(value)
        # Prepare to write data
        self.__node_locks[nodeid].acquire()
        writeString = self.__deComma(sensorType) + "," +\
                        self.__deComma(sensorid) + "," +\
                        self.__deComma(time) + "," +\
                        self.__deComma(value) + "\n"
        self.__write_buf[nodeid].append(writeString)
        self.__writes_since_flush += 1
        if history_queue_size >= MAX_SENSOR_HISTORY:
            # get rid of the oldest history data, making space for new data
            (self.__sensor_history[nodeid])[sensorid].pop()
        # Need a history before a checkTrend(), so use status = 0
        (self.__sensor_history[nodeid])[sensorid].insert(0, (sensorType, \
                                      time, float(value), 0))
        result = self.__checkTrend(nodeid, sensorid, sensorType, critical_value)
        # Now replace history with the correct status
        (self.__sensor_history[nodeid])[sensorid].pop(0)
        (self.__sensor_history[nodeid])[sensorid].insert(0, (sensorType, \
                                      time, float(value), result))
        self.__node_locks[nodeid].release()
        self.__update_lock.release()
        # If need be, initiate a flush
        if (self.__writes_since_flush >= MAX_Q_SIZE):
            self.flushWrites()
        return result

    def flushWrites(self):
        """\brief Flush any writes to disk.
        """
        #log.debug("flushWrites(): Acquiring update lock.")
        self.__update_lock.acquire()
        #log.debug("flushWrites() has update lock.")
        if self.__writes_since_flush > 0:
            #log.debug("flushWrites(): Acquiring file locks.")
            for fileLock in self.__node_locks.values():
                fileLock.acquire()
            log.debug("flushWrites(): Flushing write buffers")
            for nodeid in self.__node_fds.keys():
                nodefd = self.__node_fds[nodeid]
                while len(self.__write_buf[nodeid]) > 0:
                    writeStr = self.__write_buf[nodeid].pop(0)
                    os.write(nodefd, writeStr)
            self.__writes_since_flush = 0
            #log.debug("flushWrites(): Releasing file locks.")
            for fileLock in self.__node_locks.values():
                fileLock.release()
        #log.debug("flushWrites(): Releasing update lock.")
        self.__update_lock.release()
        #log.debug("flushWrites() releases update lock.")

    def rotateLogs(self):
        """\brief Takes the "current" logfile and compresses. Then opens a new
        "current" file. Takes average of the file's readings and places in file
        "average" in node dir.
        """
        # Acquire all locks
        log.debug("MonitorDB: Acquiring all locks for rotation.")
        self.__update_lock.acquire()
        for fileLock in self.__node_locks.values():
            fileLock.acquire()
        # Get the time since epoch for the daily rotation
        timenow = int(time.time())
        datestring = datetime.datetime.fromtimestamp(timenow).\
                        strftime("%Y-%m-%d-%H:%M:%S")
        log.debug("MonitorDB: Compressing current logfiles")
        broken = False
        try:
            for nodeid in self.__node_fds.keys():
                nodedir = self.__db_dir + nodeid + "/"
                # 1) Calculate daily averages of sensor, append to "daily"
                self.__writeAverage(nodeid, timenow)
                # 2) Close "current" file.
                os.close(self.__node_fds[nodeid])
                # 3) Compress "current" file
                (sts, out) = commands.getstatusoutput(COMPRESS_COMMAND + \
                              nodedir + "current")
                if sts != 0:
                    log.critical("Compress Command Failed! Output was: " + out)
                # 4) Move compressed file to log-DD-MM-YYYY.gz
                (sts, out) = commands.getstatusoutput(MOVE_COMMAND + \
                              nodedir + "current.gz " + nodedir + "log-" + \
                              datestring + ".gz")
                if sts != 0:
                    log.critical("Move Command Failed! Output was: " + out)
                # 5) Create new "current" file (lock can remain the same)
                self.__node_fds[nodeid] = os.open(nodedir + "current",\
                                      os.O_RDWR|os.O_CREAT|os.O_APPEND, 0644)
        except Exception, e:
            log.critical("Exception: dailyLogRotate(): " + str(e))
            broken = True
        log.debug("MonitorDB: Releasing all locks from rotation.")
        for fileLock in self.__node_locks.values():
            fileLock.release()
        self.__update_lock.release()
        if broken:
            return -1
        return 0

    def __writeAverage(self, nodeid, timenow):
        """\brief Calculates the average sensor readings from the contents of
        the "current" logfile for the specified nodeid, and appends it's results
        to a file called "average", using the supplied epoch time. NOTE: This
        method should _only_ be called if the node files are locked for this
        operation.
        """
        try:
            nodeDir = self.__db_dir + nodeid
            finput = open(nodeDir + '/current', 'r')
            sensor_sum = {}
            sensor_count = {}
            sensor_type = {}
            for line in finput.readlines():
                vars = line.split(",")
                if len(vars) < 4:
                    continue
                if not sensor_sum.has_key(vars[1]):
                    sensor_sum[vars[1]] = 0.0
                sensor_sum[vars[1]] += float(vars[3])
                sensor_type[vars[1]] = vars[0]
                if not sensor_count.has_key(vars[1]):
                    sensor_count[vars[1]] = 0
                sensor_count[vars[1]] += 1
            finput.close()
            foutput = open(nodeDir + '/average', 'a')
            for sensorid in sensor_sum.keys():
                avg = sensor_sum[sensorid] / sensor_count[sensorid]
                foutput.write(str(sensor_type[sensorid]) + "," + \
                             str(sensorid) + "," + \
                             str(timenow) + "," + \
                             str(avg) + "\n")
            foutput.close()
        except Exception, e:
            log.critical("Exception: __writeAverage(" + nodeid + \
                         "): " +  str(e))

    def __checkTrend(self, nodeid, sensorid, sensorType, critical_value):
        """\brief Checks the previous sensor readings of the given node/sensor,
        to see if it is approaching (or has already reached) the critical value.
        \param nodeid -- Node ID of node sensor belongs to
        \param sensorid -- The sensor ID
        \param sensorType -- Type of sensor (used to establish which side of the
        critical value is "normal"
        \param critical_value -- The critical value at which an alarm should be
        raised
        \return status --   0 = STATUS OK
                            1 = WARNING (APPROACHING CRITICAL VALUE)
                            2 = CRITICAL VALUE REACHED
        """
        if not (self.__sensor_history[nodeid]).has_key(sensorid):
            log.critical("__checkTrend() found no sensor history (NodeID[" + \
                         nodeid + "], SensorID[" + sensorid + "])")
            return 0 # Although worring, dont cause a shutdown!
        history = (self.__sensor_history[nodeid])[sensorid]
        if not len(history) > 0:
            log.critical("__checkTrend() found no sensor history (NodeID[" + \
                         nodeid + "], SensorID[" + sensorid + "])")
            return 0 # Although worring, dont cause a shutdown!
        # establish whether critical value is lower or upper bound
        boundType = Device().getBoundTypeFromClass(sensorType)
        if boundType == None:
            log.critical("__checkTrend() found no sensor boundtype (NodeID[" + \
                         nodeid + "], SensorID[" + sensorid + "])")
            return 0 # Although worring, dont cause a shutdown!
        """
        We'll use boundtype to change the behaviour of a common simple eqn.
        For upper bounds,   CRIT_VAL - READING < 0 (for alerts)
        For lower bounds,(-)CRIT_VAL -(-)READING < 0 (for alerts)
        """
        (htype0, htime0, hval0, hstat0) = history[0]
        if boundType == 1:
            boundType = -1
        else:
            boundType = 1
        # First (simplest) check: Has the latest reading passed critical ?
        if ((boundType * critical_value) - (boundType * hval0)) < 0:
            log.critical("""
========= CRITICAL =========
date           = %s
nodeid         = %s
sensorid       = %s
boundType      = %s
critical_value = %s
latest reading = %s
============================""" % \
                (time.strftime("[%a %b %d %H:%M:%S %Y]", time.localtime()), \
                 str(nodeid), str(sensorid), str(boundType), \
                 str(critical_value), str(hval0)))
            return 2 # ALARM!
        """
        Before going any further, we should establish if the sensor reading
        is even approaching the critical value (i.e. is the temperature
        increasing ?) If the sensor isn't approaching critical, we can return
        now.
        """
        if not len(history) > 1:
            log.debug("CheckTrend(%s:%s): No 2nd history values" % \
                         (str(nodeid), str(sensorid)))
            return 0
        (htype1, htime1, hval1, hstat1) = history[1]
        unit_change = hval0 - hval1
        log.debug("hval0[%f], hval1[%f]" % (hval0, hval1))
        if (unit_change * boundType) <= 0:
            log.debug("CheckTrend(%s:%s): negative unit change is %s" % \
                  ((str(nodeid), str(sensorid), str(unit_change * boundType))))
            return 0
        """
        Now check if we'll reach the critical value within the next
        sensor update time based on the previous increase. We want at least 3
        history entries, to ensure some "settling" of values.
        """
        if not len(history) > 2:
            log.debug("CheckTrend(%s:%s): No 3rd history values" % \
                         (str(nodeid), str(sensorid)))
            return 0
        # Calculate the rate of increase (change/time)
        rate = float(unit_change) / (htime0 - htime1)
        # Using this, find the value of the sensor if it changed at this rate
        predicted_reading = hval0 + (self.__sensor_check_interval * rate)
        log.debug("CheckTrend(%s:%s): hval0[%s], rate[%s], predicted[%s]" \
          % (nodeid, sensorid, str(hval0), str(rate), str(predicted_reading)))
        if ((boundType * critical_value)-(boundType * predicted_reading)) <= 0:
            log.warning("""
========= WARNING ==========
date            = %s
nodeid          = %s
sensorid        = %s
boundType       = %s
critical_value  = %s
latest reading  = %s
rate of change  = %s
predicted value = %s
============================""" % \
                (time.strftime("[%a %b %d %H:%M:%S %Y]", time.localtime()), \
                 str(nodeid), str(sensorid), str(boundType), \
                 str(critical_value), str(hval0), str(rate), \
                 str(predicted_reading)))
            return 1 # WARNING!
        """
        At this point we can go one step further and check the second
        differential, to see if there is an increasing gradient in the readings.
        TODO: Implement
        """
        log.debug("CheckTrend(%s:%s): finished trend analysis.")
        return 0

    def __deComma(self, inputString):
        """\brief Replaces commas within string with underscores.
        \param inputString -- String to replace commas from
        """
        result = str(inputString)
        result = result.replace(",", "_")
        return result

    def __openNodeFile(self, nodeid):
        """\brief Creates write buffer, write lock, sensor history dictionaries
        and fd for given node.
        """
        nodedir = self.__db_dir + nodeid
        if not os.path.exists(nodedir):
            os.mkdir(nodedir)
        self.__node_fds[nodeid] = os.open(nodedir + "/current",\
                                      os.O_RDWR|os.O_CREAT|os.O_APPEND, 0644)
        self.__write_buf[nodeid] = []
        self.__sensor_history[nodeid] = {}
        self.__sensor_max[nodeid] = {}
        self.__node_locks[nodeid] = threading.RLock()


    def __closeNodeFile(self, nodeid):
        """\brief Removes write buffer, write lock, sensor history queue
        and fd for given node.
        WARNING: This does not flush anything left in the buffer!
        """
        self.__node_locks[nodeid].acquire()
        os.close(self.__node_fds[nodeid])
        self.__node_locks[nodeid].remove()
        self.__write_buf[nodeid].remove()
        self.__sensor_history[nodeid].remove()
        pass
