###############################################################################################################
# hen.py: the main library file for classes and functions.
#
# CLASSES
# --------------------------------------------------------------------
# Node                 Superclass for any physical piece of equipment
# ComputerNode         Subclass of Node for computer nodes
# MoteNode             Subclass of Node for motes
# SwitchNode           Subclass of Node for switches
# PowerSwitchNode      Subclass of Node for power switches (controllers)
# SerialNode           Subclass of Node for terminal servers
# RouterNode           Subclass of Node for routers
# ServiceProcessorNode Subclass of Node for a service processor
# SensorNode           Subclass of Node for sensors
# KVMNode              Subclass of Node for KVM switches
#
# Infrastructure         Superclass for any passive infrastructure (racks, etc)
# InfrastructureRack     Subclass of Infrastructure for racks
# InfrastructureFloorBox Subclass of Infrastructure for floor boxes
# FloorBoxPowerPlug      Used to hold information about a floorbox's power plug
# FloorBoxRJ45Port       Used to hold information about a floorbox's rj 45 port
#
# FileNode             Superclass for any file on the testbed
# FilesystemFileNode   Subclass for a testbed filesystem
# KernelFileNode       Subclass for a testbed kernel
# LoaderFileNode       Subclass for a testbed loader
#
# Link                 Superclass for links in the testbed
# DirectLink           Subclass for direct connections
#
# UserExperiment       Used to hold experiment information for users
# ExperimentNode       Used to hold information about a node being used in an experiment
# NetbootInfo          Used to tell a computer node what to netboot 
# DHCPConfigInfo       Used to hold information needed to create a dhcp config file
# DHCPConfigSubnetInfo Used to hold information needed to create a subnet entry in a dhcp config file
# DNSConfigInfo        Used to hold information needed to create dns forward and reverse lookup files
# UserManagement       Used to hold information about a user
# PhysicalTopologyEntry Used to hold information about an entry in the main topology.xml physical file
# ExperimentTopologyEntry Used to hold information about an entry in the main topology.xml experiment file
# TestbedFileTopologyEntry Used to hold information about an entry in the testbed files main topology.xml file
# PhysicalLocation     Used to hold information about a node's physical location
# PhysicalSize         Used to hold size information about a piece of infrastructure
# Peripheral           Used to hold information about what a node is connected to (a computer to a power switch, etc)
# Interface            Used to hold information about a network interface 
# VLAN                 Used to hold vlan information
# Port                 Used to hold information about a port on a switch
# MACTableEntry        Used to hold information about a mac address entry in a switch
# LDAPInfo             Used to hold information returned from an LDAP server
# LogEntry             Used to hold information about a testbed log entry
#
# FUNCTIONS
# --------------------------------------------------------------------
# reverseIPAddress            Reverses an IP address (12.13.14.15 becomes 15.14.13.12)
# getTime                     Gets the current time in the format %d-%b-%Y-%H-%M
# getUserName                 Returns the user name of the proccess calling the program
# datesOverlap                True if the given date ranges overlap, false otherwise
# isValueInDictionaryOfLists  True if the given value is in the dictionary of lists, false otherwise
# isVLANInList                Returns the index of the found entry, or -1 if not found
# isHigherIPAddress           Returns true if the first parameter is a higher IP address than the second one
# getPartialIPNumber          Returns a part of an IP address
# incrementIPAddress          Returns a string representing the incremented parameter's IP address
# convertHexCharacterToInt    Converts a string containing a single hex char to int
# convertIntToHexCharacter    Converts an integer between 0-15 to a string with a single hex char
#
##################################################################################################################

import copy, string, os, hashlib, commands, logging
from time import strftime, gmtime

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

class SerialInfo:
    def __init__(self):
        self.__serialNodeID = None
        self.__serialNodePort = None

    def setSerialNodeID(self, s):
        """\brief Sets the node serial node id
        \param n (\c string) The node's serial node id
        """
        self.__serialNodeID = s

    def getSerialNodeID(self):
        """\brief Gets the node serial node id
        \return (\c string) The node's serial node id
        """
        return self.__serialNodeID

    def setSerialNodePort(self, s):
        """\brief Sets the node serial node port
        \param n (\c string) The node's serial node port
        """
        self.__serialNodePort = s

    def getSerialNodePort(self):
        """\brief Gets the node serial node port
        \return (\c string) The node's serial node port
        """
        return self.__serialNodePort

class PowerInfo:
    def __init__(self):
        self.__powerNodes = None

    def setPowerNodes(self, p):
        """\brief Sets the node power node id
        \param n (\c list of string,string tuples) The node's power node ids and ports
        """
        self.__powerNodes = p

    def getPowerNodes(self):
        """\brief Gets the node power node id
        \return (\c list of string,string tuples) The node's power node ids and ports
        """
        return self.__powerNodes

    def getPowerNodeID(self):
        if (self.__powerNodes == None) or (len(self.__powerNodes) == 0) :
            return None
        return self.__powerNodes[0][0]

    def getPowerNodePort(self):
        if (self.__powerNodes == None) or (len(self.__powerNodes) == 0) :
            return None
        return self.__powerNodes[0][1]

    def setPowerNodeID(self,id):
        if self.__powerNodes == None :
            self.__powerNodes = [(None,None)]

        if len(self.__powerNodes) == 1:
            self.__powerNodes[0][0] = id
        else :
            raise Exception("attempted to set power node id ambiguously: use setPowerNodes")

    def setPowerNodePort(self,port):
        if self.__powerNodes == None :
            self.__powerNodes = [(None,None)]

        if len(self.__powerNodes) == 1:
            self.__powerNodes[0][1] = port
        else :
            raise Exception("attempted to set power node port ambiguously: use setPowerNodes")

class Node:
    """\brief Superclass for any physical piece of equipment
    The Node class acts as a virtual class for all pieces of physical equipment in the testbed, it should
    not be instantiated directly.
    """

    def __init__(self, nodeID=None, nodeType=None, interfaces=None, netBootable=None, \
                    infrastructure=None, vendor=None, model=None, attributes=None, physicalLocation=None, \
                    dhcp=None, status=None, priority=10):
        """\brief Initializes the class
        \param nodeID (\c string) The name of id of the node
        \param nodeType (\c string) The type of the node, in essence one of the subclasses of this class
        \param interfaces (\c dictionary) A dictionary whose keys are the interface types
                                          and whose values are lists of Interface objects
        \param netBootable (\c string) Set to yes if the node is netbootable, no otherwise
        \param infrastructure (\c string) Set to yes if the node is infrastructure, no if it is experimental
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param attributes (\c dictionary) The node's attributes (see henParser.parseAttributes)
        \param physicalLocation (\c PhysicalLocation) A PhysicalLocation object representing the node's location in the testbed
        \param dhcp (\c string) Whether the node will dhcp or not
        \param status (\c string) One of: operational, maintenance, retired, dead
        """
        self.__nodeID = nodeID
        self.__nodeType = nodeType
        self.__netBootable = netBootable
        self.__infrastructure = infrastructure
        self.__vendor = vendor
        self.__model = model
        self.__physicalLocation = physicalLocation
        self.__dhcp = dhcp
        self.__status = status
        self.__priority = priority
        
        if (interfaces == None):
            self.__interfaces = {}
        else:
            self.__interfaces = interfaces

        if (attributes == None):
            self.__attributes = {}
        else:
            self.__attributes = attributes

        self.__peripherals = {}

    def addPeripheral(self, p) :
        """\brief add a peripheral to node's list
        \param (\c Peripheral) peripheral object
        """
        self.__peripherals[(p.getPeripheralID(),p.getPeripheralLocalPort(),p.getPeripheralRemotePort())] = p

    def getPeripherals(self) :
        """\brief returns a dictionary of all peripherals keyed to peripheral id
        \return (\c dict) dict of peripherals 
        """
        return self.__peripherals

    def getPeripheralsByType(self,type) :
        """\brief returns a list of peripherals of a specified type
        *quick and dirty version*
        """
        return filter(lambda x : x.getPeripheralType() == type, self.__peripherals.values())

    def getPeripheralIDs(self) :
        return map(lambda x : x.getPeripheralID(), self.__peripherals.values())

    def setNodeID(self, n):
        """\brief Sets the node id
        \param n (\c string) The node's id
        """
        self.__nodeID = n

    def getNodeID(self):
        """\brief Gets the node id
        \return (\c string) The node's id
        """
        return self.__nodeID

    def setStatus(self, status):
        """\brief Sets the status of the node (either operational, maintenance, retired or dead)
        \param status (\c string) The status of the node
        """
        self.__status = status

    def getStatus(self):
        """\brief Gets the status of the node (either operational, maintenance, retired or dead)
        \return (\c string) The status of the node
        """
        return self.__status

    def setPriority(self, priority):
        """\brief Sets the priority of the node (10 low, 1 high)
        \param priority (\c int) The priority of the node
        """
        if priority == None:
            priority = 10
        self.__priority = priority

    def getPriority(self):
        """\brief Gets the priority of the node (10 low, 1 high)
        \return (\c int) The priority of the node
        """
        return self.__priority    

    def setNodeType(self, n):
        """\brief Sets the node type
        \param n (\c string) The node's type
        """
        self.__nodeType = n

    def getNodeType(self):
        """\brief Gets the node type
        \return (\c string) The node's type
        """
        return self.__nodeType

    def setInterfaces(self, interfaces, interfaceType="all"):
        """\brief Sets the node's interfaces. The data structure is a dictionary whose keys are the
                  interfaces' types and whose values are lists of Interface objects. If interfaceType
                  is set to all (the default value), the interfaces parameter should be this dictionary.
                  If interfaceType is set to one of experimental, management, infrastructure, external or
                  unassigned, then the interfaces parameter should consist of a list of Interface objects
        \param interfaces (\c dictionary or list) The interfaces
        \param interfaceType (\c string) One of all, experimental, management, infrastructure, external or unassigned
        """
        if (interfaceType == "all"):
            self.__interfaces = interfaces
        else:
            self.__interfaces[interfaceType] = interfaces
            
    def getInterfaces(self, interfaceType="all"):
        """\brief Gets the node's interfaces. The data structure is a dictionary whose keys are the
                  interfaces' types and whose values are lists of Interface objects. If interfaceType
                  is set to all, a dictionary is returned, otherwise a list is returned
        \param interfaceType (\c string) One of all, experimental, management, infrastructure, external or unassigned
        \return (\c dictionary or list) The interfaces
        """
        if (self.__interfaces == None or interfaceType == "all"):
            return self.__interfaces

        if (self.__interfaces.has_key(interfaceType)):
            return self.__interfaces[interfaceType]
        else:
            return None

    def setDHCP(self, d):
        """\brief Sets the node dhcp attribute
        \param d (\c string) The node's dhcp attribute
        """
        self.__dhcp = d

    def getDHCP(self):
        """\brief Gets the node dhcp attribute
        \return (\c string) The node's dhcp attribute
        """
        return self.__dhcp
    
    def setNetbootable(self, b):
        """\brief Sets the node netbootable attribute
        \param n (\c string) The node's netbootable attribute
        """
        self.__netBootable = b

    def getNetbootable(self):
        """\brief Gets the node netbootable attribute
        \return (\c string) The node's netbootable attribute
        """
        return self.__netBootable

    def setInfrastructure(self, i):
        """\brief Sets the node infrastructure attribute
        \param n (\c string) The node's infrastructure attribute
        """
        self.__infrastructure = i
        
    def getInfrastructure(self):
        """\brief Gets the node infrastructure attribute
        \return (\c string) The node's infrastructure attribute
        """
        return self.__infrastructure

    def setVendor(self, v):
        """\brief Sets the node vendor
        \param n (\c string) The node's vendor
        """
        self.__vendor = v

    def getVendor(self):
        """\brief Gets the node vendor
        \return (\c string) The node's vendor
        """
        return self.__vendor

    def setModel(self, m):
        """\brief Sets the node model
        \param n (\c string) The node's model
        """
        self.__model = m

    def getModel(self):
        """\brief Gets the node model
        \return (\c string) The node's model
        """
        return self.__model

    def getSingleAttribute(self, attributeKey):
        """\brief Gets a single value in the attributes dictionary.
        \param attributeKey (\c string) The key for the dictionary
        \return (\c string) The attribute's value or None if the attribute does not exist
        """
        if (self.__attributes == None):
            self.__attributes = {}

        if (self.__attributes.has_key(attributeKey)):
            return self.__attributes[attributeKey]
        else:
            return None
        
    def setSingleAttribute(self, attributeKey, value):
        """\brief Sets a single value in the attributes dictionary.
        \param attributeKey (\c string) The key for the dictionary
        \param value (\c string) The attribute's new value
        """
        if (self.__attributes == None):
            self.__attributes = {}

        self.__attributes[attributeKey] = value

    def setAttributes(self, a):
        """\brief Sets the node attributes
        \param n (\c dictionary) The node's attributes
        """
        self.__attributes = a

    def getAttributes(self):
        """\brief Gets the node attributes
        \return (\c dictionary) The node's attributes
        """
        return self.__attributes

    def setPhysicalLocation(self, p):
        """\brief Sets the node physical location
        \param n (\c string) The node's physical location
        """
        self.__physicalLocation = p

    def getPhysicalLocation(self):
        """\brief Gets the node physical location
        \return (\c string) The node's physical location
        """
        return self.__physicalLocation

    def getUsers(self):
        """\brief Virtual function placeholder
        \return (\c None)
        """        
        return None
    
    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "\tnodeID: " + str(self.getNodeID()) + "\n" + \
               "\tnodeType: " + str(self.getNodeType()) + "\n" + \
               "\tnetBootable: " + str(self.getNetbootable()) + "\n" + \
               "\tinfrastructure: " + str(self.getInfrastructure()) + "\n" + \
               "\tvendor: " + str(self.getVendor()) + "\n" + \
               "\tmodel: " + str(self.getModel()) + "\n" + \
               "\tstatus: " + str(self.getStatus()) + "\n" + \
               "\tpriority: " + str(self.getPriority()) + "\n" + \
               "\tphysicalLocation: " + str(self.getPhysicalLocation()) + "\n"

        # process interfaces
        string += "\tinterfaces: "
        interfaces = self.getInterfaces("all")
        if (interfaces == None):
            string += "None\n"
        else:
            for interfaceList in interfaces.values():
                if (interfaceList != None):
                    for interface in interfaceList:
                        string += "\n\t\t" + str(interface)
            string += "\n"
                    
        # process attributes 
        string += "\tattributes: "
        attributes = self.getAttributes()
        if (attributes == None):
            string += "None\n"
        else:
            string += "\n"
            for key in attributes.keys():
                string += "\t\tname: " + str(key) + "  value: " + str(attributes[key]) + "\n"

        return string

    def __cmp__(self,x):
        if x == None:
            return -1
        return cmp( \
            int(self.getNodeID()[len(self.getNodeType()):]), \
            int(   x.getNodeID()[len(self.getNodeType()):]) \
        )

class GenericComputerNode(Node,SerialInfo,PowerInfo):
    """ \brief subclass to group together commonalities between ServerNode, ComputerNode, MoteNode etc...
    """
    def __init__(self, nodeID=None, nodeType=None, interfaces=None, netBootable=None, \
                    infrastructure=None, vendor=None, model=None, attributes = None, \
                    physicalLocation=None):
        """\brief Initializes the class
        \param nodeID (\c string) The name of id of the node
        \param nodeType (\c string) The type of the node, in essence one of the subclasses of this class
        \param interfaces (\c dictionary) A dictionary whose keys are the interface types
                                          and whose values are lists of Interface objects
        \param netBootable (\c string) Set to yes if the node is netbootable, no otherwise
        \param infrastructure (\c string) Set to yes if the node is infrastructure, no if it is experimental
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param attributes (\c dictionary) The node's attributes (see henParser.parseAttributes)
        \param physicalLocation (\c string) The node's physical location in the building
        """
        Node.__init__(self, nodeID, nodeType, interfaces, netBootable, infrastructure, \
                vendor, model, attributes, physicalLocation)
        SerialInfo.__init__(self)
        PowerInfo.__init__(self)
        self.__kvmNodeID = None
        self.__spNodeID = None

    def setKVMNodeID(self, kvmID):
        """\brief Sets the node kvm id 
        \param n (\c string) The node's kvm id
        """
        self.__kvmNodeID = kvmID

    def getKVMNodeID(self):
        """\brief Gets the node kvm id
        \return (\c string) The node's kvm id
        """
        return self.__kvmNodeID

    def setSPNodeID(self, s):
        """\brief Sets the node service processor id 
        \param n (\c string) The node's service processor id
        """
        self.__spNodeID = s

    def getSPNodeID(self):
        """\brief Gets the node service processor id
        \return (\c string) The node's service processor id
        """
        return self.__spNodeID

    def setCPUType(self, c):
        """\brief Sets the node cpu type
        \param n (\c string) The node's cpu type
        """
        self.setSingleAttribute("cputype", c)

    def getCPUType(self):
        """\brief Gets the node cpu type
        \return (\c string) The node's cpu type
        """
        return self.getSingleAttribute("cputype")

    def setCPUSpeed(self, c):
        """\brief Sets the node cpu speed
        \param n (\c string) The node's cpu speed
        """
        self.setSingleAttribute("cpuspeed", c)

    def getCPUSpeed(self):
        """\brief Gets the node cpu speed
        \return (\c string) The node's cpu speed
        """
        return self.getSingleAttribute("cpuspeed")

    def setNumberCPUs(self, n):
        """\brief Sets the node's number of cpus
        \param n (\c string) The node's number of cpus
        """
        self.setSingleAttribute("numbercpus", n)

    def getNumberCPUs(self):
        """\brief Gets the node's number of cpus
        \return (\c string) The node's number of cpus
        """
        return self.getSingleAttribute("numbercpus")

    def setSystemMemory(self, s):
        """\brief Sets the node memory amount
        \param n (\c string) The node's memory amount
        """
        self.setSingleAttribute("memory", s)

    def getSystemMemory(self):
        """\brief Gets the node memory amount
        \return (\c string) The node's memory amount
        """
        return self.getSingleAttribute("memory")

    def setMotherboard(self, m):
        """\brief Sets the node motherboard
        \param n (\c string) The node's motherboard
        """
        self.setSingleAttribute("motherboard", m)

    def getMotherboard(self):
        """\brief Gets the node motherboard
        \return (\c string) The node's motherboard
        """
        attributes = self.getAttributes()
        if (attributes.has_key("motherboard")):
            return attributes["motherboard"]

    def __str__(self):
        string = ""
        string += Node.__str__(self)
        string += "\tserialNodeID: " + str(self.getSerialNodeID()) + "\n" + \
               "\tserialNodePort: " + str(self.getSerialNodePort()) + "\n" + \
               "\tkvmNodeID: " + str(self.getKVMNodeID()) + "\n" + \
               "\tspNodeID: " + str(self.getSPNodeID()) + "\n"
        if self.getPowerNodes() == None:
            return string
        for powerNode in self.getPowerNodes():
            string += "\tpowerNode: " + str(powerNode[0]) + "," + str(powerNode[1]) + "\n"

        return string

class ServerNode(GenericComputerNode):
    """\brief Subclass of Node for server nodes
    """
    
    def __init__(self, nodeID=None, nodeType=None, interfaces=None, netBootable=None, \
                    infrastructure=None, vendor=None, model=None, attributes = None, \
                    physicalLocation=None):
        """\brief Initializes the class
        \param nodeID (\c string) The name of id of the node
        \param nodeType (\c string) The type of the node, in essence one of the subclasses of this class
        \param interfaces (\c dictionary) A dictionary whose keys are the interface types
                                          and whose values are lists of Interface objects
        \param netBootable (\c string) Set to yes if the node is netbootable, no otherwise
        \param infrastructure (\c string) Set to yes if the node is infrastructure, no if it is experimental
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param attributes (\c dictionary) The node's attributes (see henParser.parseAttributes)
        \param physicalLocation (\c string) The node's physical location in the building
        """
        GenericComputerNode.__init__(self, nodeID, nodeType, interfaces, netBootable, \
                                infrastructure, vendor, model, attributes, physicalLocation)

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "ServerNode:\n"
        string += GenericComputerNode.__str__(self)
        string += (("-" * 60) + "\n")
        
        return string
    
