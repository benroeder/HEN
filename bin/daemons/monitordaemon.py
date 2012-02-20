#!/usr/local/bin/python
import sys
sys.path.append("/usr/local/hen/lib")

from daemonizer import Daemonizer
from daemon import Daemon
from auxiliary.timer import GracefulTimer
from henmanager import HenManager
from auxiliary.daemonlocations import DaemonLocations

from auxiliary.monitord.monitordb import MonitorDB
from auxiliary.monitord.graphmanager import GraphManager
from auxiliary.monitord.workertask import *
from auxiliary.monitord.workerthread import *

import socket, logging, threading, os, time, resource, datetime

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# seconds between queries to all sensor nodes for new data
SENSOR_UPDATE_INTERVAL = 180
# seconds between host checks (i.e. ping spam)
HOST_CHECK_INTERVAL = 120
# maintenance scheduling interval
MAINTENANCE_INTERVAL = 60
# Number of worker threads created by monitor daemon
NUM_WORKER_THREADS = 20
# Path to sendmail binary
SENDMAIL = '/usr/sbin/sendmail'

#GRAPH_BASE_URL = "http://%s/schooley/status" % DaemonLocations.monitorDaemon[0]
GRAPH_BASE_URL = "/schooley/status"
GRAPH_WEB_DIR = "/home/arkell/u0/www/data/schooley/status/"

