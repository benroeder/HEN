#################################################################################################################
# henParser.py: the main library file for parsing xml files (the hen database)
#
# FUNCTIONS (of HenParser)
# -----------------------------------------------------------------------------------------------
# __init__                  initializes parser variables and parses the physical nodes on the testbed
#
# getTestbedElementsTypes   returns a list with all the different types of elements supported by the testbed
# getNodeElementTypes       returns a list with the different types of nodes supported by the testbed
# getInfrastructureElementTypes  returns a list with the different types of infrastructures supported by the testbed
# getFileNodeElementTypes   returns a list with the different types of file nodes supported by the testbed
# getNodeStatuses           returns a list with the possible statuses that a node can have
# getInfrastructureStatuses returns a list with the possible statuses that an infrastructure can have
# getTestbedFileStatuses    returns a list with the possible statuses that a testbed file can have
# getSystemNodesDictionary  returns a dictionary containing the system nodes
# setCurrentExperimentsFile sets the current experiments file
# getCurrentExperimentsFile gets the current experiments file
# getNodeIDs                returns a list of node ids
# getSystemNodesDictionary  returns a dictionary with information about testbed nodes
# getSystemInfrastructuresDictionary  returns a dictionary with information about testbed infrastructure
# getSystemExperimentsDictionary      returns a dictionary with information about testbed experiments
# getSystemFileNodesDictionary        returns a dictionary with information about testbed file nodes
# getPhysicalFile           returns the path to the main physical topology file
# getExperimentEntries      returns a dictionary with information about experiment entries in the main experiment topology file
# getNodes                  returns a dictionary of all nodes in the testbed or of nodes of a certain type
# getInfrastructures        returns a dictionary of all infrastructure in the testbed or of infrastructure of a type
# getExperiments            returns a dictionary of all experiments in the testbed
# getFileNodes              returns a dictionary of all file nodes in the testbed or of file nodes of a certain type
# getLogEntries             returns testbed log entries
# getLogEntriesByElement    returns testbed log entries that affect a given testbed element
#
# GENERIC XML HANDLERS
# -----------------------------------
# __parseTopologyFileInit   opens an xml file, returning the parsed xml
# __getLabel                given an xml object and a key, returns the value matching that key (a string)
# __openXMLFile             opens an XML file
# __parseInterfaces         parses interface tags (used by both physical and experiment)
#
# PHYSICAL TOPOLOGY PARSE FUNCTIONS
# ------------------------------------
# __parsePhysicalEntries       parses the physical topology file
# __parsePhysicalTopologies               parses all elements of the system, including nodes and infrastructure
# __parseInfrastructures      parses all infrastructure in the system
# __parseInfrastructure       parses an object of type Infrastructure
# __parseInfrastructureRack   parses an object of type InfrastructureRack
# __parseInfrastructureFloorBox parses an object of type InfrastructureFloorBox
# __parseNodes                parses all nodes in the system
# __parseNode                 parses an object of type Node
# __parseServerNode           parses an object of type ServerNode
# __parseComputerNode         parses an object of type ComputerNode
# __parseMoteNode             parses an object of type MoteNode
# __parseSwitchNode           parses an object of type SwitchNode
# __parsePowerSwitchNode      parses an object of type PowerSwitchNode
# __parseSerialNode           parses an object of type SerialNode
# __parseRouterNode           parses an object of type RouterNode
# __parseServiceProcessorNode parses an object of type ServiceProcessorNode
# __parseSensorNode           parses an object of type SensorNode
# __parseKVMNode              parses an object of type KVM
# __parseNodeIDs              creates a list of node ids ("switch1", "serial1", ...)
# __parseAttributes           parses attribute tags
# __parsePeripherals          parses peripheral tags
# __parsePhysicalLocation     parses physicallocation tags
# __parsePhysicalSize         parses physicalsize tags
# __parseUserManagement       parses user management tags
# __parsePowerPlug            parses powerplug tags (used by floor boxes)
# __parseRJ45Port             parses rj45port tags (used by floor boxes)
#
# PHYSICAL TOPOLOGY WRITE FUNCTIONS
# ----------------------------------
# writeNodePhysicalFile       writes an initial physical file for a node
# writeInfrastructurePhysicalFile writes an initial physical file for an infrastructure
# writePhysicalEntry          writes a new entry into the main physical topology fie
# deletePhysicalEntry         deletes an entry from the main physical topology file
# changePhysicalEntryStatus   changes the status of an entry of the main physical topology file
# __writePhysicalEntries      writes all given entries into the main physical topology file
#
# EXPERIMENT TOPOLOGY PARSE FUNCTIONS 
# ---------------------------------------
# parseUserExperiment       parses an experimental topology file
# __parseExperimentEntries  parses the main experiment topology file
# __parseExperimentTopologies parses all experiments
# __parseExperimentGroups   parses experimentgroup tags
# __parseNetbootInfo        parses netbootinfo tags
# __parseCurrentExperiments parses the file with current experiments
#
# EXPERIMENT TOPOLOGY WRITE FUNCTIONS 
# ---------------------------------------
# writeExperimentNodes              writes a given list of ExperimentNode objects to the current experiments xml file
# writeExperimentNode               writes a single entry of type ExperimentNode to the current experiments xml file
# writeExperimentToCurrent          writes a given experiment topology to the file containing all experiments on the testbed
# deleteExperimentFromCurrent       deletes a given experiment topology from the file containing all experiment on the testbed
# writeExperimentEntry              writes a new entry into the main experiment topology file
# deleteExperimentEntry             deletes an entry from the main experiment topology file
# changeExperimenEntryStatus        changes the status of an entry of the main experiment topology file
# __writeExperimentEntries          writes all the given entries into the main experiments topology file
# changeExperimenTopologyFileEntryStatus changes the status of an entry of the main experiment topology file
#
# TESTBED FILE TOPOLOGY PARSE FUNCTIONS 
# ---------------------------------------
# parseTestbedFileEntries         parses the entries in the main testbed file topology files
# __parseTestbedFileTopologies      parses the actual testbed file objects pointed to by the entries in the topology file
# __parseFileNodes                  parses all filenode objects in the topology file
# __parseFileNode                   parses the super class tags of a file node topology file (see auxiliary.hen.FileNode)
# __parseKernelFileNode             parses a kernel object
# __parseFilesystemFileNode         parses a filesystem object
# __parseLoaderFileNode             parses a loader object
# __parseMd5Signature               parses md5signature tags
# __parseDescription                parses description tags
# 
# TESTBED FILE TOPOLOGY WRITE FUNCTIONS 
# ---------------------------------------
# writeFileNodeTestbedFile          writes an xml description file for a filenode object
# writeTestbedFileEntry             writes a new entry into the main testbed files topology file
# deleteTestbedFileEntry            deletes an entry from the main testbed files topology file
# changeTestbedFileEntryStatus      changes the status of an entry of the main testbed files topology file
# __writeTestbedFileEntries         writes all given entries into the main testbed files topology file
#
# LOG ENTRIES PARSE AND WRITE FUNCTIONS
# ------------------------------------
# __parseLogs                       parses all testbed logs
# __parseLog                        parses a single testbed log
# writeLogEntry                     writes a single log entry
#
# PARSER CHECKS FOR PHYSICAL TOPOLOGY
# ------------------------------------
# The parser checks that the peripheral tags have ids of nodes that are actually in the testbed's database
# The parser checks that the MAC addresses are unique throughout the testbed
#
# PARSER CHECKS FOR EXPERIMENT TOPOLOGY
# ------------------------------------
# The parser checks that the requested nodes actually exist in the testbed's database
# The parser checks that the requested interfaces' mac addresses actually belong to the requested nodes
# The parser checks that the requested experiment topology does not conflict with existing experiment topologies
#
# PARSER CHECKS FOR TESTBED FILES TOPOLOGY
# ------------------------------------
# None yet
#
##################################################################################################################
from xml.dom import minidom
from xml.dom.minidom import Element
from xml.dom.minidom import Node
from time import gmtime, strftime
import string, copy, sys, os, time, calendar, commands, fileinput
import auxiliary.hen

from auxiliary.hen import GenericComputerNode, InfrastructureRack, InfrastructureFloorBox, FloorBoxRJ45Port, FloorBoxPowerPlug, SensorNode, ServiceProcessorNode, SwitchNode, RouterNode, PowerSwitchNode, ComputerNode, ServerNode, SerialNode, Node, Peripheral, UserManagement, NetbootInfo, ExperimentNode, UserExperiment, datesOverlap, isValueInDictionaryOfLists, PhysicalLocation, PhysicalSize, PhysicalTopologyEntry, ExperimentTopologyEntry, FilesystemFileNode, KernelFileNode, LoaderFileNode, TestbedFileTopologyEntry, fileExists, LogEntry, MoteNode, VirtualComputerNode, Link, DirectLink, ExternalLink, LinkMember

import logging
logging.basicConfig()
log = logging.getLogger()
#log.setLevel(logging.DEBUG)


ELEMENT_TYPES = ["node", "infrastructure", "link"]
NODE_TYPES = ["server", "computer", "mote", "serial", "powerswitch", "switch", "router", "serviceprocessor", "sensor", "kvm", "virtualcomputer"]
INFRASTRUCTURE_TYPES = ["rack", "floorbox"]
LINK_TYPES = ["direct","external"]
TESTBEDFILE_TYPES = ["filenode"]
FILENODE_TYPES = ["filesystem", "kernel", "loader"]

INTERFACE_TYPES = ["experimental", "management", "infrastructure", "external", "unassigned", "virtual"]

LINK_STATUSES = ["up", "down", "disconnected"]
NODE_STATUSES = ["operational", "maintenance", "retired", "dead"]
INFRASTRUCTURE_STATUSES = ["operational", "maintenance", "retired", "dead"]
TESTBEDFILE_STATUSES = ["operational", "broken", "archived", "deleted"]
EXPERIMENT_STATUSES = ["active", "expired"]

class HenParser:
    """\brief A class to parse all xml files in HEN
    The HenParser class is used to parse all of the xml files in HEN, including those of actual
    physical hardware, testbed files and those describing user experiments. The parsing actually gets done during
    class initialization, and results retrieved through getter methods.
    """
####################################################################################################################
#
#   INIT, GETTERS AND SETTERES
#
####################################################################################################################
    def __init__(self, physicalTopology, experimentTopology, \
                   testbedFileTopology, logPath, etcPhysicalPath, \
                   etcExperimentPath, etcTestbedFilePath, \
                   currentExperimentsFile=None, groupName=None):
      """ \brief Initializes parser variables and parses the physical nodes on the testbed by calling parseSystem
      \param physicalTopology (\c string)  A string representing the path to the main physical topology file
      \param experimentTopology (\c string) A string representing the path to the main experiments topology file
      \param testbedFileTopology (\c string) A string representing the path to the main testbed files topology file      
      \param etcPhysicalPath (\c string) The path to the testbed's etc physical directory
      \param etcExperimentPath (\c string) The path to the testbed's etc experiment directory
      \param etcTestbedFilePath (\c string) The path to the testbed's etc testbed file directory      
      \param log (\c string) The path to the log directory
      \param currentExperimentsFile (\c string) The file containing the experiments currently on the testbed
      \param groupName (\c string) The name of the group for developers of the testbed
      """
      self.__systemInfrastructuresDictionary = {}
      self.__systemNodesDictionary = {}
      self.__systemExperimentsDictionary = {}
      self.__systemFileNodesDictionary = {}
      self.__experimentEntriesDictionary = {}
      self.__linkEntriesDictionary = {}
      self.__logsEntries = {}
      
      self.__physicalConfigFile =  physicalTopology
      self.__experimentConfigFile = experimentTopology
      self.__testbedFileConfigFile = testbedFileTopology
      self.__currentExperimentsFile = currentExperimentsFile
      self.__etcPhysicalPath = etcPhysicalPath
      self.__etcExperimentPath = etcExperimentPath
      self.__etcTestbedFilePath = etcTestbedFilePath
      self.__logPath = logPath
      self.__groupName = groupName
      self.__nodeIDs = self.__parseNodeIDs(self.__physicalConfigFile)
      self.__nodesInterfaces = {}

      # parseInterfaces uses this to see what kind of verification checks it needs to do. If it's False,
      # then it will check that there are no duplicate mac addresses in the testbed's database. If it's
      # True, then it will check that all the mac addresses begin parsed are in the testbed's database.
      # parseUserExperiment takes care of setting and unsetting this variable      
      self.__parsingExperiment = False

      # Parse full testbed database
      self.parseAll()
      
    def parseAll(self):
      # parse physical topology
      if (self.__physicalConfigFile):
          self.__parsePhysicalTopologies(self.__physicalConfigFile)
      
      # parse experiment topology
      if (self.__experimentConfigFile):
          self.__parseExperimentEntries(self.__experimentConfigFile)
          self.__parseExperimentTopologies()

      # parse testbed files topology
      if (self.__testbedFileConfigFile):
          self.__parseTestbedFileTopologies(self.__testbedFileConfigFile)

      # parse testbed logs
      self.__parseLogs()
    
    def getTestbedElementsTypes(self):
        """\brief Gets all the different types of elements supported by the testbed
        \return (\c list of strings) The different types of elements supported by the testbed
        """
        elementTypes = []

        for nodeType in NODE_TYPES:
            elementTypes.append(nodeType)

        for infrastructureType in INFRASTRUCTURE_TYPES:
            elementTypes.append(infrastructureType)

        for fileNodeType in FILENODE_TYPES:
            elementTypes.append(fileNodeType)

        for linkType in LINK_TYPES:
            elementTypes.append(linkType)
            
        return elementTypes

    def getNodeElementTypes(self):
        """\brief Returns all the different types of nodes supported by the testbed
        \return (\c list of string) The types
        """        
        return NODE_TYPES

        
    def getInfrastructureElementTypes(self):
        """\brief Returns all the different types of infrastructures supported by the testbed
        \return (\c list of string) The types
        """        
        return INFRASTRUCTURE_TYPES

    def getFileNodeElementTypes(self):
        """\brief Returns all the different types of nfile odes supported by the testbed
        \return (\c list of string) The types
        """
        return FILENODE_TYPES

    def getLinkElementTypes(self):
        """\brief Returns all the different types of links supported by the testbed
        \return (\c list of string) The types
        """
        return LINK_TYPES
