#!/usr/local/bin/python

#######################
# TODO
# add vlan deletion by name
########################

import sys, os
#sys.path.append("/usr/local/hen/lib")

import logging
import threading
import socket
import pickle
import commands
import re
import pydot
from daemonizer import Daemonizer
from daemon import Daemon
from henmanager import HenManager
from auxiliary.daemonlocations import DaemonLocations
from auxiliary.hen import Port
from auxiliary.hen import VLAN
from auxiliary.timer import GracefulTimer
from auxiliary.switchd.switchdb import SwitchDB
from auxiliary.switchd.workertask import *
from auxiliary.switchd.workerthread import *

# length of time a worker thread will sleep before checking for work
WORKERTHREAD_SLEEP_TIME = 2
# seconds between queries to all sensor nodes for new data
FDB_UPDATE_INTERVAL = 300
# Number of worker threads created by monitor daemon
NUM_WORKER_THREADS = 5
# Time to wait before removing a mac entry
FDB_TIMEOUT = 600
# maintenance scheduling interval
MAINTENANCE_INTERVAL = 600
# seconds between host checks
HOST_CHECK_INTERVAL = 300
# seconds between link checks
LINK_CHECK_INTERVAL = 300
# seconds between network map generations
NETWORK_MAP_GENERATION_INTERVAL = 300

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

