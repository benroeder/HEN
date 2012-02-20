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

class ComputerControl(Daemon):
    """\brief Implements basic computer daemon functionality.
    """
    __version = "Computer Daemon v0.1 (simple)"
    __henManager = None
    
    def __init__(self):
        Daemon.__init__(self)
        self.__henManager = HenManager()
        # Allow specialized instance dictionary to be created in hm
        # self.__henManager.createNodeInstances()
        self.__registerMethods()
        self.__computerID = self.__getComputerID()
        self.__computerInfo = self.__henManager.getNodes("computer")[self.__computerID]
        self.__ifaceIDtoNameMappings = self.__getIfaceMappings()

    def getComputerManagementIP(self):
        # Get the management ip address so that we can bind to it.
        interfaces = self.__computerInfo.getInterfaces("management")
        try:
            return interfaces[0].getIP()
        except:
            return "0.0.0.0"
        
    def __getComputerID(self):
        # Prints the name of the node that the script is run from. To do so it matches the mac addresses of
        # all running interfaces against the mac addresses in the testbed's database. Prints None if no match is found

        # First create a list containing the mac addresses of all the running interfaces
        macAddresses = []
        macAddressMatcher = re.compile('(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}')
        lines = commands.getstatusoutput("ifconfig")[1].splitlines()
        for line in lines:
            matchObject = macAddressMatcher.search(line)
            if (matchObject):
                macAddresses.append(line[matchObject.start():matchObject.end()].upper())

        # Now match the created list against all of the management mac addresses in the testbed's database
        # for computer nodes
        self.__henManager.initLogging()
        nodes = self.__henManager.getNodes("computer","all")
        nodeName = None
        for node in nodes.values():
            for interface in node.getInterfaces("management"):
                for macAddress in macAddresses:
                    if (macAddress == interface.getMAC().upper()):
                        nodeName = node.getNodeID()
        if nodeName == None:
            nodes = self.__henManager.getNodes("virtualcomputer","all")
            for node in nodes.values():
                for interface in node.getInterfaces("management"):
                    for macAddress in macAddresses:
                        if (macAddress == interface.getMAC().upper()):
                            nodeName = node.getNodeID()
        return nodeName

    def __getIfaceMappings(self):
        mappings = {}

        # Supports only Linux for now
        interfaces = self.__computerInfo.getInterfaces("experimental")
        ifacesInfo = commands.getstatusoutput("ifconfig -a | grep HWaddr")[1].splitlines()
        for interface in interfaces:
            for infoLine in ifacesInfo:
                if (infoLine.find(interface.getMAC()) != -1):
                    mappings[interface.getInterfaceID()] = infoLine[:infoLine.find(" ")]
        return mappings
    
    def __registerMethods(self):
        self.registerMethodHandler("get_computer_id", self.getComputerID)        
        self.registerMethodHandler("autodetect", self.autodetect)        
        self.registerMethodHandler("execute_command", self.executeCommand)
        self.registerMethodHandler("gcc_compile", self.gccCompile)
        self.registerMethodHandler("cat", self.cat)        
        self.registerMethodHandler("make", self.make)
        self.registerMethodHandler("mkdir", self.mkdir)        
        self.registerMethodHandler("untar", self.untar)
        self.registerMethodHandler("add_route", self.addRoute)
        self.registerMethodHandler("delete_route", self.delRoute)
        self.registerMethodHandler("config_iface", self.configIface)
        self.registerMethodHandler("click-align", self.clickAlign)
        self.registerMethodHandler("click-install", self.clickInstall)
        self.registerMethodHandler("click-uninstall", self.clickUninstall)
        self.registerMethodHandler("load_module", self.loadModule)
        self.registerMethodHandler("unload_module", self.unloadModule)
        self.registerMethodHandler("linux_forwarding_on", self.linuxForwardingOn)
        self.registerMethodHandler("linux_forwarding_off", self.linuxForwardingOff)                                        

    def __sendReply(self,prot,code,seq,payload):
        if (code == 0):
            code = 200
        else:
            code = 422 # returnCodes[422] = "error executing command"
        prot.sendReply(code, seq, payload)

    def autodetect(self,prot,seq,ln,payload):
        pass

    def getComputerID(self,prot,seq,ln,payload):
        self.__sendReply(prot,"0",seq,self.__computerID)
        
    def executeCommand(self,prot,seq,ln,payload):
        (code, payload) = commands.getstatusoutput(payload)
        self.__sendReply(prot,code,seq,payload)        
    
    def gccCompile(self,prot,seq,ln,payload):
        (workDir, filename) = pickle.loads(payload)
        name = filename[:filename.find(".")]
        (code, payload) = commands.getstatusoutput("cd " + worDir + " ; g++ -o " + name + " " + filename)
        self.__sendReply(prot,code,seq,payload)        

    def cat(self,prot,seq,ln,payload):
        #print "got cat command"
        payload = pickle.loads(payload)[0]
        (code, payload) = commands.getstatusoutput("cat " + str(payload))
        self.__sendReply(prot,code,seq,payload)

    def make(self,prot,seq,ln,payload):
        (workDir, makeTarget) = pickle.loads(payload)
        (code, payload) = commands.getstatusoutput("cd " + workDir + " ; make -f " + makeTarget)
        self.__sendReply(prot,code,seq,payload)        

    def mkdir(self,prot,seq,ln,payload):
        code = os.mkdir(payload)
        self.__sendReply(prot,code,seq,"")
        
    def untar(self,prot,seq,ln,payload):
        (tarPath, targetDir) = pickle.loads(payload)
        (code, payload) = commands.getstatusoutput("tar -xf " + path + " -C " + targetDir)
        self.__sendReply(prot,code,seq,payload)                

    def addRoute(self,prot,seq,ln,payload):
        (network, netmask, gateway, interface) = pickle.loads(payload)
        (code, payload) = commands.getstatusoutput("route add -net " + network + \
                                                   " netmask " + netmask + \
                                                   " gw " + gateway \
                                                   + " dev " + interface)
        self.__sendReply(prot,code,seq,payload)

    def delRoute(self,prot,seq,ln,payload):
        (network, netmask) = pickle.loads(payload)
        (code, payload) = commands.getstatusoutput("route del -net " + network + " netmask " + netmask)
        self.__sendReply(prot,code,seq,payload)

    def configIface(self,prot,seq,ln,payload):
        (interfaceID, address, mask, status) = pickle.loads(payload)
        try:
            cmd = "ifconfig " + self.__ifaceIDtoNameMappings[interfaceID] + " "
        except KeyError:
            log.error("Key error "+str( self.__ifaceIDtoNameMappings))
            (code, payload) = (400, "Key error for interface")
            self.__sendReply(prot,code,seq,payload)
            return
        if (status == "on"):
            cmd += address + " netmask " + mask + " up"
        else:
            cmd += "down"
        (code, payload) = commands.getstatusoutput(cmd)
        self.__sendReply(prot,code,seq,payload)        

    def clickAlign(self,prot,seq,ln,payload):
        (clickAlignPath, configFile) = pickle.loads(payload)
        basePath = configFile[:configFile.rfind("/")]
        filename = configFile[configFile.rfind("/") + 1: configFile.find(".")]
        newPathToFile = basePath + "/" + filename + "-aligned.click'"
        (code, payload) = commands.getstatusoutput(clickAlignPath + " " + configFile + " > " + newPathToFile)
        self.__sendReply(prot,code,seq,payload)                

    def clickInstall(self,prot,seq,ln,payload):
        (clickInstallPath, configFile, numberThreads) = pickle.loads(payload)
        cmd = click-installPath + " "
        if (int(numberThreads) != 0):
            cmd += "--threads=" + numberThreads + " "
        cmd += configFile
        (code, payload) = commands.getstatusoutput(cmd)
        self.__sendReply(prot,code,seq,payload)        

    def clickUninstall(self,prot,seq,ln,payload):
        (code, payload) = commands.getstatusoutput(payload)
        self.__sendReply(prot,code,seq,payload)        

    def loadModule(self,prot,seq,ln,payload):
        (code, payload) = commands.getstatusoutput("insmod " + payload)
        self.__sendReply(prot,code,seq,payload)                

    def unloadModule(self,prot,seq,ln,payload):
        (code, payload) = commands.getstatusoutput("rmmod " + payload)
        self.__sendReply(prot,code,seq,payload)                        

    def linuxForwardingOn(self,prot,seq,ln,payload):
        (code, payload) = commands.getstatusoutput("echo '1' \> /proc/sys/net/ipv4/ip_forward")
        self.__sendReply(prot,code,seq,payload)                                

    def linuxForwardingOff(self,prot,seq,ln,payload):
        (code, payload) = commands.getstatusoutput("echo '0' \> /proc/sys/net/ipv4/ip_forward")
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
        log.info("Stopping ComputerDaemon (self)")
        self.stop()

class ComputerDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    #__bind_addr = DaemonLocations.computerDaemon[0]
    #__bind_addr = "0.0.0.0"
    __port = DaemonLocations.computerDaemon[1]
    __sockd = None
    __computercontrol = None
    
    def __init__(self, doFork):
        Daemonizer.__init__(self, doFork)

    def run(self):
        log.debug("Creating ComputerDaemon")
        self.__computercontrol = ComputerControl()
        # get the management ip address and bind to that
        self.__bind_addr = self.__computercontrol.getComputerManagementIP()
        # Creating socket
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        #self.__sockd.settimeout(2) # 2 second timeouts
        log.info("Starting ComputerDaemon")
        self.__computercontrol.start()
        while self.__computercontrol.isAlive():
            if self.__computercontrol.acceptingConnections():
                # allow timeout of accept() to avoid blocking a shutdown
                try:
                    (s,a) = self.__sockd.accept()
                    log.debug("New connection established from " + str(a))
                    self.__computercontrol.addSocket(s)
                except KeyboardInterrupt:
                    os_exit(1)
            else:
                log.warning(\
                      "ComputerDaemon still alive, but not accepting connections")
                time.sleep(2)
        log.debug("Closing socket.")
        self.__sockd.shutdown(socket.SHUT_RDWR)
        self.__sockd.close()
        while threading.activeCount() > 1:
            cThreads = threading.enumerate()
            log.warning("Waiting on " + str(threading.activeCount()) + \
                        " active threads...")
            time.sleep(2)
        log.info("ComputerDaemon Finished.")
        # Now everything is dead, we can exit.
        sys.exit(0)

def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    WORKDIR = '/var/hen/computerdaemon'
    PIDDIR = '/var/run/hen'
    LOGDIR = '/var/log/hen/computerdaemon'
    LOGFILE = 'computerdaemon.log'
    PIDFILE = 'computerdaemon.pid'
    GID = 3000 # hen
    UID = 0 # root
    computerd = ComputerDaemon(False)
    computerd.setWorkingDir(WORKDIR)
    computerd.setPIDDir(PIDDIR)
    computerd.setLogDir(LOGDIR)
    computerd.setLogFile(LOGFILE)
    computerd.setPidFile(PIDFILE)
    computerd.setUid(UID)
    computerd.setGid(GID)
    computerd.start()

if __name__ == "__main__":
    main()
