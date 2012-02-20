#!/usr/local/bin/python
import sys
sys.path.append("/usr/local/hen/lib")

from daemonizer import Daemonizer
from daemon import Daemon
from auxiliary.timer import GracefulTimer
from auxiliary.daemonlocations import DaemonLocations
from auxiliary.daemonstatus import DaemonStatus
from auxiliary.protocol import Protocol
import os, logging, threading, time, socket

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# seconds between checks
CHECKER_INTERVAL = 60
STATUS_TIMEOUT = 10

class DaemonStatusChecker(threading.Thread):
    
    __checkMethod = None
    __stopEvent = None
    __doneEvent = None
    __daemonStatus = None
    __timeout = None
    
    def __init__(self, checkMethod, doneEvent, timeout=3):
        threading.Thread.__init__(self)
        self.__checkMethod = checkMethod
        self.__stopEvent = threading.Event()
        self.__doneEvent = doneEvent
        self.__timeout = timeout
        self.__daemonStatus = False
    
    def run(self):
        self.__daemonStatus = self.__checkMethod(self.__timeout)
        self.__doneEvent.set()
        
    def isOnline(self):
        self.__stopEvent.set()
        return self.__daemonStatus

class HenStatusChecker(Daemon):
    """
    \brief Implements the StatusDaemon external interface
    This class contains the methods called when requests are recieved by the
    Daemon (inherited).
    """
    __version = "Hen Status Daemon v0.1"
    __checker_timer = None
    __checker_lock = None

    __stoppedDaemons = None
    __runningDaemons = None
    __checkerThreads = None
    __doneList = None
    
    __cli_commands_xml = None
    __cli_commands = None

    def __init__(self):
        """\brief Registers remote methods and starts update thread (timer)
        """
        Daemon.__init__(self)
        self.__registerMethods()
        self.__checker_lock = threading.Lock()

        self.__stoppedDaemons = []
        self.__runningDaemons = []
        self.__checkerThreads = {}
        self.__doneList = []
        self.__cli_commands = {}

    def getCLICommandXML(self,prot,seq,ln,payload):
        """\brief Returns the complete XML interpretation of the CLI commands
        available from all the running daemons, plus the standard CLI functions
        such as "exit" and "help".
        """
        if not self.__cli_commands_xml: 
            # This should never happen
            prot.sendReply(500, seq, "No commands found by daemon!")
        

    def getHenStatus(self,prot,seq,ln,payload):
        log.debug("getHenStatus() called.")
        self.__checker_lock.acquire()
        results = "Content-type: text/xml\n"
        results += "Cache-Control: no-store, no-cache, must-revalidate\n\n"
        results += "<processmanagement>\n"
        results += "\t<running>\n"
        for daemon in self.__runningDaemons:
            results += "\t\t<process name=\"%s\" />\n" % str(daemon)
        results += "\t</running>\n"
        results += "\t<stopped>\n"
        for daemon in self.__stoppedDaemons:
            results += "\t\t<process name=\"%s\" />\n" % str(daemon)
        results += "\t</stopped>\n"
        results += "</processmanagement>\n"
        self.__checker_lock.release()
        prot.sendReply(200, seq, results)

    def killDaemon(self,prot,seq,ln,payload):
        prot.sendReply(200, seq, "Killing Daemon!")
        os.abort()

    def getVersion(self,prot,seq,ln,payload):
        """\brief Returns version"""
        payload = self.__version
        prot.sendReply(200, seq, payload)
    
    def stopDaemon(self,prot,seq,ln,payload):
        """\brief Stops the daemon and all threads
        This method will first stop any more incoming queries, then wait for
        any update tasks to complete, before stopping itself.
        """
        log.debug("stopDaemon called.")
        prot.sendReply(200, seq, "Accepted stop request.")
        log.debug("Stopping Checker Timer")
        self.__checker_timer.stop()
        self.acceptConnections(False)
        log.debug("Stopping Hen Status Daemon (self)")
        Daemon.stop(self)
    
    def startCheckerTimer(self):
        self.__checker_timer = GracefulTimer(CHECKER_INTERVAL, \
                                    self.checkHenStatus, True)
        self.__checker_timer.start()
    
    def stopCheckerTimer(self):
        self.__checker_timer.stop()
        
    def checkerTimerIsRunning(self):
        if self.__checker_timer:
            if self.__checker_timer.isAlive():
                return True
        return False
    
    def __registerMethods(self):
        log.debug("Registering method handlers...")
        self.registerMethodHandler("get_version", self.getVersion)
        #self.registerMethodHandler("stop_daemon", self.stopDaemon)
        #self.registerMethodHandler("kill_daemon", self.killDaemon)
        self.registerMethodHandler("get_henstatus", self.getHenStatus)
        self.registerMethodHandler("get_cli_command_xml", self.getCLICommandXML)
    
    def __createStatusThreads(self):
        for (daemon, method) in DaemonStatus().getAllDaemonStatusMethods():
            doneEvent = threading.Event()
            self.__checkerThreads[daemon] = \
                DaemonStatusChecker(method, doneEvent, STATUS_TIMEOUT)
            self.__checkerThreads[daemon].start()
            self.__doneList.append(doneEvent)

    def __waitForResults(self):
        while 1:
            done = True
            for doneEvent in self.__doneList:
                if not doneEvent.isSet():
                    done = False
            if done:
                break
            time.sleep(2)
    
    def __collectResults(self):
        for daemon in self.__checkerThreads.keys():
            if self.__checkerThreads[daemon].isOnline():
                self.__runningDaemons.append(daemon)
            else:
                self.__stoppedDaemons.append(daemon)

    def __generateCommandXML(self):
        self.__cli_commands_xml = "<testbedcommands>"
        
        # TODO: !!!

        for daemon in self.__runningDaemons:
            pass
        
    def checkHenStatus(self):
        log.debug("checkHenStatus() called.")
        self.__checker_lock.acquire()
        self.__stoppedDaemons = []
        self.__runningDaemons = []
        self.__checkerThreads = {}
        self.__doneList = []
        self.__createStatusThreads()
        self.__waitForResults()
        self.__collectResults()
        self.__generateCommandXML()
        self.__checker_lock.release()
    
class StatusDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    __bind_addr = DaemonLocations.henstatusDaemon[0]
    __port = DaemonLocations.henstatusDaemon[1]
    __sockd = None
    __emergency_checker = None
    
    def __init__(self, doFork):
        Daemonizer.__init__(self, doFork)
    
    def run(self):
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        self.__sockd.settimeout(2) # 2 second timeouts
        log.debug("Creating HenStatusChecker")
        self.__henstatus_checker = HenStatusChecker()
        log.debug("Starting HenStatusChecker")
        self.__henstatus_checker.startCheckerTimer()
        self.__henstatus_checker.start()
        while self.__henstatus_checker.isAlive():
            if self.__henstatus_checker.acceptingConnections():
                # allow timeout of accept() to avoid blocking a shutdown
                try:
                    (s,a) = self.__sockd.accept()
                    log.info("New connection established from " + str(a))
                    self.__henstatus_checker.addSocket(s)
                except:
                    pass
            else:
                log.debug("HenStatusChecker still alive, but not accepting " + \
                          "connections")
                time.sleep(2)
        log.debug("Closing socket.")
        self.__sockd.shutdown(socket.SHUT_RDWR)        
        self.__sockd.close()
        while threading.activeCount() > 1:
            cThreads = threading.enumerate()
            log.debug("Waiting on " + str(threading.activeCount()) + \
                      " active threads...")
            time.sleep(2)
        log.debug("StatusDaemon Finished.")
        # Now everything is dead, we can exit.  
        sys.exit(0)
        
def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    WORKDIR = '/var/hen/henstatusdaemon'
    PIDDIR = '/var/run/hen'
    LOGDIR = '/var/log/hen/henstatusdaemon'
    LOGFILE = 'henstatusdaemon.log'
    PIDFILE = 'henstatusdaemon.pid'
    GID = 17477 # schooley
    UID = 17477 # schooley
    henstatusd = StatusDaemon(True)
    henstatusd.setWorkingDir(WORKDIR)
    henstatusd.setPIDDir(PIDDIR)
    henstatusd.setLogDir(LOGDIR)
    henstatusd.setLogFile(LOGFILE)
    henstatusd.setPidFile(PIDFILE)
    henstatusd.setUid(UID)
    henstatusd.setGid(GID)
    henstatusd.start()
        
if __name__ == "__main__":
    main()
