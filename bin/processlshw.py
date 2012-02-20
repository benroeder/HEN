#!/usr/bin/env python
##################################################################################################################
# processlsh.py: Class and runnable script that parses output from lshw, autodetects interface information, and
#                prints a string to the console containing a node's physical description file
#
##################################################################################################################
import sys, os
sys.path.append("/usr/local/hen/lib")
os.environ["PATH"] += ":/usr/local/bin:/usr/bin"
from xml.dom import minidom
from xml.dom.minidom import Node, Element
import time, commands, ConfigParser
from henmanager import HenManager
from auxiliary.hen import Interface

# Defines how many times to try to detect mac addresses from the url before giving up
URL_GET_MAX_NUMBER_TRIES = 1
# Defines how many seconds to sleep between tries
SLEEP_TIME = 3

class LSHardwareProcessor:
    """\brief A class that parses output from lshw, autodetects interface information, and
              can print a string to the console containing a node's physical description file
    """
    
    def __init__(self, manager=None, macTableURL=None):
        """\brief Initializes class
        \param manager (\c HenManager) The HenManager object used to parse the testbed's database
        \param macTableURL (\c string) URL to retrieve switch database information from
        """
        self.__manager = manager
        self.__macTableURL = macTableURL

    def parseFileAndPrint(self, filename, theNodeID):
        """\brief Parses the given filename produced by lshw and creates a node's physical description
                  file from it. It also autodetects interface information for the node, including their
                  speeds, models, and what switch and port they're plugged into. It then creates a string
                  with all this information and prints this string to the console
        \param filename (\c string) The path and filename of the lshw output
        \param theNodeID (\c string) The id of the node to process information for
        """
        interfaces = [] 
        motherboard = None
        memorySize = None
        cpuDescription = None
        cpuSpeed = None
        numberCPUs = None
    
        # Determine the number of cpus in the sytem
        result = commands.getstatusoutput("cat /proc/cpuinfo | grep processor | wc -l")
        if (result[0] == 0):
            numberCPUs = result[1]
        
        xmldoc = minidom.parse(filename)
        nodeXML = xmldoc.getElementsByTagName("node")
        for tag in nodeXML :
            macAddress = None
            ethernetName = None
            ethernetModel = None
            ethernetSpeed = None

            if (tag.attributes.has_key("class")):
                nodeClass = tag.attributes["class"].value
                nodeID = tag.attributes["id"].value

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

                # Retrieve cpu information
                counter = 0
                if (nodeClass == "processor"):
                    logName = tag.getElementsByTagName("product")
                    for l in logName:
                        cpuDescription = self.__getData(l)
                    logName = tag.getElementsByTagName("size")
                    for l in logName:
                        if counter == 0:
                            cpuSpeed = self.__getData(l)
                            counter = counter + 1
		
                # Retrieve system memory information
                if (nodeClass == "memory" and nodeID == "memory"):
                    logName = tag.getElementsByTagName("size")
                    for l in logName:
                        memorySize = self.__getData(l)
		
                # Retrieve network interface information
                if (nodeClass == "network"):
                    logName = tag.getElementsByTagName("serial")
                    for l in logName:
                        macAddress = self.__getData(l)
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
                    self.__pollInterface(interface)

        # We now must append information about what switch and port number the interfaces are connected to
        interfaces = self.__getMACTable(interfaces)

        # We now have the full information for the interfaces, construct the Node object
        theNode = None
        nodes = self.__manager.getNodes("computer", "all")
        for computerNode in nodes.values():
            if (computerNode.getNodeID() == theNodeID):
                theNode = computerNode

        # Append attribute information to the node
        theNode.setSingleAttribute("numbercpus", numberCPUs)
        theNode.setSingleAttribute("cputype", cpuDescription)
        theNode.setSingleAttribute("cpuspeed", cpuSpeed)
        theNode.setSingleAttribute("memory", memorySize)
        theNode.setSingleAttribute("motherboard", motherboard)        

        # At this point the current xml file for the node has only its management interface, retrieve it
        managementInterface = theNode.getInterfaces("management")[0]

        # nodeInterfaces will contain the full interface information for this node
        nodeInterfaces = {}
        nodeInterfaces["management"] = []
        nodeInterfaces["experimental"] = []
            
        for detectedInterface in interfaces:
            # We've found switch and port info for the management interface, update it
            if (detectedInterface.getMAC().upper() == managementInterface.getMAC().upper()):
                managementInterface.setSwitch(detectedInterface.getSwitch())
                managementInterface.setPort(detectedInterface.getPort())
                managementInterface.setSpeed(detectedInterface.getSpeed())
                managementInterface.setModel(detectedInterface.getModel())
                managementInterface.setName(detectedInterface.getName())
                nodeInterfaces["management"].append(managementInterface)
            # The interface is experimental, just add it to the list of experimental interfaces
            else:
                nodeInterfaces["experimental"].append(detectedInterface)
       
        # Now readd the interfaces into the node
        theNode.setInterfaces(nodeInterfaces, "all")

        # We now have the full information in a node object, construct a string for the node's
        # physical description file and print it
        self.__printNodePhysicalFile(theNode)
    
    def __getMACTable(self, interfaces):
        """\brief Retrieves mac address information from the given url, matching it against the
              mac addresses of the given interfaces. If a match is found, that interface's
              switch and port entries are updated. The list of updated interfaces is then
              returned. The url is a link to a webpage retrieving the switch databases of all
              management switches on the testbed. These databases may take a bit to update, so
              the detection process is run twice, spleeing three seconds between tries or only
              once if all the interfaces are matched straight away.
        \param interfaces (\clist of Interfaces) The interfaces to match against
        """
        numberIfaces = len(interfaces)
        numberIfacesFound = 0
        numberTries = 0
        foundInterfaces = []

        cmd = "lynx -dump " + self.__macTableURL
        while ((numberIfacesFound != numberIfaces) and (numberTries < URL_GET_MAX_NUMBER_TRIES)):
            lines = commands.getstatusoutput(cmd)[1].splitlines()

            for line in lines:
                line = (line.lstrip(' ')).split(' ')
                for index in range (0, len(interfaces)):
                    interface = interfaces[index]
                    if (interface.getMAC() == line[0] and interface.getMAC() not in foundInterfaces):
                        interfaces[index].setSwitch(line[1])
                        if (line[1] == "switch14"):
                            interfaces[index].setPort(line[2]+" "+line[3])
                        else:
                            interfaces[index].setPort(line[2])
                        foundInterfaces.append(interface.getMAC())
                        numberIfacesFound += 1

            if (numberIfacesFound != numberIfaces):
                for interface in interfaces:
                    self.__pollInterface(interface)
            
            time.sleep(SLEEP_TIME)
            numberTries += 1

        return interfaces	

    def __pollInterface(self, interface):
        """\brief Brings the given interface up and sends a dummy ethernet frame on it
        \param interface (\c Interface) An Interface object representing the interface to poll
        """
        cmd = "/sbin/ifconfig " + interface.getName() + " up"
        os.system(cmd)
        cmd = "etherwake -i " + interface.getName() + " 00:11:22:33:44:55"
        os.system(cmd)

    def __getData(self, parent):
        """ Returns an xml node's data
        \parent (\c xml node) The parent to obtain data from
        \return (\c string) The data
        """
        nodes = parent.childNodes
        for node in nodes:
            if node.nodeType == Node.TEXT_NODE:
                return node.data.strip()

    def __printNodePhysicalFile(self, node):
        """\brief Writes the initial physical file for a node
        \param node (\c Node) An object sub-classed from Node with the necessary information
        """
        # Write node tag
        string = '<node type="' + str(node.getNodeType()) + '" id="' + str(node.getNodeID()) + \
                 '" netbootable="' + str(node.getNetbootable()) + '" infrastructure="' + \
                 str(node.getInfrastructure())

        # Write vendor attribute, if any
        if (node.getVendor() != None):
            string += '" vendor="' + str(node.getVendor())

        # Write model attribute, if any
        if (node.getModel() != None):
            string += '" model="' + str(node.getModel())

        # Write end of node tag
        string += '">\n\n'

        # Write physical location tag, if any
        physicalLocation = node.getPhysicalLocation()
        if (physicalLocation!= None):
            string += '\t<physicallocation building="' + str(physicalLocation.getBuilding()) + \
                      '" floor="' + str(physicalLocation.getFloor()) + \
                      '" room="' + str(physicalLocation.getRoom()) + \
                      '" rackrow="' + str(physicalLocation.getRackRow()) + \
                      '" rackname="' + str(physicalLocation.getRackName()) + \
                      '" rackstartunit="' + str(physicalLocation.getRackStartUnit()) + \
                      '" rackendunit="' + str(physicalLocation.getRackEndUnit()) + \
                      '" position="' + str(physicalLocation.getNodePosition()) + '" />\n'

        # Write serial peripheral, if any
        if (node.getSerialNodeID() != None):
            string += '\t<peripheral type="serial" id="' + str(node.getSerialNodeID()) + \
                      '" remoteport="' + str(node.getSerialNodePort()) + '" />\n'

        # Write power switch peripheral, if any
        if (node.getPowerNodeID() != None):
            string += '\t<peripheral type="powerswitch" id="' + str(node.getPowerNodeID()) + \
                      '" remoteport="' + str(node.getPowerNodePort()) + '" />\n'

        # Write service processor perirepheral, if any
        if (node.getSPNodeID() != None):
            string += '\t<peripheral type="serviceprocessor" id="' + str(node.getSPNodeID()) + '" />\n'

        string += '\n'
        # Write infrastructure interfaces, if any
        interfaces = node.getInterfaces("infrastructure")
        if ((interfaces != None) and (len(interfaces) != 0)):
            for interface in interfaces:
                string += '\t<interface type="infrastructure" ip="' + str(interface.getIP()) + \
                          '" subnet="' + str(interface.getSubnet()) + '" mac="' + str(interface.getMAC()) + \
                          '" switch="' + str(interface.getSwitch()) + '" port="' + str(interface.getPort()) + \
                          '" model="' + str(interface.getModel()) + '" speed="' + str(interface.getSpeed()) + '" />\n'
            string += '\n'

        # Write management interfaces, if any
        interfaces = node.getInterfaces("management")
        if ((interfaces != None) and (len(interfaces) != 0)):
            interface = interfaces[0]
            for interface in interfaces:
                string += '\t<interface type="management" ip="' + str(interface.getIP()) + \
                          '" subnet="' + str(interface.getSubnet()) + '" mac="' + str(interface.getMAC()) + \
                          '" switch="' + str(interface.getSwitch()) + '" port="' + str(interface.getPort()) + \
                          '" model="' + str(interface.getModel()) + '" speed="' + str(interface.getSpeed()) + '" />\n'
            string += '\n'

        # Write experimental interfaces, if any
        interfaces = node.getInterfaces("experimental")
        if ((interfaces != None) and (len(interfaces) != 0)):
            interface = interfaces[0]
            for interface in interfaces:
                string += '\t<interface type="experimental" ip="' + str(interface.getIP()) + \
                          '" subnet="' + str(interface.getSubnet()) + '" mac="' + str(interface.getMAC()) + \
                          '" switch="' + str(interface.getSwitch()) + '" port="' + str(interface.getPort()) + \
                          '" model="' + str(interface.getModel()) + '" speed="' + str(interface.getSpeed()) + '" />\n'
            string += '\n'
        
        # Write user management, if any
        #user = node.getUser()
        #if (user != None):
        #    string += '\t<usermanagement username="' + user.getUsername() + '" password="' + user.getPassword() + '" />\n'
        #string += '\n'
        
        # Write attributes, if any
        attributes = node.getAttributes()
        if (attributes != None and len(attributes) != 0):
            for attribute in attributes.keys():
                string += '\t<attribute name="' + str(attribute) + '" value="' + str(attributes[attribute]) + '" />\n'

        # Write closing tag
        string += '\n</node>'

        print string


###########################################################################################
#   Main execution
###########################################################################################
if (len(sys.argv) != 3):
	print "usage: python processlshw [xml file] [node id]"
	os._exit(1)
else:
        configFile = ConfigParser.ConfigParser()	
        configFile.read('/usr/local/hen/etc/configs/config')
        macTableURL = configFile.get('AUTODETECT', 'MACTABLE_URL')
        manager = HenManager()
        manager.initLogging()

        processor = LSHardwareProcessor(manager, macTableURL)
        processor.parseFileAndPrint(sys.argv[1], sys.argv[2])