class Monitor(Daemon):
    """
    \brief Implements the MonitorD external interface
    This class contains the methods called when requests are recieved by the
    Daemon (inherited).
    """
    __version = "Monitor Daemon v0.1"
    __update_timer = None
    __host_check_timer = None
    __mainenance_timer = None
    __update_lock = threading.Lock()
    __worker_threads = {}
    __monitordb = None
    __hm = None
    __gm = None
    __last_mem_usage = None
    __nodeInstances = None
    __pingchecknodes = None

    def __init__(self):
        """\brief Registers remote methods and starts update thread (timer)
        """
        Daemon.__init__(self)
        self.__monitordb = MonitorDB()
        self.__registerMethods()
        self.__hm = HenManager()
        self.__gm = GraphManager(GRAPH_BASE_URL, GRAPH_WEB_DIR)
        self.initiateNodes()
        for workerNumber in range(NUM_WORKER_THREADS):
            self.__worker_threads[workerNumber] = WorkerThread(workerNumber, \
                                                               self.__monitordb)
            self.__worker_threads[workerNumber].setHenManager(self.__hm)
            self.__worker_threads[workerNumber].start()

    def __registerMethods(self):
        self.registerMethodHandler("get_version", self.getVersion)
        #self.registerMethodHandler("test_method", self.testMethod)
        self.registerMethodHandler("get_threadqueues", \
                                   self.getWorkerTaskQueueStatus)
        self.registerMethodHandler("get_dbstats", \
                                   self.getMonitorDBStats)
        #self.registerMethodHandler("stop_daemon", self.stopDaemon)
        #self.registerMethodHandler("kill_daemon", self.killDaemon)
        self.registerMethodHandler("get_currentsensorreadings", \
                                   self.getAllCurrentSensorReadings)
        self.registerMethodHandler("get_lastnumsensorreadings", \
                                   self.getLastNumSensorReadings)
        self.registerMethodHandler("get_sensorreadingssincetime", \
                                   self.getSensorReadingsSinceTime)
        self.registerMethodHandler("rotate_logs", self.rotateLogs)
        self.registerMethodHandler("get_hoststatuses", self.getHostStatuses)
        self.registerMethodHandler("get_nodesensorgraph", \
                                   self.getNodeSensorGraph)


    def testMethod(self,prot,seq,ln,payload):
        log.debug("testMethod() called.")
        nodeid = "computer30"
        sensorid = "pdb.t_amb"
        data = self.__monitordb.getSensorReadingsSinceTime(nodeid, \
                     sensorid, 1170688588)
        sensortype = self.getTypeFromSensorID(nodeid, sensorid)
        if sensortype == None:
            sensortype = "unknown"
        try:
            url = self.__gm.createGraph(data, nodeid, sensorid, sensortype, 1170688588)
            prot.sendReply(200, seq, url)
        except Exception, e:
            prot.sendReply(500, seq, str(e))

    def getNodeSensorGraph(self,prot,seq,ln,payload):
        log.debug("getNodeSensorGraph() called.")
        args = payload.split(" ")
        if len(args) != 3:
            prot.sendReply(400, seq, \
                   "Incorrect arguments supplied. payload [%s]" % str(payload))
            return
        if len(args[0]) < 1 or len(args[1]) < 1 or len(args[2]) < 1:
            prot.sendReply(400, seq, "Incorrect lengths of arguments.")
            return
        nodeid = args[0]
        sensorid = args[1]
        timerange = int(args[2])
        sincetime = int(time.time()) - timerange
        data = self.__monitordb.getSensorReadingsSinceTime(nodeid, \
                     sensorid, sincetime)
        sensortype = self.getTypeFromSensorID(nodeid, sensorid)
        if sensortype == None:
            sensortype = "unknown"
        try:
            url = self.__gm.createGraph(data, nodeid, sensorid, \
                                        sensortype, sincetime)
            prot.sendReply(200, seq, url)
        except Exception, e:
            prot.sendReply(500, seq, "Exception: %s" % str(e))

    def getTypeFromSensorID(self, nodeid, sensorid):
        """\brief Attempts to find and return the sensor type, given a sensor
            and node id.
            \param nodeid - nodeid to which the sensor belongs
            \param sensorid - sensorid to get type of
            \return sensortype - type of sensor, as defined in Devices
        """
        if self.__nodeInstances.has_key(nodeid):
            try:
                (node, instance) = self.__nodeInstances[nodeid]
                desc = instance.getSensorDescriptions()
                return instance.getSensorClassFromName(desc, sensorid)
            except Exception, e:
                log.warning("getTypeFromSensorID(): %s" % str(e))
        return None

    def killDaemon(self,prot,seq,ln,payload):
        prot.sendReply(200, seq, "Killing Daemon!")
        os.abort()

    def getMonitorDBStats(self,prot,seq,ln,payload):
        payload = ""
        stats = self.__monitordb.getStorageStats()
        for desc in stats.keys():
            payload += "[" + str(desc) + "] = " + str(stats[desc]) + "\n"
        prot.sendReply(200, seq, payload)

    def getWorkerTaskQueueStatus(self,prot,seq,ln,payload):
        payload = ""
        for workerNumber in range(NUM_WORKER_THREADS):
            payload += "WorkerThread[" + str(workerNumber) + "]: Queue size = "\
                + str(self.__worker_threads[workerNumber].getTaskQueueSize()) +\
            "\n"
        prot.sendReply(200, seq, payload)

    def getHostStatuses(self,prot,seq,ln,payload):
        """\brief Returns node statuses in XML format:
        <nodestatuses>
            <nodestatus id="nodeid" status="{0,1}" />
        </nodestatuses>
        Where status=0 means OK, status=1 means OFFLINE
        """
        log.debug("getHostStatuses() called.")
        payload = "<nodestatuses>\n"
        statusDictionary = self.__monitordb.getHostStatuses()
        for nodeid in statusDictionary.keys():
            payload = payload + "\t<nodestatus id=\"" + str(nodeid) + \
                "\" status=\"" + str(statusDictionary[nodeid]) + "\" />\n"
        payload += "</nodestatuses>\n\n"
        prot.sendReply(200, seq, payload)

    def rotateLogs(self,prot,seq,ln,payload):
        """\brief Initiates a log rotation."""
        log.debug("rotateLogs() called.")
        results = self.__monitordb.rotateLogs()
        if results < 0:
            prot.sendReply(500, seq, "An error occurred during the log " + \
                                   "rotation. Please check the monitord logs.")
        else:
            prot.sendReply(200, seq, "Log rotation completed.")

    def getVersion(self,prot,seq,ln,payload):
        """\brief Returns version"""
        payload = self.__version
        prot.sendReply(200, seq, payload)

    def getAllCurrentSensorReadings(self,prot,seq,ln,payload):
        """\brief Returns an XML payload for each node, in the following format:
        <nodereadings>
            <nodereading id="nodeid">
                <reading id="sensorid" sensortype="type" readingtime="time" \
                    value="currentreading" max="maxreading" status="status" />
            </nodereading>
        </nodereadings>
        """
        log.debug("getAllCurrentSensorReadings() called.")
        payload = "<nodereadings>\n"
        currentReadings = self.__monitordb.getAllCurrentSensorReadings()
        if not currentReadings:
            log.debug("getAllCurrentSensorReadings() returned no data!")
        for nodeid in currentReadings.keys():
            xmlString = ""
            overallStatus = "0"
            for sensorid in currentReadings[nodeid].keys():
                (type,time,val,maxval,status) = \
                                currentReadings[nodeid][sensorid]
                xmlString += "\t\t<reading id=\"" + sensorid + \
                        "\" type=\"" + str(type) + \
                        "\" time=\"" + str(int(time)) + \
                        "\" value=\"" + str(val) + \
                        "\" max=\"" + str(maxval) + \
                        "\" status=\"" + str(status) + \
                        "\" />\n"
                if int(status) > overallStatus:
                    overallStatus = int(status)
            xmlString = xmlString + "\t</nodereading>\n"
            xmlString = "\t<nodereading id=\"" + nodeid + "\" overallstatus=\""\
                         + str(overallStatus) + "\">\n" + xmlString
            payload = payload + xmlString
        payload += "</nodereadings>\n\n"
        prot.sendReply(200, seq, payload)

    def getLastNumSensorReadings(self,prot,seq,ln,payload):
        """\brief Returns the last N readings for a given sensor on a given
            node, in the following format:
            <nodereading nodeid="nodeid" sensorid="sensorid">
                <reading readingtime="time" value="reading" />
            </nodereading>

            Incoming payload must be in the format:
                nodeid sensorid nreadings
        """
        log.debug("getLastNumSensorReadings() called.")
        args = payload.split(" ")
        if len(args) != 3:
            prot.sendReply(400, seq, "Incorrect arguments supplied.")
            return
        if len(args[0]) < 1 or len(args[1]) < 1 or len(args[2]) < 1:
            prot.sendReply(400, seq, "Incorrect lengths of arguments.")
            return
        nodeid = args[0]
        sensorid = args[1]
        n_readings = int(args[2])

        readings = self.__monitordb.getLastNumSensorReadings(nodeid, \
                                                     sensorid, n_readings)
        if readings:
            payload = "<nodereading nodeid=\"" + nodeid + "\" sensorid=\"" + \
                        sensorid + "\">\n"
            for (time,val) in readings:
                payload = payload + "\t<reading readingtime=\"" + str(time) + \
                            "\" value=\"" + str(val) + "\" />\n"
            payload = payload + "</nodereading>\n"
            prot.sendReply(200, seq, payload)
        else:
            log.debug("Got no readings from getLastNumSensorReadings()")
            prot.sendReply(500, seq, "No readings found.")

    def getSensorReadingsSinceTime(self,prot,seq,ln,payload):
        """\brief Returns all readings for a given sensor on a given
            node, since a given time, in the following format:
            <nodereading nodeid="nodeid" sensorid="sensorid">
                <reading readingtime="time" value="reading" />
            </nodereading>

            Incoming payload must be in the format:
                nodeid sensorid timesinceepoch
        """
        log.debug("getSensorReadingsSinceTime() called.")
        args = payload.split(" ")
        if len(args) != 3:
            prot.sendReply(400, seq, "Incorrect arguments supplied.")
            return
        if len(args[0]) < 1 or len(args[1]) < 1 or len(args[2]) < 1:
            prot.sendReply(400, seq, "Incorrect lengths of arguments.")
            return
        nodeid = args[0]
        sensorid = args[1]
        sincetime = int(args[2])
        # Check time isnt in future (wasted effort otherwise)
        currenttime = int(time.time())
        if sincetime > currenttime:
            log.warning("getSensorReadingsSinceTime(): time supplied [" + \
                        str(sincetime) + "] is in the future! [current time = "\
                        + str(currenttime) + "]")
            prot.sendReply(400, seq, "Time provided is in the future.")
            return

        readings = self.__monitordb.getSensorReadingsSinceTime(nodeid, \
                                                     sensorid, sincetime)
        if readings:
            payload = "<nodereading nodeid=\"" + nodeid + "\" sensorid=\"" + \
                        sensorid + "\">\n"
            for (rtime,rval) in readings:
                payload = payload + "\t<reading readingtime=\"" + str(rtime) + \
                            "\" value=\"" + str(rval) + "\" />\n"
            payload = payload + "</nodereading>\n"
            prot.sendReply(200, seq, payload)
        else:
            log.debug("Got no readings from getSensorReadingsSinceTime()")
            prot.sendReply(500, seq, "No readings found.")

    def stopWorkerThreads(self):
        total_threads = threading.activeCount()
        for workerNumber in range(NUM_WORKER_THREADS):
            self.__worker_threads[workerNumber].stop()

    def stopDaemon(self,prot,seq,ln,payload):
        """\brief Stops the daemon and all threads
        This method will first stop any more incoming queries, then wait for
        any update tasks to complete, before stopping itself.
        """
        log.info("stopDaemon called.")
        prot.sendReply(200, seq, "Accepted stop request.")
        log.debug("Sending stopDaemon() response")
        self.acceptConnections(False)
        log.debug("Attempting to acquire update lock")
        self.__update_lock.acquire()
        log.debug("Stopping maintenance timer")
        self.__mainenance_timer.stop()
        log.debug("Stopping host status timer")
        self.__host_check_timer.stop()
        log.debug("Stopping update timer")
        self.__update_timer.stop()
        log.info("Stopping worker threads (please be patient)")
        self.stopWorkerThreads()
        log.debug("Stopping MonitorDB timer")
        self.__monitordb.stopTimer()
        log.debug("Releasing update lock")
        self.__update_lock.release()
        log.info("Stopping Monitor (self)")
        self.stop()

    def scheduleTasks(self, taskid):
        """\brief Schedules a batch of tasks (specified by taskid) for all nodes
        in HEN.
        \param taskid - The taskid. 0 = sensor readings, 1 = host status check
        Note: serviceprocessor node types are ignored - they are used through
        the nodes they are attached to.
        """
        # Don't start a new update if shutting down (not accepting connections)
        if self.acceptingConnections():
            log.debug("scheduleTasks(): Acquiring update lock.")
            self.__update_lock.acquire()
            if taskid == TaskID.checkSensorTask:
                taskCount = self.scheduleSensorChecks(taskid)
                log.debug("scheduleSensorChecks: %s tasks scheduled." % \
                     str(taskCount))
            elif taskid == TaskID.hostStatusTask:
                taskCount = self.scheduleHostPingChecks(taskid)
                log.debug("scheduleHostPingChecks: %s tasks scheduled." % \
                     str(taskCount))
            else:
                log.critical(
                     "Monitor.scheduleTasks() found unknown taskid [%s]" % \
                     str(task.taskid))
            log.debug("scheduleTasks(): Releasing update lock.")
            self.__update_lock.release()

    def scheduleSensorChecks(self, taskid):
        workerNumber = self.chooseNextWorker()
        taskCount = 0
        for nodeid in self.__nodeInstances.keys():
            timeScheduled = int(time.time())
            (node, nodeInstance) = self.__nodeInstances[nodeid]
            task = WorkerTask(node, nodeInstance, taskid, timeScheduled)
            self.__worker_threads[workerNumber].runTaskQueueMaintenance()
            taskCount += 1
            self.__worker_threads[workerNumber].addTask(task)
            workerNumber = self.chooseNextWorker()
        return taskCount

    def scheduleHostPingChecks(self, taskid):
        """\brief Schedules host ping checks"""
        workerNumber = self.chooseNextWorker()
        taskCount = 0
        for nodeid in self.__pingchecknodes.keys():
            timeScheduled = int(time.time())
            node = self.__pingchecknodes[nodeid]
            task = WorkerTask(node, None, taskid, timeScheduled)
            self.__worker_threads[workerNumber].runTaskQueueMaintenance()
            taskCount += 1
            self.__worker_threads[workerNumber].addTask(task)
            workerNumber = self.chooseNextWorker()
        return taskCount

    def chooseNextWorker(self):
        """\brief Selects the next worker thread number for use in scheduling.
            Note that this function needs to be quickish, as it's run on a
            _per-task-schedule_ basis.
        """
        queueSizes = []
        for threadnum in range(NUM_WORKER_THREADS):
            queueSizes.append( \
              (self.__worker_threads[threadnum].getTaskQueueSize(), threadnum))
        (qsize, tnum) = min(queueSizes)
        return tnum

    def initiateNodes(self):
        """\brief Creates a {nodeid:(node,nodeinstance)} dictionary for sensor
            readings, and a {nodeid:node} dictionary for host ping checking.
            In the case where a computer node uses a serviceprocessor, the
            nodeinstance for the computer node will be that of a
            serviceprocessor.

            NOTE: Service Processors are excluded as being a primary node, as
            they are attached to a computer node.
        """
        log.debug("Creating NodeInstance map")
        self.__nodeInstances = {}
        self.__pingchecknodes = {}
        nodes = self.__hm.getNodes("all", "all")
        spnodes = self.__hm.getNodes("serviceprocessor", "all")
        for nodeType in nodes.keys():
            if nodeType == "serviceprocessor" \
                or nodeType == "mote":
                continue
            nodeTypes = nodes[nodeType]
            for node in nodeTypes.values():
                self.__pingchecknodes[node.getNodeID()] = node
                serviceProcessor = None
                nodeInstanceRef = node
                if node.getNodeType() == "computer":
                    if spnodes.has_key(node.getSPNodeID()):
                        nodeInstanceRef = spnodes[node.getSPNodeID()]
                try:
                    self.__nodeInstances[node.getNodeID()] = \
                                        (node, nodeInstanceRef.getInstance())
