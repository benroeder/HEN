from auxiliary.monitord.workertask import *
from auxiliary.monitord.monitordb import MonitorDB
from auxiliary.monitord.checksensortask import CheckSensorTask
from auxiliary.protocol import Protocol
from auxiliary.daemonlocations import DaemonLocations
from auxiliary.daemonstatus import DaemonStatus

import threading, time, logging, commands

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# length of time a worker thread will sleep before checking for work
WORKERTHREAD_SLEEP_TIME = 0.5
# The time in seconds between the scheduled time of the next task and that
# of current time. If this decay time is exceeded, the worker threads are
# stalling on something. In order not to fill the queue with old tasks, the
# queue will be cleared if the decay time is hit.
TASK_DECAY_TIME = 300
# Maximum number of tasks a worker can have queued. This is only in case tasks
# take too long to complete (i.e. if named dies)
MAX_WORKER_TASKS = 50
# Command to use for ipmiping
IPMIPING_COMMAND = '/usr/local/sbin/ipmiping -c 1 -t 5 '
# Command to use for pinging
PING_COMMAND = 'ping -c 1 -t 3 -q '
# Time to wait before giving up on sensor reading
SENSOR_READING_TIMEOUT = 30

POWER_STATUS_TIMEOUT = 5

class WorkerThread(threading.Thread):
    __worker_number = None
    __hen_manager = None
    __monitordb = None
    __tasks = None
    __stop = None
    __workDone = None
    __powerStatusCallbackEvent = None
    __powerResults = None

    def __init__(self, workerNumber, monitorDB):
        threading.Thread.__init__(self)
        self.__worker_number = workerNumber
        self.__monitordb = monitorDB
        self.__tasks = []
        self.__stop = threading.Event()
        self.__powerStatusCallbackEvent = threading.Event()

    def stop(self):
        if self.__workDone:
            self.__workDone.set()
        self.__stop.set()

    def run(self):
        while not self.__stop.isSet():
            if len(self.__tasks) > 0:
                task = self.__tasks.pop()
                self.doTask(task)
                del task
            else:
                self.__stop.wait(WORKERTHREAD_SLEEP_TIME)

    def runTaskQueueMaintenance(self):
        if len(self.__tasks) > 0:
            if (int(time.time()) - self.__tasks[0].timeScheduled) > \
                TASK_DECAY_TIME:
                log.critical("WorkerThread[" + str(self.__worker_number) + \
                     "] wiped task queue due to task decay. This means the" + \
                     " previos task took more than " + str(TASK_DECAY_TIME) + \
                     "seconds to complete!")
                del self.__tasks[:]
                self.__tasks = []

    def addTask(self, task):
        if len(self.__tasks) < MAX_WORKER_TASKS:
            self.__tasks.append(task)
        else:
            log.critical("WorkerThread[" + str(self.__worker_number) + \
                     "] reached scheduled task queue limit. Task dropped.")
            del task

    def hasWork(self):
        if len(self.__tasks) > 0:
            return True
        else:
            return False

    def setHenManager(self, hm):
        self.__hen_manager = hm

    def doTask(self, task):
        if task.taskid == TaskID.checkSensorTask:
            self.checkNodeSensors(task.node, task.nodeinstance, \
                                  task.timeScheduled)
        elif task.taskid == TaskID.hostStatusTask:
            self.checkHostStatus(task.node)
        else:
            log.critical("WorkerThread.doTask() found unknown taskid [" + \
                         str(task.taskid) + "]")

    def checkHostStatus(self, node):
        (status, output) = \
                commands.getstatusoutput(PING_COMMAND + str(node.getNodeID()))
        if status == 0:
            self.__monitordb.setHostStatus(node.getNodeID(), \
                                           self.__monitordb.HOSTONLINE)
        else:
            self.__monitordb.setHostStatus(node.getNodeID(), \
                                           self.__monitordb.HOSTOFFLINE)

    def checkNodeSensors(self, node, nodeInstance, timeScheduled):
        if not self.nodeIsReachable(node):
            return
        try:
            """
            Check to see if the node is up. First check the service processor
            if one is used, as it's a quick and simple test. If not using a SP,
            check if the power status is "on". If that fails, just see if we
            can ping the host.
            """
            sensorReadings = None
            self.__workDone = threading.Event()
            sensorWorker = None
            sensorWorker = CheckSensorTask(nodeInstance, self.__workDone)
            sensorWorker.start()
            self.__workDone.wait(SENSOR_READING_TIMEOUT)
            (sensorDescriptions, sensorReadings) = \
                                        sensorWorker.getSensorReadings()
            if sensorReadings != None and sensorDescriptions != None:
                self.writeToDB(node.getNodeID(), sensorReadings, \
                      sensorDescriptions, int(time.time()))
        except Exception, e:
            log.debug("checkNode(" + node.getNodeID() + \
                      "): Exception: " + str(e))
            pass

    def nodeIsReachable(self, node):
        """\brief Checks whether a node can be reached.
            This is acheived by checking both power status and pinging.
            It is assumed that the SP or host replies to [ipmi]pinging.
        """
        if node.getNodeType() == "computer": # Special case for SPs)
            if self.serviceProcessorIsOn(node.getSPNodeID()) > 0:
                return True
            else:
                return False
        # If we're here, we have a node that probably doesn't have a well
        # defined power state. Lets try power status, and pinging
        powerStatus = self.nodeIsOn(node)
        
        # Power status might be "on", but can we ping/ipmiping ?
        pingStatus = self.__monitordb.getHostStatus(node.getNodeID())
        if pingStatus == -1: # Node hasn't had it's status checked yet.
            self.checkHostStatus(node)
            pingStatus = self.__monitordb.getHostStatus(node.getNodeID())
        if (powerStatus > 0) or (pingStatus > 0):
            return True
        return False

    def serviceProcessorIsOn(self, spid):
        """\brief Uses ipmiping to check whether serviceprocessor is up
        \param spid - service processor id
        \return result - 0 = off, 1 = on
        """
        (status, output) = commands.getstatusoutput( \
                            IPMIPING_COMMAND + spid)
        if status != 0:
            return 0
        return 1

    def nodeIsOn(self, node):
        """\brief Checks if given node is on.
        \param nodeInstance - Instance of node to check
        \return result - 0 = off, 1 = on, -1 = unknown/unsupported
        XXX TODO: Use powerd for query, removing dependance on having a ref to
                    henmanager
        XXX Small leaking here, as powerSilent creates node instances...
        """
        self.__powerStatusCallbackEvent.clear()
        p = Protocol(None)
        if DaemonStatus().powerDaemonIsOnline(5):
            p.open(DaemonLocations.monitorDaemon[0], \
                   DaemonLocations.monitorDaemon[1])
            p.sendRequest("get_power_status", node.getNodeID(), \
                          self.powerStatusHandler)
            p.readAndProcess()
            self.__powerStatusCallbackEvent.wait(POWER_STATUS_TIMEOUT)
            p.close()
        try:
            pnodeid = node.getPowerNodeID()
            if (pnodeid == "None" or pnodeid == "none"):
                return -1
            if self.__powerResults:
                (st,msg) = (0, self.__powerResults)
            else:
                (st,msg) = self.__hen_manager.powerSilent(node.getNodeID(), \
                                                          "status", pnodeid)
            if (st == 0 and msg == "on"):
                return 1
            if (st == 0 and msg == "off"):
                return 0
        except Exception, e:
            log.debug("nodeIsOn Exception: %s" % str(e))
        return -1

    def powerStatusHandler(self,code,seq,size,payload):
        if code == 200:
            self.__powerResults = payload
        if (code != 200) or (len(payload) == 0):
            self.__powerResults = None            
        self.__powerStatusCallbackEvent.set()
        
    def writeToDB(self, nodeid, sensorReading, sensor_descriptions, timeRead):
        """\brief Writes a dictionary of sensor readings to the monitor db file.
        """
        for sensorType in sensorReading.keys():
            for sensorid in sensorReading[sensorType].keys():
                reading = (sensorReading[sensorType])[sensorid]
                if reading == -1:
                    continue # Ignore disabled or non-functional sensors
                if (sensor_descriptions[sensorType]).has_key(sensorid):
                    result = self.__monitordb.writeMonitorValue( \
                                nodeid, sensorid, sensorType, \
                                timeRead, reading, \
                                (sensor_descriptions[sensorType])[sensorid])
                    # TODO: Handle alarms/warnings
                    if result == 2:
                        msg = "Sensor [" + sensorid + \
                                            "] on Node [" + nodeid + \
                                            "] reads CRITICAL!"
                        self.sendEmailAlert("CRITICAL", \
                                            "t.schooley@cs.ucl.ac.uk", msg)
                        log.critical(msg)
                    elif result == 1:
                        msg = "Sensor [" + sensorid + \
                                "] on Node [" + nodeid + \
                                "] is approaching CRITICAL!"
                        self.sendEmailAlert("WARNING", \
                                            "t.schooley@cs.ucl.ac.uk", msg)
                        log.warning(msg)
                else:
                    log.critical("writeToDB(): have reading for sensor with" + \
                         "no critical value! (NodeID[" + node.getNodeID() + \
                         "], SensorID[" + sensorid + "])")
        pass

    def sendEmailAlert(self, alertLevel, recipient, alertMessage):
        subject = "\"[HEN] Monitor Daemon Alert Message\""
        msg = "==== Monitor Daemon Alert Message ====\n" + \
              "Alert Time: " + str(time.localtime()) + "\n" \
              "Alert Level: " + alertLevel + "\n" + \
              "Alert Message: " + alertMessage + "\n"
        # quick hack - just stuff it in a file
        emailfile = open(self.__monitordb.__db_dir + 'warnings', 'a')
        emailfile.write(msg)
        emailfile.close()
        log.critical(msg)
        """
        cmdpipe = os.popen("%s -t" % SENDMAIL, "w")
        cmdpipe.write("To: " + recipient + "\n")
        cmdpipe.write("Subject: " + subject + "\n")
        cmdpipe.write("\n")
        cmdpipe.write(msg)
        status = cmdpipe.close()
        if status != 0:
            log.critical("WARNING: SENDING OF ALERT EMAIL FAILED!")
        """

    def getTaskQueueSize(self):
        return len(self.__tasks)