class SwitchMonitor(Daemon):
    """\brief Implements basic switch monitor functionality.
    """
    __version = "Switch Monitor v0.2 (simple)"
    __henManager = None
    __update_timer = None
    __update_lock = threading.Lock()
    __fdb_timer = None
    __fdb_lock = threading.Lock()
    __accept_connections = True
    __worker_threads = {}
    __switchdb = None
    __nodeInstances = None
    __pingchecknodes = None
                                        
    def __init__(self):
        Daemon.__init__(self)
        # Initalise variables
        self.__henManager = HenManager()
        self.__nodes = None
        self.__vlans = {} # 
        self.__vlan_info = {} # switch_name -> [vlan_name,vlan_name,...]
        self.__switch_instances = {}
        self.__debug = False
        
        self.__switchdb = SwitchDB()
        log.debug("Switchdb "+str(self.__switchdb))
        # Register hen rpc methods and handlers
        log.debug("Registering methods")
        self.__registerMethods()
        # Setup mac polling
        log.debug("Loading henmanager")
        self.__switchdb.setHenManager(self.__henManager)
        log.debug("Loading links Db")
        self.__switchdb.loadLinksDb()
        log.debug("Initiating Nodes")
        self.initiateNodes()

        for workerNumber in range(NUM_WORKER_THREADS):
            self.__worker_threads[workerNumber] = WorkerThread(workerNumber, \
                                                               self.__switchdb)
            self.__worker_threads[workerNumber].setHenManager(self.__henManager)
            self.__worker_threads[workerNumber].start()
                                                                        
        
    def __registerMethods(self):
        # mac detection stuff
        self.registerMethodHandler("find_mac", self.findMAC)
        self.registerMethodHandler("find_unique_macs", self.findUniqueMACs)
        self.registerMethodHandler("show_macs", self.showMACs)
        self.registerMethodHandler("redetect_fdb", self.redetectFDB)
        self.registerMethodHandler("dump_switchdb", self.dumpSwitchDB)
        # network topology mac
        self.registerMethodHandler("create_network_svg", self.createNetworkSvg)
        # testing
        self.registerMethodHandler("run_task", self.runTask)
        
    def __sendReply(self,prot,code,seq,payload):
        if (code == 0):
            code = 200
        else:
            code = 422 # returnCodes[422] = "error executing command"
        prot.sendReply(code, seq, payload)

    def __getNodes(self):
        self.__nodes = self.__henManager.getNodes("all")

    def __getComputer(self, computer_str):
        if self.__nodes == None:
            self.__getNodes()
        for node_type in self.__nodes:
            for node in self.__nodes[node_type]:
                if self.__nodes[node_type][node].getNodeID() == computer_str:
                    return self.__nodes[node_type][node]
        return None

    def __getSwitchLocation(self, computer, interface_str):
        interfaces = computer.getInterfaces()
        for interface_type in interfaces:
            for iface in interfaces[interface_type]:
                if iface.getInterfaceID() == interface_str:
                    return (iface.getSwitch(), iface.getPort())
        return (None,None)

    def showMACs(self,proto,seq,ln,payload):
        log.debug("showMACs called.")
        res = self.__switchdb.dumpFdb()
        log.debug(res)
        proto.sendReply(200,seq,res)

    # monitoring code
    def findMAC(self,proto,seq,ln,payload):
        log.debug("findMAC called.")
        res = self.__switchdb.findMAC(payload.upper())
        log.debug(res)
        proto.sendReply(200,seq,res)

    def findUniqueMACs(self,proto,seq,ln,payload):
        log.debug("findUniqueMACs called.")
        print "updating fdb info", self.__switchdb
        macs = pickle.loads(payload)
        self.updateSwitchFdb();

        res = {}
        for m in macs:
            mac = m.upper()
            entry = self.__switchdb.locateMac(mac,True)
            if entry == None:
                res[mac] = [("None","None")]
            else:
                res[mac] = entry
        log.debug(res)
        proto.sendReply(200,seq,pickle.dumps(res))
        
    def redetectFDB(self,proto,seq,ln,payload):
        self.updateFDBInfo();
        payload = "running"
        proto.sendReply(200, seq, payload)
        
    def dumpSwitchDB(self,proto,seq,ln,payload):
        if payload == "unique":
            payload = str(self.__switchdb.dumpFdb(True))
        else:
            payload = str(self.__switchdb.dumpFdb())
        proto.sendReply(200, seq, payload)
        
    def createNetworkSvg(self,proto,seq,ln,payload):
        payload = (self.__switchdb.createNetworkSvg())
        proto.sendReply(200, seq, payload)

    def runTask(self,proto,seq,ln,payload):
        if payload == "updateHostStatus":
            log.debug("updateHostStatus")
            self.updateHostStatus()
            payload = "success"
        elif payload == "updateSwitchFdb":
            log.debug("updateSwitchFdb")
            self.updateSwitchFdb()
            payload = "success"
        elif payload == "updateLinkStatus":
            log.debug("updateLink")
            self.updateLinkStatus()
            payload = "success"
        elif payload == "updateHostStatus":
            log.debug("updateHostStatus")
            self.updateHostStatus()
            payload = "success"
        elif payload == "networkMapGeneration":
            log.debug("networkMapGeneration")
            self.networkMapGeneration()
            payload = "success"

        else:
            payload = "failure"
        proto.sendReply(200, seq, payload)

    def initiateNodes(self):
        """\brief Creates a {nodeid:(node,nodeinstance)} dictionary for sensor
        readings, and a {nodeid:node} dictionary for host ping checking.
        """
        log.debug("Creating NodeInstance map")
        self.__nodeInstances = {}
        self.__pingchecknodes = {}
        nodes = self.__henManager.getNodes("all", "all")
        
        for nodeType in nodes.keys():
            if nodeType != "switch" :
                continue
            nodeTypes = nodes[nodeType]
            for node in nodeTypes.values():
                if node.getStatus() != "operational":
                    continue
                elif node.getVendor() != "force10" and node.getVendor() != "linksys" :
                    log.debug("Not creating instance for node [%s]" % \
                              str(node.getNodeID())) 
                    continue
                #self.__pingchecknodes[node.getNodeID()] = node
                
                try:
                    
                    self.__nodeInstances[node.getNodeID()] = \
                                                           (node, node.getInstance())
                    log.debug("Created instance for node [%s]" % \
                              str(node.getNodeID()))
                except Exception, e:
                    log.debug("Creating node instance failed for node [%s]: %s" % (str(node.getNodeID()), str(e)))
        log.debug("initiateNodes() completed. NodeInstances[%s], Nodes[%s]" % \
                  (str(len(self.__nodeInstances.keys())), \
                   str(len(self.__pingchecknodes.keys()))))
        counter = 0
        for nodeid in self.__nodeInstances.keys():
            log.debug("[%s] %s" % (str(counter), nodeid))
            counter += 1

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
            if taskid == TaskID.switchReadFdbTask:
                taskCount = self.scheduleSwitchReadFdbChecks(taskid)
                log.debug("scheduleSwitchReadFdbChecks: %s tasks scheduled." %\
                          str(taskCount))
            elif taskid == TaskID.hostStatusTask:
                taskCount = self.scheduleHostPingChecks(taskid)
                log.debug("scheduleHostPingChecks: %s tasks scheduled." % \
                          str(taskCount))
            elif taskid == TaskID.linkStatusTask:
                taskCount = self.scheduleLinkStatusChecks(taskid)
                log.debug("scheduleLinkStatusChecks: %s tasks scheduled." % \
                          str(taskCount))
            elif taskid == TaskID.networkMapGenerationTask:
                taskCount = self.scheduleNetworkMapGeneration(taskid)
                log.debug("scheduleLinkStatusChecks: %s tasks scheduled." % \
                          str(taskCount))
            else:
                log.critical(
                    "Monitor.scheduleTasks() found unknown taskid [%s]" % \
                    str(task.taskid))
            log.debug("scheduleTasks(): Releasing update lock.")
            self.__update_lock.release()
            
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

    def scheduleLinkStatusChecks(self, taskid):
        """\brief Schedules link status checks"""
        workerNumber = self.chooseNextWorker()
        taskCount = 0
        links = self.__switchdb.getLinks()
        for linkid in links.keys():
            link = links[linkid]
            timeScheduled = int(time.time())
            task = WorkerTask(linkid, link, taskid, timeScheduled)
            self.__worker_threads[workerNumber].runTaskQueueMaintenance()
            taskCount += 1
            self.__worker_threads[workerNumber].addTask(task)
            workerNumber = self.chooseNextWorker()
        return taskCount

    def scheduleNetworkMapGeneration(self, taskid):
        """\brief Schedules generation of the network map"""
        workerNumber = self.chooseNextWorker()
        taskCount = 1
        timeScheduled = int(time.time())
        task = WorkerTask(None, None, taskid, timeScheduled)
        self.__worker_threads[workerNumber].runTaskQueueMaintenance()
        self.__worker_threads[workerNumber].addTask(task)
        return taskCount
        
    def scheduleSwitchReadFdbChecks(self, taskid):
        """\brief Schedules reading a switch fdb"""
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
                                                    
        
    def updateHostStatus(self):
        """\brief Initiates a host check of all HEN nodes"""
        log.debug("updateHostStatus() called.")
        self.scheduleTasks(TaskID.hostStatusTask)

    def updateLinkStatus(self):
        """\brief Initiates a link check of all HEN links"""
        log.debug("updateLinkStatus() called.")
        self.scheduleTasks(TaskID.linkStatusTask)

    def updateSwitchFdb(self):
        """\brief Initiates a switch fdb fetch"""
        log.debug("updateSwitchFdb() called.")
        self.scheduleTasks(TaskID.switchReadFdbTask)

    def networkMapGeneration(self):
        """\brief Initiates a task to generate the network map"""
        log.debug("networkMapGeneration() called.")
        self.scheduleTasks(TaskID.networkMapGenerationTask)

    def startUpdateTimers(self):
        # Setup and start maintence timers
        self.__maintenance_timer = GracefulTimer(MAINTENANCE_INTERVAL, \
                                                self.runMaintenanceTasks, True)
        if not self.__debug :
            self.__maintenance_timer.start()

        # Setup and start forward database polling timers
        self.__fdb_timer = GracefulTimer(FDB_UPDATE_INTERVAL, \
                                         self.updateSwitchFdb, True)
        if not self.__debug :
            self.__fdb_timer.start()

        # Check whether switches are up
        #self.__host_check_timer = GracefulTimer(HOST_CHECK_INTERVAL, \
        #                                        self.updateHostStatus, True)
        #if not self.__debug :
        #    self.__host_check_timer.start()

        # Check the status of links
        #self.__link_check_timer = GracefulTimer(LINK_CHECK_INTERVAL, \
        #                                        self.updateLinkStatus, True)
        #if not self.__debug :
        #    self.__link_check_timer.start()

        # Create network map
        #self.__network_map_generation_timer = GracefulTimer(NETWORK_MAP_GENERATION_INTERVAL, self.networkMapGeneration, True)
        #if not self.__debug :
        #    self.__network_map_generation_timer.start()
        

    def runMaintenanceTasks(self):
        """\brief Method run by maintenance timer. Use this for miscellaneous
        tasks that need running periodically. Refer to MAINTENANCE_INTERVAL
        for the scheduled period.
        """
        self.__switchdb.cleanFdb()
        #self.logResourceUsage()    
    
    ## Internal methods
        
    def updateFDBInfo(self):
        """\brief Initiates a new scan of sensor readings. This method hands off
        the checking of sensor readings to all available worker threads, which
        in turn handle writing of data to file.
        """
        # Don't start a new update if shutting down (not accepting connections)
        if self.__accept_connections:
            self.__update_lock.acquire()
            for worker in self.__switch_worker_threads.values():
                log.debug("readFDB")
                worker.addTask(worker.readFDB)
            self.__update_lock.release()

    def acceptingConnections(self):
        """\brief To question whether the monitor is accepting connections"""
        return self.__accept_connections
    
    def setDBDirectory(self, dbDir):
        self.__switchdb.setDBDirectory(dbDir)
        
    def startDB(self):
        self.__switchdb.startTimer()
                                                


    
    ## Library functions

    # Given a switch name, return a switch object
    def __getSwitchInstance(self,switch_str):
        if self.__switch_instances.has_key(switch_str):
            return self.__switch_instances[switch_str]
        if self.__nodes == None:
            self.__getNodes()
        for node_type in self.__nodes:
            for node in self.__nodes[node_type]:
                if self.__nodes[node_type][node].getNodeID() == switch_str:
                    switch = self.__nodes[node_type][node]
                    if (switch.getStatus() == "operational" ): #and switch_str =="switch14"):
                        switch_obj = switch.getInstance()
                    else:
                        log.debug("Not creating an instance of "+str(switch_str))
                        return (None,None)
                    self.__switch_instances[switch_str] = (switch,switch_obj)
                    if not self.__vlans.has_key(switch_str):
                        self.__vlans[switch_str] = None
                        try:
                            self.__vlan_info[switch_str] = switch_obj.getVlanInfo()
                        except:
                            pass
                    return (switch, switch_obj)
        return (None,None)

    def __getDeviceObjects(self,computer_str, interface_str):
        computer = self.__getComputer(computer_str)
                
        if computer == None:
            log.info("Computer "+computer_str+" doesn't exist.")
            return (None, None, None, None, None)

        (switch_str, port_str) = self.__getSwitchLocation(computer,interface_str)
        if switch_str == "":
            log.info("Switch not found for computer "+computer_str+" interface "+interface_str)
            return (None, None, None, None, None)
        
        (switch, switch_obj) = self.__getSwitchInstance(switch_str)
        
        if switch_obj == None:
            log.info("Can't create switch instance for "+switch_str)
            return (None, None, None, None, None)

        return (computer, switch_str, switch, switch_obj, port_str)


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
        log.debug("Stopping update timer")
        self.__update_timer.stop()
        log.debug("Releasing update lock")
        self.__update_lock.release()
        log.info("Stopping SwitchMonitor (self)")
        self.stop()

class SwitchMonitorDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    __bind_addr = DaemonLocations.switchMonitorDaemon[0]
    __port = DaemonLocations.switchMonitorDaemon[1]
    __sockd = None
    __switchmonitor = None

    def __init__(self, doFork):
        Daemonizer.__init__(self, doFork)

    def run(self):
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        self.__sockd.settimeout(2) # 2 second timeouts
        log.debug("Creating SwitchMonitor")
        self.__switchmonitor = SwitchMonitor()
        log.debug("Starting DB")
        self.__switchmonitor.setDBDirectory(self.__switch_db_dir)
        self.__switchmonitor.startDB()
        self.__switchmonitor.startUpdateTimers()
        log.info("Starting SwitchMonitor")
        self.__switchmonitor.start()
        while self.__switchmonitor.isAlive():
            if self.__switchmonitor.acceptingConnections():
                # allow timeout of accept() to avoid blocking a shutdown
                try:
                    (s,a) = self.__sockd.accept()
                    log.debug("New connection established from " + str(a))
                    self.__switchmonitor.addSocket(s)
                except:
                    pass
            else:
                log.warning(\
                      "SwitchMonitor still alive, but not accepting connections")
                time.sleep(2)
        log.debug("Closing socket.")
        self.__sockd.shutdown(socket.SHUT_RDWR)
        self.__sockd.close()
        while threading.activeCount() > 1:
            cThreads = threading.enumerate()
            log.warning("Waiting on " + str(threading.activeCount()) + \
                        " active threads...")
            time.sleep(2)
        log.info("SwitchMonitor Finished.")
        # Now everything is dead, we can exit.
        sys.exit(0)

    def setDBDirectory(self, dbDir):
        self.__switch_db_dir = dbDir
                    

def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    WORKDIR = '/var/hen/switchmonitor'
    PIDDIR = '/var/run/hen'
    LOGDIR = '/var/log/hen/switchmonitor'
    LOGFILE = 'switchmonitor.log'
    PIDFILE = 'switchmonitor.pid'
    DBDIR = '%s/switchdb' % WORKDIR    
    GID = 18122 # hen
    UID = 18122 # root
    switchd = SwitchMonitorDaemon(False)
    switchd.setWorkingDir(WORKDIR)
    switchd.setDBDirectory(DBDIR)
    switchd.setPIDDir(PIDDIR)
    switchd.setLogDir(LOGDIR)
    switchd.setLogFile(LOGFILE)
    switchd.setPidFile(PIDFILE)
    switchd.setUid(UID)
    switchd.setGid(GID)
    switchd.start()

if __name__ == "__main__":
    main()