class VirtualComputerNode(GenericComputerNode):
    """\brief Subclass of Node for virtual computer nodes
    """    
    def __init__(self, nodeID=None, nodeType=None, interfaces=None, netBootable=None, \
                    infrastructure=None, vendor=None, model=None, attributes=None, physicalLocation=None):
        """\brief Initializes the class
        \param nodeID (\c string) The name of id of the node
        \param nodeType (\c string) The type of the node, in essence one of the subclasses of this class
        \param interfaces (\c dictionary) A dictionary whose keys are the interface types
                                          and whose values are lists of Interface objects
        \param netBootable (\c string) Set to yes if the node is netbootable, no otherwise
        \param infrastructure (\c string) Set to yes if the node is infrastructure, no if it is experimental
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param attributes (\c dictionary) The node's attributes (see henParser.parseAttributes)
        \param physicalLocation (\c string) The node's physical location in the building
        """
        GenericComputerNode.__init__(self, nodeID, nodeType, interfaces, netBootable, infrastructure, vendor, model, attributes, physicalLocation)

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "VirtualComputerNode:\n"
        string += GenericComputerNode.__str__(self)
        string += (("-" * 60) +"\n")
        
        return string
    
class ComputerNode(GenericComputerNode):
    """\brief Subclass of Node for computer nodes
    """
    
    def __init__(self, nodeID=None, nodeType=None, interfaces=None, netBootable=None, \
                    infrastructure=None, vendor=None, model=None, attributes=None, physicalLocation=None):
        """\brief Initializes the class
        \param nodeID (\c string) The name of id of the node
        \param nodeType (\c string) The type of the node, in essence one of the subclasses of this class
        \param interfaces (\c dictionary) A dictionary whose keys are the interface types
                                          and whose values are lists of Interface objects
        \param netBootable (\c string) Set to yes if the node is netbootable, no otherwise
        \param infrastructure (\c string) Set to yes if the node is infrastructure, no if it is experimental
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param attributes (\c dictionary) The node's attributes (see henParser.parseAttributes)
        \param physicalLocation (\c string) The node's physical location in the building
        """
        GenericComputerNode.__init__(self, nodeID, nodeType, interfaces, netBootable, infrastructure, vendor, model, attributes, physicalLocation)
        
    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "ComputerNode:\n"
        string += GenericComputerNode.__str__(self)
        string += (("-" * 60) + "\n")
        return string
        
# XXX needs to inherit from Peripheral
# XXX peripheral should inherit from Node
class MoteNode(Node):
    """\brief Subclass of Node for Mote nodes
    """

    def __init__(self, nodeID=None, nodeType=None, interfaces=None, vendor=None, \
                    model=None, attributes=None, physicalLocation=None):
        """\brief Initializes the class
        \param nodeID (\c string) The name of id of the node
        \param nodeType (\c string) The type of the node, in essence one of the subclasses of this class
        \param interfaces (\c dictionary) A dictionary whose keys are the interface types
                                          and whose values are lists of Interface objects
        \param netBootable (\c string) Set to yes if the node is netbootable, no otherwise
        \param infrastructure (\c string) Set to yes if the node is infrastructure, no if it is experimental
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param attributes (\c dictionary) The node's attributes (see henParser.parseAttributes)
        \param physicalLocation (\c string) The node's physical location in the building
        """
        Node.__init__(self, nodeID, nodeType, interfaces, "no", "no", vendor, model, attributes, physicalLocation)

    def setReference(self, c):
        """\brief Sets the node's unique reference
        \param c (\c string) The node's reference
        """
        self.setSingleAttribute("reference", c)

    def getReference(self):
        """\brief Gets the node's unique reference
        \return (\c string) The node's unique reference
        """
        return self.getSingleAttribute("reference")

    # XXX REMOVE
    def getMACAddresses(self):
        """\brief Gets the node's MAC addresses
        \return (\c list) The node's MAC addresses
        """
        values = []
        interfaces = self.getInterfaces("external")
        if interfaces:
            for interface in interfaces:
                values.append(interface.getMAC())

        return values

    def setControllerID(self, c):
        """\brief Sets the node's controller's id
        \param c (\c string) The id of the node's controller
        """
        self.setSingleAttribute("controllerid", c)

    def getControllerID(self):
        """\brief Gets the node's controller's id
        \return (\c string) The id of the node's controller
        """
        return self.getSingleAttribute("controllerid")

    def getInstance(self):
        """\brief Returns a sub-subclass of a switch object based upon the xml description. For instance,
                  if the mote vendor is moteiv and the model is tmotesky, this function returns an
                  object of type MoteivTmoteskyMote with its mac address set to that of this class and a
                  controller instance instantiate through the controllerid of this class.
        \return (\c sub-subclass of Mote) A new mote object of the correct type
        """
        modulename = "hardware.motes." + self.getVendor().lower()
        classname = self.getVendor()[0:1].upper() + self.getVendor()[1:] \
        + self.getModel()[0:1].upper() + self.getModel()[1:].replace(" ", "").lower() + "Mote"
        try:
            module = __import__(modulename,globals(),locals(),[classname])
        except ImportError:
            return None
        return (vars(module)[classname])(self)

class GenericSwitchNode(Node,SerialInfo):
    """\brief Subclass of Node for switch nodes
    """
    def __init__(self, nodeID=None, nodeType=None, interfaces=None, netBootable=None, \
                    infrastructure=None, vendor=None, model=None, attributes=None, physicalLocation=None, \
                    numberPorts=None):
        """\brief Initializes the class
        \param nodeID (\c string) The name of id of the node
        \param nodeType (\c string) The type of the node, in essence one of the subclasses of this class
        \param interfaces (\c dictionary) A dictionary whose keys are the interface types
                                          and whose values are lists of Interface objects
        \param netBootable (\c string) Set to yes if the node is netbootable, no otherwise
        \param infrastructure (\c string) Set to yes if the node is infrastructure, no if it is experimental
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param attributes (\c dictionary) The node's attributes (see henParser.parseAttributes)
        \param physicalLocation (\c string) The node's physical location in the building
        \param numberPorts (\c string) The number of ports on the node        
        """
        Node.__init__(self, nodeID, nodeType, interfaces, netBootable, infrastructure, vendor, model, attributes, physicalLocation)
        SerialInfo.__init__(self)
        self.setSingleAttribute("numberports", numberPorts)
        self.setSingleAttribute("snmpreadcommunity", "public")
        self.setSingleAttribute("snmpwritecommunity", "private")
        self.__switchperipherals = []

    def setNumberPorts(self, n):
        """\brief Sets the node number of ports
        \param n (\c string) The node's number of ports
        """
        self.setSingleAttribute("numberports", n)

    def getNumberPorts(self):
        """\brief Gets the node number of ports
        \return (\c string) The node's number of ports
        """
        return self.getSingleAttribute("numberports")

    def setSNMPreadCommunity(self, c):
        """\brief Sets the node's snmp read community
        \param c (\c string) The node's snmp read community
        """
        self.setSingleAttribute("snmpreadcommunity", c)

    def getSNMPreadCommunity(self):
        """\brief Gets the node's snmp read community
        \return (\c string) The node's snmp read community
        """
        return self.getSingleAttribute("snmpreadcommunity")

    def setSNMPwriteCommunity(self, c):
        """\brief Sets the node's snmp write community
        \param c (\c string) The node's snmp write community
        """
        self.setSingleAttribute("snmpwritecommunity", c)

    def getSNMPwriteCommunity(self):
        """\brief Gets the node's snmp write community
        \return (\c string) The node's snmp write community
        """
        return self.getSingleAttribute("snmpwritecommunity")

    def addSwitchPeripheral(self,p):
        self.__switchperipherals.append(p)

    def getSwitchPerhipherals(self):
        return self.__switchperipherals
        
    def __str__(self):
        string = ""
        string += Node.__str__(self)
        string += "\tserialNodeID: " + str(self.getSerialNodeID()) + "\n" + \
               "\tserialNodePort: " + str(self.getSerialNodePort()) + "\n" + \
               "\tnumberPorts: " + str(self.getNumberPorts()) + "\n" + \
               "\tsnmpreadCommunity: " + str(self.getSNMPreadCommunity()) + "\n" + \
               "\tsnmpwriteCommunity: " + str(self.getSNMPwriteCommunity()) + "\n"
        return string
 
class SwitchNode(GenericSwitchNode,PowerInfo):
    """\brief Subclass of Node for switch nodes
    """

    def __init__(self, nodeID=None, nodeType=None, interfaces=None, netBootable=None, \
                    infrastructure=None, vendor=None, model=None, attributes=None, physicalLocation=None, \
                    numberPorts=None):
        """\brief Initializes the class
        \param nodeID (\c string) The name of id of the node
        \param nodeType (\c string) The type of the node, in essence one of the subclasses of this class
        \param interfaces (\c dictionary) A dictionary whose keys are the interface types
                                          and whose values are lists of Interface objects
        \param netBootable (\c string) Set to yes if the node is netbootable, no otherwise
        \param infrastructure (\c string) Set to yes if the node is infrastructure, no if it is experimental
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param attributes (\c dictionary) The node's attributes (see henParser.parseAttributes)
        \param physicalLocation (\c string) The node's physical location in the building
        \param numberPorts (\c string) The number of ports on the node        
        """
        GenericSwitchNode.__init__(self, nodeID, nodeType, interfaces, netBootable, infrastructure, vendor, model, attributes, physicalLocation)
        PowerInfo.__init__(self)

    def getInstance(self):
        """\brief Returns a sub-subclass of a switch object based upon the xml description. For instance,
                  if the switch vendor is threecom and the model is superstack, this function returns an
                  object of type ThreecomSuperstackSwitch with its ip address set to the ip of the management
                  interface of this class and the community set to 'private'
        \return (\c sub-subclass of Switch) A new switch object of the correct type
        """
        #log.debug("Trying to create a switch instance for "+str(self))
        #print "Trying to create a switch instance for "+str(self)
        moduleName = "hardware.switches." + self.getVendor()
        className = self.getVendor()[0:1].upper() + self.getVendor()[1:] + self.getModel()[0:1].upper() + self.getModel()[1:] + "Switch"
        try:
            module = __import__(moduleName, globals(), locals(), [className])
        except ImportError:
            return None

        return (vars(module)[className])(self)

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "SwitchNode:\n"
        string += GenericSwitchNode.__str__(self)

        for powerNode in self.getPowerNodes():
            string += "\tpowerNode: " + str(powerNode[0]) + "," + str(powerNode[1]) + "\n"
            
        string += (("-" * 60) + "\n")
        
        return string

class PowerSwitchNode(GenericSwitchNode):
    """\brief Subclass of Node for power switch nodes
    """

    def __init__(self, nodeID=None, nodeType=None, interfaces=None, netBootable=None, \
                    infrastructure=None, vendor=None, model=None, attributes=None, \
                    physicalLocation=None, numberPorts=None):
        """\brief Initializes the class
        \param nodeID (\c string) The name of id of the node
        \param nodeType (\c string) The type of the node, in essence one of the subclasses of this class
        \param interfaces (\c dictionary) A dictionary whose keys are the interface types
                                          and whose values are lists of Interface objects
        \param netBootable (\c string) Set to yes if the node is netbootable, no otherwise
        \param infrastructure (\c string) Set to yes if the node is infrastructure, no if it is experimental
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param attributes (\c dictionary) The node's attributes (see henParser.parseAttributes)
        \param physicalLocation (\c string) The node's physical location in the building
        \param numberPorts (\c string) The number of ports on the node
        """
        GenericSwitchNode.__init__(self, nodeID, nodeType, interfaces, netBootable, infrastructure, vendor, model, attributes, physicalLocation)
        self.__users = None

    def setUsers(self, u):
        """\brief Sets the node's users
        \param u (\c UserManagement) The node's users
        """
        self.__users = u

    def getUsers(self):
        """\brief Gets the node's users
        \return (\c list of UserManagement) The node's users
        """
        return self.__users

    def getInstance(self):
        """\brief Returns a subclass of a powerswitch object based upon the xml description. For instance,
                  if the powerswitch vendor is blackbox and the model is master, this function returns an
                  object of type BlackboxMasterPowerswitch
        \return (\c subclass of Powerswitch) A new powerswitch object of the correct type
        """
        modulename = "hardware.powerswitches." + self.getVendor()
        classname = self.getVendor()[0:1].upper() + self.getVendor()[1:] + self.getModel()[0:1].upper() + self.getModel()[1:] + "Powerswitch"
        #print modulename
        #print classname
        try:
            module = __import__(modulename,globals(),locals(),[classname])
        except ImportError:
            print "bugger"
            return None
        except Exception,e:
            print "damn",e
        #print "helloe"
        return (vars(module)[classname])(self)

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "PowerSwitchNode:\n"
        string += GenericSwitchNode.__str__(self)

        # process user management items
        for user in self.getUsers():
            string += "\tusermanagement: "
            if (user == None):
                string += "None \n"
            else:
                string += "\n\t\t" + str(user) + "\n"
        
        string += (("-" * 60) + "\n")
        
        return string

class SerialNode(Node,SerialInfo,PowerInfo):
    """\brief Subclass of Node for serial nodes
    """

    def __init__(self, nodeID=None, nodeType=None, interfaces=None, netBootable=None, \
                    infrastructure=None, vendor=None, model=None, attributes=None, physicalLocation=None, \
                    numberPorts=None):
        """\brief Initializes the class
        \param nodeID (\c string) The name of id of the node
        \param nodeType (\c string) The type of the node, in essence one of the subclasses of this class
        \param interfaces (\c dictionary) A dictionary whose keys are the interface types
                                          and whose values are lists of Interface objects
        \param netBootable (\c string) Set to yes if the node is netbootable, no otherwise
        \param infrastructure (\c string) Set to yes if the node is infrastructure, no if it is experimental
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param attributes (\c dictionary) The node's attributes (see henParser.parseAttributes)
        \param physicalLocation (\c string) The node's physical location in the building
        \param numberPorts (\c string) The number of ports on the node        
        """
        Node.__init__(self, nodeID, nodeType, interfaces, netBootable, infrastructure, vendor, model, attributes, physicalLocation)
        SerialInfo.__init__(self)
        PowerInfo.__init__(self)
        self.setSingleAttribute("numberports", numberPorts)
        self.__users = None

    def setUsers(self, u):
        """\brief Sets the node's users
        \param u (\c UserManagement) The node's users
        """
        self.__users = u

    def getUsers(self):
        """\brief Gets the node's users
        \return (\c list of UserManagement) The node's users
        """
        return self.__users

    def setNumberPorts(self, n):
        """\brief Sets the node number of ports
        \param n (\c string) The node's number of ports
        """
        self.setSingleAttribute("numberports", n)        

    def getNumberPorts(self):
        """\brief Gets the node number of ports
        \return (\c string) The node's number of ports
        """
        return self.getSingleAttribute("numberports")

    def getInstance(self):
        """\brief Returns a subclass of a terminalserver object based upon the xml description. For instance,
                  if the terminalserver vendor is opengear and the model is cm4148, this function returns an
                  object of type OpengearCm4148Terminalserver.
        \return (\c subclass of Terminalserver) A new terminalserver object of the correct type
        """
        modulename = "hardware.terminalservers." + self.getVendor()
        classname = self.getVendor()[0:1].upper() + self.getVendor()[1:] + self.getModel()[0:1].upper() + self.getModel()[1:] + "Terminalserver"
        try:
            module = __import__(modulename,globals(),locals(),[classname])
        except ImportError:
            return None
        return (vars(module)[classname])(self)

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "SerialNode:\n"
        string += Node.__str__(self)

        string += "\tnumberPorts: " + str(self.getNumberPorts()) + "\n"

        for powerNode in self.getPowerNodes():
            string += "\tpowerNode: " + str(powerNode[0]) + "," + str(powerNode[1]) + "\n"
            
        # process user management item
        for user in self.getUsers():
            string += "\tusermanagement: "
            if (user == None):
                string += "None \n"
            else:
                string += "\n\t\t" + str(user) + "\n"

        string += "---------------------------------------------------------------------------------\n"
        
        return string
    
class RouterNode(Node,PowerInfo,SerialInfo):
    """\brief Subclass of Node for router nodes
    """

    def __init__(self, nodeID=None, nodeType=None, interfaces=None, netBootable=None, \
                    infrastructure=None, vendor=None, model=None, attributes=None, physicalLocation=None, \
                    numberPorts=None):
        """\brief Initializes the class
        \param nodeID (\c string) The name of id of the node
        \param nodeType (\c string) The type of the node, in essence one of the subclasses of this class
        \param interfaces (\c dictionary) A dictionary whose keys are the interface types
                                          and whose values are lists of Interface objects
        \param netBootable (\c string) Set to yes if the node is netbootable, no otherwise
        \param infrastructure (\c string) Set to yes if the node is infrastructure, no if it is experimental
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param attributes (\c dictionary) The node's attributes (see henParser.parseAttributes)
        \param physicalLocation (\c string) The node's physical location in the building
        \param numberPorts (\c string) The number of ports on the node
        """
        Node.__init__(self, nodeID, nodeType, interfaces, netBootable, infrastructure, vendor, model, attributes, physicalLocation)
        PowerInfo.__init__(self)
        SerialInfo.__init__(self)
        self.setSingleAttribute("numberports", numberPorts)
        self.__expInterfaces = None

    def setNumberPorts(self, n):
        """\brief Sets the node number of ports
        \param n (\c string) The node's number of ports
        """
        self.setSingleAttribute("numberports", n)        

    def getNumberPorts(self):
        """\brief Gets the node number of ports
        \return (\c string) The node's number of ports
        """
        return self.getSingleAttribute("numberports")
    
    def setExpInterfaces(self, e):
        """\brief Sets the node experimental interfaces
        \param n (\c string) The node's experimental interfaces
        """
        self.__expInterfaces = e

    def getExpInterfaces(self):
        """\brief Gets the node experimental interfaces
        \return (\c list) A list of Interface objects
        """
        return self.__expInterfaces

    def setOSType(self, o):
        """\brief Sets the node operating system type
        \param n (\c string) The node's operating system type
        """
        self.setSingleAttribute("operatingsystemtype", c)

    def getOSType(self):
        """\brief Gets the node operating system type
        \return (\c string) The node's operating system type
        """
        attributes = self.getAttributes()
        if (attributes == None):
            return None
        if (attributes.has_key("operatingsystemtype")):
            return attributes["operatingsystemtype"]

    def setOSVersion(self, o):
        """\brief Sets the node operating system version
        \param n (\c string) The node's operating system version
        """
        self.setSingleAttribute("operatingsystemversion", c)

    def getOSVersion(self):
        """\brief Gets the node operating system version
        \return (\c string) The node's operating system version
        """
        attributes = self.getAttributes()
        if (attributes == None):
            return None
        if (attributes.has_key("operatingsystemversion")):
            return attributes["operatingsystemversion"]

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "RouterNode:\n"
        string += Node.__str__(self)

        string += "\tserialNodeID: " + str(self.getSerialNodeID()) + "\n" + \
               "\tserialNodePort: " + str(self.getSerialNodePort()) + "\n" + \
               "\tosType: " + str(self.getOSType()) + "\n" + \
               "\tnumberPorts: " + str(self.getNumberPorts()) + "\n" + \
               "\tosVersion: " + str(self.getOSVersion()) + "\n"        

        for powerNode in self.getPowerNodes():
            string += "\tpowerNode: " + str(powerNode[0]) + "," + str(powerNode[1]) + "\n"

        string += (("-" * 60) + "\n")
        return string        
    