# start from here
    def getNodeStatuses(self):
        """\brief Returns the possible statuses that a node can have
        \return (\c list of string) The possible statuses
        """
        return NODE_STATUSES

    def getInfrastructureStatuses(self):
        """\brief Returns the possible statuses that an infrastructure can have
        \return (\c list of string) The possible statuses
        """        
        return INFRASTRUCTURE_STATUSES

    def getTestbedFileStatuses(self):
        """\brief Returns the possible statuses that a testbed file can have
        \return (\c list of string) The possible statuses
        """        
        return TESTBEDFILE_STATUSES

    def getLinkStatuses(self):
        """\brief Returns the possible statuses that a link can have
        \return (\c list of string) The possible statuses
        """        
        return LINK_STATUSES

    def setCurrentExperimentsFile(self, c):
        """\brief Sets the current experiments file
        \param c (\c string) The current experiments file
        """
        self.__currentExperimentsFile = c
        
    def getCurrentExperimentsFile(self):
        """\brief Returns the current experiments file
        \return (\c string) The current experiments file
        """
        return self.__currentExperimentsFile

    def getNodeIDs(self):
        """\brief Returns a list of node ids previously parsed by parseNodeIDs
        \return (\c List) A list of node ids
        """
        return self.__nodeIDs

    def getSystemNodesDictionary(self):
        """\brief Returns a dictionary containing the parsed node information
        \return (dictionary of dictionaries) The dictionary containing the parsed information
        """
        return self.__systemNodesDictionary

    def getSystemInfrastructuresDictionary(self):
        """\brief Returns a dictionary containing the parsed infrastructure information
        \return (dictionary of dictionaries) The dictionary containing the parsed information
        """        
        return self.__systemInfrastructuresDictionary

    def getSystemExperimentsDictionary(self):
        """\brief Returns a dictionary containing the parsed experiment information
        \return (dictionary of dictionaries) The dictionary containing the parsed information
        """        
        return self.__systemExperimentsDictionary

    def getSystemFileNodesDictionary(self):
        """\brief Returns a dictionary containing the parsed file nodes information
        \return (dictionary of dictionaries) The dictionary containing the parsed information
        """        
        return self.__systemFileNodesDictionary
    
    def getSystemLinksDictionary(self):
        """\brief Returns a dictionary containing the parsed links information
        \return (dictionary of dictionaries) The dictionary containing the parsed information
        """        
        return self.__linkEntriesDictionary    
    
    def getPhysicalFile(self):
        """ \brief Returns the path to the main physical topology file
        \return (\c string) The path to the main physical topology file
        """
        return self.__physicalConfigFile

    def getExperimentEntries(self, status):
        """\brief Returns a dictionary whose keys are the experiment ids of the experiments currently
                  in the testbed and whose values ExperimentTopologyEntry objects
        \param status (\c string) Filter by the status of the experiment. If set to 'all', no filtering is performed
        \return (\c dictionaryof ExperimentTopologyEntry objects) A dictionary with information
                  about experiments currently on the testbed.
        """
        if (status == "all"):
            return self.__experimentEntriesDictionary


        filteredDictionary = {}

        for key in self.__experimentEntriesDictionary.keys():
            experimentTopologyEntry = self.__experimentEntriesDictionary[key]
            if (experimentTopologyEntry.getStatus() == status):
                filteredDictionary[key] = experimentTopologyEntry
                
        return filteredDictionary

    def getExperiments(self, status):
        """\brief Returns a dictionary whose keys are the experiment ids of the experiments currently
                  in the testbed and whose values are UserExperiment objects
        \param status (\c string) Filter by the status of the experiment. If set to 'all', no filtering is performed
        \return (\c dictionaryof UserExperiment objects) A dictionary with information
                  about experiments currently on the testbed.
        """
        if (status == "all"):
            return self.__systemExperimentsDictionary

        filteredDictionary = {}

        for key in self.__experimentEntriesDictionary.keys():
            experimentTopologyEntry = self.__experimentEntriesDictionary[key]
            if (experimentTopologyEntry.getStatus() == status):
                filteredDictionary[key] = self.__systemExperimentsDictionary[key]
                
        return filteredDictionary

    def getNodes(self, key, status):
        """\brief Returns a dictionary of a certain type of node in the testbed, for instance switch or router.
                  If the key given is set to all, this function returns a dictionary of dictionaries (see explanation
                  of function parseNodes). If the key is of an unknown type, None is returned.
        \param key (\c string) The type of node to be retrieve, or all
        \param status (\c string) Filter by the status of the node. If set to 'all', no filtering is performed
       s \return (\c dictionary) A dictionary if a type is specified, or dictionary of dictionaries if all is specified
        """
        if (self.__systemNodesDictionary.has_key(key)):
            specificTypeDictionary = self.__systemNodesDictionary[key]

            # If status is set to 'all', perform no filtering
            if (status == "all"):
                return specificTypeDictionary

            # Perform filtering based on the status given
            filteredDictionary = {}
            for specificNodeKey in specificTypeDictionary.keys():
                if (specificTypeDictionary[specificNodeKey].getStatus() == status):
                    filteredDictionary[specificNodeKey] = specificTypeDictionary[specificNodeKey]

            return filteredDictionary
        
        elif (key == "all"):
            nodesDictionary = self.__systemNodesDictionary

            # If status is set to 'all', perform no filtering
            if (status == "all"):
                return nodesDictionary

            # Perform filtering based on the status given
            filteredDictionary = {}

            for typeKey in nodesDictionary.keys():
                specificTypeDictionary = nodesDictionary[typeKey]
                specificTypeFilteredDictionary = {}
                for nodeKey in specificTypeDictionary.keys():
                    node = specificTypeDictionary[nodeKey]

                    if (node.getStatus() == status):
                        specificTypeFilteredDictionary[nodeKey] = node
                        
                filteredDictionary[typeKey] = specificTypeFilteredDictionary

            return filteredDictionary
                
        else:
            # Expecting {} if no entries exists in topology file for valid node types i.e mote
            return {}
            #return None

    def getInfrastructures(self, key, status):
        """\brief Returns a dictionary of a certain type of infrastructure in the testbed, for instance a rack.
                  If the key given is set to all, this function returns a dictionary of dictionaries (see explanation
                  of function parseInfrastructure). If the key is of an unknown type, None is returned.
        \param key (\c string) The type of node to be retrieve, or all
        \param status (\c string) Filter by the status of the infrastructure. If set to 'all', no filtering is performed        
        \return (\c dictionary) A dictionary if a type is specified, or dictionary of dictionaries if all is specified
        """
        if (self.__systemInfrastructuresDictionary.has_key(key)):
            specificTypeDictionary = self.__systemInfrastructuresDictionary[key]

            # If status is set to 'all', perform no filtering
            if (status == "all"):
                return specificTypeDictionary

            # Perform filtering based on the status given
            filteredDictionary = {}
            for specificInfrastructureKey in specificTypeDictionary.keys():
                if (specificTypeDictionary[specificInfrastructureKey].getStatus() == status):
                    filteredDictionary[specificInfrastructureKey] = specificTypeDictionary[specificInfrastructureKey]

            return filteredDictionary
        
        elif (key == "all"):
            infrastructuresDictionary = self.__systemInfrastructuresDictionary

            # If status is set to 'all', perform no filtering
            if (status == "all"):
                return infrastructuresDictionary

            # Perform filtering based on the status given
            filteredDictionary = {}

            for typeKey in infrastructuresDictionary.keys():
                specificTypeDictionary = infrastructuresDictionary[typeKey]
                specificTypeFilteredDictionary = {}
                for infrastructureKey in specificTypeDictionary.keys():
                    infrastructure = specificTypeDictionary[infrastructureKey]

                    if (infrastructure.getStatus() == status):
                        specificTypeFilteredDictionary[infrastructureKey] = infrastructure
                        
                filteredDictionary[typeKey] = specificTypeFilteredDictionary

            return filteredDictionary
                
        else:
            return None

    def getFileNodes(self, key, status):
        """\brief Returns a dictionary of a certain type of file node in the testbed, for instance a kernel.
        If the key given is set to all, this function returns a dictionary of dictionaries (see explanation
        of function parseFileNodes). If the key is of an unknown type, None is returned.
        \param key (\c string) The type of node to be retrieve, or all
        \param status (\c string) Filter by the status of the file node. If set to 'all', no filtering is performed        
        \return (\c dictionary) A dictionary if a type is specified, or dictionary of dictionaries if all is specified
        """
        if (self.__systemFileNodesDictionary.has_key(key)):
            specificTypeDictionary = self.__systemFileNodesDictionary[key]

            # If status is set to 'all', perform no filtering
            if (status == "all"):
                return specificTypeDictionary

            # Perform filtering based on the status given
            filteredDictionary = {}
            for specificFileNodeKey in specificTypeDictionary.keys():
                if (specificTypeDictionary[specificFileNodeKey].getStatus() == status):
                    filteredDictionary[specificFileNodeKey] = specificTypeDictionary[specificFileNodeKey]

            return filteredDictionary
        
        elif (key == "all"):
            fileNodesDictionary = self.__systemFileNodesDictionary

            # If status is set to 'all', perform no filtering
            if (status == "all"):
                return fileNodesDictionary

            # Perform filtering based on the status given
            filteredDictionary = {}

            for typeKey in fileNodesDictionary.keys():
                specificTypeDictionary = fileNodesDictionary[typeKey]
                specificTypeFilteredDictionary = {}
                for fileNodeKey in specificTypeDictionary.keys():
                    fileNode = specificTypeDictionary[fileNodeKey]

                    if (fileNode.getStatus() == status):
                        specificTypeFilteredDictionary[fileNodeKey] = fileNode
                        
                filteredDictionary[typeKey] = specificTypeFilteredDictionary

            return filteredDictionary
                
        else:
            return None

    def getLinks(self, key, status):
        """\brief Returns a dictionary of a certain type of link in the testbed. If the key given is set to all, this function returns a dictionary of dictionaries (see explanation of function parseLinks). If the key is of an unknown type, None is returned.
        \param key (\c string) The type of link to be retrieve, or all
        \param status (\c string) Filter by the status of the link. If set to 'all', no filtering is performed
        \return (\c dictionary) A dictionary if a type is specified, or dictionary of dictionaries if all is specified
        """
        
        if (self.__linkEntriesDictionary.has_key(key)):
            specificTypeDictionary = self.__linkEntriesDictionary[key]

            # If status is set to 'all', perform no filtering
            if (status == "all"):
                return specificTypeDictionary

            # Perform filtering based on the status given
            filteredDictionary = {}
            for specificNodeKey in specificTypeDictionary.keys():
                if (specificTypeDictionary[specificNodeKey].getStatus() == status):
                    filteredDictionary[specificNodeKey] = specificTypeDictionary[specificNodeKey]

            return filteredDictionary
        
        elif (key == "all"):
            nodesDictionary = self.__linkEntriesDictionary

            # If status is set to 'all', perform no filtering
            if (status == "all"):
                return nodesDictionary

            # Perform filtering based on the status given
            filteredDictionary = {}

            for typeKey in nodesDictionary.keys():
                specificTypeDictionary = nodesDictionary[typeKey]
                specificTypeFilteredDictionary = {}
                for nodeKey in specificTypeDictionary.keys():
                    node = specificTypeDictionary[nodeKey]

                    if (node.getStatus() == status):
                        specificTypeFilteredDictionary[nodeKey] = node
                        
                filteredDictionary[typeKey] = specificTypeFilteredDictionary

            return filteredDictionary
                
        else:
            # Expecting {} if no entries exists in topology file for valid node types i.e mote
            return {}
            #return None
            
    def getLogs(self, filename="all"):
        """\brief Returns either all logs in the testbed or all log entries in a particular log
        \param filename (\c string) If this parameter is given, the log entries of the file are returned. If not,
                                    entries for all the logs in the testbed are returned. The parameter should be
                                    just the file name, without the path
        \return (\c list of LogEntry or dictionary of list of LogEntry) The log information
        """
        if (filename == "all"):
            return self.__logsEntries
        else:
            try:
                return self.__logsEntries[filename]
            except:
                print "filename " + filename + " does not exist on the testbed"
                return -1

    def getLogEntriesByElement(self, elementID):
        """\brief Returns all log entries affecting a given element on the testbed
        \param elementID (\c string) The element to retrieve information for
        \return (\c list of LogEntry) All entries affecting the element given
        """
        entries = []

        for logFile in self.__logsEntries.values():
            for logEntry in logFile:
                if (elementID in logEntry.getAffectedElementsIDs()):
                    entries.append(logEntry)
        return entries


####################################################################################################################
#
#   GENERIC XML HANDLERS
#
####################################################################################################################
    def __parseTopologyFileInit(self, filename, topologyType):
        """\brief Open an XML file and retrieves anything under a topology tag whose type is equal to
                  the given parameter
        \param filename (\c string) The filename containing the xml to parse
        \param topologyType (\c string) The topology type to match against (experiment or physical)
        """
        try:
            xmldoc = self.__openXMLFile(filename)
            if (xmldoc == None):
                #print "cannot parse, physical toplogy file missing"
                return -1
            
            xmlRoot = xmldoc.getElementsByTagName("topology")[0]

            if xmlRoot.attributes.has_key("type"):
                topology_type=xmlRoot.attributes["type"].value
            else:
                pass
                #self.getLogger().debug("\t topology type not set! please set the topology type [physical|experiment]")
	       
            if topology_type != topologyType:
                pass
                #self.getLogger().debug("\t topology set incorrectly to: " + topology_type)
                #self.getLogger().info("\t topology set incorrectly to: " + topology_type)

            return xmldoc
        
        except IOError:
            pass
            #self.getLogger().debug("\t IOError - File: " + self.getPhysicalFile() + " doest NOT EXIST")
            #self.getLogger().info("\t IOError - File: " + self.getPhysicalFile() + " doest NOT EXIST")

    def __getLabel(self, key, xmlObject):
        """\brief Given an xml object and a key, returns the value matching that key
                  (a string) or None if nothing matches the key.
        \param key (\c string) The key to search for
        \param xmlObject (\c minidom.Node) The xml object to search for the key in
        \return (\c string) The value found or None if no value was found for the given key
        """
	if xmlObject.attributes.has_key(key):
	    return xmlObject.attributes[key].value
	else:
	    return None	   
	   
    def __openXMLFile(self, fileName):
       """ \brief Attempt to open an XML file. If the operation is successful this will
                  return a minidom object of the file descriptor.
       \param fileName (\c string) The path representing the filename to open
       \return (\c see xml.dom.minidom) A minidom object representing the file
       """
       try:
          xmldoc = minidom.parse(fileName)   
	  return xmldoc 
     
       except IOError:
           #self.getLogger().debug("\t IOError - File: " + fileName + " doest NOT EXIST")
           #self.getLogger().info("\t IOError - File: " + fileName + " doest NOT EXIST")
           return None
       except Exception, e:
           print "problem with xml file "+str(fileName)
           # should raise an error here
           return None

    def __parseInterfaces(self, interfacesXML, interfaceType, nodeID):
        """\brief Parses interface tags using interfaceType as a filter. The function
                  returns a list of Interface objects or None if the given interfacesXML
                  object contained no elements. Only the following attributes of the
                  interface tagged are parsed: type, mac, ip, subnet, switch, port, vlan,
                  model, speed. The accepted types of interfaces are experimental, management
                  (the management interfaces on experimental nodes), infrastructure
                  (the management interfaces on infrastructure nodes), external (the interfaces
                  connected to the external Internet) and unassigned for all others. If a mac
                  address appears in the testbed's database more than once, and error message is
                  printed
        \param interfacesXML (\c minidom.Node) The xml object representing the file to search interface tags in
        \param interfacesType (\c string) The function will only return interfaces of this type (either management, experimental or infrastructure)
        \param nodeID (\c string) The id of the node whose interfaces are being parsed
        \return (\c list) A list of objects of type Interface, representing the parsed interface information
        """                
        if (len(interfacesXML) == 0):
            return None
        
	interfaces = []
	for interfaceXML in interfacesXML:
            ifaceType = self.__getLabel("type", interfaceXML)
            if (ifaceType == interfaceType):
                mac = self.__getLabel("mac", interfaceXML)     
                ip = self.__getLabel("ip", interfaceXML)     
                subnet = self.__getLabel("subnet", interfaceXML)     
                switch = self.__getLabel("switch", interfaceXML)     
                port = self.__getLabel("port", interfaceXML)
                vlan = self.__getLabel("vlan", interfaceXML)
                model = self.__getLabel("model", interfaceXML)
                speed = self.__getLabel("speed", interfaceXML)
                interfaceID = self.__getLabel("id", interfaceXML)

                if (self.__parsingExperiment):
                    if ( not(self.__nodesInterfaces.has_key(nodeID)) or (mac.upper() not in self.__nodesInterfaces[nodeID]) ):
                        print "the requested mac address " + mac.upper() + " does not belong to node " + nodeID
                else:
                    if (not(isValueInDictionaryOfLists(mac.upper(), self.__nodesInterfaces))):
                        if (not(self.__nodesInterfaces.has_key(nodeID))):
                            self.__nodesInterfaces[nodeID] = []
                        self.__nodesInterfaces[nodeID].append(mac.upper())
                    #else:
                    #    print "mac address " + mac.upper() + " of node " + nodeID + " already belongs to another node"

                # Add the interface to the list
                interface = auxiliary.hen.Interface(mac, ip, subnet, switch, port, vlan, ifaceType, speed, model, None, interfaceID)
                interfaces.append(interface)

	return interfaces
    
