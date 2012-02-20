#!/usr/local/bin/python
import sys
sys.path.append("/usr/local/hen/lib")

import os, socket, pickle, ConfigParser, time, logging
from xml.dom import minidom
from xml.dom.minidom import Node, Element
import auxiliary.protocol
from henmanager import HenManager
from auxiliary.hen import Interface
from auxiliary.daemonlocations import DaemonLocations
from daemonizer import Daemonizer
from daemon import Daemon
import threading

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

HEN_CONFIG = '/usr/local/hen/etc/configs/config'

class LSHardwareProcessor:
    """\brief A class that parses output from lshw, autodetects interface
        information, and can print a string to the console containing a node's
        physical description file
    """
    def __init__(self, manager=None, macTableURL=None):
        """\brief Initializes class
        \param manager (\c HenManager) The HenManager object used to parse the testbed's database
        \param macTableURL (\c string) URL to retrieve switch database information from
        """
        self.__manager = manager
        self.__macTableURL = macTableURL
        self.__detectedInterfaces = None
        self.__toGiga = (1.0 / 10 ** 9)
        self.__toGigaBinary = (1.0 / 2 ** 30)
        self.__MAX_NUMBER_DETECTION_TRIES = 3
        self.__debug_mode = False
        
    def parseFileAndPrint(self, theNodeID, lshwOutput):
        """\brief Parses the given string produced by lshw and creates a node's
        physical description file from it. It also autodetects interface
        information for the node, including their speeds, models, and what
        switch and port they're plugged into. It then writes this information
        to the node's physical description file.
        \param theNodeID (\c string) The id of the node
        \param lshwOuput (\c string) The lshw output received from the client.
                This consists of the xml output from lshw prepended by:
                <numbercpus>x</numbercpus>, where x is the number of cpus in
                the system.
        """
        log.debug("parsing lshw output...")

        # First retrieve the number of cpus and remove this from the string
        # containing the lshw data
        numberCPUs = lshwOutput[lshwOutput.find(">") + \
                                1:lshwOutput.find("<", 1)]
        lshwOutput = lshwOutput[lshwOutput.find("/numbercpus") + 12:]

        # Do the same for the number of cores per cpu
        numberCoresPerCPU = lshwOutput[lshwOutput.find(">") + \
                                       1:lshwOutput.find("<", 1)]
        lshwOutput = lshwOutput[lshwOutput.find("/numbercorespercpu") + 19:]

        # Retrieve the mac addresses of interfaces that have no carrier sense
        #<nocarriermacs>00:14:4F:40:77:5D,00:11:22:33:44:55</nocarriermacs>
        noCarrierMACs = lshwOutput[lshwOutput.find(">") + \
                                   1:lshwOutput.find("<", 1)]
        noCarrierMACs = noCarrierMACs.split(",")
        lshwOutput = lshwOutput[lshwOutput.find("/nocarriermacs") + 15:]

        try:
            xmldoc = minidom.parseString(lshwOutput)
            nodeXML = xmldoc.getElementsByTagName("node")
        except Exception, e:
            log.debug("error while parsing, ignoring client request..."+str(lshwOutput))
            #raise Exception("parseFileAndPrint(): %s" % str(e))

        # Retrieve the total system memory
        systemMemory = self.__memoryToGiga(self.__getSystemMemory(xmldoc))

        macAddresses = []
        interfaces = []
        motherboard = None
        cpuDescription = None
        cpuSpeed = None
        serialNumber = None
        usbVersion = None
        usbVersionMap = {"01":"1.0", "0b":"1.1", "02":"2.0"}
        
        for tag in nodeXML :
            macAddress = None
            ethernetName = None
            ethernetModel = None
            ethernetSpeed = None

            if (tag.attributes.has_key("class")):
                nodeClass = tag.attributes["class"].value
                nodeID = tag.attributes["id"].value

                # Retrieve USB version information
                if ( (not usbVersion) and nodeClass == "bus" and nodeID.find("usb:") != -1):
                    elements = tag.getElementsByTagName("version")
                    try:
                        for element in elements:
                            usbVersion = usbVersionMap[self.__getData(element)]
                            break
                    except:
                        usbVersion = -1
                                                                                                               
                # Retrieve motherboard information
                if (nodeClass == "system"):
                    counter = 0
                    logName = tag.getElementsByTagName("vendor")
                    for l in logName:
                        if counter == 0:
                            motherboard = self.__getData(l)
                            counter = counter + 1

                    logName = tag.getElementsByTagName("product")
                    for l in logName:
                        if counter == 1:
                            motherboard += " " + self.__getData(l)
                            counter = counter + 1

                    logName = tag.getElementsByTagName("serial")
                    for l in logName:
                        if (not serialNumber):
                            serialNumber = self.__getData(logName[0])

                # Retrieve cpu information
                if (nodeClass == "processor"):
                    logName = tag.getElementsByTagName("product")
                    for l in logName:
                        if (not cpuDescription):
                            cpuDescription = self.__getData(l)

                    logName = tag.getElementsByTagName("size")
                    for l in logName:
                        if (not cpuSpeed):
                            cpuSpeed = \
                                self.__cpuSpeedToGiga((self.__getData(l)))

                # Retrieve network interface information
                if (nodeClass == "network"):
                    logName = tag.getElementsByTagName("serial")
                    for l in logName:
                        macAddress = self.__getData(l)
                        macAddresses.append(self.__getData(l))
                    logName = tag.getElementsByTagName("logicalname")
                    for l in logName:
                        ethernetName = self.__getData(l)
                    logName = tag.getElementsByTagName("product")
                    for l in logName:
                        ethernetModel = self.__getData(l)
                    logName = tag.getElementsByTagName("size")
                    for l in logName:
                        ethernetSpeed = str(int(self.__getData(l)) / 1000000)

                if (macAddress != None and ethernetName != None):
                    interface = Interface(macAddress.upper(), None, None, None,\
                                          None, None, None, ethernetSpeed, \
                                          ethernetModel, ethernetName)
                    interfaces.append(interface)

        """
        Auto detect which switch and port each interface is connected to.
        Results are stored in self.__detectedInterfaces, a dictionary of
        (switchid, port name) tuples. First force switch daemon to query switch
        databases
        """
        #log.debug("waiting 20 seconds for switch databases to 'settle'...")
        #time.sleep(20)

        p = auxiliary.protocol.Protocol(None)
        p.open(DaemonLocations.switchMonitorDaemon[0], DaemonLocations.switchMonitorDaemon[1])
        method = "redetect_fdb"
        log.debug("forcing switch daemon to query switch databases")
        #p.sendRequest(method, pickle.dumps(macAddresses), \
        #              self.__processQuerySwitchDBsReply)
        #p.readAndProcess()

        numberTries = 0
        undetectedInterfaces = True
        method = "find_unique_macs"
        while (numberTries < self.__MAX_NUMBER_DETECTION_TRIES \
               and undetectedInterfaces):
            log.debug("sleeping for 30 secs...")
            time.sleep(30)
            log.debug("sending request to switch daemon's find_macs for: " + \
                      str(macAddresses))
            p.sendRequest(method, pickle.dumps(macAddresses), \
                          self.__processDetectIfacesReply)
            p.readAndProcess()
            numberTries += 1

            # Go through the reply for the switch daemon. If any of them is
            # unknown and the interface has carrier sense, try again, up to
            # MAX_NUMBER_TRIES
            undetectedInterfaces = False
            for detectedInterfaceMAC in self.__detectedInterfaces.keys():
                if (self.__detectedInterfaces[detectedInterfaceMAC][0] == \
                                                                    "unknown"):
                    if (detectedInterfaceMAC.upper() not in noCarrierMACs):
                        log.debug("the following mac was not found: " + \
                                  detectedInterfaceMAC)
                        undetectedInterfaces = True
                    else:
                        log.debug("the following mac is being ignored due to" +\
                                  " lack of carrier sense: " + \
                                  detectedInterfaceMAC)

        # nodeInterfaces will contain the full interface info for this node
        nodeInterfaces = {}
        nodeInterfaces["management"] = []
        nodeInterfaces["experimental"] = []

        # Fill in information for the management interface (some of its info
        # is already in its skeleton xml file, parse it and add to it)
        theNode = None
        nodes = self.__manager.getNodes("computer", "all")
        
        for computerNode in nodes.values():
            if (computerNode.getNodeID() == theNodeID):
                theNode = computerNode
                #log.debug("Power node id "+str(theNode.getPowerNodeID()))
                #log.debug("Power node class "+str(theNode.__class__))
                 

        
        managementInterface = theNode.getInterfaces("management")[0]
        log.debug(str(self.__detectedInterfaces[managementInterface.getMAC().upper()]))
        try:
            if ( (self.__detectedInterfaces) and \
                 (self.__detectedInterfaces.has_key(managementInterface.getMAC().upper())) ):
                try:
                    managementInterface.setSwitch(self.__detectedInterfaces[managementInterface.getMAC().upper()][0][0])
                    managementInterface.setPort(self.__detectedInterfaces[managementInterface.getMAC().upper()][0][1])
                except Exception, e:
                    log.critical(str(e))
        except:
            log.debug("unable to lookup management interface: " + str(managementInterface.getMAC().upper()))

        nodeInterfaces["management"].append(managementInterface)

        # Fill in information for the experimental interfaces
        
        
        for interface in interfaces:
            if ( (self.__detectedInterfaces != None ) and \
                 (self.__detectedInterfaces.has_key(interface.getMAC().upper()) ) ):
                try:

                    interface.setSwitch(self.__detectedInterfaces[interface.getMAC().upper()][0][0])
                    interface.setPort(self.__detectedInterfaces[interface.getMAC().upper()][0][1])
                except Exception, e:
                    log.critical(str(e))
                    log.critical(str(interface.getMAC().upper()))
                    log.critical(str(self.__detectedInterfaces[interface.getMAC().upper()]))
                    #interface.setSwitch("None")
                    #interface.setPort("None")
            if (interface.getMAC().upper() != \
                nodeInterfaces["management"][0].getMAC().upper()):
                nodeInterfaces["experimental"].append(interface)
        
        
        # We now have the full information for the interfaces, construct the
        # Node object
        log.debug("writing description file...")

        # Append attribute information to the node
        theNode.setSingleAttribute("usbversion", usbVersion)    
        theNode.setSingleAttribute("serialnumber", serialNumber)
        theNode.setSingleAttribute("numbercpus", numberCPUs)
        theNode.setSingleAttribute("numbercorespercpu", numberCoresPerCPU)
        theNode.setSingleAttribute("cputype", cpuDescription)
        theNode.setSingleAttribute("cpuspeed", cpuSpeed)
        theNode.setSingleAttribute("memory", systemMemory)
        theNode.setSingleAttribute("motherboard", motherboard)

        # Add the interfaces into the node
        theNode.setInterfaces(nodeInterfaces, "all")

        # We now have the full information in a node object, write it out
        if self.__debug_mode:
            log.debug("Running in debug mode")
            log.debug("return code: %s" % \
                      str(self.__manager.parser.writeNodePhysicalFile(theNode,True)))
            log.debug("Power node id "+str(theNode.getPowerNodeID()))
        else:
            log.debug("return code: %s" % \
                      str(self.__manager.parser.writeNodePhysicalFile(theNode)))
            
    def __cpuSpeedToGiga(self, cpuSpeed):
        """\brief Converts a CPU's speed in hertz to GHz
        \param cpuSpeed (\c string) A string with the CPU's speed in Hz
        \return (\c int) The CPU's speed in GHz
        """
        try:
            cpuSpeed = int(cpuSpeed)
        except:
            return -1
        return cpuSpeed * self.__toGiga

    def __memoryToGiga(self, memory):
        """\brief Converts a computer's main memory from bytes to GBs
        \param memory (\c string) A string with the computer's main memory in
                                    bytes
        \return (\c int) The computer's main memory in GBs
        """
        try:
            memory = int(memory)
        except:
            return -1
        return memory * self.__toGigaBinary

    def __processQuerySwitchDBsReply(self, code, seq, sz, payload):
        """\brief Callback handler for request to query switches' databases
        """
        pass

    def __processDetectIfacesReply(self, code, seq, sz, payload):
        """\brief Callback handler for request to retrieve the ports that a
            node's interfaces are connected to.
        """
        #self.__detectedInterfaces = None
        self.__detectedInterfaces = pickle.loads(payload)
        log.debug("detected interfaces:"+str(self.__detectedInterfaces))

    def __getData(self, parent):
        """\brief Returns an xml node's data
        \param (\c xml node) The parent to obtain data from
        \return (\c string) The data
        """
        nodes = parent.childNodes
        for node in nodes:
            if node.nodeType == Node.TEXT_NODE:
                return node.data.strip()

    def __getSystemMemory(self, nodeXML):
        """\brief Adds all the memory in the different banks and returns that
            value
        \param (\c xml node) The parent node containing the memory information
        \return (\c int) The total system memory in bytes
        """
        systemMemory = 0
        for xmlNode in nodeXML.getElementsByTagName("node"):
            theID = xmlNode.attributes["id"].value
            if (theID.find("memory") != -1):
                for memoryNode in xmlNode.getElementsByTagName("node"):
                    memorySize = memoryNode.getElementsByTagName("size")
                    if (memorySize):
                        systemMemory += \
                            int(memorySize.item(0).firstChild.nodeValue)
        return systemMemory

    def enableDebugMode(self):
        self.__debug_mode = True

    def disableDebugMode(self):
        self.__debug_mode = False