class ServiceProcessorNode(Node,PowerInfo):
    """\brief Subclass of Node for service processor nodes
    """

    def __init__(self, nodeID=None, nodeType=None, interfaces=None, netBootable=None, \
                    infrastructure=None, vendor=None, model=None, attributes=None, physicalLocation=None):
        """\brief Initializes the class
        \param nodeID (\c string) The name of id of the node
        \param nodeType (\c string) The type of the node, in essence one of the subclasses of this class
        \param interfaces (\c dictionary) A dictionary whose keys are the interface types
                                          and whose values are lists of Interface objects
        \param netBootable (\c string) Set to yes if the node is netbootable, no otherwise
        \param infrastructure (\c string) Set to yes if the node is infrastructure, no if it is experimental
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param attributes (\c dictionary) The node's attributes (see henParser.parseAttributes)
        \param physicalLocation (\c string) The node's physical location in the building
        """
        Node.__init__(self, nodeID, nodeType, interfaces, netBootable, infrastructure, vendor, model, attributes, physicalLocation)
        PowerInfo.__init__(self)
        self.__users = None

    def setUsers(self, u):
        """\brief Sets the node's users
        \param u (\c UserManagement) The node's users
        """
        self.__users = u

    def getUsers(self):
        """\brief Gets the node's users
        \return (\c list of UserManagement) The node's users
        """
        return self.__users

    def getInstance(self):
        """\brief Returns a subclass of a service processor object based upon the xml description. For instance,
                  if the service processor vendor is sun and the model is v20z, this function returns an
                  object of type SunV20zServiceProcessor
        \return (\c subclass of ServiceProcessor) A new service processor object of the correct type
        """
        modulename = "hardware.serviceprocessors." + self.getVendor()
        classname = self.getVendor()[0:1].upper() + self.getVendor()[1:] + self.getModel()[0:1].upper() + self.getModel()[1:] + "ServiceProcessor"
        try:
            module = __import__(modulename,globals(),locals(),[classname])
        except ImportError:
            return None
        return (vars(module)[classname])(self)
    
    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "ServiceProcessorNode:\n"
        string += Node.__str__(self)

        for powerNode in self.getPowerNodes():
            string += "\tpowerNode: " + str(powerNode[0]) + "," + str(powerNode[1]) + "\n"

        # process user management item
        for user in self.getUsers():
            string += "\tusermanagement: "
            if (user == None):
                string += "None \n"
            else:
                string += "\n\t\t" + str(user) + "\n"

        string += "---------------------------------------------------------------------------------\n"
        
        return string


class SensorNode(Node):
    """\brief Subclass of Node for sensor nodes
    """

    def __init__(self, nodeID=None, nodeType=None, interfaces=None, netBootable=None, infrastructure=None, vendor=None, model=None, attributes = None, physicalLocation=None, dhcp=None):
        """\brief Initializes the class
        \param nodeID (\c string) The name of id of the node
        \param nodeType (\c string) The type of the node, in essence one of the subclasses of this class
        \param interfaces (\c dictionary) A dictionary whose keys are the interface types
                                          and whose values are lists of Interface objects
        \param netBootable (\c string) Set to yes if the node is netbootable, no otherwise, or None if n/a
        \param infrastructure (\c string) Set to yes if the node is infrastructure, no if it is experimental
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param attributes (\c dictionary) The node's attributes (see henParser.parseAttributes)
        \param physicalLocation (\c string) The node's physical location in the building
        """
        Node.__init__(self, nodeID, nodeType, interfaces, netBootable, infrastructure, vendor, model, attributes, physicalLocation, dhcp)

    def getInstance(self):
        """\brief Returns a subclass of a service processor object based upon the xml description.
        \return (\c subclass of Sensor) A new sensor object of the correct type
        """
        modulename = "hardware.sensors." + self.getVendor()
        classname = self.getVendor()[0:1].upper() + self.getVendor()[1:] + self.getModel()[0:1].upper() + self.getModel()[1:] + "Sensor"
        try:
            module = __import__(modulename,globals(),locals(),[classname])
        except ImportError:
            return None
        return (vars(module)[classname])(self)
    
    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "Sensor:\n"
        string += Node.__str__(self)

        string += (("-" * 60) + "\n")
        return string

class KVMNode(Node):
    """\brief Subclass of Node for KVM switches
    """

    def __init__(self, nodeID=None, nodeType=None, interfaces=None, netBootable=None, infrastructure=None, vendor=None, model=None, attributes = None, physicalLocation=None, dhcp=None):
        """\brief Initializes the class
        \param nodeID (\c string) The name of id of the node
        \param nodeType (\c string) The type of the node, in essence one of the subclasses of this class
        \param interfaces (\c dictionary) A dictionary whose keys are the interface types
                                          and whose values are lists of Interface objects
        \param netBootable (\c string) Set to yes if the node is netbootable, no otherwise, or None if n/a
        \param infrastructure (\c string) Set to yes if the node is infrastructure, no if it is experimental
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param attributes (\c dictionary) The node's attributes (see henParser.parseAttributes)
        \param physicalLocation (\c string) The node's physical location in the building
        """
        Node.__init__(self, nodeID, nodeType, interfaces, netBootable, infrastructure, vendor, model, attributes, physicalLocation, dhcp)

    def getInstance(self):
        """\brief Returns a subclass of a KVM object based upon the xml description.
        \return (\c subclass of KVM, not yet implemented) A new KVM object of the correct type
        """
        modulename = "hardware.kvm." + self.getVendor()
        classname = self.getVendor()[0:1].upper() + self.getVendor()[1:] + self.getModel()[0:1].upper() + self.getModel()[1:] + "KVM"
        try:
            module = __import__(modulename,globals(),locals(),[classname])
        except ImportError:
            return None
        return (vars(module)[classname])(self)
    
    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "KVM:\n"
        string += Node.__str__(self)
        string += (("-" * 60) + "\n")
        return string    

class Infrastructure:
    """\brief Superclass for any passive piece of infrastructure equipment such as racks, patch panels, floor boxes, etc.
    The class acts as a virtual class for all pieces of physical equipment in the testbed, it should
    not be instantiated directly.
    """
    def __init__(self, infrastructureID=None, infrastructureType=None, vendor=None, model=None, description=None, building=None, floor=None, room=None, attributes=None, physicalSize=None, status=None):
        """\brief Initializes the class
        \param infrastructureID (\c string) The name of the infrastructure component
        \param infrastructureType (\c string) The type of the infrastructure component
        \param vendor (\c string) The vendor of the infrastructure component
        \param model (\c string) The model of the infrastructure component
        \param description (\c string) A brief description of the infrastructure component
        \param building (\c string) The building that the infrastructure component is in
        \param floor (\c string) The floor that the infrastructure component is in
        \param room (\c string) The room that the infrastructure component is in
        \param attributes (\c dictionary) The infrastructure's attributes (see henParser.parseAttributes)        
        \param physicalSize (\c PhysicalSize) The physical size characteristics of the rack
        \param status (\c string) One of: operational, maintenance, retired, dead
        """
        self.__infrastructureID = infrastructureID
        self.__infrastructureType = infrastructureType
        self.__vendor = vendor
        self.__model = model
        self.__description = description
        self.__building = building
        self.__floor = floor
        self.__room = room
        self.__physicalSize = physicalSize
        self.__status = status

        if (attributes == None):
            self.__attributes = {}
        else:
            self.__attributes = attributes        

    def setStatus(self, status):
        """\brief Sets the status of the infrastructure (either operational, maintenance, retired or dead)
        \param status (\c string) The status of the infrastructure
        """
        self.__status = status

    def getStatus(self):
        """\brief Gets the status of the infrastructure (either operational, maintenance, retired or dead)
        \return (\c string) The status of the infrastructure
        """
        return self.__status
    
    def setID(self, infrastructureID):
        """\brief Sets the infrastructure id
        \param infrastructureID (\c string) The infrastructure id
        """
        self.__infrastructureID = infrastructureID

    def getID(self):
        """\brief Gets the infrastructure id
        \return (\c string) The infrastructure id
        """
        return self.__infrastructureID

    def setType(self, infrastructureType):
        """\brief Sets the infrastructure type
        \param infrastructureType (\c string) The infrastructure type
        """
        self.__infrastructureType = infrastructureType

    def getType(self):
        """\brief Gets the infrastructure type
        \return (\c string) The infrastructure type
        """
        return self.__infrastructureType

    def setVendor(self, vendor):
        """\brief Sets the infrastructure vendor
        \param vendor (\c string) The infrastructure vendor
        """
        self.__vendor = vendor

    def getVendor(self):
        """\brief Gets the infrastructure vendor
        \return (\c string) The infrastructure vendor
        """
        return self.__vendor

    def setModel(self, model):
        """\brief Sets the infrastructure model
        \param model (\c string) The infrastructure model
        """
        self.__model = model

    def getModel(self):
        """\brief Gets the infrastructure model
        \return (\c string) The infrastructure model
        """
        return self.__model

    def setDescription(self, description):
        """\brief Sets the infrastructure description
        \param description (\c string) The infrastructure description
        """
        self.__description = description

    def getDescription(self):
        """\brief Gets the infrastructure description
        \return (\c string) The infrastructure description
        """
        return self.__description

    def setBuilding(self, building):
        """\brief Sets the infrastructure building
        \param building (\c string) The infrastructure building
        """
        self.__building = building

    def getBuilding(self):
        """\brief Gets the infrastructure building
        \return (\c string) The infrastructure building
        """
        return self.__building

    def setFloor(self, floor):
        """\brief Sets the infrastructure floor
        \param floor (\c string) The infrastructure floor
        """
        self.__floor = floor

    def getFloor(self):
        """\brief Gets the infrastructure floor
        \return (\c string) The infrastructure floor
        """
        return self.__floor

    def setRoom(self, room):
        """\brief Sets the infrastructure room
        \param room (\c string) The infrastructure room
        """
        self.__room = room

    def getRoom(self):
        """\brief Gets the infrastructure room
        \return (\c string) The infrastructure room
        """
        return self.__room

    def setPhysicalSize(self, physicalSize):
        """\brief Sets the rack's physical size
        \param physicalSize (\c PhysicalSize) The rack's physical size
        """        
        self.__physicalSize = physicalSize
        
    def getPhysicalSize(self):
        """\brief Gets the rack's physical size
        \return (\c PhysicalSize) The rack's physical size
        """
        return self.__physicalSize

    def getSingleAttribute(self, attributeKey):
        """\brief Gets a single value in the attributes dictionary.
        \param attributeKey (\c string) The key for the dictionary
        \return (\c string) The attribute's value or None if the attribute does not exist
        """
        if (self.__attributes == None):
            self.__attributes = {}

        if (self.__attributes.has_key(attributeKey)):
            return self.__attributes[attributeKey]
        else:
            return None
        
    def setSingleAttribute(self, attributeKey, value):
        """\brief Sets a single value in the attributes dictionary.
        \param attributeKey (\c string) The key for the dictionary
        \param value (\c string) The attribute's new value
        """
        if (self.__attributes == None):
            self.__attributes = {}
        self.__attributes[attributeKey] = value

    def setAttributes(self, a):
        """\brief Sets the infrastructure attributes
        \param n (\c dictionary) The infrastructure's attributes
        """
        self.__attributes = a

    def getAttributes(self):
        """\brief Gets the infrastructure attributes
        \return (\c dictionary) The infrastructure's attributes
        """
        return self.__attributes

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "\id: " + str(self.getID()) + "\n" + \
               "\type: " + str(self.getType()) + "\n" + \
               "\tvendor: " + str(self.getNetbootable()) + "\n" + \
               "\tmodel: " + str(self.getInfrastructure()) + "\n" + \
               "\tdescription: " + str(self.getVendor()) + "\n" + \
               "\tbuilding: " + str(self.getModel()) + "\n" + \
               "\tfloor: " + str(self.getModel()) + "\n" + \
               "\troom: " + str(self.getPhysicalLocation()) + "\n" + \
               "\tstatus: " + str(self.getStatus()) + "\n"         
    
        # process attributes 
        string += "\tattributes: "
        attributes = self.getAttributes()
        if (attributes == None):
            string += "None\n"
        else:
            string += "\n"
            for key in attributes.keys():
                string += "\t\tname: " + key + "  value: " + attributes[key] + "\n"

        return string

                 
class InfrastructureRack(Infrastructure):
    """\brief Subclass of infrastructure for racks
    """
    def __init__(self, infrastructureID=None, infrastructureType=None, vendor=None, model=None, description=None, building=None, floor=None, room=None, attributes=None, physicalSize=None, status=None, rackRow=None, rowPosition=None, rearRightSlots=None, rearLeftSlots=None):
        """\brief Initializes the class
        \param infrastructureID (\c string) The name of the infrastructure component
        \param infrastructureType (\c string) The type of the infrastructure component
        \param vendor (\c string) The vendor of the infrastructure component
        \param model (\c string) The model of the infrastructure component
        \param description (\c string) A brief description of the infrastructure component
        \param building (\c string) The building that the infrastructure component is in
        \param floor (\c string) The floor that the infrastructure component is in
        \param room (\c string) The room that the infrastructure component is in        
        \param attributes (\c dictionary) The infrastructure's attributes (see henParser.parseAttributes)
        \param physicalSize (\c PhysicalSize) The physical size characteristics of the rack
        \param status (\c string) One of: operational, maintenance, retired, dead
        \param rackRow (\c string) The row that the rack is in
        \param rowPosition (\c string) The row position that the rack is in
        \param rearRightSlots (\c string) The number of right back vertical slots that the rack has
        \param rearLeftSlots (\c string) The number of left back vertical slots that the rack has
        """
        Infrastructure.__init__(self, infrastructureID, infrastructureType, vendor, model, description, building, floor, room, attributes, physicalSize, status)

        self.setSingleAttribute("rackrow", rackRow)
        self.setSingleAttribute("rowposition", rowPosition)
        self.setSingleAttribute("rearrightslots", rearRightSlots)
        self.setSingleAttribute("rearleftslots", rearLeftSlots)
        
    def setRackRow(self, rackRow):
        """\brief Sets the rack's row as an attribute
        \param rackRow (\c string) The rack's row
        """
        self.setSingleAttribute("rackrow", rackRow)
        
    def getRackRow(self):
        """\brief Gets the attribute rackrow
        \return (\c string) The rack's row
        """
        return self.getSingleAttribute("rackrow")

    def setRowPosition(self, rackRow):
        """\brief Sets the rack's row position as an attribute
        \param rackRow (\c string) The rack's row position
        """        
        self.setSingleAttribute("rowposition", rackRow)
        
    def getRowPosition(self):
        """\brief Gets the attribute rowposition
        \return (\c string) The rack's row position
        """        
        return self.getSingleAttribute("rowposition")            
    
    def setRearRightSlots(self,i):
        """\brief Sets the rack's number of rear right slots  as an attribute
        \param rackRow (\c string) The rack's number of rear right slots
        """        
        self.setSingleAttribute("rearrightslots", i)        
        
    def getRearRightSlots(self):
        """\brief Gets the number of rear right slots
        \return (\c string) The rack's number of rear right slots
        """        
        return self.getSingleAttribute("rearrightslots")        

    def setRearLeftSlots(self,i):
        """\brief Sets the rack's number of rear left slots as an attribute
        \param rackRow (\c string) The rack's number of rear left slots
        """        
        self.setSingleAttribute("rearleftslots", i)        
        
    def getRearLeftSlots(self):
        """\brief Gets the rack's number of rear left slots
        \return (\c string) The rack's number of rear left slots
        """        
        return self.getSingleAttribute("rearleftslots")        

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        return "InfrastructureRack:" + \
               " rackID=" + str(self.getID()) + \
               " vendor=" + str(self.getVendor()) + \
               " model=" + str(self.getModel()) + \
               " building=" + str(self.getBuilding()) + \
               " floor=" + str(self.getFloor()) + \
               " room=" + str(self.getRoom()) + \
               " rackRow=" + str(self.getRackRow()) + \
               " rowPosition=" + str(self.getRowPosition()) +\
               " rearRightSlots=" + str(self.getRearRightSlots()) +\
               " rearLeftSlots=" + str(self.getRearLeftSlots()) +\
               " description=" + str(self.getDescription()) + "\n" +\
               str(self.getPhysicalSize())
    
    
class InfrastructureFloorBox(Infrastructure):
    """\brief Subclass of infrastructure for racks
    """
    def __init__(self, infrastructureID=None, infrastructureType=None, vendor=None, model=None, description=None, building=None, floor=None, room=None, attributes=None, status=None, rackRow=None, rowPosition=None, maxCurrent=None, powerPlugs=None, rj45Ports=None):
        """\brief Initializes the class
        \param infrastructureID (\c string) The name of the infrastructure component
        \param infrastructureType (\c string) The type of the infrastructure component
        \param vendor (\c string) The vendor of the infrastructure component
        \param model (\c string) The model of the infrastructure component
        \param description (\c string) A brief description of the infrastructure component
        \param building (\c string) The building that the infrastructure component is in
        \param floor (\c string) The floor that the infrastructure component is in
        \param room (\c string) The room that the infrastructure component is in
        \param rackRow (\c string) The row that the floorbox is in
        \param rowPosition (\c string) The row position that the floorbox is in
        \param maxCurrent (\c int) The maximum current supported by the floor box (in amps)
        \param powerPlugs (\c list of FloorBoxPowerPlug) A list with the floorbox's power plugs
        \param rj45Ports (\c list of FloorBoxRJ45Port) A list with the floorbox's RJ45 ports
        """
        Infrastructure.__init__(self, infrastructureID, infrastructureType, vendor, model, description, building, floor, room, attributes, None, status)

        self.setSingleAttribute("rackrow", rackRow)
        self.setSingleAttribute("rowposition", rowPosition)

        if (maxCurrent != None):
            maxCurrent = int(maxCurrent)
        self.setSingleAttribute("maxcurrent", maxCurrent)

        self.__powerPlugs = powerPlugs
        self.__rj45Ports = rj45Ports
        
    def setRackRow(self, rackRow):
        """\brief Sets the floorbox's rack row as an attribute
        \param rackRow (\c string) The floorbox's rack row
        """
        self.setSingleAttribute("rackrow", rackRow)
        
    def getRackRow(self):
        """\brief Gets the attribute rackrow
        \return (\c string) The floorbox's rack row
        """
        return self.getSingleAttribute("rackrow")

    def setRowPosition(self, rowPosition):
        """\brief Sets the floorbox's row position as an attribute
        \param rackRow (\c string) The floorbox's row position
        """        
        self.setSingleAttribute("rowposition", rowPosition)
        
    def getRowPosition(self):
        """\brief Gets the attribute rowposition
        \return (\c string) The floorbox's row position
        """        
        return self.getSingleAttribute("rowposition")

    def getMaxCurrent(self):
        """\brief Gets the maximum current supported by the floor box
        \return (\c int) The maximum current (in amps)
        """                
        return self.getSingleAttribute("maxcurrent")

    def setMaxCurrent(self, maxCurrent):
        """\brief Sets the floorbox's maximum current
        \param rackRow (\c int) The floorbox's maximum current (in amps)
        """        
        self.setSingleAttribute("maxcurrent", int(maxCurrent))
        

    def getPowerPlugs(self):
        """\brief Gets the floorbox's power plugs
        \return (\c list of FloorBoxPowerPlug objects) The power plugs
        """
        return self.__powerPlugs

    def setPowerPlugs(self, powerPlugs):
        """\brief Sets the floorbox's power plugs
        \param powerPlugs (\c list of FloorBoxPowerPlug objects) The power plugs
        """
        self.__powerPlugs = powerPlugs

    def getRJ45Ports(self):
        """\brief Gets the floorbox's rj45 ports
        \return (\c list of FloorBoxRJ45Port objects) The rj45 ports
        """        
        return self.__rj45Ports

    def setRJ45Ports(self, rj45Ports):
        """\brief Sets the floorbox's rj45 ports
        \param powerPlugs (\c list of FloorBoxRJ45Port objects) The rj45 ports
        """        
        self.__rj45Ports = rj45Ports

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "InfrastructureFloorBox:" + \
                 " floorboxID=" + str(self.getID()) + \
                 " vendor=" + str(self.getVendor()) + \
                 " model=" + str(self.getModel()) + \
                 " building=" + str(self.getBuilding()) + \
                 " floor=" + str(self.getFloor()) + \
                 " room=" + str(self.getRoom()) + \
                 " maxcurrent=" + str(self.getMaxCurrent()) + \
                 " rackRow=" + str(self.getRackRow()) + \
                 " rowPosition=" + str(self.getRowPosition()) + \
                 " description=" + str(self.getDescription()) + "\n"

        for powerPlug in self.getPowerPlugs():
            string += "\t" + str(powerPlug)
        for rj45Port in self.getRJ45Ports():
            string += "\t" + str(rj45Port)

        return string