####################################################################################################################
#
#   PHYSICAL TOPOLOGY PARSE FUNCTIONS
#
####################################################################################################################
    def __parseNodeIDs(self, filename):
        """ \brief Returns a list of node ids used to perform checks with (for instance, a computer node is not allowed to specify a non-existing serial node).
        \param filename (\c string) A string representing the path to the main physical topology file
        \return (\c List) A list of node ids, or none if the file given did not contain any nodes
        """
        henXML = None
        nodeIDs = {}
        systemXML = self.__openXMLFile(filename)

        if (systemXML == None):
            #print "cannot parse node ids, no physical topology file exists"
            return -1
        
        henXML = systemXML.getElementsByTagName("node")
        if(henXML):
            for node in henXML:
                filename = self.__getLabel("file", node)
                # print filename
                xmlFile = self.__openXMLFile(filename)
                xmlNodes = xmlFile.getElementsByTagName("node")
                for node in xmlNodes:
                    # We use a dictionary since retrieving elements from it is easier than going through a whole list
                    # (the key's what's important, we don't care about the value, set it to dummy)
                    nodeIDs[self.__getLabel("id", node)] = "dummy"
            return nodeIDs
        
        return None

    def __parsePhysicalTopologies(self, filename):
        """ \brief Parses all elements of the system by calling parseNodes and parseInfrastructure, catching any xml errors and exiting if any occur
        \param filename (\c string) A string representing the path to the main physical topology file
        """
        xmldoc = self.__parseTopologyFileInit(filename, "physical")
        self.__parseNodes(xmldoc)
        self.__parseInfrastructures(xmldoc)
        self.__parseLinks(xmldoc)
        
    def __parseNodes(self, xmldoc):
        """ \brief Parses all nodes in the system, storing the results in self.__systemNodesDictionary.
                   This data structure is a dictionary of dictionaries. The keys of the top-most dictionary
                   are the different types of nodes, for instance switch, serial, computer, etc. The values
                   of the top-most dictionary are dictionaries themselves. The keys to each of these are the
                   actual ids of the nodes of one type, for instace switch1, switch2, etc. The values are the
                   actual objects of type SwitchNode, SerialNode, ComputerNode, etc. If a node does not have
                   a tag named type or if the type is not one of the known ones (see if/elifs below), the node
                   is ignored and an entry added to the log.
        \param xmldoc (\c minidom.Node) The xml object representing the main topology file
        """
        filename = None
        theNode = None

        if (xmldoc == None or xmldoc == -1):
            #print "cannot parse nodes, null element passed"
            return -1

        nodeXML = xmldoc.getElementsByTagName("node")
        if(nodeXML):
            for node in nodeXML:
                filename = self.__getLabel("file",node)
                status = self.__getLabel("status",node)
                xmlFile = self.__openXMLFile(filename)
                xmlNodes = xmlFile.getElementsByTagName("node")
                count = 0;
                for node in xmlNodes:
                    # check that the 'type' is set, otherwise raise an error and skip to the next iteration of the loop
                    # <node type="computer" ...>
                    nodeType = self.__getLabel("type", node)
                    if (nodeType == None):
                        count += 1
                        #self.getLogger().debug("\t node: " + str(count) + " \"type\" not set correctly")
                        continue
                    else:
                        if (nodeType == "server"):
                            theNode = self.__parseServerNode(node)
                        elif (nodeType == "computer"):
                            theNode = self.__parseComputerNode(node)
                        elif (nodeType == "mote"):
                            theNode = self.__parseMoteNode(node)
                        elif(nodeType == "switch"):
                            theNode = self.__parseSwitchNode(node)
                        elif(nodeType == "powerswitch"):
                            theNode = self.__parsePowerSwitchNode(node)
                        elif(nodeType == "serial"):
                            theNode = self.__parseSerialNode(node)
                        elif(nodeType == "router"):
                            theNode = self.__parseRouterNode(node)
                        elif(nodeType == "serviceprocessor"):
                            theNode = self.__parseServiceProcessorNode(node)
                        elif(nodeType == "sensor"):
                            theNode = self.__parseSensorNode(node)
                        elif(nodeType == "virtualcomputer"):
                            theNode = self.__parseVirtualComputerNode(node)    
                        else:
                            #print "unknown type " + nodeType
                            #self.getLogger().debug("\t node: " + str(count) + " has unknown type: " + nodeType)
                            continue

                        # XXX LIES!
                        ## status attribute is handled different for mtoes due to its more volatile nature
                        #if nodeType != "mote":
                        #    # Set the (already parsed) node's status
                        #    theNode.setStatus(status)

                        theNode.setStatus(status)

                        # create and populate the actual dictionary to store in 
                        if (self.getSystemNodesDictionary().has_key(nodeType)):
                            nodes = self.getSystemNodesDictionary()[nodeType]
                            nodes[theNode.getNodeID()] = theNode
                            self.getSystemNodesDictionary()[nodeType] = nodes
                        else:
                            nodes = {}
                            nodes[theNode.getNodeID()] = theNode
                            self.getSystemNodesDictionary()[nodeType] = nodes

    def __parseLinks(self, xmldoc):
        """ \brief Parses all links in the system, storing the results in self.__systemLinksDictionary. This data structure is a dictionary of dictionaries. The keys of the top-most dictionary are the different types of links. The values of the top-most dictionary are dictionaries themselves. The keys to each of these are the actual ids of the links of one type, for instace link1, link2, etc.
        \param xmldoc (\c minidom.Node) The xml object representing the main topology file
        """
        filename = None
        theLink = None

        if (xmldoc == None or xmldoc == -1):
            #print "cannot parse links, null element passed"
            return -1

        linkXML = xmldoc.getElementsByTagName("link")
        if(linkXML):
            for link in linkXML:
                filename = self.__getLabel("file",link)
                status = self.__getLabel("status",link)
                xmlFile = self.__openXMLFile(filename)
                xmlLinks = xmlFile.getElementsByTagName("link")
                count = 0;
                for link in xmlLinks:
                    # check that the 'type' is set, otherwise raise an error and skip to the next iteration of the loop
                    # <link type="computer" ...>
                    linkType = self.__getLabel("type", link)
                    if (linkType == None):
                        count += 1
                        #self.getLogger().debug("\t link: " + str(count) + " \"type\" not set correctly")
                        continue
                    else:
                        if (linkType == "direct"):
                            theLink = self.__parseDirectLink(link)
                        elif (linkType == "external"):
                            theLink = self.__parseExternalLink(link)
                        else:
                            print "unknown type " + linkType
                            self.getLogger().debug("\t link: " + str(count) + " has unknown type: " + linkType)
                            continue


                        # create and populate the actual dictionary to store in 
                        if (self.getSystemLinksDictionary().has_key(linkType)):
                            links = self.getSystemLinksDictionary()[linkType]
                            links[theLink.getLinkId()] = theLink
                            self.getSystemLinksDictionary()[linkType] = links
                        else:
                            links = {}
                            links[theLink.getLinkId()] = theLink
                            self.getSystemLinksDictionary()[linkType] = links

    def __parseInfrastructures(self, xmldoc):
        """ \brief Parses all infrastructure the system, storing the results in self.__systemInfrastructuresDictionary.
                   This data structure is a dictionary of dictionaries. The keys of the top-most dictionary
                   are the different types of infrastructure, for instance rack, patch panels, etc. The values
                   of the top-most dictionary are dictionaries themselves. The keys to each of these are the
                   actual ids of the nodes of one type, for instace rack1, patchpanel1, etc. The values are the
                   actual objects of type InfrastructureRack, etc. If a node does not have
                   a tag named type or if the type is not one of the known ones (see if/elifs below), the node
                   is ignored and an entry added to the log.
        \param xmldoc (\c minidom.Node) The xml object representing the main topology file
        """
        filename = None
        theNode = None

        if (xmldoc == None or xmldoc == -1):
            #print "cannot parse infrastructure, null element passed"
            return -1

        infrastructureXML = xmldoc.getElementsByTagName("infrastructure")
        if(infrastructureXML):
            for infrastructure in infrastructureXML:
		filename = self.__getLabel("file",infrastructure)
                status = self.__getLabel("status",infrastructure)
		xmlFile = self.__openXMLFile(filename)
                xmlInfrastructures = xmlFile.getElementsByTagName("infrastructure")
                count = 0;
                for infrastructure in xmlInfrastructures:
                    # check that the 'type' is set, otherwise raise an error and skip to the next iteration of the loop
                    # <infrastructure type="rack" ...>
                    infrastructureType = self.__getLabel("type", infrastructure)
                    if (infrastructureType == None):
                        count += 1
                        #self.getLogger().debug("\t infrastructure: " + str(count) + " \"type\" not set correctly")
                        continue
                    else:
                        if (infrastructureType == "rack"):
                            theInfrastructure = self.__parseInfrastructureRack(infrastructure)
                        elif (infrastructureType == "floorbox"):
                            theInfrastructure = self.__parseInfrastructureFloorBox(infrastructure)
                        else:
                            #print "unknown type " + infrastructureType
                            #self.getLogger().debug("\t infrastructure: " + str(count) + " has unknown type: " + infrastructureType)
                            continue

                        # Set the (already parsed) infrastructure's status
                        theInfrastructure.setStatus(status)
                        
                        # create and populate the actual dictionary to store in 
                        if (self.getSystemInfrastructuresDictionary().has_key(infrastructureType)):
                            infrastructures = self.getSystemInfrastructuresDictionary()[infrastructureType]
                            infrastructures[theInfrastructure.getID()] = theInfrastructure
                            self.getSystemInfrastructuresDictionary()[infrastructureType] = infrastructures
                        else:
                            infrastructures = {}
                            infrastructures[theInfrastructure.getID()] = theInfrastructure
                            self.getSystemInfrastructuresDictionary()[infrastructureType] = infrastructures

    def __parseInfrastructure(self, xmldoc, infrastructure):
        """\brief Given an xml entry representing a physical piece of infrastructure, this
                  function parses all of tags that are to be stored in the Infrastructure superclass.
        \param xmldoc (\c minidom.Node) The xml object representing the file for the infrastructure
        \param node (\c subclass of hen.Node) The Node subclass object to store the results into
        \return (\c subclass of hen.Node) The Node subclass object with the parsed results stored in it 
        """
        infrastructureType = self.__getLabel("type", xmldoc)		   
        if (infrastructureType == None):
            pass
            #self.getLogger().info("no type for infrastructure " + str(xmldoc))
             
        infrastructureID = self.__getLabel("id", xmldoc)		   
        if (infrastructureID == None):
            pass
            #self.getLogger().info("no id for infrastructure " + str(xmldoc))

        vendor = self.__getLabel("vendor", xmldoc)
        if (vendor == None):
            pass
            #self.getLogger().info("no vendor for infrastructure " + str(xmldoc))
        model = self.__getLabel("model", xmldoc)
        if (model == None):
            pass
            #self.getLogger().info("no model for infrastructure " + str(xmldoc))

        description = self.__getLabel("description", xmldoc)
        if (description == None):
            pass
            #self.getLogger().info("no description for infrastructure " + str(xmldoc))

        building = self.__getLabel("building", xmldoc)
        if (building == None):
            pass
            #self.getLogger().info("no building for infrastructure " + str(xmldoc))

        floor = self.__getLabel("floor", xmldoc)
        if (floor == None):
            pass
            #self.getLogger().info("no floor for infrastructure " + str(xmldoc))

        room = self.__getLabel("room", xmldoc)
        if (room == None):
            pass
            #self.getLogger().info("no room for infrastructure " + str(xmldoc))

        infrastructure.setType(infrastructureType)
        infrastructure.setID(infrastructureID)
        infrastructure.setVendor(vendor)
        infrastructure.setModel(model)
        infrastructure.setDescription(description)
        infrastructure.setBuilding(building)
        infrastructure.setFloor(floor)
        infrastructure.setRoom(room)

        # Parse and set attributes
        infrastructure.setAttributes(self.__parseAttributes(xmldoc))

        return infrastructure
    
    def __parseInfrastructureRack(self, xmldoc):
        """\brief Parses an object of type InfrastructureRack. 
        \param xmldoc (\c minidom.Node) The xml object representing the rack's file
        \return (\c InfrastructureRack) An InfrastructureRack object containg the parsed information
        """        
        infrastructureRack = InfrastructureRack()
        infrastructureRack.setType("rack")
        infrastructureRack = self.__parseInfrastructure(xmldoc, infrastructureRack)
        infrastructureRack.setPhysicalSize(self.__parsePhysicalSize(xmldoc))
        
        return infrastructureRack

    def __parseInfrastructureFloorBox(self, xmldoc):
        """\brief Parses an object of type InfrastructureFloorBox. 
        \param xmldoc (\c minidom.Node) The xml object representing the floor box's file
        \return (\c InfrastructureFloorBox) An InfrastructureFloorBox object containg the parsed information
        """        
        infrastructureFloorBox = InfrastructureFloorBox()
        infrastructureFloorBox.setType("floorbox")
        infrastructureFloorBox = self.__parseInfrastructure(xmldoc, infrastructureFloorBox)
        infrastructureFloorBox.setPowerPlugs(self.__parsePowerPlugs(xmldoc))
        infrastructureFloorBox.setRJ45Ports(self.__parseRJ45Ports(xmldoc))
        
        return infrastructureFloorBox    

    def __parsePowerPlugs(self, xmldoc):
        """\brief Parses powerplug tags, returning a list of FloorBoxPowerPlug objects.
                  Each powerplug tag is only allowed the following attributes: label, enabled, maxcurrent
                  If the given xml object does not have any powerplug tags, None is returned.
        \param xmldoc (\c minidom.Node) The xml object representing the file to search powerplug tags in
        \return (\c list of FloorBoxPowerPlug objects) The parsed information
        """                
        powerPlugXML = xmldoc.getElementsByTagName("powerplug")

        powerPlugs = []
        if ( (powerPlugXML != None) and (len(powerPlugXML) != 0) ):
            for powerPlug in powerPlugXML:
                label = self.__getLabel("label", powerPlug)
                enabled = self.__getLabel("enabled", powerPlug)
                if (enabled == "yes"):
                    enabled = True
                else:
                    enabled = False
                maxCurrent = int(self.__getLabel("maxcurrent", powerPlug))

                powerPlugs.append(FloorBoxPowerPlug(label, maxCurrent, enabled))
                
            return powerPlugs
        return None

    def __parseRJ45Ports(self, xmldoc):
        """\brief Parses rj45port tags, returning a list of FloorBoxRJ45Port objects.
                  Each rj45port tag is only allowed the following attributes: label, enabled, maxcurrent
                  If the given xml object does not have any rj45port tags, None is returned.
        \param xmldoc (\c minidom.Node) The xml object representing the file to search rj45port tags in
        \return (\c list of FloorBoxRJ45Port objects) The parsed information
        """                
        rj45PortXML = xmldoc.getElementsByTagName("rj45port")

        rj45Ports = []
        if ( (rj45PortXML != None) and (len(rj45PortXML) != 0) ):
            for rj45Port in rj45PortXML:
                portType = self.__getLabel("type", rj45Port)
                label = self.__getLabel("label", rj45Port)
                description = self.__getLabel("description", rj45Port)
                rj45Ports.append(FloorBoxRJ45Port(portType, label, description))
                
            return rj45Ports
        return None

    def __parseNode(self, xmldoc, node):
        """\brief Given an xml entry representing a physical piece of hardware, this
                  function parses all of tags that are to be stored in the Node superclass;
                  these include any subtags of the node tag as well as the attribute tags.
                  The following subtags are currently supported: type, id, netbootable,
                  infrastructure, vendor, model, physicallocation.
        \param xmldoc (\c minidom.Node) The xml object representing the file for the node
        \param node (\c subclass of hen.Node) The Node subclass object to store the results into
        \return (\c subclass of hen.Node) The Node subclass object with the parsed results stored in it 
        """
        nodeType = self.__getLabel("type", xmldoc)		   
        if (nodeType == None):
            pass
            #self.getLogger().info("no type for node " + str(xmldoc))
             
        nodeID = self.__getLabel("id", xmldoc)
        if (nodeID == None):
            pass
            #self.getLogger().info("no id for node " + str(xmldoc))

        netbootable = self.__getLabel("netbootable", xmldoc)
        if (netbootable == None):
            pass
            #self.getLogger().info("no netbootable for node " + str(xmldoc))

        infrastructure = self.__getLabel("infrastructure", xmldoc)
        if (infrastructure == None):
            pass
            #self.getLogger().info("no infrastructure for node " + str(xmldoc))

        dhcp = self.__getLabel("dhcp", xmldoc)
        if (dhcp == None):
            pass
            #self.getLogger().info("no infrastructure for node " + str(xmldoc))            

        vendor = self.__getLabel("vendor", xmldoc)
        if (vendor == None):
            pass
            #self.getLogger().info("no vendor for node " + str(xmldoc))
        model = self.__getLabel("model", xmldoc)
        if (model == None):
            pass
            #self.getLogger().info("no model for node " + str(xmldoc))

        priority = self.__getLabel("priority", xmldoc)
        if (priority == None):
            pass


        node.setNodeType(nodeType)
        node.setNodeID(nodeID)
        node.setNetbootable(netbootable)
        node.setInfrastructure(infrastructure)
        node.setDHCP(dhcp)
        node.setVendor(vendor)
        node.setModel(model)
        node.setPriority(priority)
        #node.setPhysicalLocation(physicalLocation)

        # Parse and set node's physical location
        node.setPhysicalLocation(self.__parsePhysicalLocation(xmldoc))
        
        # Parse and set attributes
        node.setAttributes(self.__parseAttributes(xmldoc))

        # Parse and set interfaces
        interfaces = {}
        interfacesXML = xmldoc.getElementsByTagName("interface")

        if (interfacesXML != None):
            for interfaceType in INTERFACE_TYPES:
                listInterfaces = self.__parseInterfaces(interfacesXML, interfaceType, nodeID)
                interfaces[interfaceType] = listInterfaces
                if (listInterfaces == None or (len(listInterfaces) == 0)):
                    #self.getLogger().info("node " + node.getNodeID() + " has no interfaces of type " + interfaceType)
                    pass
                
        node.setInterfaces(interfaces, "all")
        return node

    def __parseServerNode(self, xmldoc):
        """\brief Parses an object of type ServerNode, including peripherals, attributes
                  (parsed indirectly though the super class) and interfaces. This parser will
                  ignore peripherals that are not of type serial; the management
                  interface will be parsed by the super class parser and the experimental interfaces
                  by this one. Although all attributes will be parsed, only the following will be
                  stored as members of the subclass: cputype, cpuspeed, numbercpus, memory and
                  motherboard.
        \param xmldoc (\c minidom.Node) The xml object representing the server node's file
        \return (\c ServerNode) A ServerNode object containg the parsed information
        """
        serverNode = ServerNode()
        serverNode.setNodeType("server")
        serverNode = self.__parseNode(xmldoc, serverNode)

        # parse peripherals
        peripherals = self.__parsePeripherals(xmldoc, serverNode.getNodeID())
        powerNodes = []
        if (peripherals != None):
            for peripheral in peripherals:

                serverNode.addPeripheral(peripheral)

                if (peripheral.getPeripheralType() == "powerswitch"):
                    powerNodes.append((peripheral.getPeripheralID(), peripheral.getPeripheralRemotePort()))
                elif (peripheral.getPeripheralType() == "serial"):
                    serverNode.setSerialNodeID(peripheral.getPeripheralID())
                    serverNode.setSerialNodePort(peripheral.getPeripheralRemotePort())
                elif (peripheral.getPeripheralType() == "serviceprocessor"):
                    serverNode.setSPNodeID(peripheral.getPeripheralID())                    
                elif (peripheral.getPeripheralType() == "kvm"):
                    serverNode.setKVMNodeID(peripheral.getPeripheralID())

        serverNode.setPowerNodes(powerNodes)
        return serverNode
    
    def __parseComputerNode(self, xmldoc):
        """\brief Parses an object of type ComputerNode, including peripherals, attributes
                  (parsed indirectly though the super class) and interfaces. This parser will
                  ignore peripherals that are not of type powerswitch or serial; the management
                  interface will be parsed by the super class parser and the experimental interfaces
                  by this one. Although all attributes will be parsed, only the following will be
                  stored as members of the subclass: cputype, cpuspeed, numbercpus, memory and
                  motherboard.
        \param xmldoc (\c minidom.Node) The xml object representing the computer node's file
        \return (\c ComputerNode) A ComputerNode object containg the parsed information
        """
        computerNode = ComputerNode()
        computerNode.setNodeType("computer")
        computerNode = self.__parseNode(xmldoc, computerNode)
        
        # parse peripherals
        peripherals = self.__parsePeripherals(xmldoc, computerNode.getNodeID())
        powerNodes = []
        if (peripherals != None):
            for peripheral in peripherals:

                computerNode.addPeripheral(peripheral)

                if (peripheral.getPeripheralType() == "powerswitch"):
                    powerNodes.append((peripheral.getPeripheralID(), peripheral.getPeripheralRemotePort()))
                elif (peripheral.getPeripheralType() == "serial"):
                    computerNode.setSerialNodeID(peripheral.getPeripheralID())
                    computerNode.setSerialNodePort(peripheral.getPeripheralRemotePort())
                elif (peripheral.getPeripheralType() == "serviceprocessor"):
                    computerNode.setSPNodeID(peripheral.getPeripheralID())
                elif (peripheral.getPeripheralType() == "kvm"):
                    computerNode.setKVMNodeID(peripheral.getPeripheralID())

        computerNode.setPowerNodes(powerNodes)
        return computerNode

    def __parseVirtualComputerNode(self, xmldoc):
        """\brief Parses an object of type VirtualComputerNode, including peripherals, attributes
                  (parsed indirectly though the super class) and interfaces. This parser will
                  ignore peripherals that are not of type powerswitch or serial; the management
                  interface will be parsed by the super class parser and the experimental interfaces
                  by this one. Although all attributes will be parsed, only the following will be
                  stored as members of the subclass: cputype, cpuspeed, numbercpus, memory and
                  motherboard.
        \param xmldoc (\c minidom.Node) The xml object representing the computer node's file
        \return (\c VirtualComputerNode) A VirtualComputerNode object containg the parsed information
        """
        virtualComputerNode = VirtualComputerNode()
        virtualComputerNode.setNodeType("virtualcomputer")
        virtualComputerNode = self.__parseNode(xmldoc, virtualComputerNode)
        # not much here yet
        return virtualComputerNode
        
    def __parseMoteNode(self, xmldoc):
        """\brief Parses an object of type MoteNode, including peripherals, attributes
                  (parsed indirectly though the super class) and interfaces. This parser will
                  ignore peripherals that are not of type powerswitch or serial; the management
                  interface will be parsed by the super class parser and the experimental interfaces
                  by this one. Although all attributes will be parsed, only the following will be
                  stored as members of the subclass: cputype, cpuspeed, numbercpus, memory, flash and
                  storage.
        \param xmldoc (\c minidom.Node) The xml object representing the mote node's file
        \return (\c MoteNode) A MoteNode object containg the parsed information
        """
        moteNode = MoteNode()
        moteNode.setNodeType("mote")
        moteNode = self.__parseNode(xmldoc, moteNode)
        return moteNode

    # Returns object of type SwitchNode
    def __parseSwitchNode(self, xmldoc):
        """\brief Parses an object of type SwitchNode, including peripherals. This
                  parser will ignore peripherals that are not of type powerswitch or serial.
        \param xmldoc (\c minidom.Node) The xml object representing the switch node's file
        \return (\c SwitchNode) A SwitchNode object containg the parsed information
        """        
        switchNode = SwitchNode()
        switchNode.setNodeType("switch")
        switchNode = self.__parseNode(xmldoc, switchNode)

        peripherals = self.__parsePeripherals(xmldoc, switchNode.getNodeID())
        powerNodes = []        
        if (peripherals != None):
            for peripheral in peripherals:
                if (peripheral.getPeripheralType() == "powerswitch"):
                    powerNodes.append((peripheral.getPeripheralID(), peripheral.getPeripheralRemotePort()))
                elif (peripheral.getPeripheralType() == "serial"):
                    switchNode.setSerialNodeID(peripheral.getPeripheralID())
                    switchNode.setSerialNodePort(peripheral.getPeripheralRemotePort())
                elif (peripheral.getPeripheralType() == "switch"):
                    switchNode.addSwitchPeripheral(peripheral)
                    
        switchNode.setPowerNodes(powerNodes)                            
        return switchNode
    
    def __parsePowerSwitchNode(self, xmldoc):
        """\brief Parses an object of type PowerSwitchNode, including peripherals,
                  attributes and usermanagement tags. This parser will ignore peripherals
                  that are not of type serial. Although all attributes will be parsed,
                  only the following will be stored as members of the subclass: numports.
        \param xmldoc (\c minidom.Node) The xml object representing the power switch node's file
        \return (\c PowerSwitchNode) A PowerSwitchNode object containg the parsed information
        """                
        powerSwitchNode = PowerSwitchNode()        
        powerSwitchNode.setNodeType("powerswitch")
        powerSwitchNode = self.__parseNode(xmldoc, powerSwitchNode)
            
        peripherals = self.__parsePeripherals(xmldoc, powerSwitchNode.getNodeID())
        powerNodes = []
        if (peripherals != None):
            for peripheral in peripherals:
                if (peripheral.getPeripheralType() == "serial"):
                    powerSwitchNode.setSerialNodeID(peripheral.getPeripheralID())
                    powerSwitchNode.setSerialNodePort(peripheral.getPeripheralRemotePort())

        # the attributes were parsed by the super node parser, just retrieve them
        if (powerSwitchNode.getAttributes() != None):
            for attribute in powerSwitchNode.getAttributes().keys():
                if (attribute == "numports"):
                    powerSwitchNode.setNumberPorts(powerSwitchNode.getAttributes()[attribute])
        
        powerSwitchNode.setUsers(self.__parseUserManagement(xmldoc))

        return powerSwitchNode

    def __parseSerialNode(self, xmldoc):
        """\brief Parses an object of type SerialNode, including peripherals, attributes
                  and usermanagement tags. This parser will ignore peripherals that are not
                  of type powerswitch. Although all attributes will be parsed, only the following
                  will be stored as members of the subclass: numports.
        \param xmldoc (\c minidom.Node) The xml object representing the serial node's file
        \return (\c SerialNode) A SerialNode object containg the parsed information
        """                        
        serialNode = SerialNode()
        serialNode.setNodeType("serial")
        serialNode = self.__parseNode(xmldoc, serialNode)

        peripherals = self.__parsePeripherals(xmldoc, serialNode.getNodeID())
        powerNodes = []
        if (peripherals != None):
            for peripheral in peripherals:
                if (peripheral.getPeripheralType() == "powerswitch"):
                    powerNodes.append((peripheral.getPeripheralID(), peripheral.getPeripheralRemotePort()))
                elif (peripheral.getPeripheralType() == "serial"):
                    serialNode.setSerialNodeID(peripheral.getPeripheralID())
                    serialNode.setSerialNodePort(peripheral.getPeripheralRemotePort())
        # the attributes were parsed by the super node parser, just retrieve them
        if (serialNode.getAttributes() != None):
            for attribute in serialNode.getAttributes().keys():
                if (attribute == "numports"):
                    serialNode.setNumberPorts(serialNode.getAttributes()[attribute])

        serialNode.setUsers(self.__parseUserManagement(xmldoc))

        serialNode.setPowerNodes(powerNodes)        
        return serialNode

    def __parseRouterNode(self, xmldoc):
        """\brief Parses an object of type RouterNode, including peripherals, attributes
                  (parsed indirectly though the super class), interfaces and usermanagement tags.
                  This parser will ignore peripherals that are not of type powerswitch or serial;
                  the management interface will be parsed by the super class parser and the
                  experimental interfaces by this one. Although all attributes will be parsed, only
                  the following will be stored as members of the subclass: operatingsystemtype,
                  operatingsystemversion.
        \param xmldoc (\c minidom.Node) The xml object representing the router node's file
        \return (\c RouterNode) A RouterNode object containg the parsed information
        """        
        routerNode = RouterNode()
        routerNode.setNodeType("router")
        routerNode = self.__parseNode(xmldoc, routerNode)

        peripherals = self.__parsePeripherals(xmldoc, routerNode.getNodeID())

        # parse peripherals
        powerNodes = []        
        if (peripherals != None):
            for peripheral in peripherals:
                if (peripheral.getPeripheralType() == "powerswitch"):
                    powerNodes.append((peripheral.getPeripheralID(), peripheral.getPeripheralRemotePort()))
                elif (peripheral.getPeripheralType() == "serial"):
                    routerNode.setSerialNodeID(peripheral.getPeripheralID())
                    routerNode.setSerialNodePort(peripheral.getPeripheralRemotePort())

        routerNode.setPowerNodes(powerNodes)        
        return routerNode

    def __parseServiceProcessorNode(self, xmldoc):
        """\brief Parses an object of type ServiceProcessorNode, including peripherals
                  and usermanagement tags. This parser will ignore peripherals that are
                  not of type powerswitch.
        \param xmldoc (\c minidom.Node) The xml object representing the service processor node's file
        \return (\c ServiceProcessorNode) A ServiceProcessorNode object containg the parsed information
        """                                
        serviceProcessorNode = ServiceProcessorNode()
        serviceProcessorNode.setNodeType("serviceprocessor")
        serviceProcessorNode = self.__parseNode(xmldoc, serviceProcessorNode)

        peripherals = self.__parsePeripherals(xmldoc, serviceProcessorNode.getNodeID())

        # parse peripherals
        powerNodes = []        
        if (peripherals != None):
            for peripheral in peripherals:
                if (peripheral.getPeripheralType() == "powerswitch"):
                    powerNodes.append((peripheral.getPeripheralID(), peripheral.getPeripheralRemotePort()))

        # parse user management tags
        serviceProcessorNode.setUsers(self.__parseUserManagement(xmldoc))
        serviceProcessorNode.setPowerNodes(powerNodes)        

        return serviceProcessorNode

    def __parseSensorNode(self, xmldoc):
        """\brief Parses an object of type SensorNode
        \param xmldoc (\c minidom.Node) The xml object representing the sensor node's file
        \return (\c SensorNode) A SensorNode object containg the parsed information
        """                                
        sensorNode = SensorNode()
        sensorNode.setNodeType("sensor")
        sensorNode = self.__parseNode(xmldoc, sensorNode)
        return sensorNode

    def __parseKVMNode(self, xmldoc):
        """\brief Parses an object of type KVMNode
        \param xmldoc (\c minidom.Node) The xml object representing the sensor node's file
        \return (\c KVMNode) A KVMNode object containg the parsed information
        """                                
        kvmNode = KVMNode()
        kvmNode.setNodeType("kvm")
        kvmNode = self.__parseNode(xmldoc, kvmNode)
        return kvmNode
    
    def __parsePhysicalLocation(self, xmldoc):
        """\brief Parses physicallocation tags, returning a PhysicalLocation objects.
                  Each physicallocation tag is only allowed the following attributes: building,
                  floor, room, rackrow, rackname, rackunit. If the given xml object does not have any physicallocation
                  tags, None is returned.
        \param xmldoc (\c minidom.Node) The xml object representing the file to search physicallocation tags in
        \return (\c PhysicalLocation) A Physicallocation object representing the parsed physicallocation information
        """                
        physicalLocationXML = xmldoc.getElementsByTagName("physicallocation")

        if ( (physicalLocationXML != None) and (len(physicalLocationXML) != 0) ):
            physicalLocation = physicalLocationXML[0]
            building = self.__getLabel("building", physicalLocation)
            floor = self.__getLabel("floor", physicalLocation)
            room = self.__getLabel("room", physicalLocation)
            rackRow = self.__getLabel("rackrow", physicalLocation)
            rackName = self.__getLabel("rackname", physicalLocation)
            rackStartUnit = self.__getLabel("rackstartunit", physicalLocation)
            rackEndUnit = self.__getLabel("rackendunit", physicalLocation)
            description = self.__getLabel("description", physicalLocation)
            nodePosition = self.__getLabel("position", physicalLocation)
            return PhysicalLocation(building, floor, room, rackRow, rackName, rackStartUnit, rackEndUnit, description, nodePosition)

        return None

    def __parsePhysicalSize(self, xmldoc):
        """\brief Parses physicalsize tags, returning a PhysicalSize object.
                  Each physicalsize tag is only allowed the following attributes: height, width, depth, numberunits.
                  If the given xml object does not have any physicalsize tags, None is returned.
        \param xmldoc (\c minidom.Node) The xml object representing the file to search physicalsize tags in
        \return (\c PhysicalSize) A PhysicalSize object representing the parsed physicalsize information
        """                
        physicalSizeXML = xmldoc.getElementsByTagName("physicalsize")

        if ( (physicalSizeXML != None) and (len(physicalSizeXML) != 0) ):
            physicalSize = physicalSizeXML[0]
            height = self.__getLabel("height", physicalSize)
            width = self.__getLabel("width", physicalSize)
            depth = self.__getLabel("depth", physicalSize)
            numberUnits = self.__getLabel("numberunits", physicalSize)
            return PhysicalSize(height, width, depth, numberUnits)

        return None    

    def __parseAttributes(self, xmldoc):
        """\brief Parses attribute tags, returning a dictionary in which the name
                  of the attribute is the key and the value of the attribute is the
                  value in the dictionary. If the given xml object does not have any
                  attribute tags, None is returned.
        \param xmldoc (\c minidom.Node) The xml object representing the file to search attribute tags in
        \return (\c dictionary) A dictionary object containing the parsed attribute information
        """
        attributes = None
        attributesXML = xmldoc.getElementsByTagName("attribute")
        if ( (attributesXML != None) and (len(attributesXML) != 0) ):
            attributes = {}
            for attribute in attributesXML:
                attributeName = self.__getLabel("name", attribute)
                attributeValue = self.__getLabel("value", attribute)

                attributes[attributeName] = attributeValue
        return attributes

    def __parsePeripherals(self, xmldoc, nodeID):
        """\brief Parses peripheral tags, returning a list of Peripheral objects. Each
                  peripheral tag is only allowed the following attributes: id, type, port.
                  If the given xml object does not have any peripheral tags, None is returned.
        \param xmldoc (\c minidom.Node) The xml object representing the file to search peripheral tags in
        \param nodeID (\c string) The id of the node whose peripherals are being parsed
        \return (\c list) A list of objects of type Peripheral, representing the parsed peripheral information
        """        
        peripherals = None
        peripheralsXML = xmldoc.getElementsByTagName("peripheral")
        if ( (peripheralsXML != None) and (len(peripheralsXML) != 0) ):
            peripherals = []
            for peripheral in peripheralsXML:
                peripheralID = self.__getLabel("id", peripheral)

                if (peripheralID not in self.getNodeIDs()):
                    pass
                    #print "invalid peripheral " + peripheralID + " for node: " + nodeID
                peripheralType = self.__getLabel("type", peripheral)
                peripheralPort = self.__getLabel("port", peripheral)
                peripheralRemotePort = self.__getLabel("remoteport", peripheral)
                peripheralLocalPort = self.__getLabel("localport", peripheral)                
                peripheralDescription = self.__getLabel("description", peripheral)
                
                peripheral = Peripheral(peripheralID, peripheralType, peripheralRemotePort, peripheralLocalPort, peripheralDescription)
                peripherals.append(peripheral)
        return peripherals        

    def __parseUserManagement(self, xmldoc):
        """\brief Parses usermanagement tags, returning a list of UserManagement objects.
                  Each usermanagement tag is only allowed the following attributes: username,
                  password, email. If the given xml object does not have any usermanagement
                  tags, None is returned.
        \param xmldoc (\c minidom.Node) The xml object representing the file to search usermanagement tags in
        \return (\c list) A list of objects of type UserManagement, representing the parsed usermanagement information
        """                
        users = []
        userManagementXML = xmldoc.getElementsByTagName("usermanagement")
        """
        if ( (userManagementXML != None) and (len(userManagementXML) != 0) ):
            user = userManagementXML[0]
            username = self.__getLabel("username", user)
            password = self.__getLabel("password", user)
            email = self.__getLabel("email", user)
            description = self.__getLabel("description", user)
            users.append(UserManagement(username, password, email, description))
        """
        for user in userManagementXML:
            username = self.__getLabel("username", user)
            password = self.__getLabel("password", user)
            email = self.__getLabel("email", user)
            description = self.__getLabel("description", user)
            users.append(UserManagement(username, password, email, description))

        return users

    def __parsePhysicalEntries(self):
        """\brief Parses the main physical topology file, returning a dictionary whose keys are the
                  paths and filenames of the node files and whose values are the nodes' types
        \return (\c list of PhysicalTopologyEntry objects) A list with the parsed information
        """
        topologyEntries = []
        xmldoc = self.__parseTopologyFileInit(self.__physicalConfigFile, "physical")

        if (xmldoc == None or xmldoc == -1):
            #print "cannot parse physical topology, file missing"
            return -1

        for elementType in ELEMENT_TYPES:            
            xml = xmldoc.getElementsByTagName(elementType)
            if(xml):
                for element in xml:
                    filename = self.__getLabel("file", element)
                    nodeType = self.__getLabel("type", element)
                    status = self.__getLabel("status", element)
                    topologyEntries.append(PhysicalTopologyEntry(elementType, nodeType, filename, status))

        return topologyEntries

    def __parseLinkMembership(self,xmldoc,link):

        linkMembersXML = xmldoc.getElementsByTagName("member")
        linkMembers = []
        if ( (linkMembersXML != None) and (len(linkMembersXML) != 0)):
            for linkMember in linkMembersXML:
                deviceId = self.__getLabel("id",linkMember)
                devicePort = self.__getLabel("interface",linkMember)

                linkMembers.append(LinkMember(deviceId,devicePort))
            return linkMembers
        return None
            

    def __parseLink(self,xmldoc, link):

        linkType = self.__getLabel("type", xmldoc)
        if (linkType == None):
            pass

        linkId = self.__getLabel("id",xmldoc)
        if (linkId == None):
            pass

        link.setLinkType(linkType)
        link.setLinkId(linkId)
        link.setLinkMembers(self.__parseLinkMembership(xmldoc,link))

        return link
    
    def __parseDirectLink(self,xmldoc):
        directLink = DirectLink()
        directLink.setLinkType("direct")
        directLink = self.__parseLink(xmldoc, directLink)

        return directLink

    def __parseExternalLink(self,xmldoc):
        externalLink = ExternalLink()
        externalLink.setLinkType("external")
        externalLink = self.__parseLink(xmldoc, externalLink)

        return externalLink
    
