from auxiliary.switchd.workertask import *
from auxiliary.switchd.switchdb import SwitchDB
from auxiliary.switchd.readswitchfdbtask import ReadSwitchFdbTask
from auxiliary.switchd.linkstatustask import LinkStatusTask
from auxiliary.protocol import Protocol
from auxiliary.daemonlocations import DaemonLocations
from auxiliary.daemonstatus import DaemonStatus

import threading, time, logging, commands, traceback, sys

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# length of time a worker thread will sleep before checking for work
WORKERTHREAD_SLEEP_TIME = 0.5
# The time in seconds between the scheduled time of the next task and that
# of current time. If this decay time is exceeded, the worker threads are
# stalling on something. In order not to fill the queue with old tasks, the
# queue will be cleared if the decay time is hit.
TASK_DECAY_TIME = 60
# Maximum number of tasks a worker can have queued. This is only in case tasks
# take too long to complete (i.e. if named dies)
MAX_WORKER_TASKS = 50
# Command to use for ipmiping
IPMIPING_COMMAND = '/usr/local/sbin/ipmiping -c 1 -t 5 '
# Command to use for pinging
PING_COMMAND = 'ping -c 1 -t 3 -q '
# Time to wait before giving up on sensor reading
SENSOR_READING_TIMEOUT = 30
# Time to wait before giving up on sensor reading
POWER_STATUS_TIMEOUT = 5
# Time to wait before giving up on reading the fdb
FDB_READING_TIMEOUT = 30
# Time to wait before giving up on checking a link status
LINK_STATUS_TIMEOUT = 30

class WorkerThread(threading.Thread):
    __worker_number = None
    __hen_manager = None
    __switchdb = None
    __tasks = None
    __stop = None
    __workDone = None
    __powerStatusCallbackEvent = None
    __powerResults = None

    def __init__(self, workerNumber, switchdB):
        threading.Thread.__init__(self)
        self.__worker_number = workerNumber
        self.__switchdb = switchdB
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
                critical_msg = "WorkerThread[" + str(self.__worker_number) + \
                     "] wiped task queue due to task decay. This means the" + \
                     " previos task took more than " + str(TASK_DECAY_TIME) + \
                     " seconds to complete! "
                for i in self.__tasks:
                    critical_msg += " "+str(i)
                log.critical(critical_msg)
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
        elif task.taskid == TaskID.linkStatusTask:
            self.checkLinkState(task.node, task.nodeinstance, \
                                task.timeScheduled)
        elif task.taskid == TaskID.switchReadFdbTask:
            self.readSwitchFdb(task.node, task.nodeinstance, \
                                  task.timeScheduled)
        elif task.taskid == TaskID.hostStatusTask:
            self.checkHostStatus(task.node)
        elif task.taskid == TaskID.networkMapGenerationTask:
            self.networkMapGeneration()
        else:
            log.critical("WorkerThread.doTask() found unknown taskid [" + \
                         str(task.taskid) + "]")

    def networkMapGeneration(self):
        self.__switchdb.networkMapGeneration()
    
    def checkHostStatus(self, node):
        (status, output) = \
                commands.getstatusoutput(PING_COMMAND + str(node.getNodeID()))
        if status == 0:
            log.debug("checkHostStatus "+str(node.getNodeID())+" is online")
            self.__switchdb.setHostStatus(node.getNodeID(), \
                                          self.__switchdb.HOSTONLINE)
        else:
            log.debug("checkHostStatus "+str(node.getNodeID())+" is offline")
            self.__switchdb.setHostStatus(node.getNodeID(), \
                                          self.__switchdb.HOSTOFFLINE)

    def checkLinkState(self, linkid, link, timeScheduled):
        try:
            newlink = None
            self.__workDone = threading.Event()
            linkWorker = None
            linkWorker = LinkStatusTask(linkid, link, self.__hen_manager, self.__switchdb, self.__workDone)
            linkWorker.start()
            self.__workDone.wait(LINK_STATUS_TIMEOUT)
            newlink = linkWorker.getLinkState()
            if newlink != None:
                self.__switchdb.setLink(linkid,newlink)
        except Exception, e:
            log.debug("checkLink(" + linkid + \
                      "): Exception: " + str(e))
            pass
                                
            
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

    def readSwitchFdb(self, node, nodeInstance, timeScheduled):
        if not self.nodeIsReachable(node):
            return
        try:
            """
            Check to see if the node is up. First check the service processor
            if one is used, as it's a quick and simple test. If not using a SP,
            check if the power status is "on". If that fails, just see if we
            can ping the host.
            """
            fdbReadings = None
            self.__workDone = threading.Event()
            switchWorker = None
            switchWorker = ReadSwitchFdbTask(nodeInstance, self.__workDone)
            switchWorker.start()
            self.__workDone.wait(FDB_READING_TIMEOUT)
            macTable = switchWorker.getMacTable()
            if macTable != None:
                self.writeToDB(node.getNodeID(), macTable, int(time.time()))
                #print (node.getNodeID(), int(time.time()))
                #for mt in macTable:
                #    print "mac 0adas ",mt,
            else:
                log.critical("Empty mac table from "+node.getNodeID())
        except Exception, e:
            log.debug("checkNode(" + node.getNodeID() + \
                      "): Exception: " + str(e))
            pass

    def writeToDB(self, nodeid, macTable, timeRead):
        """\brief Writes a dictionary of fdb to the switch db file.
        """
        #if (nodeid == "switch14"):
        #    log.debug("switch14 stuff")

#        log.debug("Writing "+str(nodeid)+" to switchdb of len "+str(len(macTable)))
        print macTable
        for mac in macTable:
            s = "node id "+str(nodeid)+"\n"
            if (nodeid == "switch14"):
                s += "Entry "+str(nodeid)+" : "+str(mac)+"\n"
            try:
                self.__switchdb.writeFdbEntry(nodeid,mac[0],mac[1],timeRead)
            except Exception, e:
                print "some error",e,s
                traceback.print_exc(file=sys.stdout)
        #if (nodeid == "switch14"):
        #    print s
        #self.__switchdb.dumpFdb()
        #self.__switchdb.dumpUnknownFdb()

    def nodeIsReachable(self, node):
        """\brief Checks whether a node can be reached.
            This is acheived by checking both power status and pinging.
            It is assumed that the SP or host replies to [ipmi]pinging.
        """
        # If we're here, we have a node that probably doesn't have a well
        # defined power state. Lets try power status, and pinging
        powerStatus = self.nodeIsOn(node)
        
        # Power status might be "on", but can we ping/ipmiping ?
        pingStatus = self.__switchdb.getHostStatus(node.getNodeID())
        if pingStatus == -1: # Node hasn't had it's status checked yet.
            self.checkHostStatus(node)
            pingStatus = self.__switchdb.getHostStatus(node.getNodeID())
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
            p.open(DaemonLocations.switchDaemon[0], \
                   DaemonLocations.switchDaemon[1])
            p.sendRequest("get_power_status", node.getNodeID(), \
                          self.powerStatusHandler)
            p.readAndProcess()
            self.__powerStatusCallbackEvent.wait(POWER_STATUS_TIMEOUT)
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
        
    def getTaskQueueSize(self):
        return len(self.__tasks)