class FileNode:
    """\brief Superclass for any file on the testbed
    The FileNode class acts as a virtual class for all files on the testbed, it should
    not be instantiated directly.
    """

    def __init__(self, fileID=None, fileType=None, path=None, architecture=None, osType=None, version=None, mustClone=None, attributes=None, md5Signature=None, description=None, status=None, owner=None):
        """\brief Initializes the class
        \param fileID (\c string) The name of id of the testbed file
        \param type (\c string) The type of the testbed file, in essence one of the subclasses of this class
        \param path (\c string) The full path to the file
        \param architecture (\c string) The file's processor architecture
        \param osType (\c string) The file's OS type (linux, freebsd, debian, etc)
        \param version (\c string) The file's version 
        \param mustClone (\c string) Whether a file is read only and must be copied before writing to it (yes or no)       
        \param attributes (\c dictionary) The file's attributes (see henParser.parseAttributes)
        \param md5Signature (\c string) The file's MD5 signature, used for file versioning
        \param description (\c string) The file's description
        \param status (\c string) The file's status (operational, broken or archived)
        \param owner (\c string) The login id of the file's owner
        """
        self.__id = fileID
        self.__type = fileType
        self.__path = path
        self.__architecture = architecture
        self.__osType = osType
        self.__version = version
        self.__mustClone = mustClone
        self.__md5Signature = md5Signature
        self.__description = description
        self.__status = status
        self.__owner = owner
        
        if (attributes == None):
            self.__attributes = {}
        else:
            self.__attributes = attributes


    def setID(self, fileID):
        """\brief Sets the id
        \param fileID (\c string) The id
        """
        self.__id = fileID

    def getID(self):
        """\brief Gets the id
        \return (\c string) The id
        """
        return self.__id

    def setType(self, fileType):
        """\brief Sets type
        \param fileType (\c string) The type
        """
        self.__type = fileType

    def getType(self):
        """\brief Gets the type
        \return (\c string) The type
        """
        return self.__type

    def setPath(self, path):
        """\brief Sets the path
        \param path (\c string) The path
        """
        self.__path = path

    def getPath(self):
        """\brief Gets the path
        \return (\c string) The path
        """
        return self.__path

    def setArchitecture(self, architecture):
        """\brief Sets the architecture
        \param architecture (\c string) The architecture
        """
        self.__architecture = architecture

    def getArchitecture(self):
        """\brief Gets the architecture
        \return (\c string) The architecture
        """
        return self.__architecture

    def setOsType(self, osType):
        """\brief Sets the OS type
        \param osType (\c string) The OS type
        """
        self.__osType = osType

    def getOsType(self):
        """\brief Gets the OS type
        \return (\c string) The OS type
        """
        return self.__osType

    def setVersion(self, version):
        """\brief Sets the version
        \param version (\c string) The version
        """
        self.__version = version

    def getVersion(self):
        """\brief Gets the version
        \return (\c string) The version
        """
        return self.__version

    def setMustClone(self, mustClone):
        """\brief Whether a file must be cloned before it can be written to
        \param mustClone (\c string) The mustClone attribute (yes or no)
        """
        self.__mustClone = mustClone

    def getMustClone(self):
        """\brief Gets the mustClone attribute
        \return (\c string) Whether a file must be cloned before it can be written to (yes or no)
        """
        return self.__mustClone

    def getSingleAttribute(self, attributeKey):
        """\brief Gets a single value in the attributes dictionary.
        \param attributeKey (\c string) The key for the dictionary
        \return (\c string) The attribute's value or None if the attribute does not exist
        """
        if (self.__attributes == None):
            self.__attributes = {}

        if (self.__attributes.has_key(attributeKey)):
            return self.__attributes[attributeKey]
        else:
            return None
        
    def setSingleAttribute(self, attributeKey, value):
        """\brief Sets a single value in the attributes dictionary.
        \param attributeKey (\c string) The key for the dictionary
        \param value (\c string) The attribute's new value
        """
        if (self.__attributes == None):
            self.__attributes = {}
        self.__attributes[attributeKey] = value

    def setAttributes(self, a):
        """\brief Sets the file attributes
        \param n (\c dictionary) The file's attributes
        """
        self.__attributes = a

    def getAttributes(self):
        """\brief Gets the file attributes
        \return (\c dictionary) The file's attributes
        """
        return self.__attributes

    def setMd5Signature(self, md5Signature):
        """\brief Sets the MD5 signature
        \param md5Signature (\c string) The MD5 signature
        """
        self.__md5Signature = md5Signature

    def getMd5Signature(self):
        """\brief Gets the MD5 signature
        \return (\c string) The MD5 signature
        """
        return self.__md5Signature    

    def setDescription(self, description):
        """\brief Sets the description
        \param description (\c string) The description
        """
        self.__description = description

    def getDescription(self):
        """\brief Gets the description
        \return (\c string) The description
        """
        return self.__description

    def setOwner(self, owner):
        """\brief Sets the owner
        \param owner (\c string) The owner
        """
        self.__owner = owner

    def getOwner(self):
        """\brief Gets the owner
        \return (\c string) The owner
        """
        return self.__owner
    
    def setStatus(self, status):
        """\brief Sets the status of the node (either operational, broken, archived)
        \param status (\c string) The status of the node
        """
        self.__status = status

    def getStatus(self):
        """\brief Gets the status of the node (either operational, broken, archived)
        \return (\c string) The status of the node
        """
        return self.__status    

    def getOwnerOnFilesystem(self):
        """\brief Gets the file's owner as reported by the file system
        \return (\c string) The file's owner or an return code if an error occurred
        """
        cmd = "ls -l " + self.getPath() + "| awk '{print $3}'"
        result = commands.getstatusoutput(cmd)
        if (result[0] != 0):
            return str(result[0])

        return result[1]

    def getGroup(self):
        """\brief Gets the file's group
        \return (\c string) The file's group or an return code if an error occurred
        """        
        cmd = "ls -l " + self.getPath() + "| awk '{print $4}'"        
        if (result[0] != 0):
            return str(result[0])

        return result[1]

    def fileExists(self):
        """\brief Returns whether a file exists or not
        \param filename (\c string) The full path of the file
        \return (\c boolean) True if the file exists, false otherwise
        """        
        return fileExists(self.getPath())

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "\tid: " + str(self.getID()) + "\n" + \
               "\ttype: " + str(self.getType()) + "\n" + \
               "\tpath: " + str(self.getPath()) + "\n" + \
               "\tarchitecture: " + str(self.getArchitecture()) + "\n" + \
               "\tosType: " + str(self.getOsType()) + "\n" + \
               "\tversion: " + str(self.getVersion()) + "\n" + \
               "\tmustClone: " + str(self.getMustClone()) + "\n" + \
               "\tmd5Signature: " + str(self.getMd5Signature()) + "\n" + \
               "\tdescription: " + str(self.getDescription()) + "\n" + \
               "\towner: " + str(self.getOwner()) + "\n" + \
               "\tstatus: " + str(self.getStatus()) + "\n"               

        # process attributes 
        string += "\tattributes: "
        attributes = self.getAttributes()
        if (attributes == None):
            string += "None\n"
        else:
            string += "\n"
            for key in attributes.keys():
                string += "\t\tname: " + key + "  value: " + attributes[key] + "\n"

        return string
    

class FilesystemFileNode(FileNode):
    """\brief Subclass of FileNode for filesystems
    """
    
    def __init__(self, fileID=None, path=None, architecture=None, osType=None, version=None, mustClone=None, attributes=None, md5Signature=None, description=None, status=None, owner=None, userManagement=None):
        """\brief Initializes the class
        \param fileID (\c string) The name of id of the testbed file
        \param path (\c string) The full path to the file
        \param architecture (\c string) The file's processor architecture
        \param osType (\c string) The file's OS type (linux, freebsd, debian, etc)
        \param version (\c string) The file's version 
        \param mustClone (\c string) Whether a file is read only and must be copied before writing to it (yes or no)       
        \param attributes (\c dictionary) The file's attributes (see henParser.parseAttributes)
        \param md5Signature (\c string) The file's MD5 signature, used for file versioning
        \param description (\c string) The file's description
        \param status (\c string) The file's status (operational, broken or archived)
        \param userManagement(\c list of UserManagement) The user information for the filesystem (used to save login information)
        """
        FileNode.__init__(self, fileID, "filesystem", path, architecture, osType, version, mustClone, attributes, md5Signature, description, status, owner)
        self.__userManagement = userManagement

    def setUserManagement(self, userManagement):
        """\brief Sets the user information for the filesystem (used to save login information)
        \param userManagement (\c list of UserManagement) The user management information
        """
        self.__userManagement = userManagement

    def getUserManagement(self):
        """\brief Sets the user information for the filesystem (used to save login information)
        \return (\c list of UserManagement) The user management information
        """
        return self.__userManagement

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "FilesystemFileNode:\n"
        string += FileNode.__str__(self)

        userManagement = self.getUserManagement()
        if (not userManagement):
            string += "\tuserManagement: None\n"
        else:
            for user in userManagement:
                string += "\t" + str(user)
        string += "---------------------------------------------------------------------------------\n"
        
        return string


class KernelFileNode(FileNode):
    """\brief Subclass of FileNode for kernels
    """
    
    def __init__(self, fileID=None, path=None, architecture=None, osType=None, version=None, mustClone=None, attributes=None, md5Signature=None, description=None, status=None, owner=None):
        """\brief Initializes the class
        \param fileID (\c string) The name of id of the testbed file
        \param path (\c string) The full path to the file
        \param architecture (\c string) The file's processor architecture
        \param osType (\c string) The file's OS type (linux, freebsd, debian, etc)
        \param version (\c string) The file's version 
        \param mustClone (\c string) Whether a file is read only and must be copied before writing to it (yes or no)       
        \param attributes (\c dictionary) The file's attributes (see henParser.parseAttributes)
        \param md5Signature (\c string) The file's MD5 signature, used for file versioning
        \param description (\c string) The file's description
        \param status (\c string) The file's status (operational, broken or archived)
        """
        FileNode.__init__(self, fileID, "kernel", path, architecture, osType, version, mustClone, attributes, md5Signature, description, status, owner)

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "KernelFileNode:\n"
        string += FileNode.__str__(self)

        string += "---------------------------------------------------------------------------------\n"
        
        return string


class LoaderFileNode(FileNode):
    """\brief Subclass of FileNode for loaders
    """
    def __init__(self, fileID=None, path=None, architecture=None, osType=None, version=None, mustClone=None, attributes=None, md5Signature=None, description=None, status=None, owner=None):
        """\brief Initializes the class
        \param fileID (\c string) The name of id of the testbed file
        \param path (\c string) The full path to the file
        \param architecture (\c string) The file's processor architecture
        \param osType (\c string) The file's OS type (linux, freebsd, debian, etc)
        \param version (\c string) The file's version 
        \param mustClone (\c string) Whether a file is read only and must be copied before writing to it (yes or no)       
        \param attributes (\c dictionary) The file's attributes (see henParser.parseAttributes)
        \param md5Signature (\c string) The file's MD5 signature, used for file versioning
        \param description (\c string) The file's description
        \param status (\c string) The file's status (operational, broken or archived)
        """
        FileNode.__init__(self, fileID, "loader", path, architecture, osType, version, mustClone, attributes, md5Signature, description, status, owner)
    
    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "LoaderFileNode:\n"
        string += FileNode.__str__(self)
        string += "---------------------------------------------------------------------------------\n"
        
        return string                                    

class Link:
    def __init__(self,linkType=None, linkId=None, linkStatus=None):
        self.__linkType = linkType
        self.__linkId = linkId
        self.__linkMembers = []
        self.__linkStatus = linkStatus

    def setStatus(self,linkStatus):
        self.__linkStatus = linkStatus

    def getStatus(self):
        return self.__linkStatus
    
    def setLinkType(self,linkType):
        self.__linkType = linkType

    def getLinkType(self):
        return self.__linkType

    def setLinkId(self,linkId):
        self.__linkId = linkId

    def getLinkId(self):
        return self.__linkId
    
    def setLinkMembers(self,linkMembers):
        self.__linkMembers = linkMembers

    def getLinkMembers(self):
        return self.__linkMembers
    
class DirectLink(Link):
    def __init__(self,linkType=None, linkId=None):
        Link.__init__(self,linkType,linkId)

    def __str__(self):
        s = "Direct Link\n"
        for i in self.getLinkMembers():
            s = s + "\t" + str(i) + "\n"
        return s

class ExternalLink(Link):
    def __init__(self,linkType=None, linkId=None):
        Link.__init__(self,linkType,linkId)

    def __str__(self):
        s = "External Link\n"
        for i in self.getLinkMembers():
            s = s + "\t" + str(i) + "\n"
        return s
    
class LinkMember:
    def __init__(self,deviceId=None,devicePort=None):
        self.__deviceId = deviceId
        self.__devicePort = devicePort

    def setDevicePort(self,devicePort):
        self.__devicePort = devicePort

    def getDevicePort(self):
        return self.__devicePort
    
    def setDeviceId(self,deviceId):
        self.__deviceId = deviceId
        
    def getDeviceId(self):
        return self.__deviceId

    def __str__(self):
        return str(self.__deviceId)+" "+str(self.__devicePort)
        
class FloorBoxRJ45Port:
    """\brief Simple class to hold information about an rj45 port in a floor box
    """
    def __init__(self, portType=None, positionLabel=None, description=None):
        """\brief Initializes class
        \param portType (\c string) The type of port (ethernet, serial, telephone, etc)
        \param positionLabel(\c string) If the floorbox is labeled, then this corresponds to the label on the port. Otherwise
                                        it can be used to denote a port's position within the floor box
        \param description (\c string) A description of what the port is connected to
        """
        self.__portType = portType
        self.__positionLabel = positionLabel
        self.__description = description

    def getPortType(self):
        """\brief Gets the port's type
        \return (\c string) The port's type
        """
        return self.__portType

    def setPortType(self, portType):
        """\brief Sets the port's type
        \param (\c string) The port's type (ethernet, serial, telephone, etc)
        """
        self.__portType = portType

    def getPositionLabel(self):
        """\brief Gets the port's position label
        \return (\c string) The port's position label
        """
        return self.__positionLabel

    def setPositionLabel(self, positionLabel):
        """\brief Sets the port's position label
        \param (\c string) The port's position label
        """
        self.__positionLabel = positionLabel

    def getDescription(self):
        """\brief Gets the port's description
        \return (\c string) The port's description
        """
        return self.__description

    def setDescription(self, description):
        """\brief Sets the port's description
        \param (\c string) The port's description
        """
        self.__description = description
        
    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        return "FloorBoxRJ45Port:" + \
               " type="+str(self.getPortType()) + \
               " label="+str(self.getPositionLabel()) + \
               " description="+str(self.getDescription()) + "\n"

    
class FloorBoxPowerPlug:
    """\brief Simple class to hold information about an rj45 port in a floor box
    """
    def __init__(self, positionLabel=None, maxCurrent=None, portEnabled=None):
        """\brief Initializes class
        \param positionLabel(\c string) If the floorbox is labeled, then this corresponds to the label on the plug. Otherwise
                                        it can be used to denote a plug's position within the floor box
        \param maxCurrent (\c int) The maximum current supported by the plug (in amps)
        \param portEnabled (\c boolean) Whether the port is switched on or not
        """
        self.__positionLabel = positionLabel
        self.__maxCurrent = int(maxCurrent)
        self.__portEnabled = portEnabled

    def getPositionLabel(self):
        """\brief Gets the plug's position label
        \return (\c string) The plug's position label
        """
        return self.__positionLabel

    def setPositionLabel(self, positionLabel):
        """\brief Sets the plug's position label
        \param (\c string) The plug's position label
        """
        self.__positionLabel = positionLabel

    def getMaxCurrent(self):
        """\brief Gets the plug's maximum current (in amps)
        \return (\c int) The plug's maximum current (in amps)
        """
        return self.__maxCurrent

    def setMaxCurrent(self, maxCurrent):
        """\brief Sets the plug's maximum current (in amps)
        \param (\c int) The plug's maximum current (in amps)
        """
        self.__maxCurrent = int(maxCurrent)

    def isPortEnabled(self):
        """\brief Gets whether the port is enabled or not
        \return (\c boolean) Whether the port is enabled or not
        """
        return self.__portEnabled

    def setPortEnabled(self, portEnabled):
        """\brief Sets whether the port is enabled or not
        \param (\c boolean) Whether the port is enabled or not
        """
        self.__portEnabled = portEnabled
        
    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        return "FloorBoxPowerPlug:" + \
               " label="+str(self.getPositionLabel()) + \
               " maxcurrent="+str(self.getMaxCurrent()) + \
               " portenabled="+str(self.getPortEnabled()) + "\n"

    
class Peripheral:
    """\brief Class to hold information about what a node is connected to (a computer to a power switch, etc)
    """

    def __init__(self, peripheralID=None, peripheralType=None, peripheralRemotePort=None, peripheralLocalPort=None, peripheralDescription=None):
        """\brief Initializes the class
        \param peripheralID (\c string) The id of the peripheral
        \param peripheralType (\c string) The type of the peripheral
        \param peripheralRemotePort (\c string) The port on the peripheral
        \param peripheralLocalPort (\c string) The port on the local device that connects to the peripheral
        \param peripheralDescription (\c string) Extra information describing the peripheral; first char specifies the delimeter
        """
        self.__peripheralID = peripheralID
        self.__peripheralType = peripheralType
        self.__peripheralRemotePort = peripheralRemotePort
        self.__peripheralLocalPort = peripheralLocalPort
        self.__peripheralDescription = peripheralDescription

    def setPeripheralID(self, p):
        """\brief Sets the peripheral id
        \param n (\c string) The peripheral's id
        """
        self.__peripheralID = p

    def getPeripheralID(self):
        """\brief Gets the peripheral id
        \return (\c string) The peripheral's id
        """
        return self.__peripheralID

    def setPeripheralType(self, p):
        """\brief Sets the peripheral type
        \param n (\c string) The peripheral's type
        """
        self.__peripheralType = p

    def getPeripheralType(self):
        """\brief Gets the peripheral type
        \return (\c string) The peripheral's type
        """
        return self.__peripheralType

    def setPeripheralRemotePort(self, p):
        """\brief Sets the peripheral port
        \param n (\c string) The peripheral's port
        """
        self.__peripheralRemotePort = p

    def getPeripheralRemotePort(self):
        """\brief Gets the peripheral port
        \return (\c string) The peripheral's port
        """
        return self.__peripheralRemotePort

    def setPeripheralLocalPort(self, p):
        """\brief Sets the peripheral port
        \param n (\c string) The peripheral's port
        """
        self.__peripheralLocalPort = p

    def getPeripheralLocalPort(self):
        """\brief Gets the peripheral port
        \return (\c string) The peripheral's port
        """
        return self.__peripheralLocalPort    

    def setPeripheralDescription(self, p):
        """\brief Sets the peripheral extra info
        \param n (\c string) The peripheral's extra info
        """
        self.__peripheralDescription = p

    def getPeripheralDescription(self):
        """\brief Gets the peripheral extra info
        \return (\c string) The peripheral's extra info
        """
        return self.__peripheralDescription

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        return "Peripheral:" + \
               " peripheralID=" + str(self.getPeripheralID()) + \
               " peripheralType=" + str(self.getPeripheralType()) + \
               " peripheralRemotePort=" + str(self.getPeripheralRemotePort()) + \
               " peripheralLocalPort=" + str(self.getPeripheralLocalPort()) + \
               " peripheralDescription=" + str(self.getPeripheralDescription())


class UserManagement:
    """\brief Class to hold information about a user
    """    
    def __init__(self, username=None, password=None, email=None, description=None):
        """\brief Initializes the class
        \param username (\c string) The user's username
        \param password (\c string) The user's password
        \param email (\c string) The user's email
        """
        self.__username = username
        self.__password = password
        self.__description = description
        self.__email = email

    def setUsername(self, u):
        """\brief Sets the user name
        \param u (\c UserManagement) The user name
        """
        self.__username = u

    def getUsername(self):
        """\brief Gets the user name 
        \return (\c UserManagement) The user name
        """
        return self.__username

    def setPassword(self, p):
        """\brief Sets the password
        \param p (\c string) The password
        """
        self.__password = p

    def getPassword(self):
        """\brief Gets the password
        \return (\c string) The password
        """
        return self.__password

    def setDescription(self, d):
        """\brief Sets the description
        \param d (\c string) The description
        """
        self.__description = d

    def getDescription(self):
        """\brief Gets the description
        \return (\c string) The description
        """
        return self.__description    

    def setEmail(self, e):
        """\brief Sets the email
        \param n (\c string) The email
        """
        self.__email = e

    def getEmail(self):
        """\brief Gets the email
        \return (\c string) The email
        """
        return self.__email

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        return "UserManagement:" + \
               " username="+str(self.getUsername()) + \
               " password="+str(self.getPassword()) + \
               " description="+str(self.getDescription()) + \
               " email="+str(self.getEmail())+ "\n"