####################################################################################################################
#
#   PHYSICAL TOPOLOGY WRITE FUNCTIONS
#
####################################################################################################################
    def writeInfrastructurePhysicalFile(self, infrastructure):
        """\brief Writes the initial physical file for an infrastructure item
        \param infrastrucutre (\c Infrastructure) An object sub-classed from Infrastructure with the necessary information
        \return (\c int) 0 if successful, -1 otherwise
        """
        filename = self.__etcPhysicalPath + "/" + infrastructure.getID() + ".xml"

        # Write infrastructure tag
        string = '<infrastructure ' + \
                 'type="' + str(infrastructure.getType()) + \
                 '" id="' + str(infrastructure.getID()) + \
                 '" vendor="' + str(infrastructure.getVendor()) + \
                 '" model="' + str(infrastructure.getModel()) + \
                 '" description="' + str(infrastructure.getDescription()) + \
                 '" building="' + str(infrastructure.getBuilding()) + \
                 '" floor="' + str(infrastructure.getFloor()) + \
                 '" room="' + str(infrastructure.getRoom()) + \
                 '">\n\n'

        # Write physical size tag, if any
        if (infrastructure.getPhysicalSize() != None):
            string += '\t<physicalsize ' + \
                      'height="' + str(infrastructure.getPhysicalSize().getHeight()) + \
                      '" width="' + str(infrastructure.getPhysicalSize().getWidth()) + \
                      '" depth="' + str(infrastructure.getPhysicalSize().getDepth()) + \
                      '" numberunits="' + str(infrastructure.getPhysicalSize().getNumberUnits()) + \
                      '" />\n\n'
                  
        # Write attributes, if any
        attributes = infrastructure.getAttributes()
        if (attributes != None and len(attributes) != 0):
            for attribute in attributes.keys():
                string += '\t<attribute name="' + str(attribute) + '" value="' + str(attributes[attribute]) + '" />\n'
            string += '\n'

        # Write powerplug tags (only available for floorbox type), if any
        if (infrastructure.getType() == "floorbox"):
            for powerplug in infrastructure.getPowerPlugs():
                portEnabled = "no"
                if (powerplug.isPortEnabled()):
                    portEnabled = "yes"
                string += '\t<powerplug' + \
                          ' label="' + str(powerplug.getPositionLabel()) + '"' + \
                          ' enabled="' + str(portEnabled) + '"' + \
                          ' maxcurrent="' + str(powerplug.getMaxCurrent()) + '"' + \
                          ' />\n'
            string += '\n'

        # Write rj45port tags (only available for floorbox type), if any
        if (infrastructure.getType() == "floorbox"):
            for rj45port in infrastructure.getRJ45Ports():
                string += '\t<rj45port' + \
                          ' type="' + str(rj45port.getPortType()) + '"' + \
                          ' label="' + str(rj45port.getPositionLabel()) + '"' + \
                          ' description="' + str(rj45port.getDescription()) + '"' + \
                          ' />\n'
            string += '\n'
            
        # Write closing tag
        string += '\n</infrastructure>\n'

        try:
            theFile = open(filename, "w")
            theFile.write(string)
            theFile.close()
            os.system("chgrp " + self.__groupName + " " + filename)
            os.system("chmod 775 " + filename)
            
            # Add infrastructure to in-memory dictionary of infrastructures
            self.getSystemInfrastructuresDictionary()[infrastructure.getType()][infrastructure.getID()] = infrastructure

            return 0
        except:
            print "1 error while writing to " + filename
            return -1
        pass
    
    def writeNodePhysicalFileString(self, node, debug=False):
        """\brief Writes the initial physical file for a node
        \param node (\c Node) An object sub-classed from Node with the necessary information
        \return (\c int) 0 if successful, -1 otherwise
        """
        if debug:
            log.debug("Debugging enabled for writeNodePhysicalFile")
        filename = self.__etcPhysicalPath + "/" + node.getNodeID() + ".xml"

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
        string += '" >\n\n'

        # write all peripherals
        peripherals = node.getPeripherals().values()
        for p in peripherals :
            
            string += '\t<peripheral type="' + str(p.getPeripheralType()) + '" id="' + str(p.getPeripheralID()) + \
                    '" remoteport="' + str(p.getPeripheralRemotePort()) + '" localport="' + str(p.getPeripheralLocalPort()) + \
                    '" description="' + str(p.getPeripheralDescription()) + '" />\n'
                        
        # Write interfaces
        interfaceIDNumber = 0

        for interfaceType in INTERFACE_TYPES:
            interfaces = node.getInterfaces(interfaceType)
            if ((interfaces != None) and (len(interfaces) != 0)):
                interface = interfaces[0]
                for interface in interfaces:
                    string += '\t<interface type="' + str(interfaceType) + '" ip="' + str(interface.getIP()) + \
                              '" subnet="' + str(interface.getSubnet()) + '" mac="' + str(interface.getMAC()) + \
                              '" switch="' + str(interface.getSwitch()) + '" port="' + str(interface.getPort()) + \
                              '" model="' + str(interface.getModel()) + '" speed="' + str(interface.getSpeed())
                    interfaceID = interface.getInterfaceID()
                    if (not interfaceID):
                        interfaceID = "interface" + str(interfaceIDNumber)
                        interfaceIDNumber += 1
                    string += '" id="' + str(interfaceID) + '" />\n\n'
        
        # Write physical location tag, if any
        try:
            physicalLocation = node.getPhysicalLocation()
        except:
            pass
        if (physicalLocation):
            string += '\t<physicallocation '
            if (physicalLocation.getBuilding()):
                string += 'building="' + str(physicalLocation.getBuilding()) + '" '
            if (physicalLocation.getFloor()):
                string += 'floor="' + str(physicalLocation.getFloor()) + '" '
            if (physicalLocation.getRoom()):
                string += 'room="' + str(physicalLocation.getRoom()) + '" '
            if (physicalLocation.getRackRow()):
                string += 'rackrow="' + str(physicalLocation.getRackRow()) + '" '
            if (physicalLocation.getRackName()):
                string += 'rackname="' + str(physicalLocation.getRackName()) + '" '
            if (physicalLocation.getRackStartUnit()):
                string += 'rackstartunit="' + str(physicalLocation.getRackStartUnit()) + '" '
            if (physicalLocation.getRackEndUnit()):
                string += 'rackendunit="' + str(physicalLocation.getRackEndUnit()) + '" '
            if (physicalLocation.getNodePosition()):
                string += 'position="' + str(physicalLocation.getNodePosition()) + '" '                
            if (physicalLocation.getDescription()):
                string += 'description="' + str(physicalLocation.getDescription()) + '" '
            string += '/>\n'
        
        # Write user management items, if any
        try:
            for user in node.getUsers():
                if (user != None):
                    string += '\t<usermanagement username="' + user.getUsername() + '" password="' + user.getPassword() + '" />\n'
                    string += '\n'
        except:
            pass
        
        # Write attributes, if any
        attributes = node.getAttributes()
        if (attributes != None and len(attributes) != 0):
            for attribute in attributes.keys():
                string += '\t<attribute name="' + str(attribute) + '" value="' + str(attributes[attribute]) + '" />\n'

        # Write closing tag
        string += '\n</node>'
        return string
    
    def writeNodePhysicalFile(self, node, debug=False):
        string = self.writeNodePhysicalFileString(node,debug)
        if debug:
            # Debugging mode to enable testing
            log.debug("Debugging mode :")
            log.debug("writeNodePhysicalFile")
            log.debug(string)
            return 0

        try:
            theFile = open(filename, "w")
            theFile.write(string)
            theFile.close()
            os.system("chgrp " + self.__groupName + " " + filename)
            os.system("chmod 775 " + filename)

            # Add node to in-memory dictionary of nodes
            self.getSystemNodesDictionary()[node.getNodeType()][node.getNodeID()] = node
            self.getNodeIDs()[node.getNodeID()] = "dummy"

            return 0
        except:
            print "1 error while writing to " + filename
            return -1

    def writePhysicalEntry(self, tagType, elementID, elementType, status="operational"):
        """\brief Adds an entry to the main physical topology file
        \param tagType (\c string) The tag type
        \param elementID (\c string) The id of the element
        \param elementType (\c string) The element's type
        \param status (\c string) The element's status
        \return (\c int) 0 if successful, -1 otherwise
        """
        # Make sure status has one of the allowed values
        if (status not in NODE_STATUSES):
            status = "operational"
            
        # Parse the entire physical topology file
        entriesList = self.__parsePhysicalEntries()

        # There are no entries in the current physical topology file
        if (entriesList == None or entriesList == -1):
            entriesList = []
            
        # Now append the new entry and write out the entire physical topology file
        entriesList.append(PhysicalTopologyEntry(tagType, elementType,  \
                                                 self.__etcPhysicalPath + "/" + elementID + ".xml", status))

        return self.__writePhysicalEntries(entriesList)
    
    def deletePhysicalEntry(self, elementID):
        """\brief Deletes an entry from the main phsyical topology file
        \param elementID (\c string) The id of the element whose entry is to be removed
        \return (\c int) 0 if successful, -1 otherwise
        """
        # Parse the entire physical topology file
        entriesList = self.__parsePhysicalEntries()

        # Now remove the new entry and write out the entire physical topology file
        newEntries = []
        for entry in entriesList:
            if (entry.getFilename().find(elementID) == -1):
                newEntries.append(entry)
                
        return self.__writePhysicalEntries(newEntries)

    def changePhysicalEntryStatus(self, elementID, newStatus):
        """\brief Changes the status of an entry in the main phsyical topology file
        \param elementID (\c string) The id of the element whose entry is to be changed
        \param newStatus (\c string) The new status of the entry
        \return (\c int) 0 if successful, -1 otherwise
        """
        # Only change the status if it's one of the allowed statuses
        if (newStatus not in NODE_STATUSES):
            return -1

        # Parse the entire physical topology file
        entriesList = self.__parsePhysicalEntries()

        # Now modify the necessary object
        counter = 0
        for entry in entriesList:
            if (entry.getFilename().find(elementID) != -1):
                entriesList[counter].setStatus(newStatus)
            counter += 1

        return self.__writePhysicalEntries(entriesList)
    
    def __writePhysicalEntries(self, entriesList):
        """\brief Writes the entire physical topology file based on the given list. This
                  function also takes care of writing the initial and ending topology tags
        \param entriesList (\c list of PhysicalTopologyEntry objects) A list with the information to write
        \return (\c int) 0 if successful, -1 otherwise
        """
        # Write beginning tag
        string = '<topology type="physical">\n\n'

        # Write infraststructure elements
        for infrastructureType in INFRASTRUCTURE_TYPES:
            for entry in entriesList:
                if (entry.getTagType() == "infrastructure" and entry.getElementType() == infrastructureType):
                    string += '\t<infrastructure type="' + infrastructureType + \
                              '" file="' + entry.getFilename() + \
                              '" status="' + entry.getStatus() + '" />\n'
            string += '\n'

        # Write node elements
        for nodeType in NODE_TYPES:
            for entry in entriesList:
                if (entry.getTagType() == "node" and entry.getElementType() == nodeType):
                    string += '\t<node type="' + nodeType + \
                              '" file="' + entry.getFilename() + \
                              '" status="' + entry.getStatus() + '" />\n'
            string += '\n'
            
        # Write ending tag
        string += '</topology>\n'

        try:
            theFile = open(self.__physicalConfigFile, "w")
            theFile.write(string)
            theFile.close()
        except:
            print "2 error while writing to " + self.__physicalConfigFile
            return -1
        os.system("chgrp " + self.__groupName + " " + self.__physicalConfigFile)
        os.system("chmod 775 " + self.__physicalConfigFile)

        return 0
    
