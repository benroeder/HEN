import sys, os, socket, pickle, ConfigParser, time
from xml.dom import minidom
from xml.dom.minidom import Node, Element
import auxiliary.protocol
from henmanager import HenManager
from auxiliary.hen import Interface
from auxiliary.daemonlocations import DaemonLocations

class LSHardwareProcessor:
    """\brief A class that parses output from lshw, autodetects interface information, and
    can print a string to the console containing a node's physical description file
    """
    def __init__(self, manager=None):
        """\brief Initializes class
        \param manager (\c HenManager) The HenManager object used to parse the testbed's database
        \param macTableURL (\c string) URL to retrieve switch database information from
        """
        self.__manager = manager
        self.__detectedInterfaces = None
        self.__toGiga = (1.0 / 10 ** 9)
        self.__toGigaBinary = (1.0 / 2 ** 30)
        self.__MAX_NUMBER_DETECTION_TRIES = 3

    def parseFileAndPrint(self, theNodeID, lshwOutput):
        """\brief Parses the given string produced by lshw and creates a node's physical description
        file from it. It also autodetects interface information for the node, including their
        speeds, models, and what switch and port they're plugged into. It then writes this information
        to the node's physical description file.
        \param theNodeID (\c string) The id of the node            
        \param lshwOuput (\c string) The lshw output received from the client. This consists of the xml output
                                     from lshw prepended by: <numbercpus>x</numbercpus>, where x is the number
                                     of cpus in the system.
        """
        print "parsing lshw output..."

        # First retrieve the number of cpus and remove this from the string containing the lshw data
        numberCPUs = lshwOutput[lshwOutput.find(">") + 1:lshwOutput.find("<", 1)]
        lshwOutput = lshwOutput[lshwOutput.find("/numbercpus") + 12:]

        # Do the same for the number of cores per cpu
        numberCoresPerCPU = lshwOutput[lshwOutput.find(">") + 1:lshwOutput.find("<", 1)]
        lshwOutput = lshwOutput[lshwOutput.find("/numbercorespercpu") + 19:]

        # Retrieve the mac addresses of interfaces that have no carrier sense
        #<nocarriermacs>00:14:4F:40:77:5D,00:11:22:33:44:55</nocarriermacs>
        noCarrierMACs = lshwOutput[lshwOutput.find(">") + 1:lshwOutput.find("<", 1)]
        noCarrierMACs = noCarrierMACs.split(",")
        lshwOutput = lshwOutput[lshwOutput.find("/nocarriermacs") + 15:]

        try:
            xmldoc = minidom.parseString(lshwOutput)
            nodeXML = xmldoc.getElementsByTagName("node")
        except:
            print "error while parsing, ignoring client request..."
            return

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
                    for element in elements:
                        usbVersion = usbVersionMap[self.__getData(element)]
                        print usbVersion
                        break
                
                # Retrieve motherboard information
                elif (nodeClass == "system"):
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
                elif (nodeClass == "processor"):
                    logName = tag.getElementsByTagName("product")
                    for l in logName:
                        if (not cpuDescription):
                            cpuDescription = self.__getData(l)
                    
                    logName = tag.getElementsByTagName("size")
                    for l in logName:
                        if (not cpuSpeed):
                            cpuSpeed = self.__cpuSpeedToGiga((self.__getData(l)))
                            
                # Retrieve network interface information
                elif (nodeClass == "network"):
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
                    interface = Interface(macAddress.upper(), None, None, None, None, None, None, ethernetSpeed, ethernetModel, ethernetName)
                    interfaces.append(interface)

        # Auto detect which switch and port each interface is connected to. Results are stored
        # in self.__detectedInterfaces, a dictionary of (switchid, port name) tuples. First
        # force switch daemon to query switch databases
        print "waiting 10 seconds for switch databases to 'settle'..."
        time.sleep(10)
        
        p = auxiliary.protocol.Protocol(None)
        p.open(DaemonLocations.switchDaemon[0], DaemonLocations.switchDaemon[1])
        method = "redetect_fdb"
        print "forcing switch daemon to query switch databases"
        p.sendRequest(method, pickle.dumps(macAddresses), self.__processQuerySwitchDBsReply)
        p.readAndProcess()        

        numberTries = 0
        undetectedInterfaces = True
        method = "find_unique_macs"
        while (numberTries < self.__MAX_NUMBER_DETECTION_TRIES and undetectedInterfaces):
            print "sleeping for 30 secs..."
            time.sleep(30)
            print "sending request to switch daemon's find_macs for:", macAddresses
            p.sendRequest(method, pickle.dumps(macAddresses), self.__processDetectIfacesReply)
            p.readAndProcess()
            numberTries += 1

            # Go through the reply for the switch daemon. If any of them is unknown and the
            # interface has carrier sense, try again, up to MAX_NUMBER_TRIES
            undetectedInterfaces = False
            for detectedInterfaceMAC in self.__detectedInterfaces.keys():
                if (self.__detectedInterfaces[detectedInterfaceMAC][0] == "unknown"):
                    if (detectedInterfaceMAC.upper() not in noCarrierMACs):
                        print "the following mac was not found:", detectedInterfaceMAC
                        undetectedInterfaces = True
                    else:
                        print "the following mac is being ignored due to lack of carrier sense:", detectedInterfaceMAC

        # nodeInterfaces will contain the full interface information for this node
        nodeInterfaces = {}
        nodeInterfaces["management"] = []
        nodeInterfaces["experimental"] = []

        # Fill in information for the management interface (some of its information
        # is already in its skeleton xml file, parse it and add to it)
        theNode = None
        nodes = self.__manager.getNodes("computer", "all")
        #print "computerid:", theNodeID
        for computerNode in nodes.values():
            if (computerNode.getNodeID() == theNodeID):
                theNode = computerNode
        
        managementInterface = theNode.getInterfaces("management")[0]
        if ( (self.__detectedInterfaces) and (self.__detectedInterfaces.has_key(managementInterface.getMAC())) ):
            managementInterface.setSwitch(self.__detectedInterfaces[managementInterface.getMAC()][0])
            managementInterface.setPort(self.__detectedInterfaces[managementInterface.getMAC()][1])            
        nodeInterfaces["management"].append(managementInterface)
                                                                    
        # Fill in information for the experimental interfaces
        for interface in interfaces:
            if ( (self.__detectedInterfaces) and (self.__detectedInterfaces.has_key(interface.getMAC()) ) ):
                interface.setSwitch(self.__detectedInterfaces[interface.getMAC()][0])
                interface.setPort(self.__detectedInterfaces[interface.getMAC()][1])
            if (interface.getMAC().upper() != nodeInterfaces["management"][0].getMAC().upper()):
                nodeInterfaces["experimental"].append(interface)
                                    
        # We now have the full information for the interfaces, construct the Node object
        print "writing description file..."        

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
        print "return code: " + str(self.__manager.parser.writeNodePhysicalFile(theNode)) + "\n"

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
        \param memory (\c string) A string with the computer's main memory in bytes
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
        """\brief Callback handler for request to retrieve the ports that a node's interfaces are connected to.
        """
        #self.__detectedInterfaces = None
        self.__detectedInterfaces = pickle.loads(payload)
        #print "detected interfaces:", self.__detectedInterfaces
    
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
        """\brief Adds all the memory in the different banks and returns that value
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
                        systemMemory += int(memorySize.item(0).firstChild.nodeValue)
        return systemMemory
    
    def ipAddressToName(self, address):
        computerNodes = self.__manager.getNodes("computer", "all")

        for computerNode in computerNodes.values():
            interfaces = computerNode.getInterfaces("management")

            for interface in interfaces:
                if (interface.getIP() == address):
                    return computerNode.getNodeID()

        return -1
        
                                                
###########################################################################################
#   Main execution
###########################################################################################
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((DaemonLocations.autodetectDaemon[0], DaemonLocations.autodetectDaemon[1]))
print DaemonLocations.autodetectDaemon[0], DaemonLocations.autodetectDaemon[1]
sock.listen(5)

try:
    configFile = ConfigParser.ConfigParser()
    configFile.read('/usr/local/hen/etc/configs/config')
    manager = HenManager()
    manager.initLogging()
    processor = LSHardwareProcessor(manager)
                                                        
    while 1:
        newSocket, address = sock.accept()

        receivedData = ""
        while 1:
            newData = newSocket.recv(1024)

            if not newData:
                break
            receivedData += newData

        if (str(address[0]) != "192.168.0.1"):
            theNodeID = processor.ipAddressToName(address[0])
            print "\nreceived data from " + str(address[0]) + " (" + str(theNodeID) + ")"
            processor.parseFileAndPrint(theNodeID, receivedData)

        newSocket.close()
finally:
    sock.close()