class PhysicalTopologyEntry:
    """\brief Class to hold information about an entry in the main topology.xml physical file
    """
    def __init__(self, tagType=None, elementType=None, filename=None, status=None):
        """\brief Initializes class
        \param tagType (\c string) The type of tag (infrastructure, node, etc)
        \param elementType (\c string) The type of the element (rack, computer, etc)
        \param filename (\c string) The path and filename holding the element's full description
        \param status (\c string) The status of the node, one of: operational, maintenance, retired, dead
        """
        self.__tagType = tagType
        self.__elementType = elementType
        self.__filename = filename
        self.__status = status

    def setTagType(self, tagType):
        """\brief Sets the tag type
        \param tagType (\c string) The type of tag
        """
        self.__tagType = tagType

    def getTagType(self):
        """\brief Gets the tag type
        \return (\c string) The tag type
        """
        return self.__tagType

    def setElementType(self, elementType):
        """\brief Sets the element type
        \param elementType (\c string) The type of element
        """
        self.__elementType = elementType

    def getElementType(self):
        """\brief Gets the element type
        \return (\c string) The element type
        """
        return self.__elementType

    def setFilename(self, filename):
        """\brief Sets the filename 
        \param filename (\c string) The filename
        """
        self.__filename = filename

    def getFilename(self):
        """\brief Gets the filename
        \return (\c string) The filename
        """
        return self.__filename    

    def setStatus(self, status):
        """\brief Sets the status, one of: operational, maintenance, retired, dead  
        \param status (\c string) The status
        """
        self.__status = status

    def getStatus(self):
        """\brief Gets the status, one of: operational, maintenance, retired, dead
        \return (\c string) The status
        """
        return self.__status    

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        return "PhysicalTopologyEntry:" + \
               " tagtype=" + str(self.getTagType()) + \
               " elementtype=" + str(self.getElementType()) + \
               " filename=" + str(self.getFilename()) + \
               " status=" + str(self.getStatus())+ "\n"


class ExperimentTopologyEntry:
    """\brief Class to hold information about an entry in the main topology.xml experiment file
    """
    def __init__(self, filename=None, status=None):
        """\brief Initializes class
        \param filename (\c string) The path and filename holding the element's full description
        \param status (\c string) The status of the node, one of: operational, maintenance, retired, dead
        """
        self.__filename = filename
        self.__status = status

    def setFilename(self, filename):
        """\brief Sets the filename 
        \param filename (\c string) The filename
        """
        self.__filename = filename

    def getFilename(self):
        """\brief Gets the filename
        \return (\c string) The filename
        """
        return self.__filename    

    def setStatus(self, status):
        """\brief Sets the status, one of: operational, maintenance, retired, dead  
        \param status (\c string) The status
        """
        self.__status = status

    def getStatus(self):
        """\brief Gets the status, one of: operational, maintenance, retired, dead
        \return (\c string) The status
        """
        return self.__status
    
    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        return "ExperimentTopologyEntry:" + \
               " filename=" + str(self.getFilename()) + \
               " status=" + str(self.getStatus())+ "\n"


class TestbedFileTopologyEntry:
    """\brief Class to hold information about an entry in the testbed file's topology.xml file
    """
    def __init__(self, tagType=None, elementType=None, filename=None, status=None):
        """\brief Initializes class
        \param tagType (\c string) The type of tag (filenode, etc)
        \param elementType (\c string) The type of the element (filesystem, loader, kernel, etc)
        \param filename (\c string) The path and filename holding the element's full description
        \param status (\c string) The status of the node, one of: operational, broken, archived 
        """
        self.__tagType = tagType
        self.__elementType = elementType
        self.__filename = filename
        self.__status = status

    def setTagType(self, tagType):
        """\brief Sets the tag type
        \param tagType (\c string) The type of tag
        """
        self.__tagType = tagType

    def getTagType(self):
        """\brief Gets the tag type
        \return (\c string) The tag type
        """
        return self.__tagType

    def setElementType(self, elementType):
        """\brief Sets the element type
        \param elementType (\c string) The type of element
        """
        self.__elementType = elementType

    def getElementType(self):
        """\brief Gets the element type
        \return (\c string) The element type
        """
        return self.__elementType

    def setFilename(self, filename):
        """\brief Sets the filename 
        \param filename (\c string) The filename
        """
        self.__filename = filename

    def getFilename(self):
        """\brief Gets the filename
        \return (\c string) The filename
        """
        return self.__filename    

    def setStatus(self, status):
        """\brief Sets the status, one of: operational, maintenance, retired, dead  
        \param status (\c string) The status
        """
        self.__status = status

    def getStatus(self):
        """\brief Gets the status, one of: operational, maintenance, retired, dead
        \return (\c string) The status
        """
        return self.__status    

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        return "TestbedFileTopologyEntry:" + \
               " tagtype=" + str(self.getTagType()) + \
               " elementtype=" + str(self.getElementType()) + \
               " filename=" + str(self.getFilename()) + \
               " status=" + str(self.getStatus())+ "\n"
    


class PhysicalLocation:
    """\brief Class to hold information about the physical location of a node on the testbed. Note that the x, y and
              z position parameters are in reference to the top-left corner of the room or floorplan when looking
              at it from overhead.
    """
    
    def __init__(self, building=None, floor=None, room=None, rackRow=None, rackName=None, rackStartUnit=None, rackEndUnit=None, description=None, nodePosition=None, xPosition=None, yPosition=None, zPosition=None):
        """\brief Initializes class
        \param building (\c string) The building that the node is in
        \param floor (\c string) The floor that the node is in
        \param room (\c string) The room that the node is in
        \param rackRow (\c string) The rack row that the node is in
        \param rackName (\c string) The rack name that the node is in
        \param rackStartUnit (\c string) The rack unit that the node is in
        \param rackEndUnit (\c string) The rack end unit that the node is in (in case the node takes up more than 1U)
        \param description (\c string) For misc info, such as if the node is a rack and so does not make use of all the other attributes
        \param nodePosition (\c string) Whether the node is facing to the front or the rear of the rack
        \param xPosition (\c int) The x position of a node within a room in meters
        \param yPosition (\c int) The y position of a node within a room in meters
        \param zPosition (\c int) The z (height or altitude) position of a node within a room in meters
        """
        self.__building = building
        self.__floor = floor
        self.__room = room
        self.__rackRow = rackRow
        self.__rackName = rackName
        self.__description = description
        self.__rackStartUnit = rackStartUnit
        self.__rackEndUnit = rackEndUnit
        self.__nodePosition = nodePosition
        self.__xPosition = xPosition
        self.__yPosition = yPosition
        self.__zPosition = zPosition

    def setBuilding(self, b):
        """\brief Sets the building
        \param b (\c string) The building
        """
        self.__building = b

    def getBuilding(self):
        """\brief Gets the building
        \return (\c string) The building
        """
        return self.__building

    def setFloor(self, f):
        """\brief Sets the floor
        \param b (\c string) The floor
        """        
        self.__floor = f

    def getFloor(self):
        """\brief Gets the floor
        \return (\c string) The floor
        """        
        return self.__floor

    def setRoom(self, r):
        """\brief Sets the room
        \param b (\c string) The room
        """        
        self.__room = r

    def getRoom(self):
        """\brief Gets the room
        \return (\c string) The room
        """        
        return self.__room

    def setRackRow(self, r):
        """\brief Sets the rack row
        \param b (\c string) The rack row
        """        
        self.__rackRow = r

    def getRackRow(self):
        """\brief Gets the rack row
        \return (\c string) The rack row
        """        
        return self.__rackRow

    def setRackName(self, r):
        """\brief Sets the rack name
        \param b (\c string) The rack name
        """        
        self.__rackName = r

    def getRackName(self):
        """\brief Gets the rack name
        \return (\c string) The rack name
        """       
        return self.__rackName

    def setRackStartUnit(self, r):
        """\brief Sets the rack start unit
        \param r (\c string) The rack start unit
        """        
        self.__rackStartUnit = r

    def getRackStartUnit(self):
        """\brief Gets the rack start unit
        \return (\c string) The rack start unit
        """        
        return self.__rackStartUnit

    def setRackEndUnit(self, r):
        """\brief Sets the rack end unit
        \param r (\c string) The rack end unit
        """        
        self.__rackEndUnit = r

    def getRackEndUnit(self):
        """\brief Gets the rack end unit
        \return (\c string) The rack end unit
        """        
        return self.__rackEndUnit

    def setDescription(self, d):
        """\brief Sets the description
        \param d (\c string) The description
        """        
        self.__description = d

    def getDescription(self):
        """\brief Gets the description
        \return (\c string) The description
        """        
        return self.__description

    def setNodePosition(self, p):
        """\brief Sets the node's position
        \param p (\c string) The node's position
        """        
        self.__nodePosition = p

    def getNodePosition(self):
        """\brief Gets the node's position
        \return (\c string) The node's position
        """        
        return self.__nodePosition

    def setXPosition(self, xPosition):
        """\brief Sets the node's x position within a room in meters
        \param xPosition (\c int) The node's x position
        """
        self.__xPosition = xPosition

    def getXPosition(self):
        """\brief Gets the node's x position within a room in meters
        \return (\c int) The node's x position
        """
        return self.__xPosition
    
    def setYPosition(self, yPosition):
        """\brief Sets the node's y position within a room in meters
        \param yPosition (\c int) The node's y position
        """
        self.__yPosition = yPosition

    def getYPosition(self):
        """\brief Gets the node's y position within a room in meters
        \return (\c int) The node's y position
        """
        return self.__yPosition
    
    def setZPosition(self, zPosition):
        """\brief Sets the node's z position (height) within a room in meters
        \param zPosition (\c int) The node's z position
        """
        self.__zPosition = zPosition

    def getZPosition(self):
        """\brief Gets the node's z position (height) within a room in meters
        \return (\c int) The node's z position
        """
        return self.__zPosition
        
    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        
        return "PhysicalLocation:" + "\n" + \
                " building=" + str(self.getBuilding()) + "\n" + \
                " floor=" + str(self.getFloor()) + "\n" + \
                " room=" + str(self.getRoom()) + "\n" + \
                " rackRow=" + str(self.getRackRow()) + "\n" + \
                " rackName=" + str(self.getRackName()) + "\n" + \
                " rackStartUnit=" + str(self.getRackStartUnit()) + "\n" + \
                " rackEndUnit=" + str(self.getRackEndUnit()) + "\n" + \
                " nodePosition=" + str(self.getNodePosition()) + "\n" + \
                " description=" + str(self.getDescription()) + "\n" + \
                " xPosition=" + str(self.getXPosition()) + "\n" + \
                " yPosition=" + str(self.getXPosition()) + "\n" + \
                " zPosition=" + str(self.getXPosition()) + "\n"                
                

class PhysicalSize:
    """\brief General class to hold size information about a piece of infrastructure
    """

    def __init__(self,  height=None, width=None, depth=None, numberUnits=None):
        """\brief Initializes class
        \param height (\c int) The height of the infrastructure, in cm
        \param width (\c int) The width of the infrastructure, in cm
        \param depth (\c int) The depth of the infrastructure, in cm
        \param numberUnits (\c int) The number of units of the infrastructure (for a rack, for instance)

        """
        self.__height = height
        self.__width = width
        self.__depth = depth
        self.__numberUnits = numberUnits

    def setHeight(self, height):
        """\brief Sets the height of the infrastructure
        \param height (\c int) The height in cm
        """
        self.__height = height

    def getHeight(self):
        """\brief Gets the height of the infrastructure
        \return (\c int) The height in cm
        """
        return self.__height

    def setWidth(self, width):
        """\brief Sets the width of the infrastructure
        \param width (\c int) The width in cm
        """
        self.__width = width

    def getWidth(self):
        """\brief Gets the width of the infrastructure
        \return (\c int) The width in cm
        """
        return self.__width

    def setDepth(self, depth):
        """\brief Sets the depth of the infrastructure
        \param depth (\c int) The depth in cm
        """
        self.__depth = depth

    def getDepth(self):
        """\brief Gets the depth of the infrastructure
        \return (\c int) The depth in cm
        """
        return self.__depth

    def setNumberUnits(self, numberUnits):
        """\brief Sets the number of units of the infrastructure
        \param numberUnits (\c int) The number of units
        """
        self.__numberUnits = numberUnits

    def getNumberUnits(self):
        """\brief Gets the number of units of the infrastructure
        \return (\c int) The number of units
        """
        return self.__numberUnits

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        
        return "PhysicalSize:" + "\n" + \
                " height=" + str(self.getHeight()) + "\n" + \
                " width=" + str(self.getWidth()) + "\n" + \
                " depth=" + str(self.getDepth()) + "\n" + \
                " numberunits=" + str(self.getNumberUnits()) + "\n"


class UserExperiment:
    """\brief Class to hold information about a user experiment
    """

    def __init__(self, experimentNodes=None, user=None, startDate=None, endDate=None, experimentID=None, experimentFile=None, startTime=None, endTime=None, experimentGroups=None):
        """\brief Initializes the class
        \param experimentNodes (\c dictionary of dictionaries of ExperimentNode) The experiment nodes
        \param user (\c UserManagement) The UserManagement object containing the user's info
        \param startDate (\c string) The start date for the experiment
        \param endDate (\c string) The end date for the experiment
        \param experimentID (\c string) The experiment id
        \param experimentFile (\c string) The xml file containing the experiment's topology
        \param startTime (\c string) The start time for the experiment
        \param endTime (\c string) The end time for the experiment
        \param experimentGroups (\c list of string) The experiment groups that the experiment belongs to
        """
        self.__experimentNodes = experimentNodes
        self.__user = user
        self.__startDate = startDate
        self.__endDate = endDate
        self.__experimentID = experimentID
        self.__experimentFile = experimentFile
        self.__startTime = startTime
        self.__endTime = endTime
        self.__experimentGroups = experimentGroups

    def setExperimentNodes(self, e):
        """\brief Sets the experiment nodes
        \param e (\c dictionary of dictionaries) The experiment nodes
        """
        self.__experimentNodes = e

    def getExperimentNodes(self):
        """\brief Gets the experiment nodes
        \return (\c dictionary of dictionaries) The experiment nodes
        """
        return self.__experimentNodes

    def setUser(self, u):
        """\brief Sets the user
        \param e (\c UserManagement) The user
        """
        self.__user = u

    def getUser(self):
        """\brief Gets the user
        \return (\c UserManagement) The user
        """
        return self.__user

    def setStartDate(self, s):
        """\brief Sets the start date
        \param e (\c string) The start date
        """
        self.__startDate = s

    def getStartDate(self):
        """\brief Gets the start date
        \return (\c string) The start date
        """
        return self.__startDate

    def setEndDate(self, e):
        """\brief Sets the end date
        \param e (\c string) The end date
        """
        self.__endDate = e

    def getEndDate(self):
        """\brief Gets the end date
        \return (\c string) The end date
        """
        return self.__endDate


    def setStartTime(self, s):
        """\brief Sets the start time
        \param s (\c string) The start time
        """
        self.__startTime = s

    def getStartTime(self):
        """\brief Gets the start time
        \return (\c string) The start time
        """
        return self.__startTime

    def setEndTime(self, e):
        """\brief Sets the end time
        \param e (\c string) The end time
        """
        self.__endTime = e

    def getEndTime(self):
        """\brief Gets the end time
        \return (\c string) The end time
        """
        return self.__endTime

    def setExperimentGroups(self, experimentGroups):
        """\brief Sets the experiment groups
        \param experimentGroups (\c list of string) The experiment groups
        """
        self.__experimentGroups = experimentGroups

    def getExperimentGroups(self):
        """\brief Gets the experiment groups
        \return (\c list of string) The experiment groups
        """
        return self.__experimentGroups    


    def setExperimentID(self, e):
        """\brief Sets the experiment id
        \param e (\c string) The experiment id
        """
        self.__experimentID = e

    def getExperimentID(self):
        """\brief Gets the experiment id
        \return (\c string) The experiment id
        """
        return self.__experimentID

    def setExperimentFile(self, f):
        """\brief Sets the xml file with the experiment topology
        \param e (\c string) The xml file with the experiment topology
        """
        self.__experimentFile = f

    def getExperimentFile(self):
        """\brief Gets the xml file with the experiment topology
        \return (\c string) The xml file with the experiment topology
        """
        return self.__experimentFile

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        
        string = "UserExperiment:" + "\n" + \
                 " user=" + str(self.getUser()) + \
                 " experimentID=" + str(self.getExperimentID()) + "\n" + \
                 " startDate=" + str(self.getStartDate()) + "\n" + \
                 " endDate=" + str(self.getEndDate()) + "\n" + \
                 " startTime=" + str(self.getStartTime()) + "\n" + \
                 " endTime=" + str(self.getEndTime()) + "\n" + \
                 " experimentFile=" + str(self.getExperimentFile()) + "\n"

        for nodeTypeDictionary in self.getExperimentNodes().values():
            for node in nodeTypeDictionary.values():
                string += "\t\t" + str(node)

        return string
    

class ExperimentNode:
    """\brief
    Used to hold information about a node being used in an experiment
    """
    def __init__(self, node=None, netbootInfo=None, experimentID=None, user=None, startDate=None, endDate=None, startTime=None, endTime=None):
        """
        \param node (\c Node) The Node object used to hold information
        \param netbootInfo (\c NetbootInfo) The NetbootInfo object used to hold information
        \param experimentID (\c string) The experiment's id that the node belongs to
        \param user (\c UserManagement) The user who owns the experiment
        \param startDate (\c string) The experiment's start date
        \param endDate (\c string) The experiment's end date
        \param startTime (\c string) The experiment's start time
        \param endTime (\c string) The experiment's end time        
        """
        self.__node = node
        self.__netbootInfo = netbootInfo
        self.__experimentID = experimentID
        self.__user = user
        self.__startDate = startDate
        self.__endDate = endDate
        self.__startTime = startTime
        self.__endTime = endTime        

    def setNode(self, s):
        """\brief Sets the Node object
        \param e (\c Node) The Node object
        """
        self.__node = s

    def getNode(self):
        """\brief Gets the Node object
        \return (\c Node) The Node object
        """
        return self.__node

    def setNetbootInfo(self, n):
        """\brief Sets the netboot information object
        \param e (\c NetbootInfo) The netboot information object
        """
        self.__netbootInfo = n

    def getNetbootInfo(self):
        """\brief Gets the netboot information object
        \return (\c NetbootInfo) The netboot information object
        """
        return self.__netbootInfo

    def setUser(self, u):
        """\brief Sets the user
        \param e (\c UserManagement) The user
        """
        self.__user = u

    def getUser(self):
        """\brief Gets the user
        \return (\c UserManagement) The user
        """
        return self.__user

    def setStartDate(self, s):
        """\brief Sets the start date
        \param e (\c string) The start date
        """
        self.__startDate = s

    def getStartDate(self):
        """\brief Gets the start date
        \return (\c string) The start date
        """
        return self.__startDate

    def setEndDate(self, e):
        """\brief Sets the end date
        \param e (\c string) The end date
        """
        self.__endDate = e

    def getEndDate(self):
        """\brief Gets the end date
        \return (\c string) The end date
        """
        return self.__endDate

    def setStartTime(self, s):
        """\brief Sets the start time
        \param e (\c string) The start time
        """
        self.__startTime = s

    def getStartTime(self):
        """\brief Gets the start time
        \return (\c string) The start time
        """
        return self.__startTime

    def setEndTime(self, e):
        """\brief Sets the end time
        \param e (\c string) The end time
        """
        self.__endTime = e

    def getEndTime(self):
        """\brief Gets the end time
        \return (\c string) The end time
        """
        return self.__endTime

    def setExperimentID(self, e):
        """\brief Sets the experiment id
        \param e (\c string) The experiment id
        """
        self.__experimentID = e

    def getExperimentID(self):
        """\brief Gets the experiment id
        \return (\c string) The experiment id
        """
        return self.__experimentID

    def getNodeID(self):
        """\brief Gets the node id
        \return (\c string) The node id
        """
        return self.__node.getNodeID()

    def getNodeType(self):
        """\brief Gets the node type
        \return (\c string) The node type
        """
        return self.__node.getNodeType()

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        return "ExperimentNode:" + "\n" + \
               " netbootinfo=" + str(self.getNetbootInfo()) + "\n" + \
               " user=" + str(self.getUser()) + "\n" + \
               " experimentID=" + str(self.getExperimentID()) + "\n" + \
               " startDate=" + str(self.getStartDate()) + "\n" + \
               " endDate=" + str(self.getEndDate()) + "\n" + \
               " startTime=" + str(self.getStartTime()) + "\n" + \
               " endTime=" + str(self.getEndTime()) + "\n" + \
               " node=" + str(self.getNode())
        
    