####################################################################################################################
#
#   EXPERIMENT TOPOLOGY PARSE FUNCTIONS
#
####################################################################################################################
    def parseUserExperiment(self, topologyFile):
        """ Parses an experimental topology file
        \param topologyFile (\c string) Path and filename of the xml file containing the experiment's topology
        \return (\c UserExperiment) A UserExperiment object containing the parsed information
        """
        xmldoc = self.__parseTopologyFileInit(topologyFile, "experiment")
        xmlRoot = xmldoc.getElementsByTagName("topology")[0]
        startDate = self.__getLabel("startdate", xmlRoot)
        endDate = self.__getLabel("enddate", xmlRoot)
        startTime = self.__getLabel("starttime", xmlRoot)
        endTime = self.__getLabel("endtime", xmlRoot)        
        experimentID = self.__getLabel("experimentid", xmlRoot)
        self.__parsingExperiment = True

        # There should only be one user, so grab the first and only item in the list
        user = self.__parseUserManagement(xmldoc)[0]
        
        xmlNodes = xmldoc.getElementsByTagName("node")
        count = 0;
        nodesDictionary = {}

        # Parse experiment group tags
        experimentGroups = self.__parseExperimentGroups(xmldoc)
        for node in xmlNodes:
            # check that the 'type' is set, otherwise raise an error and skip to the next iteration of the loop
            # <node type="computer" ...>
            nodeType = self.__getLabel("type", node)
            if (nodeType == None):
                count += 1
                #self.getLogger().debug("\t node: " + str(count) + " \"type\" not set correctly")
                continue
            else:
                # An ExperimentNode object (created further down) has a Node object in it. This node
                # objects already exists, search for it
                theNode = None
                nodeID = self.__getLabel("id", node)
                nodes = self.getNodes("all", "all")
                for nodeTypesDictionary in nodes.values():
                    for nodeObject in nodeTypesDictionary.values():
                        if (nodeObject.getNodeID() == nodeID):
                            theNode = nodeObject
                            break

                # at this point the experimental interfaces are incomplete, they're missing their
                # switch and port number, which should be gotten from their physical files. This
                # information is already parsed and available through self.getNodes
                experimentalInterfaces = theNode.getInterfaces("experimental")
                if (experimentalInterfaces != None and len(experimentalInterfaces) != 0):
                    nodes = self.getNodes("all","all")
                    # The next four lines set up a loop through the physical node's interfaces
                    for specificNodeTypeDictionary in nodes.values():
                        for physicalNode in specificNodeTypeDictionary.values():
                            physicalInterfaces = physicalNode.getInterfaces("experimental")
                           
                            if physicalInterfaces != None:
                                for physicalInterface in physicalInterfaces:
                                    # For each physical interface and each experimental interface, match
                                    # on the mac address and copy switch and port information from the
                                    # physical interface to the experimental interface
                                    for index in range(0, len(experimentalInterfaces)):
                                        if (physicalInterface.getMAC() == experimentalInterfaces[index].getMAC()):
                                            experimentalInterfaces[index].setSwitch(physicalInterface.getSwitch())
                                            experimentalInterfaces[index].setPort(physicalInterface.getPort())
                                        
                # now readd the list of experimental interfaces into the node and create the
                # ExperimentNode object
                theNode.setInterfaces(experimentalInterfaces, "experimental")
                expNode = ExperimentNode(theNode, self.__parseNetbootInfo(node))

                # check that the requested node actually exists in the testbed's database
                if (theNode.getNodeID() not in self.getNodeIDs()):
                    print "requested node with id " + theNode.getNodeID() + " does not exist in the testbed's database"
                    
                # create and populate the actual dictionary to store in 
                if (nodesDictionary.has_key(nodeType)):
                    nodes = nodesDictionary[nodeType]
                    nodes[theNode.getNodeID()] = expNode
                    nodesDictionary[nodeType] = nodes
                else:
                    nodes = {}
                    nodes[theNode.getNodeID()] = expNode
                    nodesDictionary[nodeType] = nodes

        self.__parsingExperiment = False
        return UserExperiment(nodesDictionary, user, startDate, endDate, experimentID, \
                              topologyFile, startTime, endTime, experimentGroups)

    def __parseExperimentGroups(self, xmldoc):
        """\brief Parses experimentgroup tags. Currently only supports an 'id' attribute
        \param xmldoc (\c minidom.Node) The xml object representing the file to parse
        \return (\c list of strings) A list with the experiment groups' ids
        """
        experimentGroups = None
        experimentGroupsXML = xmldoc.getElementsByTagName("experimentgroup")
        if ( (experimentGroupsXML != None) and (len(experimentGroupsXML) != 0) ):
            experimentGroups = []
            for experimentGroup in experimentGroupsXML:
                experimentGroups.append(self.__getLabel("id", experimentGroup))

        return experimentGroups
    
    def __parseExperimentTopologies(self):
        """\brief Parses all experimental topologies in the testbed, storing the result in
        self.__systemExperimentsDictionary
        """
        for experimentID in  self.__experimentEntriesDictionary.keys():
            filename = self.__experimentEntriesDictionary[experimentID].getFilename()
            self.__systemExperimentsDictionary[experimentID] = self.parseUserExperiment(filename)
            
    def __parseExperimentEntries(self, experimentFile):
        """\brief Parses the experiment topology file, storing the parsed information
                  in the variable self.__experimentEntriesDictionary, which is a dictionary
                  of ExperimentTopologyEntry objects
        """
        xmldoc = self.__parseTopologyFileInit(experimentFile, "experiment")
        if (xmldoc == None or xmldoc == -1):
            #print "cannot parse experiment topology"
            return -1
        
        experimentsXML = xmldoc.getElementsByTagName("experiment")
        if (experimentsXML):
            for experiment in experimentsXML:
                theID = self.__getLabel("id", experiment);
                filename = self.__getLabel("file", experiment);
                status = self.__getLabel("status", experiment);


                self.__experimentEntriesDictionary[theID] = ExperimentTopologyEntry(filename, status);            
                #self.__experimentEntriesDictionary[self.__getLabel("id", experiment)] = self.__getLabel("file", experiment)

    def __parseNetbootInfo(self, xmldoc):
        """\brief Parses a single netbootinfo tag, returning an object of type Netbootinfo.
                  The netboot tag is only allowed the following attributes: loader,
                  filesystem, kernel. If the given xml object does not have a netbootinfo
                  tag, None is returned.
        \param xmldoc (\c minidom.Node) The xml object representing the file to search usermanagement tags in
        \return (\c NetbootInfo) The netboot information
        """                
        netbootInfo = None
        netbootInfoXML = xmldoc.getElementsByTagName("netbootinfo")

        if ( (netbootInfoXML != None) and (len(netbootInfoXML) != 0) ):
            loader = self.__getLabel("loader", netbootInfoXML[0])
            filesystem = self.__getLabel("filesystem", netbootInfoXML[0])
            kernel = self.__getLabel("kernel", netbootInfoXML[0])
            netbootInfo = NetbootInfo(loader, filesystem, kernel)
        
        return netbootInfo

    def __parseCurrentExperiments(self):
        """\brief Parses the xml file containing information about all the experiments
                  currently on the testbed. The function returns a list of objects of
                  type ExperimentalNode
        \return (\c list) A list of ExperimentNode objects containing the information parsed
        """
        xmldoc = self. __parseTopologyFileInit(self.getCurrentExperimentsFile(), "experiment")
        # Current experiment file does not exist
        if (xmldoc == -1):
            return -1

        experimentNodesXML = xmldoc.getElementsByTagName("experimentnode")        
        nodeList = []
        for node in experimentNodesXML:
            nodeType = self.__getLabel("type", node)
            nodeID = self.__getLabel("id", node)
            experimentID = self.__getLabel("experimentid", node)
            username = self.__getLabel("username", node)
            email = self.__getLabel("email", node)
            startDate = self.__getLabel("startdate", node)
            endDate = self.__getLabel("enddate", node)            
            startTime = self.__getLabel("starttime", node)
            endTime = self.__getLabel("endtime", node)

            nodeObject = None
            if (nodeType == "computer"):
                nodeObject = ComputerNode()
                nodeObject.setNodeType("computer")
            elif(nodeType == "router"):
                nodeObject = RouterNode()
                nodeObject.setNodeType("router")
            elif(nodeType == "switch"):
                nodeObject = SwitchNode()
                nodeObject.setNodeType("switch")
            nodeObject.setNodeID(nodeID)

            userManagement = UserManagement(username, None, email)
            experimentNode = ExperimentNode(nodeObject, None, experimentID, userManagement, startDate, endDate, startTime, endTime)
            nodeList.append(experimentNode)
        return nodeList
    