#                    log.debug("Created instance for node [%s]" % \
#                                  str(node.getNodeID()))
                except Exception, e:
                    log.debug("Creating node instance failed for node [%s]: %s"\
                              % (str(node.getNodeID()), str(e)))
        log.debug("initiateNodes() completed. NodeInstances[%s], Nodes[%s]" % \
                  (str(len(self.__nodeInstances.keys())), \
                   str(len(self.__pingchecknodes.keys()))))
        counter = 0
        for nodeid in self.__nodeInstances.keys():
            log.debug("[%s] %s" % (str(counter), nodeid))
            counter += 1

    def updateNodeInfo(self):
        """\brief Initiates a new scan of sensor readings."""
        log.debug("updateNodeInfo() called.")
        self.scheduleTasks(TaskID.checkSensorTask)

    def updateHostStatus(self):
        """\brief Initiates a host check of all HEN nodes"""
        log.debug("updateHostStatus() called.")
        self.scheduleTasks(TaskID.hostStatusTask)

    def runMaintenanceTasks(self):
        """\brief Method run by maintenance timer. Use this for miscellaneous
            tasks that need running periodically. Refer to MAINTENANCE_INTERVAL
            for the scheduled period.
        """
        self.__gm.cleanOldFiles()
        #self.logResourceUsage()

    def logResourceUsage(self):
        """\brief Checks the resource usage of the entire monitor daemon
        and logs it.
        """
        timenow = int(time.time())
        datestring = datetime.datetime.fromtimestamp(timenow).\
                        strftime("%Y-%m-%d-%H:%M:%S")
        sys_page_size = resource.getpagesize()
        max_mem_bytes = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        log.info("RESOURCE[" + datestring + "][Max Memory Usage] = {" + \
                 str(max_mem_bytes) + "Kb, " + \
                 str(max_mem_bytes / 1024) + "Mb}")
        if self.__last_mem_usage == None:
            self.__last_mem_usage = max_mem_bytes
        difference = max_mem_bytes - self.__last_mem_usage
        if difference > 0:
            log.info("RESOURCE[difference] = {+" + str(difference) + "Kb}")
        elif difference < 0:
            log.info("RESOURCE[difference] = {-" + str(difference) + "Kb}")
        else:
            log.info("RESOURCE[difference] = {None}")
        self.__last_mem_usage = max_mem_bytes

    def setDBDirectory(self, dbDir):
        self.__monitordb.setDBDirectory(dbDir)
        self.__monitordb.setSensorCheckInterval(SENSOR_UPDATE_INTERVAL)

    def startDB(self):
        self.__monitordb.startTimer()

    def startUpdateTimers(self):
        self.__mainenance_timer = GracefulTimer(MAINTENANCE_INTERVAL, \
                                    self.runMaintenanceTasks, True)
        self.__mainenance_timer.start()
        self.__host_check_timer = GracefulTimer(HOST_CHECK_INTERVAL, \
                                    self.updateHostStatus, True)
        self.__host_check_timer.start()
        self.__update_timer = GracefulTimer(SENSOR_UPDATE_INTERVAL, \
                                    self.updateNodeInfo, True)
        self.__update_timer.start()

class MonitorDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    __bind_addr = DaemonLocations.monitorDaemon[0]
    __port = DaemonLocations.monitorDaemon[1]
    __sockd = None
    __monitor = None
    __monitor_db_dir = None

    def __init__(self, doFork):
        Daemonizer.__init__(self, doFork)

    def run(self):
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        self.__sockd.settimeout(2) # 2 second timeouts
        log.debug("Creating Monitor")
        self.__monitor = Monitor()
        log.info("Starting DB")
        self.__monitor.setDBDirectory(self.__monitor_db_dir)
        self.__monitor.startDB()
        log.info("Starting Monitor")
        self.__monitor.startUpdateTimers()
        self.__monitor.start()
        while self.__monitor.isAlive():
            if self.__monitor.acceptingConnections():
                # allow timeout of accept() to avoid blocking a shutdown
                try:
                    (s,a) = self.__sockd.accept()
                    log.debug("New connection established from " + str(a))
                    self.__monitor.addSocket(s)
                except:
                    pass
            else:
                log.warning(\
                        "Monitor still alive, but not accepting connections")
                time.sleep(2)
        log.debug("Closing socket.")
        self.__sockd.shutdown(socket.SHUT_RDWR)
        self.__sockd.close()
        while threading.activeCount() > 1:
            cThreads = threading.enumerate()
            log.warning("Waiting on " + str(threading.activeCount()) + \
                      " active threads...")
            time.sleep(2)
        log.info("MonitorDaemon Finished.")
        # Now everything is dead, we can exit.
        sys.exit(0)

    def setDBDirectory(self, dbDir):
        self.__monitor_db_dir = dbDir

def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    WORKDIR = '/var/hen/monitordaemon'
    PIDDIR = '/var/run/hen'
    LOGDIR = '/var/log/hen/monitordaemon'
    LOGFILE = 'monitordaemon.log'
    PIDFILE = 'monitordaemon.pid'
    DBDIR = '%s/monitordb' % WORKDIR
    GID = 17477 # schooley
    UID = 17477 # schooley
    monitord = MonitorDaemon(True)
    monitord.setWorkingDir(WORKDIR)
    monitord.setPIDDir(PIDDIR)
    monitord.setLogDir(LOGDIR)
    monitord.setDBDirectory(DBDIR)
    monitord.setLogFile(LOGFILE)
    monitord.setPidFile(PIDFILE)
    monitord.setUid(UID)
    monitord.setGid(GID)
    monitord.start()

if __name__ == "__main__":
    main()