class NetbootInfo:
    """\brief Class used to hold information about what a node should netboot
    """
    
    def __init__(self, loader=None, filesystem=None, kernel=None):
        """\brief Initializes the class
        \param loader (\c string) The path to the loader to be used
        \param filesystem (\c string) The path to the filesystem to be used
        \param kernel (\c string) The path to the kernel to be used
        """
        self.__loader = loader
        self.__filesystem = filesystem
        self.__kernel = kernel

    def setLoader(self, l):
        """\brief Sets the loader
        \param l (\c string) The path to the loader
        """
        self.__loader = l
        
    def getLoader(self):
        """\brief Gets the loader
        \return (\c string) The path to the loader
        """
        return self.__loader

    def setFileSystem(self, f):
        """\brief Sets the filesystem
        \param f (\c string) The path to the filesystem
        """
        self.__filesystem = f

    def getFileSystem(self):
        """\brief Gets the filesystem
        \return (\c string) The path to the filesystem
        """
        return self.__filesystem

    def setKernel(self, k):
        """\brief Sets the kernel
        \param k (\c string) The path to the kernel
        """
        self.__kernel = k
        
    def getKernel(self):
        """\brief Gets the kernel
        \return (\c string) The path to the kernel
        """
        return self.__kernel
    
    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        return "NetbootInfo:" + \
               " loader=" + str(self.getLoader()) + \
               " filesystem=" + str(self.getFileSystem()) + \
               " kernel=" + str(self.getKernel())

class DHCPConfigInfo:
    """\brief Class used to hold information needed to create a dhcp config file
    """
    
    def __init__(self, domainName=None, domainNameServers=None, defaultLeaseTime=None, maximumLeaseTime=None, authoritative=None, ddnsUpdateStyle=None, logFacility=None, subnetInfoList=None):
        """\brief Initializes class
        \param domainName (\c string) The domain name
        \param domainNameServers (\c string) The domain name servers
        \param defaultLeaseTime (\c string) The default lease time
        \param maximumLeaseTime (\c string) The maximum lease time
        \param authoritative (\c string) Whether the server is authoritative or not (set to authoritative for yes)
        \param ddnsUpdateStyle (\c string) The ddns update style
        \param logFacility (\c string) The log facility
        \param subnetInfoList (\c list) A list of DHCPConfigSubnetInfo objects, one for each subnet in the config file
        """
        self.__domainName = domainName
        self.__domainNameServers = domainNameServers
        self.__defaultLeaseTime = defaultLeaseTime
        self.__maximumLeaseTime = maximumLeaseTime
        self.__authoritative = authoritative
        self.__ddnsUpdateStyle = ddnsUpdateStyle
        self.__logFacility = logFacility                          
        self.__subnetInfoList = subnetInfoList

    def setDomainName(self, d):
        """ Sets the domain name
        \param d (\c string) The domain name
        """
        self.__domainName = d

    def getDomainName(self):
        """ Gets the domain name
        \return (\c string) The domain name
        """
        return self.__domainName

    def setDomainNameServers(self, d):
        """ Sets the domain name servers 
        \param d (\c string) The domain name servers
        """
        self.__domainNameServers = d

    def getDomainNameServers(self):
        """ Gets the domain name servers 
        \return (\c string) The domain name servers
        """
        return self.__domainNameServers

    def setDefaultLeaseTime(self, d):
        """ Sets the default lease time
        \param d (\c string) The default lease time
        """
        self.__defaultLeaseTime = d

    def getDefaultLeaseTime(self):
        """ Gets the default lease time
        \return (\c string) The default lease time
        """
        return self.__defaultLeaseTime

    def setMaximumLeaseTime(self, d):
        """ Sets the maximum lease time
        \param d (\c string) The maximum lease time
        """
        self.__maximumLeaseTime = d

    def getMaximumLeaseTime(self):
        """ Gets the maximum lease time
        \return (\c string) The maximum lease time
        """
        return self.__maximumLeaseTime

    def setAuthoritative(self, a):
        """ Sets whether the server is authoritative or not
        \param a (\c string) Whether the server is authoritative or not
        """
        self.__authoritative = a

    def getAuthoritative(self):
        """ Gets whether the server is authoritative or not
        \return (\c string) Whether the server is authoritative or not
        """
        return self.__authoritative

    def setDDNSUpdateStyle(self, d):
        """ Sets the ddns update style
        \param d (\c string) The ddns update style
        """
        self.__ddnsUpdateStyle = d

    def getDDNSUpdateStyle(self):
        """ Gets the ddns update style
        \return (\c string) The ddns update style
        """
        return self.__ddnsUpdateStyle

    def setLogFacility(self, l):
        """ Sets the log facility
        \param l (\c string) The log facility
        """
        self.__logFacility = l

    def getLogFacility(self):
        """ Gets the log facility
        \return (\c string) The log facility
        """
        return self.__logFacility

    def setSubnetInfoList(self, s):
        """ Sets the list of DHCPConfigSubnetInfo objects representing the config file's subnets
        \param s (\c list) The list of DHCPConfigSubnetInfo objects representing the config file's subnets
        """
        self.__subnetInfoList = s

    def getSubnetInfoList(self):
        """ Gets the list of DHCPConfigSubnetInfo objects representing the config file's subnets
        \return (\c list) The list of DHCPConfigSubnetInfo objects representing the config file's subnets
        """
        return self.__subnetInfoList

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "DHCPConfigInfo:" + "\n" + \
                 " domainName=" + str(self.getSubnet()) + "\n" + \
                 " domainNameServers=" + str(self.getNetmask()) + "\n" + \
                 " defaultLeaseTime=" + str(self.getUseHostDeclNames()) + "\n" + \
                 " maximumLeaseTime=" + str(self.getSubnetMask()) + "\n" + \
                 " authoritative=" + str(self.getBroadcastAddress()) + "\n" + \
                 " ddnsUpdateStyle=" + str(self.getDomainName()) + "\n" + \
                 " logFacility=" + str(self.getRouters()) + "\n"
        
        # process DHCPConfigSubnetInfo list
        string += "\tdchp subnets info: "
        subnetInfoList = self.getSubnetInfoList()
        if (subnetInfoList == None or len(subnetInfoList) == 0):
            string += "None \n"
        else:
            for subnetInfo in subnetInfoList:
                string += "\n\t\t" + str(subnetInfo) + "\n"
            
        return string
    
    
class DHCPConfigSubnetInfo:
    """\brief Class used to hold information needed to create a subnet entry
              in a dhcp config file
    """
    def __init__(self, subnet=None, netmask=None, useHostDeclNames=None, subnetMask=None, broadcastAddress=None, domainName=None, routers=None, nextServer=None, subnetType=None):
        """\brief Initializes class
        \param subnet (\c string) The ip address for the subnet
        \param netmask (\c string) The netmask
        \param useHostDeclNames (\c string) Whether to use host declination names (on|off)
        \param subnetMask (\c string) The netmask for the subnet
        \param broadcastAddress (\c string) The broadast ip address for the subnet
        \param domainName (\c string) The domain name for the subnet
        \param routers (\c string) The ip addresses for the routers for the subnet
        \param nextServer (\c string) The ip address for the next server for the subnet
        \param subnetType (\c string) The subnet type (either experimental or infrastructure)
        """
        self.__subnet = subnet
        self.__netmask = netmask
        self.__useHostDeclNames = useHostDeclNames
        self.__subnetMask = subnetMask
        self.__broadcastAddress = broadcastAddress
        self.__domainName = domainName
        self.__routers = routers
        self.__nextServer = nextServer
        self.__subnetType = subnetType

    def setSubnet(self, s):
        """ Sets the ip address for the subnet
        \param s (\c string) The ip address
        """
        self.__subnet = s

    def getSubnet(self):
        """ Gets the ip address for the subnet
        \return (\c string) The ip address
        """
        return self.__subnet

    def setNetmask(self, n):
        """ Sets the ip netmask for the subnet
        \param n (\c string) The netmask
        """
        self.__netmask = n

    def getNetmask(self):
        """ Gets the netmask for the subnet
        \return (\c string) The netmask
        """
        return self.__netmask

    def setUseHostDeclNames(self, u):
        """ Sets whether to use host declination names or not
        \param u (\c string) Either yes or no
        """
        self._useHostDeclNames = u

    def getUseHostDeclNames(self):
        """ Gets whether to use host declination names or not
        \return (\c string) Either yes or no
        """
        return self.__useHostDeclNames

    def setSubnetMask(self, s):
        """ Sets the netmask for the subnet
        \param s (\c string) The netmask
        """
        self.__subnetMask = s

    def getSubnetMask(self):
        """ Gets the netmask for the subnet
        \return (\c string) The ip address
        """
        return self.__subnetMask

    def setBroadcastAddress(self, b):
        """ Sets the broadcast address for the subnet
        \param b (\c string) The broadcast address
        """
        self.__broadcastAddress = b

    def getBroadcastAddress(self):
        """ Gets the ip broadcast address for the subnet
        \return (\c string) The broadcast address
        """
        return self.__broadcastAddress

    def setDomainName(self, d):
        """ Sets the domain name for the subnet
        \param d (\c string) The domain name
        """
        self.__domainName = d

    def getDomainName(self):
        """ Gets the domain name for the subnet
        \return (\c string) The domain name
        """
        return self.__domainName

    def setRouters(self, r):
        """ Sets the routers for the subnet
        \param r (\c string) The routers
        """
        self.__routers = r

    def getRouters(self):
        """ Gets the routers for the subnet
        \return (\c string) The routers
        """
        return self.__routers

    def setNextServer(self, n):
        """ Sets the next server for the subnet
        \param n (\c string) The next server
        """
        self.__nextServer = n

    def getNextServer(self):
        """ Gets the next server for the subnet
        \return (\c string) The next server
        """
        return self.__nextServer

    def setSubnetType(self, s):
        """ Sets the subnet type (either experimental or infrastructure)
        \param s (\c string) The subnet type
        """
        self.__subnetType = s

    def getSubnetType(self):
        """ Gets the subnet type (either experimental or infrastructure)
        \return (\c string) The subnet type
        """
        return self.__subnetType

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        return "DHCPConfigSubnetInfo:" + "\n" + \
               " subnet=" + str(self.getSubnet()) + "\n" + \
               " netmask=" + str(self.getNetmask()) + "\n" + \
               " useHostDeclNames=" + str(self.getUseHostDeclNames()) + "\n" + \
               " subnetMask=" + str(self.getSubnetMask()) + "\n" + \
               " broadcastAddress=" + str(self.getBroadcastAddress()) + "\n" + \
               " domainName=" + str(self.getDomainName()) + "\n" + \
               " routers=" + str(self.getRouters()) + "\n" + \
               " nextServer=" + str(self.getNextServer()) + "\n" + \
               " subnetType=" + str(self.getSubnetType()) 


class DNSConfigInfo:
    """\brief Class used to hold information needed to create dns forward and reverse lookup files
    """

    def __init__(self, ttl=None, contact=None, refreshTime=None, retryTime=None, expiryTime=None, minimumTime=None, experimentalBaseNetworkAddress = None, experimentalDomainName=None, experimentalServerAddress=None, infrastructureBaseNetworkAddress=None, infrastructureDomainName=None, infrastructureServerAddress=None,virtualBaseNetworkAddress=None, virtualDomainName=None, virtualServerAddress=None):
        """\brief Initializes class
        \param ttl (\c string) The DNS TTL
        \param contact (\c string) The DNS contact (an email address)
        \param refreshTime (\c string) The DNS refresh time
        \param retryTime (\c string) The DNS retry time
        \param expiryTime (\c string) The DNS expirty time
        \param minimumTime (\c string) The DNS minimum time
        \param experimentalBaseNeworkAddress (\c string) The experimental subnet's base network address (192.168.0 for instance)
        \param experimentalDomainName (\c string) The experimental subnet's domain name
        \param experimentalServerAddress (\c string) The experimental subnet's server address
        \param infrastructureBaseNeworkAddress (\c string) The infrastructure subnet's base network address (192.168.1 for instance)        
        \param infrastructureDomainName (\c string) The infrastructure subnet's domain name
        \param infrastructureServerAddress (\c string) The infrastructure subnet's server address
        """
        self.__ttl = ttl
        self.__contact = contact
        self.__refreshTime = refreshTime
        self.__retryTime = retryTime
        self.__expiryTime = expiryTime
        self.__minimumTime = minimumTime
        self.__experimentalBaseNetworkAddress = experimentalBaseNetworkAddress
        self.__experimentalDomainName = experimentalDomainName
        self.__experimentalServerAddress = experimentalServerAddress
        self.__infrastructureBaseNetworkAddress = infrastructureBaseNetworkAddress        
        self.__infrastructureDomainName = infrastructureDomainName        
        self.__infrastructureServerAddress = infrastructureServerAddress
        self.__virtualBaseNetworkAddress = virtualBaseNetworkAddress        
        self.__virtualDomainName = virtualDomainName        
        self.__virtualServerAddress = virtualServerAddress

    def setTTL(self, t):
        """ Sets the DNS ttl
        \param t (\c string) The DNS ttl
        """
        self.__ttl = t

    def getTTL(self):
        """ Gets the DNS ttl
        \return (\c string) The DNS ttl
        """
        return self.__ttl

    def setContact(self, c):
        """ Sets the DNS contact (an email address)
        \param c (\c string) The DNS contact
        """
        self.__contact = c

    def getContact(self):
        """ Gets the DNS contact
        \return (\c string) The DNS contact
        """
        return self.__contact

    def setRefreshTime(self, t):
        """ Sets the DNS refresh time
        \param d (\c string) The DNS refresh time
        """
        self.__refreshTime = t

    def getRefreshTime(self):
        """ Gets the DNS refresh time
        \return (\c string) The DNS refresh time
        """
        return self.__refreshTime

    def setRetryTime(self, t):
        """ Sets the DNS retry time
        \param d (\c string) The DNS retry time
        """
        self.__retryTime = t

    def getRetryTime(self):
        """ Gets the DNS retry time
        \return (\c string) The DNS retry time
        """
        return self.__retryTime

    def setExpiryTime(self, t):
        """ Sets the DNS expiry time
        \param d (\c string) The DNS expiry time
        """
        self.__expiryTime = t

    def getExpiryTime(self):
        """ Gets the DNS expiry time
        \return (\c string) The DNS expiry time
        """
        return self.__expiryTime

    def setMinimumTime(self, t):
        """ Sets the DNS minimum time
        \param d (\c string) The DNS minimum time
        """
        self.__minimumTime = t

    def getMinimumTime(self):
        """ Gets the DNS minimum time
        \return (\c string) The DNS minimum time
        """
        return self.__minimumTime

    def setExperimentalBaseNetworkAddress(self, e):
        """ Sets the experimental subnet's base network address (192.168.0 for instance)
        \param e (\c string) The experimental subnet's base network address
        """
        self.__experimentalBaseNetworkAddress = e

    def getExperimentalBaseNetworkAddress(self):
        """ Gets experimental subnet's base network address (192.168.0 for instance)
        \return (\c string) The experimental subnet's base network address
        """
        return self.__experimentalBaseNetworkAddress

    def setExperimentalDomainName(self, e):
        """ Sets the experimental subnet domain name
        \param e (\c string) The experimental subnet domain name
        """
        self.__experimentalDomainName = e

    def getExperimentalDomainName(self):
        """ Gets the experimental subnet domain name
        \return (\c string) The experimental subnet domain name
        """
        return self.__experimentalDomainName

    def setExperimentalServerAddress(self, e):
        """ Sets the experimental subnet server address
        \param e (\c string) The experimental subnet server address
        """
        self.__experimentalServerAddress = e

    def getExperimentalServerAddress(self):
        """ Gets the experimental subnet server address
        \return (\c string) The experimental subnet server address
        """
        return self.__experimentalServerAddress

    def setInfrastructureBaseNetworkAddress(self, i):
        """ Sets the infrastructure subnet's base network address (192.168.0 for instance)
        \param i (\c string) The infrastructure subnet's base network address
        """
        self.__infrastructureBaseNetworkAddress = i

    def getInfrastructureBaseNetworkAddress(self):
        """ Gets infrastructure subnet's base network address (192.168.0 for instance)
        \return (\c string) The infrastructure subnet's base network address
        """
        return self.__infrastructureBaseNetworkAddress

    def setInfrastructureDomainName(self, i):
        """ Sets the infrastructure subnet domain name
        \param i (\c string) The infrastructure subnet domain name
        """
        self.__infrastructureDomainName = i

    def getInfrastructureDomainName(self):
        """ Gets the infrastructure subnet domain name
        \return (\c string) The infrastructure subnet domain name
        """
        return self.__infrastructureDomainName

    def setInfrastructureServerAddress(self, i):
        """ Sets the infrastructure subnet server address
        \param i (\c string) The infrastructure subnet server address
        """
        self.__infrastructureServerAddress = i

    def getInfrastructureServerAddress(self):
        """ Gets the infrastructure subnet server address
        \return (\c string) The infrastructure subnet server address
        """
        return self.__infrastructureServerAddress
    
    def setVirtualBaseNetworkAddress(self, i):
        """ Sets the virtual subnet's base network address (192.168.0 for instance)
        \param i (\c string) The virtual subnet's base network address
        """
        self.__virtualBaseNetworkAddress = i

    def getVirtualBaseNetworkAddress(self):
        """ Gets virtual subnet's base network address (192.168.0 for instance)
        \return (\c string) The virtual subnet's base network address
        """
        return self.__virtualBaseNetworkAddress

    def setVirtualDomainName(self, i):
        """ Sets the virtual subnet domain name
        \param i (\c string) The virtual subnet domain name
        """
        self.__virtualDomainName = i

    def getVirtualDomainName(self):
        """ Gets the virtual subnet domain name
        \return (\c string) The virtual subnet domain name
        """
        return self.__virtualDomainName

    def setVirtualServerAddress(self, i):
        """ Sets the virtual subnet server address
        \param i (\c string) The virtual subnet server address
        """
        self.__virtualServerAddress = i

    def getVirtualServerAddress(self):
        """ Gets the virtual subnet server address
        \return (\c string) The virtual subnet server address
        """
        return self.__virtualServerAddress

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        return "DNSConfigInfo:" + "\n" + \
               " ttl=" + str(self.getTTL()) + "\n" + \
               " contact=" + str(self.getContact()) + "\n" + \
               " refreshTime=" + str(self.getRefreshTime()) + "\n" + \
               " retryTime=" + str(self.getRetryTime()) + "\n" + \
               " expiryTime=" + str(self.getExpiryTime()) + "\n" + \
               " minimumTime=" + str(self.getMinimumTime()) + "\n" + \
               " experimentalBaseNetworkAddress=" + str(self.getExperimentalBaseNetworkAddress()) + "\n" + \
               " experimentalDomainName=" + str(self.getExperimentalDomainName()) + "\n" + \
               " experimentalServerAddress=" + str(self.getExperimentalServerAddress()) + "\n" + \
               " infrastructureBaseNetworkAddress=" + str(self.getInfrastructureBaseNetworkAddress()) + "\n" + \
               " infrastructureDomainName=" + str(self.getInfrastructureDomainName()) + "\n" + \
               " infrastructureDomainName=" + str(self.getInfrastructureServerAddress()) + "\n" +         \
               " virtualBaseNetworkAddress=" + str(self.getVirtualBaseNetworkAddress()) + "\n" + \
               " virtualDomainName=" + str(self.getVirtualDomainName()) + "\n" + \
               " virtualServerAddress=" + str(self.getVirtualServerAddress()) + "\n"  

        