####################################################################################################################
#
#   EXPERIMENT TOPOLOGY WRITE FUNCTIONS
#
####################################################################################################################
    def __writeExperimentNodes(self, experimentNodes):
        """\brief Writes a given list of ExperimentNode objects to the current experiments xml file.
        \param experimentNodes (\c list of ExperimentNodes) The nodes to write to the file
        \return (\c int) 0 if sucessfull, -1 otherwise
        """
        try:
            currentExperimentsFile = open(self.getCurrentExperimentsFile(), "w")
            string = '<topology type="experiment">\n\n'
            for currentNode in experimentNodes:
                string += self.__writeExperimentNode(currentNode) + '\n'

            string += '\n</topology>\n'
            currentExperimentsFile.write(string)
            currentExperimentsFile.close()
                
            return 0
        except Exception, e:
            print "3 error while writing to " + self.getCurrentExperimentsFile()
            return -1

    def __writeExperimentNode(self, experimentNode):
        """\brief Creates an xml string out of the given experiment node
        \param experimentNode (\c ExperimentNode) An ExperimentNode object containing the information to write
        \return (\c string) An xml string representing the information in the ExperimentNode object
        """
        return '<experimentnode ' + \
                'type="' + experimentNode.getNode().getNodeType() + '" ' + \
                'id="' + experimentNode.getNode().getNodeID() + '" ' + \
                'username="' + experimentNode.getUser().getUsername() + '" ' + \
                'email="' + experimentNode.getUser().getEmail() + '" ' + \
                'experimentid="' + experimentNode.getExperimentID() + '" ' + \
                'startdate="' + experimentNode.getStartDate() + '" ' + \
                'enddate="' + experimentNode.getEndDate() + '" ' + \
                'starttime="' + experimentNode.getStartTime() + '" ' + \
                'endtime="' + experimentNode.getEndTime() + '" ' + \
                '/>'

    def writeExperimentToCurrent(self, userExperiment):
        """\brief Writes a given experiment topology to the file containing all
                  experiments on the testbed. This file is then used to verify
                  that a new experiment does not conflict with any current ones.
        \param userExperiment (\c UserExperiment) The UserExperiment object containing the information to write
        \return (\c int) 0 if successful, -1 otherwise
        """
        # Parse the nodes currently used in experiments, we will use this
        # against the information in userExperiment to verify that the user
        # is not asking for a topology that has nodes already assigned
        currentExperimentNodes = self.__parseCurrentExperiments()

        if (currentExperimentNodes == -1):
            try:
                currentExperimentsFile = open(self.getCurrentExperimentsFile(), "w")
                string = '<topology type="experiment">\n\n</topology>'
                currentExperimentsFile.write(string)
                currentExperimentsFile.close()
                currentExperimentNodes = self.__parseCurrentExperiments()                
            except Exception, e:
                print "henparser.py::writeExperimentToCurrent: error while writing to " + self.getCurrentExperimentsFile()
                return -1
            
        startDate = userExperiment.getStartDate()
        endDate = userExperiment.getEndDate()
        startTime = userExperiment.getStartTime()
        endTime = userExperiment.getEndTime()
        experimentID = userExperiment.getExperimentID()
        user = userExperiment.getUser()
        experimentNodes = userExperiment.getExperimentNodes()

        for specificNodeTypeDictionary in experimentNodes.values():
            for node in specificNodeTypeDictionary.values():
                # we now have a specific node, make sure that it's not
                # assigned to anything else
                for currentNode in currentExperimentNodes:
                    if (currentNode.getNode().getNodeID() == node.getNode().getNodeID()):
                        # user is requesting a node that is already assigned to an experiment,
                        # make sure that the dates don't conflict
                        currentStartDate = currentNode.getStartDate()
                        currentEndDate = currentNode.getEndDate()

                        if (datesOverlap(startDate, endDate, currentStartDate, currentEndDate) == True):
                            print "conflict with node " + currentNode.getNode().getNodeID() + " between experiments:"
                            print experimentID + ": " + startDate + "-" + endDate + " (new experiment)"
                            print currentNode.getExperimentID() + ": " + currentStartDate + "-" + currentEndDate
                            return -2

        # There are no conflicts, add the new experiment nodes to the file containing all
        # current experiments on the testbed. To do so, just append the new experiment nodes
        # to the list of current experiment nodes
        for specificNodeTypeDictionary in experimentNodes.values():
            for newNode in specificNodeTypeDictionary.values():
                newNode.setStartDate(startDate)
                newNode.setEndDate(endDate)
                newNode.setStartTime(startTime)
                newNode.setEndTime(endTime)
                newNode.setExperimentID(experimentID)
                newNode.setUser(user)
                currentExperimentNodes.append(newNode)

        # Now write all of the experiment nodes
        return self.__writeExperimentNodes(currentExperimentNodes)

    def deleteExperimentFromCurrent(self, experimentID):
        """\brief Deletes a given experiment topology from the file containing all
                  experiments on the testbed. 
        \param experimentID (\c string) The id of the experiment to delete
        \return (\c int) 0 if successful, -1 otherwise
        """
        currentExperimentNodes = self.__parseCurrentExperiments()

        remainingExperimentNodes = []
        for experimentNode in currentExperimentNodes:
            if (experimentNode.getExperimentID() != experimentID):
                remainingExperimentNodes.append(experimentNode)
            
        return self.__writeExperimentNodes(remainingExperimentNodes)

    def __writeExperimentEntries(self, entriesDictionary):
        """\brief Writes the entire experiment topology file based on the given dictionary. The
                  dictionary's keys are the path and filename of each experiment's file
                  and its values are the experiments' ids. This function also takes care of writing
                  the initial and ending topology tags
        \param entriesDictionary (\c dictionary) A dictionary with the information to write
        \return (\c int) 0 if successful, -1 otherwise
        """
        # Write beginning tag
        string = '<topology type="experiment">\n\n'

        # Write nodes
        for key in entriesDictionary.keys():
            string += '\t<experiment id="' + str(key) + \
                      '" file="' + str(entriesDictionary[key].getFilename()) + \
                      '" status="' + str(entriesDictionary[key].getStatus()) + \
                      '" />\n'

        # Write ending tag
        string += '\n</topology>\n'

        try:
            theFile = open(self.__experimentConfigFile, "w")
            theFile.write(string)
            theFile.close()
        except:
            print "4 error while writing to " + self.__experimentConfigFile
            return -1
        
        return 0

    def writeExperimentEntry(self, experimentID, experimentFile, status="active"):
        """\brief Adds an entry to the main experiment topology file
        \param experimentID (\c string) The id of the experiment
        \param experimentFile (\c string) The full path and filename to the experiment's xml file
        \return (\c int) 0 if successful, -1 otherwise
        """
        # Make sure that the status is one of the allowed types
        if (status not in EXPERIMENT_STATUSES):
            status = "active"

        # Parse the entire experiment topology file
        entriesDictionary = self.getExperimentEntries(status)

        # Now append the new entry and write out the entire experimental topology file
        entriesDictionary[experimentID] = ExperimentTopologyEntry(experimentFile, status);
        
        return self.__writeExperimentEntries(entriesDictionary)

    def deleteExperimentEntry(self, experimentID, status="active"):
        """\brief Deletes an entry from the main experiment topology file
        \param experimentID (\c string) The id of the experiment whose entry is to be removed
        \return (\c int) 0 if successful, -1 otherwise
        """
        # Make sure that the status is one of the allowed types
        if (status not in EXPERIMENT_STATUSES):
            status = "active"
            
        # Parse the entire experiment topology file
        entriesDictionary = self.getExperimentEntries(status)

        # Now remove the new entry and write out the entire experiment topology file
        newEntries = {}
        for entry in entriesDictionary.keys():
            if (entry.find(experimentID) == -1):
                newEntries[entry] = entriesDictionary[entry]
                

        return self.__writeExperimentEntries(newEntries)        

    def changeExperimentEntryStatus(self, experimentID, newStatus):
        """\brief Changes the status of an entry in the main experiment topology file
        \param experimentID (\c string) The id of the experiment whose entry is to be changed
        \param newStatus (\c string) The new status of the entry
        \return (\c int) 0 if successful, -1 otherwise
        """
        # Make sure that the status is one of the allowed types
        if (newStatus not in EXPERIMENT_STATUSES):
            return -1
            
        # Parse the entire experiment topology file
        entriesDictionary = self.getExperimentEntries("all")
        
        # Now modify the necessary object
        for key in entriesDictionary.keys():
            if (key == experimentID):
                entriesDictionary[key].setStatus(newStatus)

        return self.__writeExperimentEntries(entriesDictionary)