class AutodetectManager(Daemon):

    __hen_manager = None
    __hardware_processor = None

    def __init__(self):
        Daemon.__init__(self)
        self.__hen_manager = HenManager()
        self.__hen_manager.initLogging()
        self.__hardware_processor = LSHardwareProcessor(self.__hen_manager, \
                                                    self.__parseMacTableURL())
        self.__registerMethods()

    def __parseMacTableURL(self):
        """\brief Parses the Hen config file, and returns the MACTABLE_URL
            \return macTableURL - the value of MACTABLE_URL in the Hen config
        """
        configFile = ConfigParser.ConfigParser()
        configFile.read(HEN_CONFIG)
        return configFile.get('AUTODETECT', 'MACTABLE_URL')

    def __registerMethods(self):
        self.registerMethodHandler("receive_detectiondata", \
                                   self.receiveDetectionData)
        self.registerMethodHandler("enable_debug_mode", \
                                   self.enableDebugMode)
        self.registerMethodHandler("disable_debug_mode", \
                                   self.disableDebugMode)

    def enableDebugMode(self,prot,seq,ln,payload):
        self.__hardware_processor.enableDebugMode()
        prot.sendReply(200, seq, "")

    def disableDebugMode(self,prot,seq,ln,payload):
        self.__hardware_processor.disableDebugMode()
        prot.sendReply(200, seq, "")
        
    def receiveDetectionData(self,prot,seq,ln,payload):
        """\brief Method called when detection data is received from
            autodetectclient scripts being run on remote hosts.
        """
        log.debug("receiveDetectionData() called.")
        (nodeid, addr) = self.__ipAddressToNodeID(prot.getSocket())
        if not nodeid or not addr:
            log.warning("Bad results from __ipAddressToNodeID().")
            prot.sendReply(500, seq, \
                   "Failure: Daemon could not resolve IP to nodeid.")
            return
        log.info("received data from %s (%s)" % (str(addr), str(nodeid)))
        prot.sendReply(200, seq, "")
        self.__hardware_processor.parseFileAndPrint(nodeid, payload)


    def __ipAddressToNodeID(self, sock):
        """\brief Retrieves the IP address of the connected client, then tries
            to look up a nodeid for it from HenManager
            \param sock - socket on which the client is connected
            \return nodeid - id of node to which IP address belongs, -1 if not
                                found
        """
        try:
            (addr, port) = sock.getpeername()       
            log.debug("addr %" + str(addr))            
            computerNodes = self.__hen_manager.getNodes("computer", "all")
            for computerNode in computerNodes.values():
                interfaces = computerNode.getInterfaces("management")
                for interface in interfaces:
                    if (interface.getIP() == addr):
                        return (computerNode.getNodeID(), addr)
        except:
            pass
        return (None, None)

class AutodetectDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    __bind_addr = DaemonLocations.autodetectDaemon[0]
    __port = DaemonLocations.autodetectDaemon[1]
    __sockd = None
    __am = None

    def __init__(self, doFork):
        Daemonizer.__init__(self, doFork)

    def run(self):
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        self.__sockd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        self.__sockd.settimeout(2) # 2 second timeouts
        log.debug("Creating AutodetectManager")
        self.__am = AutodetectManager()
        log.debug("Starting AutodetectManager")
        self.__am.start()
        while self.__am.isAlive():
            if self.__am.acceptingConnections():
                # allow timeout of accept() to avoid blocking a shutdown
                try:
                    (s,a) = self.__sockd.accept()
                    log.info("New connection established from " + str(a))
                    self.__am.addSocket(s)
                except:
                    pass
            else:
                log.debug("AutodetectManager still alive, but not accepting" + \
                          " connections")
                time.sleep(2)
        log.debug("Closing socket.")
        self.__sockd.shutdown(socket.SHUT_RDWR)
        self.__sockd.close()
        while threading.activeCount() > 1:
            cThreads = threading.enumerate()
            log.debug("Waiting on " + str(threading.activeCount()) + \
                      " active threads...")
            time.sleep(2)
        log.debug("AutodetectDaemon Finished.")
        # Now everything is dead, we can exit.
        sys.exit(0)

    def setDBDirectory(self, dbDir):
        self.__monitor_db_dir = dbDir

def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    WORKDIR = '/var/hen/autodetectdaemon'
    PIDDIR = '/var/run/hen'
    LOGDIR = '/var/log/hen/autodetectdaemon'
    LOGFILE = 'autodetectdaemon.log'
    PIDFILE = 'autodetectdaemon.pid'
    GID = 17477 # schooley
    UID = 17477 # schooley
    autodetectd = AutodetectDaemon(False)
    autodetectd.setWorkingDir(WORKDIR)
    autodetectd.setPIDDir(PIDDIR)
    autodetectd.setLogDir(LOGDIR)
    autodetectd.setLogFile(LOGFILE)
    autodetectd.setPidFile(PIDFILE)
    autodetectd.setUid(UID)
    autodetectd.setGid(GID)
    autodetectd.start()

if __name__ == "__main__":
    main()