class Interface:
    """\brief Class used to hold information about a network interface
    """
    
    def __init__(self, mac=None, ip=None, subnet=None, switch=None, port=None, vlan=None, ifaceType=None, speed=None, model=None, name=None, interfaceID=None):
        """\brief Initializes the class
        \param mac (\c string) The interface's mac address
        \param ip (\c string) The interface's ip address 
        \param subnet (\c string) The interface's subnet mask (in dot notation)
        \param switch (\c string) The switch that the interface is connected to
        \param port (\c string) The port on the switch that the interface is connected to
        \param vlan (\c string) The vlan on the switch that the interface is connected to
        \param ifaceType (\c string) The interface's type (management or experimental)
        \param speed (\c string) The interface's speed
        \param model (\c string) The interface's model
        \param name (\c string) The interface's name (eth0 in Linux, for instance)
        \param interfaceID(\c string) The id of the interface (interface1 for instance). The id is unique within the scope
                                      of the device it's on, and generally interface0 will be reserved for a management
                                      interface
        """
        self.__mac = mac
        self.__ip = ip
        self.__subnet = subnet
        self.__switch = switch
        self.__port = port
        self.__vlan = vlan
        self.__ifaceType = ifaceType
        self.__speed = speed
        self.__model = model
        self.__name = name
        self.__interfaceID = interfaceID
        self.__tdr_success = None
        self.__tdr_output = None
        
    def setMAC(self, m):
        """\brief Sets the interface's mac address
        \param n (\c string) The interface's mac address
        """
        self.__mac = m
        
    def getMAC(self):
        """\brief Gets the interface's mac address
        \return (\c string) The interface's mac address
        """
        return self.__mac

    def setIP(self, i):
        """\brief Sets the interface's ip address
        \param n (\c string) The interface's ip address
        """
        self.__ip= i

    def getIP(self):
        """\brief Gets the interface's ip address
        \return (\c string) The interface's ip address
        """
        return self.__ip

    def setSubnet(self, s):
        """\brief Sets the interface's subnet
        \param n (\c string) The inteface's subnet
        """
        self.__subnet = s

    def getSubnet(self):
        """\brief Gets the interface's subnet
        \return (\c string) The inteface's subnet
        """
        return self.__subnet
    
    def setSwitch(self, s):
        """\brief Sets the switch that the interface is connected to
        \param n (\c string) The switch that the interface is connected to
        """
       	self.__switch = s

    def getSwitch(self):
        """\brief Gets the the switch that the interface is connected to
        \return (\c string) The switch that the interface is connected to
        """
        return self.__switch

    def setPort(self, p):
        """\brief Sets the port on the switch that the interface is connected to
        \param n (\c string) The port on the switch that the interface is connected to
        """
       	self.__port = p

    def getPort(self):
        """\brief Gets the port on the switch that the interface is connected to
        \return (\c string) The port on the switch that the interface is connected to
        """
        return self.__port
    
    def setVLAN(self, v):
        """\brief Sets the vlan that the interface is on
        \param n (\c string) The vlan that the interface is on
        """
        self.__vlan = v

    def getVLAN(self):
        """\brief Gets the vlan that the interface is on
        \return (\c string) The vlan that the interface is on
        """
        return self.__vlan

    def setIfaceType(self, i):
        """\brief Sets the interface's type
        \param n (\c string) The interface's type (either management or experimental)
        """
        self.__ifaceType = i

    def getIfaceType(self):
        """\brief Gets the interface's type
        \return (\c string) The interface's type (either management or experimental)
        """
        return self.__ifaceType

    def setSpeed(self, s):
        """\brief Sets the interface's speed
        \param n (\c string) The interface's speed
        """
        self.__speed = s

    def getSpeed(self):
        """\brief Gets the interface's speed
        \return (\c string) The interface's speed
        """
        return self.__speed

    def setModel(self, m):
        """\brief Sets the interface's model
        \param m (\c string) The interface's model
        """
        self.__model = m

    def getModel(self):
        """\brief Gets the inteface's model
        \return (\c string) The interface's model
        """
        return self.__model

    def setName(self, n):
        """\brief Sets the interface's name
        \param n (\c string) The interface's name
        """
        self.__name = n

    def getName(self):
        """\brief Gets the inteface's name
        \return (\c string) The interface's name
        """
        return self.__name

    def setInterfaceID(self, interfaceID):
        """\brief Sets the interface's ID
        \param interfaceID (\c string) The interface's ID
        """
        self.__interfaceID = interfaceID

    def getInterfaceID(self):
        """\brief Gets the inteface's ID
        \return (\c string) The interface's ID
        """
        return self.__interfaceID

    def setTdrSuccess(self,s):
        self.__tdr_success = s

    def getTdrSuccess(self):
        return self.__tdr_success

    def getTdrOutput(self):
        return self.__tdr_output

    def setTdrOutput(self,s):
        self.__tdr_output = s
    
    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "Interface:" + \
               " type=" + str(self.getIfaceType()) + \
               " mac=" + str(self.getMAC()) + \
               " ip=" + str(self.getIP()) + \
               " subnet=" + str(self.getSubnet()) + \
               " switch=" + str(self.getSwitch()) + \
               " port=" + str(self.getPort()) + \
               " vlan=" + str(self.getVLAN()) + \
               " model=" + str(self.getModel()) + \
               " speed=" + str(self.getSpeed()) + \
               " name=" + str(self.getName()) + \
               " interfaceID=" + str(self.getInterfaceID())     
        if self.__tdr_success == False:
            string = string + " tdrSuccess=Failed tdrOutput=" + str(self.__tdr_output)
        return string

class VLAN:
    """\brief Class used to hold information about a vlan. The ports and switches are stored in
              a dictionary whose keys are the switches' ids and whose values are lists of strings
              representing the ports
    """

    def __init__(self, vlanName=None, vlanSwitches={}, vlanID=None, vlanInternalID=None, vlanTaggedID=None):
        """\brief Initializes the class.
        \param vlanName (\c string) The name of the vlan
        \param vlanID (\c string) The external id of the vlan
        \param vlanInternalID (\c string) The internal id of the vlan
        \param vlanTaggedID (\c string) The id of the tagged vlan (3com specific ?)
        \param vlanSwitches (\c dictionary of lists of Port objects) The switches and ports that the vlan is on
        """
        self.__vlanName = vlanName
        self.__vlanID = vlanID
        self.__vlanInternalID = vlanInternalID
        self.__vlanTaggedID = vlanTaggedID
        self.__vlanSwitches = vlanSwitches

    def setName(self, n):
        """\brief Sets the vlan's name
        \param n (\c string) The vlan's name
        """
        self.__vlanName = n

    def getName(self):
        """\brief Gets the vlan's name
        \return (\c string) The vlan's name
        """
        return self.__vlanName

    def setID(self, i):
        """\brief Sets the vlan's external id
        \param i (\c string) The vlan's external id
        """
        self.__vlanID = i

    def getID(self):
        """\brief Gets the vlan's external id
        \return (\c string) The vlan's external id
        """
        return self.__vlanID

    def setInternalID(self, i):
        """\brief Sets the vlan's internal id
        \param i (\c string) The vlan's internal id
        """
        self.__vlanInternalID = i

    def getInternalID(self):
        """\brief Gets the vlan's internal id
        \return (\c string) The vlan's internal id
        """
        return self.__vlanInternalID

    def setTaggedID(self, i):
        """\brief Sets the vlan's tagged id
        \param i (\c string) The vlan's tagged id
        """
        self.__vlanTaggedID = i

    def getTaggedID(self):
        """\brief Gets the vlan's internal id
        \return (\c string) The vlan's internal id
        """
        return self.__vlanTaggedID    

    def setSwitches(self, s):
        """\brief Sets the dictionary of switches
        \param s (\c dictionary of lists) The dictionary of switches
        """        
        self.__vlanSwitches = s
        
    def getSwitches(self):
        """\brief Gets the dictionary of switches
        \return (\c dictionary of lists) The dictionary of switches
        """        
        return self.__vlanSwitches

    def getPorts(self):
        """\brief Gets all the ports on all the switches for the vlan
        \return (\c dictionary of lists of Port objects) The ports
        """
        return self.__vlanSwitches
    
    def getPortsOnSwitch(self, switchID):
        """\brief Gets the vlan ports that belong to the given switch
        \param switchID (\c string) The switch whose ports are needed
        \return (\c list of Port objects) A list of string representing the ports, None if the switchID
                                     does not match any of the switches in the vlan
        """
        if (self.__vlanSwitches == None):
            return None
        
        if (not(self.__vlanSwitches.has_key(switchID))):
            return None
        else:
            return self.__vlanSwitches[switchID]
        
    def addPorts(self, ports, switchID):
        """\brief Adds the given ports to the given switch. If the switch is not part
                  of the vlan it is added to the vlan. A switch is considered not to belong to the vlan
                  if the switchID is not a key in the dictionary or if the value corresponding to
                  the key is None. Only ports that are not already in the switch are added.
        \param ports (\c list of Port objects) The ports to add
        \param switchID (\c string) The id of the switch to add ports to
        """
        if (self.__vlanSwitches == None):
            self.__vlanSwitches = {}
            
        if ( (not(self.__vlanSwitches.has_key(switchID))) or (self.__vlanSwitches[switchID] == None) ):
            self.addSwitch(switchID)

        for port in ports:
            if (not(self.__isPortInList(port, self.__vlanSwitches[switchID]))):
                self.__vlanSwitches[switchID].append(port)

    def deletePorts(self, ports, switchID):
        """\brief Deletes the given ports from the given switch. If the switch is not part
                  of the vlan nothing is done. Ports that do not belong to the given switch are
                  ignored.
        \param ports (\c list of strings) The ports to delete
        \param switchID (\c string) The id of the switch to delete ports from
        """
        if ( (not(self.__vlanSwitches.has_key(switchID))) or (self.__vlanSwitches[switchID] == None) ):
            return

        for port in ports:
            if (self.__isPortInList(port, self.__vlanSwitches[switchID])):
                self.__vlanSwitches[switchID].remove(port)
    
    def addSwitch(self, switchID):
        """\brief Adds a switch to the vlan
        \param switchID (\c string) The id of the switch to add to the vlan
        """
        self.__vlanSwitches[switchID] = []

    def deleteSwitch(self, switchID):
        """\brief Deletes a switch from the vlan
        \param switchID (\c string) The id of the switch to delete from the vlan        
        """
        self.__vlanSwitches[switchID] = None

    def isPortInVLAN(self, searchPort):
        """\brief Returns true if the given port is in the vlan, False otherwise. The
                  port is matched on its external id (port number) and on whether it is
                  tagged or untagged.
        \param searchPort (\c Port) The Port object to search for
        \return (\c boolean) True if found, False otherwise
        """
        for portList in self.__vlanSwitches.values():
            for port in portList:
                if (port.getPortNumber() == searchPort.getPortNumber() and \
                    port.getTagged() == searchPort.getTagged()):
                    return True

        return False

    def isPortInVLANIgnorePortType(self, searchPort):
        """\brief Returns true if the given port is in the vlan, False otherwise. The
                  port is matched only on its external id (port number).
        \param searchPort (\c Port) The Port object to search for
        \return (\c boolean) True if found, False otherwise
        """
        for portList in self.__vlanSwitches.values():
            for port in portList:
                if (port.getInternalID() == searchPort):
                    return True

        return False

    def __isPortInList(self, port, portsList):
        """\brief Returns whether the given Port object exists in the given lists of Port objects. The function
                  matches on the Port object's getPortNumber function
        \param port (\c Port) The port object to search for in the list
        \param portsList (\c list of Port objects) The list to search the port in
        \return (\c boolean) True if the port exists in the list, False otherwise
        """
        for listPort in portsList:
            if (listPort.getPortNumber() == port.getPortNumber()):
                return True
            
        return False
        
    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "VLAN:"+\
                 " name=" + str(self.getName()) + \
                 " id=" + str(self.getID()) + \
                 " internalID=" + str(self.getInternalID())        
        if self.getTaggedID != None:
            string = string + " taggedID=" + str(self.getTaggedID())

        switches = self.getSwitches()
        for key in switches.keys():
            string += "\n\t" + str(key) + ":\n"
            for port in switches[key]:
                string += "\t\t" + str(port)

        return string

    def __eq__(self,other):
        """\brief Compares two vlans.
        \param other (\c VLAN) a vlan object to compare with this one.
        \return (\c Boolean) True if the vlans are the same.
        """
        if self.getName() != other.getName():
            return False
        if self.getID() != other.getID():
            return False
        if self.getInternalID() != other.getInternalID():
            return False
        if (len(self.getSwitches()) != len(other.getSwitches())):
            return False
        for sk in self.getSwitches():
            if other.getSwitches().has_key(sk):
                if (len(self.getSwitches()[sk]) != len(other.getSwitches()[sk])):
                    return False
                for i in range(0,len(self.getSwitches()[sk])):
                    if not(self.getSwitches()[sk][i] == other.getSwitches()[sk][i]):
                        return False
            else:
                return False
        return True

class VlanOwner:
    def __init__(self,name=None,owner=None,vid=None):
        self.__name=name
        self.__owner=owner
        self.__vid=vid
    def __str__(self):
        return "Vlan "+str(self.__name)+"("+str(self.__vid)+") owned by "+str(self.__owner)

    def getName(self):
        return self.__name

    def getOwner(self):
        return self.__owner

    def getVid(self):
        return self.__vid

    def toFileString(self):
        return str(self.__name)+","+str(self.__owner)+","+str(self.__vid)

    def fromFileString(self,file_str):
        args = file_str.split(',')
        self.__name = args[0]
        self.__owner = args[1]
        try:
            self.__vid = args[2]
        except:
            self.__vid = -1

class SimpleVlan:
    def __init__(self,name=None,ident=None,local_id=None,switch=None):
        self.__name=name
        self.__id=ident
        self.__local_id=local_id
        self.__switch=switch
        self.__untagged = []
        self.__tagged = []
        self.__pvid = []
        self.__notes = None
    def setName(self, n):
        self.__name = n
    def getName(self):
        return self.__name
    def setId(self, i):
        self.__id = i
    def getId(self):
        return self.__id
    def setLocalId(self, i):
        self.__local_id = i
    def getLocalId(self):
        return self.__local_id
    def setSwitch(self, s):
        self.__switch = s
    def getSwitch(self):
        return self.__switch
    def setUntagged(self,u_list):
        self.__untagged = u_list
    def getUntagged(self):
        return self.__untagged
    def setPvid(self,p_list):
        self.__pvid = p_list
    def getPvid(self):
        return self.__pvid
    def setTagged(self,t_list):
        self.__tagged = t_list
    def getTagged(self):
        return self.__tagged
    def setNotes(self,notes):
        self.__notes = notes
    def getNotes(self):
        return self.__notes
    def toString(self,ports):
        s = str(self.__name)
        if self.__id != None:
            s = s +  " (" + str(self.__id) + ")"
        if self.__local_id != None:
            s = s +  " [" + str(self.__local_id) + "]"
        s = s + " " + str(self.__switch)
        if self.__untagged != []:
            s = s + "\n\t untagged :"
            for u in self.__untagged:
                s = s + " " + str(ports[u].getName())
        if self.__tagged != []:
            s = s + "\n\t tagged :"
            for t in self.__tagged:
                s = s + " " + str(ports[t].getName())
        if self.__pvid != []:
            s = s + "\n\t pvid :"
            for p in self.__pvid:
                s = s + " " + str(ports[p].getName())
        if self.__notes != None:
            s = s + "\nNotes : "+str(self._notes)
        else:
            s = s + "\n"
        return s
    def __str__(self):
        s = str(self.__name)
        if self.__id != None:
            s = s +  " (" + str(self.__id) + ")"
        if self.__local_id != None:
            s = s +  " [" + str(self.__local_id) + "]"
        s = s + " " + str(self.__switch)
        if self.__untagged != []:
            s = s + "\n\t untagged :"
            for u in self.__untagged:
                s = s + " " + str(u)
        if self.__tagged != []:
            s = s + "\n\t tagged :"
            for t in self.__tagged:
                s = s + " " + str(t)
        if self.__pvid != []:
            s = s + "\n\t pvid :"
            for p in self.__pvid:
                s = s + " " + str(p)
        if self.__notes != None:
            s = s + "\nNotes : "+str(self._notes)
        else:
            s = s + "\n"
        return s

class SimplePort:
    VLANMODE=['UNKNOWN','General','Access','Trunk']    
    def __init__(self,name=None,ident=None,switch=None):
        self.__name=name
        self.__id=ident
        self.__switch=switch
        self.__untagged = (None,None)
        self.__tagged = []
        self.__macs = []
        self.__pvid = (None,None)
        self.__notes = None
        self.__vlan_mode = 0
    def setName(self, n):
        self.__name = n
    def getName(self):
        return self.__name
    def setId(self, i):
        self.__id = i
    def getId(self):
        return self.__id
    def setSwitch(self, s):
        self.__switch = s
    def getSwitch(self):
        return self.__switch
    def setUntagged(self,v):
        self.__untagged = (v[0],v[1])
    def getUntagged(self):
        return self.__untagged
    def setPvid(self,v):
        self.__pvid = (v[0],v[1])
    def getPvid(self):
        return self.__pvid
    def setTagged(self,t_list):
        self.__tagged = t_list
    def getTagged(self):
        return self.__tagged
    def setMacs(self,t_macs):
        self.__macs = t_macs
    def getMacs(self):
        return self.__macs
    def setNotes(self,notes):
        self.__notes = notes
    def getNotes(self):
        return self.__notes
    def getVlanMode(self):
        return self.__vlan_mode
    def setVlanMode(self,mode):
        self.__vlan_mode = mode
        
    def __str__(self):
        s = str(self.__name)
        if self.__id != None:
            s = s +  " [" + str(self.__id) + "]"
        s = s + " " + str(self.__switch)
        if self.__untagged != (None,None):
            s = s + "\n\t untagged : "+str(self.__untagged[0])
            if self.__untagged[1] != None:
                s = s + " (" + str(self.__untagged[1]) + ")"
            
        if self.__tagged != []:
            s = s + "\n\t tagged :"
            for t in self.__tagged:
                if t != (None,None):
                    s = s + " "+str(t[0])
                    if t[1] != None:
                        s = s + " (" + str(t[1]) + ")"
                              
        if self.__pvid != (None,None):
            s = s + "\n\t pvid : "+str(self.__pvid[0])
            if self.__pvid[1] != None:
                s = s + " (" + str(self.__pvid[1]) + ")"

        if self.__macs != []:
            s = s + "\n\t macs :"
            for t in self.__macs:
                s = s + " "+str(t)
        if self.__vlan_mode != 0:
            s = s + "\n\t vlan mode : "+str(SimplePort.VLANMODE[self.__vlan_mode])
        if self.__notes != None:
            s = s + "\nNotes : "+str(self._notes)
        else:
            s = s + "\n"
        return s
    
        
