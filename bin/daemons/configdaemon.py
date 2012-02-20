#!/usr/local/bin/python
import sys, os
sys.path.append("/usr/local/hen/lib")

from daemonizer import Daemonizer
from daemon import Daemon
import logging, threading, socket, pickle
from henmanager import HenManager
from auxiliary.timer import GracefulTimer
from auxiliary.daemonlocations import DaemonLocations
import commands, re

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

class ConfigReader(Daemon):
    """\brief Implements basic config daemon functionality.
    """
    __version = "Config Daemon v0.1 (simple)"
    __henManager = None
    
    def __init__(self):
        Daemon.__init__(self)
        self.__henManager = HenManager()
        self.__registerMethods()
        
    def __registerMethods(self):
        self.registerMethodHandler("get_object_for_id", self.getObjectForId)
        self.registerMethodHandler("stop_daemon", self.stopDaemon)
        
    def __sendReply(self,prot,code,seq,payload):
        if (code == 0):
            code = 200
        else:
            code = 422 # returnCodes[422] = "error executing command"
        prot.sendReply(code, seq, payload)

    def getObjectForId(self,prot,seq,ln,payload):
        nodes = self.__henManager.getNodes("all")
        for ntk in nodes:
            #print "ntk ",str(ntk)
            for nk in nodes[ntk]:
                #print "nk ",str(nk)
                if nodes[ntk][nk].getNodeID() == payload:
                    payload=pickle.dumps(nodes[ntk][nk])
                    code = 0
                    self.__sendReply(prot,code,seq,payload)
                    return
        payload = "not found"
        code = -1
        self.__sendReply(prot,code,seq,payload)        

    def stopDaemon(self,prot,seq,ln,payload):
        """\brief Stops the daemon and all threads
        This method will first stop any more incoming queries, then wait for
        any update tasks to complete, before stopping itself.
        """
        log.info("stopDaemon called.")
        prot.sendReply(200, seq, "Accepted stop request.")
        log.debug("Sending stopDaemon() response")
        self.acceptConnections(False)
        log.info("Stopping ConfigDaemon (self)")
        self.stop()

class ConfigDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    __bind_addr = DaemonLocations.configDaemon[0]
    __port = DaemonLocations.configDaemon[1]
    __sockd = None
    __configcontrol = None
    
    def __init__(self, doFork):
        Daemonizer.__init__(self, doFork)

    def run(self):
        log.debug("Creating ConfigDaemon")
        self.__configreader = ConfigReader()
        # Creating socket
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        #self.__sockd.settimeout(2) # 2 second timeouts
        log.info("Starting ConfigDaemon")
        self.__configreader.start()
        while self.__configreader.isAlive():
            if self.__configreader.acceptingConnections():
                # allow timeout of accept() to avoid blocking a shutdown
                try:
                    (s,a) = self.__sockd.accept()
                    log.debug("New connection established from " + str(a))
                    self.__configreader.addSocket(s)
                except KeyboardInterrupt:
                    os_exit(1)
            else:
                log.warning(\
                      "ConfigDaemon still alive, but not accepting connections")
                time.sleep(2)
        log.debug("Closing socket.")
        self.__sockd.shutdown(socket.SHUT_RDWR)
        self.__sockd.close()
        while threading.activeCount() > 1:
            cThreads = threading.enumerate()
            log.warning("Waiting on " + str(threading.activeCount()) + \
                        " active threads...")
            time.sleep(2)
        log.info("ConfigDaemon Finished.")
        # Now everything is dead, we can exit.
        sys.exit(0)

def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    WORKDIR = '/var/hen/configdaemon'
    PIDDIR = '/var/run/hen'
    LOGDIR = '/var/log/hen/configdaemon'
    LOGFILE = 'configdaemon.log'
    PIDFILE = 'configdaemon.pid'
    GID = 18122 # hen
    UID = 18122 # root
    configd = ConfigDaemon(False)
    configd.setWorkingDir(WORKDIR)
    configd.setPIDDir(PIDDIR)
    configd.setLogDir(LOGDIR)
    configd.setLogFile(LOGFILE)
    configd.setPidFile(PIDFILE)
    configd.setUid(UID)
    configd.setGid(GID)
    configd.start()

if __name__ == "__main__":
    main()