####################################################################################################################
#
#   TESTBEDFILE TOPOLOGY PARSE FUNCTIONS
#
####################################################################################################################
    def parseTestbedFileEntries(self):
        """\brief Parses the main testbed files topology file, returning a dictionary whose keys are the
                  paths and filenames of the testbed files and whose values are their types
        \return (\c list of TestbedFilesTopologyEntry objects) A list with the parsed information
        """
        topologyEntries = []
        xmldoc = self.__parseTopologyFileInit(self.__testbedFileConfigFile, "testbedfile")

        if (xmldoc == None or xmldoc == -1):
            #print "cannot parse testbed file topology, file missing"
            return -1

        for testbedFileType in TESTBEDFILE_TYPES:
            xml = xmldoc.getElementsByTagName(testbedFileType)

            if(xml):
                for element in xml:
                    filename = self.__getLabel("file", element)
                    testbedFileElementType = self.__getLabel("type", element)
                    status = self.__getLabel("status", element)
                    topologyEntries.append(TestbedFileTopologyEntry(testbedFileType, testbedFileElementType, filename, status))

        return topologyEntries

    def __parseTestbedFileTopologies(self, filename):
        """ \brief Parses all testbed file elements of the system 
        \param filename (\c string) A string representing the path to the main testbed files topology file
        """
        xmldoc = self.__parseTopologyFileInit(filename, "testbedfile")
        self.__parseFileNodes(xmldoc)

    def __parseFileNodes(self, xmldoc):
        """ \brief Parses all file nodes in the system, storing the results in self.__systemFileNodesDictionary.
                   This data structure is a dictionary of dictionaries. The keys of the top-most dictionary
                   are the different types of file nodes, for instance loader, kernel, filesystem, etc. The values
                   of the top-most dictionary are dictionaries themselves. The keys to each of these are the
                   actual ids of the file nodes of one type, for instace kernel1, kernel2, etc. The values are the
                   actual objects of type KernelFileNode, LoaderFileNode, etc. If a file node does not have
                   a tag named type or if the type is not one of the known ones (see if/elifs below), the node
                   is ignored and an entry added to the log.
        \param xmldoc (\c minidom.Node) The xml object representing the main topology file
        """
        filename = None
        theFileNode = None

        if (xmldoc == None or xmldoc == -1):
            #print "cannot parse fileNodes, null element passed"
            return -1

        fileNodeXML = xmldoc.getElementsByTagName("filenode")
        if(fileNodeXML):
            for fileNode in fileNodeXML:
                filename = self.__getLabel("file", fileNode)
                status = self.__getLabel("status", fileNode)
                xmlFile = self.__openXMLFile(filename)
                xmlFileNodes = xmlFile.getElementsByTagName("filenode")
                count = 0;
                for fileNode in xmlFileNodes:
                    # check that the 'type' is set, otherwise raise an error and skip to the next iteration of the loop
                    # <filenode type="kernel" ...>
                    fileNodeType = self.__getLabel("type", fileNode)
                    if (fileNodeType == None):
                        count += 1
                        #self.getLogger().debug("\t filenode: " + str(count) + " \"type\" not set correctly")
                        continue
                    else:
                        if (fileNodeType == "loader"):
                            theFileNode = self.__parseLoaderFileNode(fileNode)
                        elif (fileNodeType == "kernel"):
                            theFileNode = self.__parseKernelFileNode(fileNode)
                        elif(fileNodeType == "filesystem"):
                            theFileNode = self.__parseFilesystemFileNode(fileNode)
                        else:
                            #print "unknown type " + fileNodeType
                            #self.getLogger().debug("\t filenode: " + str(count) + " has unknown type: " + fileNodeType)
                            continue

                        # Set the (already parsed) fileNode's status
                        theFileNode.setStatus(status)

                        # create and populate the actual dictionary to store in 
                        if (self.getSystemFileNodesDictionary().has_key(fileNodeType)):
                            fileNodes = self.getSystemFileNodesDictionary()[fileNodeType]
                            fileNodes[theFileNode.getID()] = theFileNode
                            self.getSystemFileNodesDictionary()[fileNodeType] = fileNodes
                        else:
                            fileNodes = {}
                            fileNodes[theFileNode.getID()] = theFileNode
                            self.getSystemFileNodesDictionary()[fileNodeType] = fileNodes
    
    def __parseFileNode(self, xmldoc, fileNode):
        """\brief Given an xml entry representing a file node, this
                  function parses all of tags that are to be stored in the FileNode superclass;
                  these include any subtags of the file node tag as well as the attribute tags.
                  The following subtags are currently supported: id, type, path,
                  architecture, ostype, version, mustclone
        \param xmldoc (\c minidom.Node) The xml object representing the file for the file node
        \param node (\c subclass of hen.FileNode) The FileNode subclass object to store the results into
        \return (\c subclass of hen.FileNode) The FileNode subclass object with the parsed results stored in it 
        """
        fileNodeID = self.__getLabel("id", xmldoc)		   
        if (fileNodeID == None):
            pass
            #self.getLogger().info("no id for fileNode " + str(xmldoc))
        fileNodeType = self.__getLabel("type", xmldoc)
        if (fileNodeType == None):
            pass
            #self.getLogger().info("no type for fileNode " + str(xmldoc))
        fileNodePath = self.__getLabel("path", xmldoc)
        if (fileNodePath == None):
            pass
            #self.getLogger().info("no path for fileNode " + str(xmldoc))
        fileNodeOwner = self.__getLabel("owner", xmldoc)
        if (fileNodeOwner == None):
            pass
            #self.getLogger().info("no owner for fileNode " + str(xmldoc))            
        fileNodeArchitecture = self.__getLabel("architecture", xmldoc)
        if (fileNodeArchitecture == None):
            pass
            #self.getLogger().info("no architecture for fileNode " + str(xmldoc))
        fileNodeOsType = self.__getLabel("ostype", xmldoc)
        if (fileNodeOsType == None):
            pass
            #self.getLogger().info("no osType for fileNode " + str(xmldoc))
        fileNodeVersion = self.__getLabel("version", xmldoc)
        if (fileNodeVersion == None):
            pass
            #self.getLogger().info("no version for fileNode " + str(xmldoc))
        fileNodeMustClone = self.__getLabel("mustclone", xmldoc)
        if (fileNodeMustClone == None):
            pass
            #self.getLogger().info("no mustClone for fileNode " + str(xmldoc))            
             
        fileNode.setID(fileNodeID)
        fileNode.setType(fileNodeType)
        fileNode.setPath(fileNodePath)
        fileNode.setOwner(fileNodeOwner)
        fileNode.setArchitecture(fileNodeArchitecture)
        fileNode.setOsType(fileNodeOsType)
        fileNode.setVersion(fileNodeVersion)
        fileNode.setMustClone(fileNodeMustClone)

        # Parse and set attributes
        fileNode.setAttributes(self.__parseAttributes(xmldoc))

        # Parse and set Md5 signature tag
        fileNode.setMd5Signature(self.__parseMd5Signature(xmldoc))

        # Parse and set description tag
        fileNode.setDescription(self.__parseDescription(xmldoc))
        
        return fileNode        
    
    def __parseKernelFileNode(self, xmldoc):
        """\brief Parses an object of type KernelFileNode. Currently all of this object's
                  attributes are contained in its super class, so all of the actual parsing
                  is done by __parseFileNode.
        \param xmldoc (\c minidom.Node) The xml object representing the kernel file node's file
        \return (\c KernelFileNode) A KernelFileNode object containg the parsed information
        """        
        kernelFileNode = KernelFileNode()
        kernelFileNode = self.__parseFileNode(xmldoc, kernelFileNode)
        return kernelFileNode
    
    def  __parseFilesystemFileNode(self, xmldoc):
        """\brief Parses an object of type FilesystemFileNode. 
        \param xmldoc (\c minidom.Node) The xml object representing the filesystem file node's file
        \return (\c FilesystemFileNode) A FilesystemFileNode object containg the parsed information
        """        
        filesystemFileNode = FilesystemFileNode()
        filesystemFileNode = self.__parseFileNode(xmldoc, filesystemFileNode)
        filesystemFileNode.setUserManagement(self.__parseUserManagement(xmldoc))
        return filesystemFileNode                
    
    def __parseLoaderFileNode(self, xmldoc):
        """\brief Parses an object of type LoaderFileNode. Currently all of this object's
                  attributes are contained in its super class, so all of the actual parsing
                  is done by __parseFileNode.
        \param xmldoc (\c minidom.Node) The xml object representing the loader file node's file
        \return (\c LoaderFileNode) A LoaderFileNode object containg the parsed information
        """        
        loaderFileNode = LoaderFileNode()
        loaderFileNode = self.__parseFileNode(xmldoc, loaderFileNode)
        return loaderFileNode        

    def __parseMd5Signature(self, xmldoc):
        """\brief Returns the text found between md5signature tags
        \param xmldoc (\c minidom.Node) The xml object representing the file to parse        
        \return (\c string) The Md5 signature
        """
        md5Signature = xmldoc.getElementsByTagName("md5signature")
        md5SignatureValue = md5Signature.item(0).firstChild.nodeValue
        return md5SignatureValue

    def __parseDescription(self, xmldoc):
        """\brief Returns the text found between description tags
        \param xmldoc (\c minidom.Node) The xml object representing the file to parse        
        \return (\c string) The description
        """        
        description = xmldoc.getElementsByTagName("description")
        descriptionValue = description.item(0).firstChild.nodeValue
        return descriptionValue