class Port:
    """\brief Class used to hold information about a port on a switch
    """

    def __init__(self, portNumber=None, tagged=False, internalID=None):
        """\brief Initializes class
        \param portNumber (\c string) The port number of the port. This should match the cli's representation of the port
        \param tagged (\c boolean) True if the port is tagged, false otherwise
        \param internalID (\c string) The internal id of the port on the switch
        """
        self.__portNumber = portNumber
        self.__tagged = tagged
        self.__internalID = internalID

    def setPortNumber(self, p):
        """\brief Sets the port number of the port. This should match the cli's representation of the port
        \param p (\c string) The port number for the port
        """
        self.__portNumber = p

    def getPortNumber(self):
        """\brief Gets the port number of the port.
        \return (\c string) The port number for the port
        """
        return self.__portNumber

    def setTagged(self, t):
        """\brief Sets whether the port is tagged or untagged
        \param t (\c boolean) True if the port is tagged, false otherwise
        """        
        self.__tagged = t

    def getTagged(self):
        """\brief Gets whether the port is tagged or untagged
        \return (\c boolean) True if the port is tagged, false otherwise
        """        
        return self.__tagged

    def setInternalID(self, i):
        """\brief Sets the port's internal id
        \param i (\c string) The port's internal id
        """        
        self.__internalID = i

    def getInternalID(self):
        """\brief Gets the port's internal id
        \return (\c string) The port's internal id
        """        
        return self.__internalID

    def __eq__(self, other):
        """\brief Equals comparison for two port objects
        \return (\c boolean) True or False
        """
        if (self.__portNumber == other.__portNumber and self.__tagged == other.__tagged and self.__internalID == other.__internalID ):
            return True
        else:
            return False

    def __cmp__(self,other):
        if (self.__portNumber == other.__portNumber and self.__tagged == other.__tagged and self.__internalID == other.__internalID ):
            return 0
        elif (self.__portNumber < other.__portNumber and self.__tagged == other.__tagged and self.__internalID < other.__internalID ):
            return -1
        elif (self.__portNumber > other.__portNumber and self.__tagged == other.__tagged and self.__internalID > other.__internalID ):
            return 1
        elif (self.__portNumber < other.__portNumber and self.__tagged == other.__tagged  ):
            return -1
        elif (self.__portNumber > other.__portNumber and self.__tagged == other.__tagged  ):
            return 1
        elif (self.__portNumber == other.__portNumber and self.__tagged == False and other.__tagged == True):
            return -1
        else:
            return 1
    
    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        string = "Port:"+\
                 " portNumber=" + str(self.getPortNumber()) + \
                 " tagged=" + str(self.getTagged()) + \
                 " internalID=" + str(self.getInternalID()) + "\n"        

        return string

    
class MACTableEntry:
    """\brief Class used to hold information about a mac address entry in a switch
    """

    def __init__(self, mac, port, learned, switch = None):
        """\brief Initializes the class
        \param id (\c string) The interal OID of the SNMP result
        \param value (\c string) The value corresponding to the OID of the SNMP result 
        """
        self.__mac = mac
        self.__port = port
        self.__learned = learned
        self.__switch = switch
        self.__device = None

    def getDevice(self):
        """\brief Gets the device associated with the mac
        \return (\c string) The device id
        """  
        return self.__device

    def setDevice(self,d):
        """\brief Sets the device associated with the mac address
        \param n (\c string) The device id
        """
        self.__device = d

    def setMAC(self, m):
        """\brief Sets the mac address
        \param n (\c string) The mac address
        """
        self.__mac = m

    def getMAC(self):
        """\brief Gets the mac address
        \return (\c string) The mac address
        """
        return self.__mac

    def setPort(self, p):
        """\brief Sets the entry's port
        \param n (\c string) The entry's port
        """
        self.__port = p

    def getPort(self):
        """\brief Gets the entry's port
        \return (\c string) The entry's port
        """
        return self.__port

    def setLearned(self, l):
        """\brief To be completed...
        \param n (\c string) To be completed...
        """
        self.__learned = l

    def getLearned(self):
        """\brief To be completed...
        \return (\c string) To be completed...
        """
        return self.__learned
    
    def setSwitch(self, s):
        """\brief Sets the switch
        \param n (\c string) The switch
        """
        self.__switch = s

    def getSwitch(self):
        """\brief Gets the switch
        \return (\c string) The switch
        """
        return self.__switch
    
    def hasSamePort(self, other):
        """\brief Compares the port on this object to that of the given object
        \param (\c MacTableEntry) The object to compare to
        \return True if the given object's port is the same as this port, false otherwise
        """
        return ((self.__port == other.getPort()) and (self.__switch == other.getSwitch()))

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        return "MACTableEntry:" + \
               " mac="+str(self.getMAC()) + \
               " port="+str(self.getPort()) + \
               " learned="+str(self.getLearned()) + \
               " switch="+str(self.getSwitch()) + "\n"


class LDAPInfo:
    """\brief Class used to hold information returned from an LDAP server
    """

    def __init__(self, baseDN=None, uid=None, uidNumber=None, gidNumber=None, cn=None, firstName=None, lastName=None, loginShell=None, homeDir=None, groups=None, email=None):
        """\brief Initializes the class
        \param baseDN (\c string) The base distinguished name
        \param uid (\c string) The user's id (login)
        \param uidNumber (\c int) The user's id number
        \param gidNumber (\c int) The user's group id number
        \param cn (\c string) The user's full name
        \param firstName (\c string) The user's first name
        \param lastName (\c string) The user's last name
        \param loginShell (\c string) The path to the user's login shell
        \param homeDir (\c string) The path to the user's home directory
        \param groups (\c List of strings) A list of the groups that the user belongs to
        \param email (\c string) The user's email address
        """
        self.__baseDN = baseDN
        self.__uid = uid
        self.__uidNumber = uidNumber
        self.__gidNumber = gidNumber
        self.__cn = cn
        self.__firstName = firstName
        self.__lastName = lastName
        self.__loginShell = loginShell
        self.__homeDir = homeDir
        self.__groups = groups
        self.__email = email

    def getBaseDN(self):
        """\brief Gets the base distinguished name
        \return (\c string) The base distinguished name
        """
        return self.__baseDN

    def setBaseDN(self, baseDN):
        """\brief Sets the base distinguished name
        \param baseDN (\c string) The base distinguished name
        """
        self.__baseDN = baseDN

    def getUID(self):
        """\brief Gets the user's id
        \return (\c string) The user's id
        """
        return self.__uid

    def setUID(self, uid):
        """\brief Sets the user's id
        \param uid (\c string) The user's id
        """
        self.__uid = uid

    def getGID(self):
        """\brief Gets the user's group id
        \return (\c string) The user's group id
        """
        return self.__gid

    def setGID(self, gid):
        """\brief Sets the user's group id
        \param gid (\c string) The user's group id
        """
        self.__gid = gid

    def getUIDNumber(self):
        """\brief Gets the user's id number
        \return (\c int) The user's id number
        """
        return self.__uidNumber

    def setUIDNumber(self, uidNumber):
        """\brief Sets the user's id number
        \param uidNumber (\c int) The user's id number
        """
        self.__uidNumber = uidNumber

    def getGIDNumber(self):
        """\brief Gets the user's group id number
        \return (\c int) The user's group id number
        """
        return self.__gidNumber

    def setGIDNumber(self, gidNumber):
        """\brief Sets the user's group id number
        \param gidNumber (\c int) The user's group id number
        """
        self.__gidNumber = gidNumber

    def getCN(self):
        """\brief Gets the user's full name
        \return (\c string) The user's full name
        """
        return self.__cn

    def setCN(self, cn):
        """\brief Sets the user's full name
        \param cn (\c string) The user's full name
        """
        self.__cn = cn

    def getFirstName(self):
        """\brief Gets the user's first name
        \return (\c string) The user's first name
        """
        return self.__firstName

    def setFirstName(self, firstName):
        """\brief Sets the user's first name
        \param firstName (\c string) The user's first name
        """
        self.__firstName = firstName

    def getLastName(self):
        """\brief Gets the user's last name
        \return (\c string) The user's last name
        """
        return self.__lastName

    def setLastName(self, lastName):
        """\brief Sets the user's last name
        \param lastName (\c string) The user's last name
        """
        self.__lastName = lastName        

    def getLoginShell(self):
        """\brief Gets the user's path to the login shell
        \return (\c string) The user's path to the login shell
        """
        return self.__loginShell

    def setLoginShell(self, loginShell):
        """\brief Sets the user's path to the login shell
        \param loginShell (\c string) The user's path to the login shell
        """
        self.__loginShell = loginShell

    def getHomeDir(self):
        """\brief Gets the user's path to the home directory
        \return (\c string) The user's path to the home directory
        """
        return self.__homeDir

    def setHomeDir(self, homeDir):
        """\brief Sets the user's path to the home directory
        \param homeDir (\c string) The user's path to the home directory
        """
        self.__homeDir = homeDir        

    def getGroups(self):
        """\brief Gets the user's groups
        \return (\c List of string) The user's groups
        """
        return self.__groups

    def setGroups(self, groups):
        """\brief Sets the user's groups
        \param groups (\c List of string) The user's groups
        """
        self.__groups = groups

    def getEmail(self):
        """\brief Gets the user's email
        \return (\c string) The user's email
        """
        return self.__email

    def setEmail(self, email):
        """\brief Sets the user's email
        \param email (\c string) The user's email
        """
        self.__email = email       

    def getMD5Object(self):
        """\brief Returns an MD5 object containing all the fields of the
                  LDAPInfo object
        \return (\c md5) An MD5 object containing all the fields of the LDAPInfo object
        """
        #message = md5.new()
        mssage = hashlib.md5()
        message.update(self.__str__())
        return message
        
    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        return "LDAPInfo:" + \
               " baseDN=" + str(self.getBaseDN()) + \
               " uid=" + str(self.getUID()) + \
               " uidNumber=" + str(self.getUIDNumber()) + \
               " gidNumber=" + str(self.getGIDNumber()) + \
               " cn=" + str(self.getCN()) + \
               " firstName=" + str(self.getFirstName()) + \
               " lastName=" + str(self.getLastName()) + \
               " loginShell=" + str(self.getLoginShell()) + \
               " homeDir=" + str(self.getHomeDir()) + \
               " groups=" + str(self.getGroups()) + \
               " email=" + str(self.getEmail()) + "\n"    


class LogEntry:
    """\brief Class used to hold information about a testbed log entry
    """

    def __init__(self, date=None, time=None, authorLoginID=None, affectedElementsIDs=None, description=None):
        """\brief Initializes the class
        \param date (\c string) The date of the log entry in the format DD/MM/YYYY
        \param time (\c string) The time of the log entry in the format HH:MM (24 hour clock), GMT
        \param authorLoginID (\c string) The login ID of the person generating the log entry, as found on the LDAP server
        \param affectedElementsIDs (\c list of strings) The ids of all the testbed elements that the log entry affects
        \param description (\c string) The log entry's description
        """
        self.__date = date
        self.__time = time
        self.__authorLoginID = authorLoginID
        self.__affectedElementsIDs = affectedElementsIDs
        self.__description = description

    def getDate(self):
        """\brief Gets the log entry's date
        \return (\c string) The log entry's date in the format DD/MM/YYYY
        """
        return self.__date

    def setDate(self, date):
        """\brief Sets the log entry's date
        \param date (\c string) The date in the format DD/MM/YYYY
        """
        self.__date = date

    def getTime(self):
        """\brief Gets the log entry's time
        \return (\c string) The log entry's time in the format HH:MM (24 hour clock), GMT
        """
        return self.__time

    def setTime(self, time):
        """\brief Sets the log entry's time
        \param time (\c string) The time in the format HH:MM (24 hour clock), GMT
        """
        self.__time = time

    def getAuthorLoginID(self):
        """\brief Gets the login id of the author of the log entry
        \return (\c string) The login id of the author of the log entry
        """
        return self.__authorLoginID

    def setAuthorLoginID(self, authorLoginID):
        """\brief Sets the login id of the author of the log entry
        \param authorLoginID (\c string) The login id of the author of the log entry
        """
        self.__authorLoginID = authorLoginID
        
    def getAffectedElementsIDs(self):
        """\brief Gets the ids of the elements that the log entry affects
        \return (\c list of strings) The ids of the elements that the log entry affects
        """
        return self.__affectedElementsIDs

    def setAffectedElementsIDs(self, affectedElementsIDs):
        """\brief Sets the ids of the elements that the log entry affects
        \param affectedElementsIDs (\c list of strings) The ids of the elements that the log entry affects
        """
        self.__affectedElementsIDs = affectedElementsIDs

    def getDescription(self):
        """\brief Gets the log entry's description
        \return (\c string) The log entry's description
        """
        return self.__description

    def setDescription(self, description):
        """\brief Sets the log entry's description
        \param description (\c string) The description
        """
        self.__description = description

    def __str__(self):
        """\brief Returns a string of the object, useful for debugging
        \return (\c string) A string of the object
        """
        return "LogEntry:" + \
               " date=" + str(self.getDate()) + \
               " time=" + str(self.getTime()) + \
               " authorLoginID=" + str(self.getAuthorLoginID()) + \
               " affectedElementsIDs=" + str(self.getAffectedElementsIDs()) + \
               " description=" + str(self.getDescription()) + "\n"




###########################################################################################
#   Functions
###########################################################################################
def reverseIPAddress(ip):
    """\brief Reverses an IP address (12.13.14.15 becomes 15.14.13.12)
    \param ip (\c string) A string representing the IP address to be reversed in dot notation
    \return (\c string) A string with the reversed IP address
    """
    if (ip == None):
        return None
    
    ip += "."
    i = len(ip)

    result = ""
    while (i > 0):
        indexOfRightDot = ip.rfind(".", 0, i)
        indexOfLeftDot = ip.rfind(".", 0, indexOfRightDot)
        result += ip[indexOfLeftDot + 1:indexOfRightDot] + "."
        i = i - (indexOfRightDot - indexOfLeftDot)
        
    return result[:len(result) - 1]

def getTime():
    """\brief Gets the current time in the format %d-%b-%Y-%H-%M (see man strftime for details)
    \return (\c string) A string representing the current time.
    """
    return str(strftime("%d-%b-%Y-%H-%M", gmtime()))

def getUserName():
    """ \brief Returns the user name of the proccess calling the program
    \return (\c string) A string containing the current username.
    """
    try:
        return str(os.environ['USER'])
    except:
        return str("web")

def datesOverlap(beginDateRange1, endDateRange1, beginDateRange2, endDateRange2):
    """\brief Returns True if the given date ranges overlap, False otherwise.
              The format for all of the parameters is DD/MM/YYYY
    \param beginDateRange1 (\c string) The begin date for the first range of dates
    \param endDateRange1 (\c string) The end date for the first range of dates
    \param beginDateRange2 (\c string) The begin date for the second range of dates
    \param endDateRange2 (\c string) The end date for the second range of dates
    \return (\c Boolean) True if the two date ranges overlap, false otherwise
    """
    if ( (isDateAfter(beginDateRange1, endDateRange2)) or (isDateAfter(beginDateRange2, endDateRange1)) ):
        return False
    else:
        return True

def isDateAfter(firstDate, secondDate):
    """\brief Returns True if firstDate is after secondDate, False otherwise. The
              dates should be in the format DD/MM/YYYY
    \param firstDate (\c string) The first date
    \param secondDate (\c string) The second date
    \return (\c Boolean) True if firstDate is after secondDate, False otherwise
    """
    if (firstDate == secondDate):
        return False

    firstDateDay = int(firstDate[:2])
    firstDateMonth = int(firstDate[3:5])
    firstDateYear = int(firstDate[6:10])

    secondDateDay = int(secondDate[:2])
    secondDateMonth = int(secondDate[3:5])
    secondDateYear = int(secondDate[6:10])

    if ( (firstDateYear < secondDateYear) or (firstDateMonth < secondDateMonth) or (firstDateDay < secondDateDay) ):
        return False
    else:
        return True

def isValueInDictionaryOfLists(value, dictionary):
    """\brief Returns True if the given value is in the dictionary of lists, False otherwise
    \param value (\c string) The string to search for in the dictionary of lists
    \param dictionary (\c dictionary of lists) The dictionary of lists to search in
    \return (\c Boolean) True if the value is found, False otherwise
    """
    for oneList in dictionary.values():
        if (value in oneList):
            return True

    return False

def isVLANInList(vlanName, vlanList):
    """\brief Searches a list of VLAN objects for a particular vlan
    \param vlanName (\c string) The name of the vlan to search for
    \param vlanList (\c list of VLAN objects) The list to search in
    \return (\c int) -1 if the vlan is not found, or its index in the list if found
    """
    if (vlanList == None):
        return -1

    index = 0
    for vlan in vlanList:
        if (vlan.getName() == vlanName):
            return index
        index += 1

    return -1

def isHigherIPAddress(address1, address2):
    """\brief Returns True if the first parameter is a higher IP address than the
              second one, False otherwise
    \param address1 (\c string) A string representing an IP address
    \param address2 (\c string) A string representing an IP address
    \return (\c Boolean) True if address1 if higher than address 2, False otherwise
    """
    if (address1 == address2):
        return False

    for i in range(0, 4):
        if (int(getPartialIPNumber(address1, i)) > int(getPartialIPNumber(address2, i))):
            return True

    return False

def getPartialIPNumber(ipAddress, sectionNumber):
    """\brief Returns a subsection of an ip address. A subsection is a part of the ip address
              bounded by dots. If sectionNumber is not between 0 and 3, None is returned
    \param ipAddress (\c string) The ip address to obtain the subsection from
    \param sectionNumber (\c int) The subsection number (0-3)
    \return (\c string) The subsection of the ip
    """
    if (sectionNumber < 0 or sectionNumber > 3):
        return None
    
    if (sectionNumber == 0):
        return ipAddress[:ipAddress.find(".")]

    firstDotIndex = 0
    for i in range(0, sectionNumber):
        firstDotIndex = ipAddress.find(".", firstDotIndex + 1)

    if (sectionNumber == 3):
        lastDotIndex = len(ipAddress) 
    else:
        lastDotIndex = ipAddress.find(".", firstDotIndex + 1)

    return ipAddress[firstDotIndex + 1:lastDotIndex]
    
def incrementIPAddress(ipAddress):
    """\brief Returns a string representing the incremented parameter's IP address. If
              the parameter is 255.255.255.255, this same value is returned
    \param ipAddress (\c string) The ip address to increment
    \return (\c string) The incremented ip address
    """
    lastPossibleSectionNumber = 255
    firstPossibleSectionNumber = 0
    
    firstSection = int(getPartialIPNumber(ipAddress, 0))
    secondSection = int(getPartialIPNumber(ipAddress, 1))
    thirdSection = int(getPartialIPNumber(ipAddress, 2))
    fourthSection = int(getPartialIPNumber(ipAddress, 3))
    
    if (fourthSection != lastPossibleSectionNumber):
        return str(firstSection) + "." + str(secondSection) + "." + \
               str(thirdSection) + "." + str(fourthSection + 1)
    elif (thirdSection != lastPossibleSectionNumber):
        return str(firstSection) + "." + str(secondSection) + "." + \
               str(thirdSection + 1) + "." + str(firstPossibleSectionNumber)
    elif (secondSection != lastPossibleSectionNumber):
        return str(firstSection) + "." + str(secondSection + 1) + "." + \
               str(firstPossibleSectionNumber) + "." + str(firstPossibleSectionNumber)        
    elif (firstSection != lastPossibleSectionNumber):
        return str(firstSection + 1) + "." + str(firstPossibleSectionNumber) + "." + \
               str(firstPossibleSectionNumber) + "." + str(firstPossibleSectionNumber)

    return "255.255.255.255"

def convertHexCharacterToInt(char):
    """\brief Converts a string containing a single hexadecimal character to an integer value
    \param char (\c string) The string containing the hex character
    \return (\c int) The integer value of the hex character
    """
    return int("0x" + char, 0)

def convertIntToHexCharacter(integer):
    """\brief Converts an integer betwen 0 and 15 to a string containing a hex
              character whose value is equivalent to the given integer.
    \param integer (\c int) The integer to convert
    \return (\c string) The converted integer
    """
    if (integer < 0 or integer > 15):
        return "-1"

    return str(hex(i))[2:].upper()
    
def findFirstNumberInString(string):
    """\brief Returns the index of the first number in the given string
    \param string (\c string) The string to search the number in
    \return (\c int) The index of the first number, or -1 if the string contains no numbers
    """
    for i in range(len(string)) :
        if string[i].isdigit() :
            return i
    return -1

def fileExists(filename):
    """\brief Returns whether a file exists or not
    \param filename (\c string) The full path of the file
    \return (\c boolean) True if the file exists, false otherwise
    """
    return os.path.exists(filename)

def generateMD5Signature(filePath):
    """\brief Generates the MD5 signature for the given file
    \param filePath (\c string) The full path of the file
    \return (\c int or string) The MD5 signature or -1 if the file does not exist
    """
    try :
        f = open(filePath)
    except IOError :
        return -1

    data = ""
    for line in f:
        data += line
    #return md5.new(data).hexdigest()
    return hashlib.md5(data).hexdigest()
