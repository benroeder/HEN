#!/usr/local/bin/python
import sys, pickle, ConfigParser
sys.path.append("/usr/local/hen/lib")

from daemonizer import Daemonizer
from daemon import Daemon
import logging, threading, socket, select, traceback
from auxiliary.daemonlocations import DaemonLocations
from auxiliary.henparser import HenParser
from auxiliary.protocol import Protocol

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

class TerminalServerConnection:

    def __init__(self, userID, port, terminalServer):
        self.__userID = userID
        self.__port = port
        self.__terminalServer = terminalServer
        self.__terminalServer.connectRaw(port, 10)
        
    def send(self, data):
        self.__terminalServer.sendRaw(data)

    def recv(self):
        return self.__terminalServer.recvRaw()

    def getAndDeleteBuffer(self):
        return self.__terminalServer.getAndDeleteBuffer()
        
    def close(self):
        self.__terminalServer.closeRaw()

    def getBuffer(self):
        return self.__buffer
    
    def getSocket(self):
        return self.__terminalServer.getSocket()

    def getUserID(self):
        return self.__userID
    
    
class ConsoleControl(Daemon):
    """\brief Implements basic console daemon functionality.
    """
    def __init__(self, configFilePath='/usr/local/hen/etc/configs/config'):
        Daemon.__init__(self)

        self.__version = "Console Daemon v0.2 (dumb)"
        self.__terminalServerConnections = {}
        self.__terminalServerSockets = []
        self.__configFilePath = configFilePath
        self.__configFile = ConfigParser.ConfigParser()
        self.__configFile.read(configFilePath)
        self.__henPhysicalTopology = self.__configFile.get('MAIN','PHYSICAL_TOPOLOGY')
        self.__henLogPath = self.__configFile.get('MAIN', 'LOG_PATH')
        self.__parser = HenParser(self.__henPhysicalTopology, \
                                  None, \
                                  None, \
                                  self.__henLogPath, \
                                  None,
                                  None,
                                  None, \
                                  None)

        self.__controlProtocol = None

        # Create instances for all terminal servers in the testbed
        self.__terminalServerNodes = {}
        for terminalServerNode in self.__parser.getNodes("serial", "all").values():
            self.__terminalServerNodes[terminalServerNode.getNodeID()] = terminalServerNode.getInstance()
        self.__computerNodes = self.__parser.getNodes("computer", "all")
                                
        self.__registerMethods()

    def __registerMethods(self):
        self.registerMethodHandler("console", self.console)

    def __getPort(self, nodeID):
        return (self.__computerNodes[nodeID].getSerialNodeID(), self.__computerNodes[nodeID].getSerialNodePort())
        
    def console(self,prot,seq,ln,payload):
        print "in console"
        if (self.__controlProtocol == None):
            self.__controlProtocol = Protocol(None)        
            self.__controlProtocol.open(DaemonLocations.controlDaemon[0], DaemonLocations.controlDaemon[1])        
        (action, username, nodeID, consoleInput) = pickle.loads(payload)
        print action, username, nodeID, consoleInput


        (serialID, serialPort) = self.__getPort(nodeID)
        # Replies are needed by doSynchronous call in control daemon
        if (action == "open"):
            terminalServerConnection = TerminalServerConnection(username, serialPort, self.__terminalServerNodes[serialID])
            self.__terminalServerConnections[terminalServerConnection.getSocket()] = terminalServerConnection
            self.__terminalServerSockets.append(terminalServerConnection.getSocket())
            self.sock_list.append(terminalServerConnection.getSocket())
            prot.sendReply(200, seq, "")
            return
        elif (action == "close"):
            for connection in self.__terminalServerConnections.values():
                if (connection.getUserID() == username):
                    connection.close()
                    self.sock_list.remove(connection.getSocket())
                    self.__terminalServerSockets.remove(connection.getSocket())
                    del self.__terminalServerConnections[connection.getSocket()]
                    break            
            prot.sendReply(200, seq, "")
            return
        elif (action == "forward"):
            for connection in self.__terminalServerConnections.values():
                if (connection.getUserID() == username):
                    connection.send(consoleInput)
        else:
            print "unrecognized action:", action

    def processTerminalServerData(self, sock):
        connection = self.__terminalServerConnections[sock]
        if (connection.recv()):
            self.__controlProtocol.sendRequest("console", \
                                               pickle.dumps((connection.getUserID(), \
                                                             connection.getAndDeleteBuffer(), \
                                                             ["console_output"])), \
                                               self.terminalServerDataReplyHandler)

    def terminalServerDataReplyHandler(self, code, seq, sz, payload):
        pass
    
    def stopDaemon(self,prot,seq,ln,payload):
        """\brief Stops the daemon and all threads
        This method will first stop any more incoming queries, then wait for
        any update tasks to complete, before stopping itself.
        """
        log.info("stopDaemon called.")
        prot.sendReply(200, seq, "Accepted stop request.")
        log.debug("Sending stopDaemon() response")
        self.acceptConnections(False)
        log.info("Stopping ConsoleDaemon (self)")
        self.stop()

    def run(self):
        """\brief Main daemon loop
        Waits for messages from clients and processes them. Only sleeps for two
        seconds, to accept new clients also.
        """
        while not self.isStopped:
            #select sockets
            (read,write,exc) = select.select(self.sock_list,[],self.sock_list,2)
            for i in read:
                s = None

                if (i in self.__terminalServerSockets):
                    self.processTerminalServerData(i)
                    continue

                # Process regular socket
                try:
                    s = i.recv(1000000,0)
                # Process SSL socket
                except:
                    try:
                        s = i.read(1000000)
                    except:
                        s = []
                try:
                    #log.debug("Read from socket:"+s.replace("\r","\\r"))

                    if (len(s)==0):
                        #log.debug("removing")
                        idx = self.sock_list.index(i)
                        del self.sock_list[idx]
                        del self.protocol_list[idx]
                    else:
                        self.protocol_list[self.sock_list.index(i)].processPacket(s)
                except Exception,e:
                    idx = self.sock_list.index(i)
                    del self.sock_list[idx]
                    del self.protocol_list[idx]
                    traceback.print_exc()
            for i in exc:
                log.debug ("exc",i)


class ConsoleDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    __bind_addr = DaemonLocations.consoleDaemon[0]
    __port = DaemonLocations.consoleDaemon[1]
    __sockd = None
    __consoleControl = None

    def __init__(self, doFork):
        Daemonizer.__init__(self, doFork)

    def run(self):
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        self.__sockd.settimeout(2) # 2 second timeouts
        log.debug("Creating ConsoleDaemon")
        self.__consoleControl = ConsoleControl()
        log.info("Starting ConsoleDaemon")
        self.__consoleControl.start()
        while self.__consoleControl.isAlive():
            if self.__consoleControl.acceptingConnections():
                # allow timeout of accept() to avoid blocking a shutdown
                try:
                    (s,a) = self.__sockd.accept()
                    log.debug("New connection established from " + str(a))
                    self.__consoleControl.addSocket(s)
                except:
                    pass
            else:
                log.warning(\
                      "ConsoleDaemon still alive, but not accepting connections")
                time.sleep(2)
        log.debug("Closing socket.")
        self.__sockd.shutdown(socket.SHUT_RDWR)
        self.__sockd.close()
        while threading.activeCount() > 1:
            cThreads = threading.enumerate()
            log.warning("Waiting on " + str(threading.activeCount()) + \
                        " active threads...")
            time.sleep(2)
        log.info("ConsoleDaemon Finished.")
        # Now everything is dead, we can exit.
        sys.exit(0)

def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    WORKDIR = '/var/hen/consoledaemon'
    PIDDIR = '/var/run/hen'
    LOGDIR = '/var/log/hen/consoledaemon'
    LOGFILE = 'consoledaemon.log'
    PIDFILE = 'consoledaemon.pid'
    GID = 17477 # schooley
    UID = 17477 # schooley
    consoled = ConsoleDaemon(False)
    consoled.setWorkingDir(WORKDIR)
    consoled.setPIDDir(PIDDIR)
    consoled.setLogDir(LOGDIR)
    consoled.setLogFile(LOGFILE)
    consoled.setPidFile(PIDFILE)
    consoled.setUid(UID)
    consoled.setGid(GID)
    consoled.start()

if __name__ == "__main__":
    main()