####################################################################################################################
#
#   TESTBEDFILE TOPOLOGY WRITE FUNCTIONS
#
####################################################################################################################
    def writeFileNodeTestbedFile(self, fileNode):
        """\brief Writes the xml description file for a tesbed file object
        \param node (\c subclass of FileNode) An object sub-classed from FileNode with the necessary information
        \return (\c int) 0 if successful, -1 otherwise
        """
        filename = self.__etcTestbedFilePath + "/" + fileNode.getID() + ".xml"

        # Write fileNode tag
        string = '<filenode type="' + str(fileNode.getType()) + \
                 '" id="' + str(fileNode.getID()) + \
                 '" owner="' + str(fileNode.getOwner()) + \
                 '" path="' + str(fileNode.getPath()) + \
                 '" architecture="' + str(fileNode.getArchitecture()) + \
                 '" ostype="' + str(fileNode.getOsType()) + \
                 '" version="' + str(fileNode.getVersion()) + \
                 '" mustclone="' + str(fileNode.getMustClone()) + \
                 '" >\n\n'

        # Write md5 signature tag, if any
        md5Signature = fileNode.getMd5Signature()
        if (md5Signature):
            string += '\t<md5signature>' + str(md5Signature) + '</md5signature>\n\n'

        # Write description tag, if any
        description = fileNode.getDescription()
        if (description):
            string += '\t<description>' + str(description) + '</description>\n\n'

        # Write user management items, if any
        try:
            for user in fileNode.getUserManagement():
                if (user != None):
                    string += '\t<usermanagement username="' + str(user.getUsername()) + \
                              '" password="' + str(user.getPassword()) + \
                              '" email="' + str(user.getEmail()) + \
                              '" description="' + str(user.getDescription()) + \
                              '" />\n'
            string += '\n'
        except:
            pass

        # Write attributes, if any
        attributes = fileNode.getAttributes()
        if (attributes != None and len(attributes) != 0):
            for attribute in attributes.keys():
                string += '\t<attribute name="' + str(attribute) + '" value="' + str(attributes[attribute]) + '" />\n'

        # Write closing tag
        string += '\n</filenode>'

        try:
            theFile = open(filename, "w")
            theFile.write(string)
            theFile.close()
            os.system("chgrp " + self.__groupName + " " + filename)
            os.system("chmod 775 " + filename)

            # Add file node to in-memory dictionary of file nodes
            self.getSystemFileNodesDictionary()[fileNode.getType()][fileNode.getID()] = fileNode
            
            return 0
        except:
            print "1 error while writing to " + filename
            return -1

    def writeTestbedFileEntry(self, tagType, elementID, elementType, status="operational"):
        """\brief Adds an entry to the main testbed file topology file
        \param tagType (\c string) The tag type
        \param elementID (\c string) The id of the element
        \param elementType (\c string) The element's type
        \return (\c int) 0 if successful, -1 otherwise
        """
        # Make sure that status has a valid value
        if (status not in TESTBEDFILE_STATUSES):
            status  = "operational"
            
        # Parse the entire testbed file topology file
        entriesList = self.parseTestbedFileEntries()

        # There are no entries in the current testbed file topology file
        if (entriesList == None or entriesList == -1):
            entriesList = []
            
        # Now append the new entry and write out the entire testbed file topology file
        entriesList.append(TestbedFileTopologyEntry(tagType, elementType,  \
                                                 self.__etcTestbedFilePath + "/" + elementID + ".xml", status))

        return self.__writeTestbedFileEntries(entriesList)
    
    def deleteTestbedFileEntry(self, elementID):
        """\brief Deletes an entry from the main testbed file topology file
        \param elementID (\c string) The id of the element whose entry is to be removed
        \return (\c int) 0 if successful, -1 otherwise
        """
        # Parse the entire testbed file topology file
        entriesList = self.parseTestbedFileEntries()

        # Now remove the new entry and write out the entire testbed file topology file
        newEntries = []
        for entry in entriesList:
            if (entry.getFilename().find(elementID) == -1):
                newEntries.append(entry)
                
        return self.__writeTestbedFileEntries(newEntries)
    
    def changeTestbedFileEntryStatus(self, elementID, newStatus):
        """\brief Changes the status of an entry in the main testbed file topology file
        \param elementID (\c string) The id of the element whose entry is to be changed
        \param newStatus (\c string) The new status of the entry
        \return (\c int) 0 if successful, -1 otherwise
        """
        # Make sure that the status has a valid value
        if (newStatus not in TESTBEDFILE_STATUSES):
            return -1
        
        # Parse the entire testbed file topology file
        entriesList = self.parseTestbedFileEntries()

        # Now modify the necessary object
        counter = 0
        for entry in entriesList:
            if (entry.getFilename().find(elementID) != -1):
                entriesList[counter].setStatus(newStatus)
            counter += 1

        return self.__writeTestbedFileEntries(entriesList)
    
    def __writeTestbedFileEntries(self, entriesList):
        """\brief Writes the entire testbed file topology file based on the given list. This
                  function also takes care of writing the initial and ending topology tags
        \param entriesList (\c list of TestbedFileTopologyEntry objects) A list with the information to write
        \return (\c int) 0 if successful, -1 otherwise
        """
        # Write beginning tag
        string = '<topology type="testbedfile">\n\n'
            
        # Write filenode elements
        for fileNodeType in FILENODE_TYPES:
            for entry in entriesList:
                if (entry.getTagType() == "filenode" and entry.getElementType() == fileNodeType):
                    string += '\t<filenode type="' + fileNodeType + \
                              '" file="' + entry.getFilename() + \
                              '" status="' + entry.getStatus() + '" />\n'
            string += '\n'

        # Write ending tag
        string += '</topology>\n'

        try:
            theFile = open(self.__testbedFileConfigFile, "w")
            theFile.write(string)
            theFile.close()
        except:
            print "2 error while writing to " + self.__testbedFileConfigFile
            return -1
        os.system("chgrp " + self.__groupName + " " + self.__testbedFileConfigFile)
        os.system("chmod 775 " + self.__testbedFileConfigFile)

        return 0

####################################################################################################################
#
#   LOG ENTRIES PARSE AND WRITE FUNCTIONS
#
####################################################################################################################
    def __parseLogs(self):
        """\brief Parses all log files in the testbed's log directory and stores the result in self.__logsEntries, a
                  dictionary whose keys are the log files' names and whose values are lists of LogEntry objects
        """
        filenames = os.listdir(self.__logPath)

        for filename in filenames:
            if (filename.find("~") == -1):
                self.__logsEntries[filename] = self.__parseLog(self.__logPath + "/" + filename)

    def __parseLog(self, filename):
        """\brief Parses a log file.
        \param filename (\c string) The full path and filename of the log file to parse
        \return (\c list of LogEntry) A list of LogEntry objects representing the parsed information
        """
        try:
            xmldoc = self.__openXMLFile(filename)
        except:
            return None
        if not xmldoc:
            return None
        xmlLog = xmldoc.getElementsByTagName("log")
        if not xmlLog:
            return None
        xmlLogEntries = xmlLog[0].getElementsByTagName("logentry")
        logEntries = []
        for xmlLogEntry in xmlLogEntries:
            logEntryDate = self.__getLabel("date", xmlLogEntry)
            logEntryTime = self.__getLabel("time", xmlLogEntry)
            logEntryAuthorLoginID = self.__getLabel("authorloginid", xmlLogEntry)            
            logEntryDescription = xmlLogEntry.getElementsByTagName("description")[0].firstChild.nodeValue.strip()

            affectedElements = []
            for xmlAffectedElement in xmlLogEntry.getElementsByTagName("affectedelement"):
                affectedElements.append(self.__getLabel("id", xmlAffectedElement))

            logEntries.append(LogEntry(logEntryDate, logEntryTime, logEntryAuthorLoginID, affectedElements, logEntryDescription))

        return logEntries
    
    def writeLogEntry(self, logEntry):
        """\brief Writes a log entry to a log file based on the current date
        \param logEntry (\c LogEntry) A LogEntry object with the information to write
        \return (\c int) 0 if successful, -1 otherwise
        """
        logEntryDate = str(strftime("%d/%m/%Y", gmtime()))
        logEntryTime = str(strftime("%H:%M", gmtime()))
        logEntryMonthYear = str(logEntryDate[3:5]) + "-" + str(logEntryDate[6:])
        filename = self.__logPath + "/" + logEntryMonthYear + ".xml"

        # Write beginning log tag only if the file does not yet exist
        string = ''
        if (not fileExists(filename)):
            string += '<log>\n'

        # Remove the final </log> file so that we can insert the new entry
        else:
            try:
                for line in fileinput.input([filename], 1):
                    if (line != "</log>\n"):
                        print line,
            except:
                print "error while removing </log> line from " + filename

        # Write logentry tag
        string += '\t<logentry date="' + str(logEntryDate) + '" ' + \
                  'time="' + str(logEntryTime) + '" ' + \
                  'authorloginid="' + str(logEntry.getAuthorLoginID()) + '" >\n'

        # Write affectedelement tags
        affectedElementsIDs = logEntry.getAffectedElementsIDs()
        for affectedElementID in affectedElementsIDs:
            string += '\t\t<affectedelement id="' + str(affectedElementID) + '" />\n'

        # Write description tag
        string += '\t\t<description>\n\t\t' + str(logEntry.getDescription()) + '\n\t\t</description>\n'

        string += '\t</logentry>\n'

        string += '</log>\n'

        try:
            theFile = None
            if (fileExists(filename)):
                theFile = open(filename, "a")
            else:
                theFile = open(filename, "w")
        
            theFile.write(string)
            theFile.close()

        except:
            print "2 error while writing to " + filename
            return -1
        os.system("chgrp " + self.__groupName + " " + filename)
        os.system("chmod 775 " + filename)

        return 0    

