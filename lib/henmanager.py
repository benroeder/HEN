################################################################################
# henmanager.py: this class acts as a wrapper between hm and the backend classes
#
# CLASSES
# --------------------------------------------------------------------
# HenManager         The class used to manipulate backend operations such as 
#                    parsing xml, interacting with switches, creating 
#                    experiments, etc
#
################################################################################
from auxiliary.henparser import HenParser
from auxiliary.hen import VLAN, Interface, DHCPConfigSubnetInfo, \
    DHCPConfigInfo, DNSConfigInfo, NetbootInfo, isVLANInList, \
    isHigherIPAddress, incrementIPAddress, ServerNode, ComputerNode, \
    SerialNode, SwitchNode, PowerSwitchNode, RouterNode, ServiceProcessorNode, \
    SensorNode, KVMNode, UserManagement, InfrastructureRack, PhysicalSize, \
    InfrastructureFloorBox, FloorBoxPowerPlug, FloorBoxRJ45Port, \
    PhysicalLocation, Port, LogEntry, generateMD5Signature, fileExists, \
    MoteNode, Peripheral

from daemonclients.reservationclient import ReservationClient
from operatingsystem.confignetboot import ConfigNetboot
from xmlrpclib import ServerProxy \
    as RemoteXMLRPCServer, Error as XMLRPCError, ProtocolError
from socket import gaierror, error as sockerr
import auxiliary.hen
import auxiliary.protocol
from auxiliary.daemonlocations import DaemonLocations
import sys, os, __builtin__, logging, ConfigParser, string, commands, time, \
    dircache, pyclbr, re, pickle, thread, datetime

# The switch class imports pysnmp which is non-standard, causing problems when 
# scripts running on the experimental nodes try to import henmanager. Since the 
# experimental nodes do not need switch functionality, we can get around this 
# with a try/except (fhuici)
try:
    import hardware.switches.switch
    from hardware.switches import *
except:
    pass

from hardware.powerswitches import *
from hardware.sensors import *
from hardware.serviceprocessors import *
from hardware.terminalservers import *

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

class HenManager:
    """\brief This class acts as a wrapper between hm and backend operations 
              such as parsing xml, interacting with switches, etc.
    """

    def __init__(self, configFilePath='/usr/local/hen/etc/configs/config'):
        """\brief Initializes the class and the logger
        \param configFilePath (\c string) The path to the config file for the 
                testbed. Default: /usr/local/hen/etc/configs/config
        """

	if configFilePath != "/usr/local/hen/etc/configs/config":
           log.info("RUNNING WITH NON STANDARD CONFIG FILE PATH : "+configFilePath)

        self.__configFilePath = configFilePath
        self.__configFile = ConfigParser.ConfigParser()
        self.__configFile.read(configFilePath)
        self.__initConfig()
        
        self.__running = None
        self.__log = None

        self.__initNetboot()

        self.initLogging()
        self.parser = HenParser(self.__henPhysicalTopology, \
                                self.__henExperimentTopology, \
                                self.__henTestbedFilesTopology, \
                                self.__henLogPath, self.__physicalPath, 
                                self.__experimentPath, self.__testbedFilePath, \
                                self.__configFile.get('MAIN', \
                                   'CURRENT_EXPERIMENTS'), self.__testbedGroup)
        self.__modelsStruct = {}
        self.__node_instances = {}
        self.__reservationsClient = None
	try:
        	self.__username = os.environ['USER']
	except:
		self.__username = "nobody"
        self.__isSuperUser = (self.__username == "root" or self.__username == "hend")
        #self.__initReservationClient()
        
    def __initReservationClient(self):
        if (not self.__isSuperUser):
            try:
                HOST = DaemonLocations.reservationDaemon[0]
                PORT = DaemonLocations.reservationDaemon[1]
                self.__reservationsClient = ReservationClient()
                self.__reservationsClient.connect(HOST, PORT)
            except:
                print "error: could not connect to reservation daemon"
                self.__reservationsClient = None
        
    def __initConfig(self):
        self.__henRoot = self.__configFile.get('DEFAULT', 'ROOT')
        self.__pythonBin = self.__configFile.get('MAIN','PYTHON_BIN')
        self.__henRoot = self.__configFile.get('MAIN','ROOT')
        self.__henBinPath = self.__configFile.get('MAIN','BIN_PATH')
        self.__henEtcPath = self.__configFile.get('MAIN','ETC_PATH')
        self.__henVarPath = self.__configFile.get('MAIN','VAR_PATH')
        self.__henLogPath = self.__configFile.get('MAIN', 'LOG_PATH')
        self.__henExperimentalBaseAddress = \
            self.__configFile.get('MAIN', 'EXPERIMENTAL_BASE_ADDRESS')
        self.__henInfrastructureBaseAddress = \
            self.__configFile.get('MAIN', 'INFRASTRUCTURE_BASE_ADDRESS')
        self.__henVirtualBaseAddress = \
            self.__configFile.get('MAIN', 'VIRTUAL_BASE_ADDRESS')

        self.__henBaseExportPath = \
            self.__configFile.get('MAIN', 'BASE_EXPORT_PATH')
        self.__henExportPath = \
            self.__configFile.get('MAIN','EXPORT_PATH')
        self.__henPhysicalTopology = \
            self.__configFile.get('MAIN','PHYSICAL_TOPOLOGY')
        self.__henExperimentTopology = \
            self.__configFile.get('MAIN','EXPERIMENTAL_TOPOLOGY')
        self.__henTestbedFilesTopology = \
            self.__configFile.get('MAIN','TESTBEDFILE_TOPOLOGY')
        self.__userLogFile = "%s%s-%s-%s"%(self.__henLogPath, "/log", \
                           auxiliary.hen.getUserName(), auxiliary.hen.getTime())
        self.__henManager = self.__configFile.get('MAIN','MANAGER')
        self.__physicalPath = self.__configFile.get('MAIN', 'PHYSICAL_PATH')
        self.__experimentPath = \
            self.__configFile.get('MAIN', 'EXPERIMENTAL_PATH')
        self.__testbedFilePath = \
            self.__configFile.get('MAIN', 'TESTBEDFILE_PATH')
        self.__testbedGroup = self.__configFile.get('NETBOOT', 'GROUP')
        self.__xmlRpcPort = int(self.__configFile.get('MOTE', 'XML_RPC_PORT'))

    def __initNetboot(self):
        self.__configNetboot = ConfigNetboot(NetbootInfo(\
                  self.__configFile.get('NETBOOT', 'AUTODETECT_LOADER'), \
                  self.__configFile.get('NETBOOT', 'AUTODETECT_FILESYSTEM'), \
                  self.__configFile.get('NETBOOT', 'AUTODETECT_KERNEL')), \
                  self.__testbedGroup, \
                  self.__configFile.get('NETBOOT', 'NFS_ROOT'), \
                  self.__configFile.get('NETBOOT', 'SERIAL_SPEED'), \
                  self.__configFile.get('NETBOOT', 'PXE_LINUX_DIRECTORY'), \
                  self.__configFile.get('NETBOOT', 'PXE_LINUX_FILE'), \
                  self.__configFile.get('NETBOOT', 'STARTUP_FILE'), \
                  self.__configFile.get('NETBOOT', 'INTERFACE_CONFIG_SCRIPT'), \
                  self.__configFile.get('NETBOOT', 'CONSOLE'), \
                  self.__henExportPath, \
                  self.__pythonBin)        

    def initLogging(self, loggerName='hen'):
        """\brief Initializes the logger
        \param loggerName (\c string) The name of the logger. Default value: hen
        """
        self.__log = logging.getLogger(loggerName)
        user = auxiliary.hen.getUserName()
        if (user != "web"):
            self.__log.setLevel(logging.DEBUG)
            sth = logging.StreamHandler()
            sth.setLevel(logging.INFO)
            self.__log.addHandler(sth)

    def createNodeInstances(self):
        """\brief Creates instances for all nodes in the hen testbed (for which
        creating an instance is possible), and places them in a dictionary of
        the form {nodetype:{nodeid:(node,instance)}}. This dictionary can then 
        be accessed through getNodeInstances()
        """
        nodes = self.getNodes("all", "all")
        for nodeType in nodes.keys():
            self.__node_instances[nodeType] = {}
            nodeTypes = nodes[nodeType]
            for node in nodeTypes.values():
                try:
                    self.__node_instances[nodeType][node.getNodeID()] = \
                                        (node, node.getInstance())
                except Exception, e:
                    pass # Silently fail - there are many nodes for which
                         # creating an instance isn't possible

    def getNodeInstances(self):
        """\brief Returns the dictionary of instances created by 
        createNodeInstances(). See createNodeInstances() for a description of
        the dictionary format.
        \return (\c dict) Dictionary of node instances if created, 
                          None otherwise
        """
        if self.__node_instances:
            return self.__node_instances
        return None
    
    def getNodeInstance(self, node):
        """\brief Given a node object, an instance of the node is returned,
        or None if this isn't possible. This method will first look to see if
        the node instance exists in the __node_instances dictionary, and if not,
        resort to creating the instance manually and adding it to the 
        dictionary.
        """
        try:
            nodeType = node.getNodeType()
            nodeid = node.getNodeID()
            if self.__node_instances.has_key(nodeType):
                if self.__node_instances[nodeType].has_key(nodeid):
                    (n, ni) = self.__node_instances[nodeType][nodeid]
                    return ni
            # If we're here, the instance isn't in the dictionary. Lets add it.
            if not self.__node_instances.has_key(nodeType):
                self.__node_instances[nodeType] = {}
            #print node.getInstance()
            nodeinstance = node.getInstance()
            self.__node_instances[nodeType][nodeid] = (node, nodeinstance)
            return nodeinstance
        except:
            # Fail silently
            return None

    def getLogEntriesByElement(self, elementID):
        """\brief Returns all log entries affecting a given element on the testbed
        \param elementID (\c string) The element to retrieve information for
        \return (\c list of LogEntry) All entries affecting the element given
        """
        return self.parser.getLogEntriesByElement(elementID)

    def writeLogEntry(self, authorLoginID, affectedElementsIDs, description):
        """\brief Writes a log entry to a log file based on the current date
        \param authorLoginID (\c string) The login id of the person creating the log
        \param affectedElementsIDs (\c list of string) The ids of the elements affected by the log
        \param description (\c string) The log's description
        \return (\c int) 0 if successful, -1 otherwise
        """
        logEntry = LogEntry(None, None, authorLoginID, affectedElementsIDs, description)

        return self.parser.writeLogEntry(logEntry)

    def getLinks(self, key, status="all"):
        return self.parser.getLinks(key,status)

    def getNodes(self, key, status="operational"):
        """\brief Returns a dictionary of objects of type key. If key is set to all, the function
                  returns a dictionary of dictionaries. Please see auxiliary.henParser.getNodes
                  documentation for more detail.
           \param key (\c string) A string set to router, switch, powerswitch, serial, computer, serviceprocessor or all
           \param status (\c string) The resulting dictionary will only contain nodes whose status is equal to this. If
                                     this is set to 'all', no filtering based on status will be performed (default is operational)
           \return (\c dictionary) Either a dictionary of objects of type key or a dictionary of dictionaries.
        """
        return self.parser.getNodes(key, status)

    def getNodeRange(self, rangeid, status="operational"):
        """\brief Returns a dictionary of objects of a type specified in the rangeid. Only one type can be specified in this way.
                  The rangeid is expand into all possible node ids within the range, including the last. If a node with that id
                  exists, it is included in the return dictionary.
        \param rangeid (\c string) A string set to one of router, switch, powerswitch, serial, computer, mote, serviceprocessor
                                   appended with a range specifier: one or two numbers,separated by - or : e.g. 1-, 22:34, -99
        \return (\c dictionary) A list of objects in the range for each loop.
        """
        noderdb = {}
        m = re.match(r'([\w][^-:,\d]+)', rangeid)
        if not m:
            self.__log.error("Invalid node range; node type not specified: %s" % rangeid)
            return noderdb
        typespec = m.group(1)
        rangespec = m.string[m.end(1):]
        for subrange in rangespec.split(','):
            minnodenum = int(self.__configFile.get('MAIN', typespec+'_NODE_MINIMUM_NUMBER'))
            maxnodenum = int(self.__getNextNodeID(typespec, str(minnodenum))[len(typespec):])
            # RE attempts to match 4 groups
            m = re.match(r'(\d+)?(-)?((?<=-)\d+)?(:)?((?<=:)\d+)?', subrange)
            if m.group(4) and not m.group(5):
                self.__log.error("Invalid node range; missing step modifier: %s" % rangeid)
                return noderdb
            if m.group(1) and m.group(2) and m.group(3):
                i, j, k = m.group(1), m.group(3), 1
                if m.group(5): k = m.group(5)
            elif m.group(2) and m.group(3):
                i, j, k = minnodenum, m.group(3), 1
                if m.group(5):
                    k = m.group(5);
                    # based on the fact that the user is more likely to want the end-node included
                    i = int(j) % int(k)
            elif m.group(1) and m.group(2):
                i, j, k = m.group(1), maxnodenum, 1
                if m.group(5): k = m.group(5)
            elif m.group(2):
                i, j, k = minnodenum, maxnodenum, 1
                if m.group(5):k = m.group(5)
            elif m.group(1) and not m.group(5):
                i, j, k = [m.group(1)]*2 + [1]
            else:
                self.__log.error("Invalid node range; invalid range or step modifiers: %s" % rangeid)
                return noderdb
            nodedb = self.getNodes(typespec, status)
            fmt = typespec+"%d"
            for id in map(fmt.__mod__, range(int(i),int(j)+1, int(k))):
                if id in nodedb:
                    noderdb[id] = nodedb[id]
        return noderdb

    def getInfrastructures(self, key, status="operational"):
        """\brief Returns a dictionary of objects of type key. If key is set to all, the function
              returns a dictionary of dictionaries. Please see auxiliary.henParser.getInfrastructures
          documentation for more details.
           \param key (\c string) A string set to rack (more types to come)
           \param status (\c string) The resulting dictionary will only contain infrastructures whose status is equal to this. If
                                     this is set to 'all', no filtering based on status will be performed
                                     (default is operational)
           \return (\c dictionary) Either a dictionary of objects of type key or a dictionary of dictionaries.
        """
        return self.parser.getInfrastructures(key, status)

    def getFileNodes(self, key, status="operational"):
        """\brief Returns a dictionary of objects of type key. If key is set to all, the function
              returns a dictionary of dictionaries. Please see auxiliary.henParser.getFileNodes
          documentation for more details.
           \param key (\c string) A string set to filesystem, kernel, loader or all
           \param status (\c string) The resulting dictionary will only contain nodes whose status is equal to this. If
                                     this is set to 'all', no filtering based on status will be performed (default is operational)
           \return (\c dictionary) Either a dictionary of objects of type key or a dictionary of dictionaries.
        """
        return self.parser.getFileNodes(key, status)

    def getExperimentEntries(self, status="active"):
        """\brief Returns a dictionary whose keys are the experiment ids of the experiments currently
                  in the testbed and whose values are ExperimentTopologyEntry objects
           \param status (\c string) The resulting dictionary will only contain experiments whose status is equal to this.
                                     If this is set to 'all', no filtering based on status will be performed
                                     (default is active).
        \return (\c dictionaryof ExperimentTopologyEntry objects) A dictionary with information
                  about experiments currently on the testbed.
        """
        return self.parser.getExperimentEntries(status)

    def getExperiments(self, status="active"):
        """\brief Returns a dictionary whose keys are the experiment ids of the experiments currently
                  in the testbed and whose values are UserExperiment objects
           \param status (\c string) The resulting dictionary will only contain experiments whose status is equal to this.
                                     If this is set to 'all', no filtering based on status will be performed
                                     (default is active).
        \return (\c dictionaryof UserExperiment objects) A dictionary with information
                  about experiments currently on the testbed.
        """
        return self.parser.getExperiments(status)

    def getConfigFileLines(self):
        """\brief Returns a list of strings representing the lines in the testbed's main config file
        \return (\c list of string) The lines in the testbed's main config file
        """
        return open(self.__configFilePath, "r").readlines()

    def writeConfigFileLines(self, lines):
        """\brief Overwrites the testbed's main config file with the given string. The previous config file is saved in the
                  'backup' subdirectory, renaming it to have the current time.
        \param lines (\c string) The string representing the new config file
        \return (\c int) 0 if successful, -1 otherwise
        """
        # Make the backup directory if it does not already exist
        if (not fileExists(self.__henEtcPath + "/configs/backup")):
            if ((commands.getstatusoutput("mkdir " + self.__henEtcPath + "/configs/backup")[0]) != 0):
                return -1

        # Copy the current config file to the backup directory
        backupFilename = str(time.strftime("%d-%b-%Y-%H:%M:%S", time.gmtime())) + ".config"
        if ((commands.getstatusoutput("cp " + self.__configFilePath + " " + self.__henEtcPath + "/configs/backup/" + backupFilename)[0]) != 0):
            return -1

        # Overwrite the existing config file with the given lines
        try:
            theFile = open(self.__configFilePath, "w")
            theFile.write(lines)
            theFile.close()
        except:
            print "writeConfigFileLines::error while writing to " + self.__configFilePath
            return -1

        return 0

    def getInventory(self, action, argument=None, lshw=False):
        """\brief Prints testbed inventory information
           \param action (\c string) Either element, type, all, or alltypes. If element, argument2 will be the id and the
                                     command will print information on that element. If type, argument will be
                                     the type of element and the command will print the ids of all elements of the
                                     specified type. If all, the command will print all node ids on the testbed. If
                                     alltypes, the command will print all the available element types in the testbed.

           \param argument (\c string) If action is element, this will the element id. If action is type, this will be
                                       the element type. If action is all, this will be None
        """
        if (action == "all"):
            nodes = self.getNodes("all")
            infrastructures = self.getInfrastructures("all")

            print "Nodes:"
            print "----------------"
            for specificNodeTypes in nodes.values():
                for nodeID in specificNodeTypes.keys():
                    print nodeID

            print "\nInfrastructures:"
            print "----------------"
            for specifcInfrastructureTypes in infrastructures.values():
                for infrastructureID in specifcInfrastructureTypes.keys():
                    print infrastructureID
            return 0

        elif (action == "alltypes"):
            nodes = self.getNodes("all")
            infrastructures = self.getInfrastructures("all")

            print "Node types:"
            print "----------------"
            for nodeType in nodes.keys():
                print nodeType

            print "\nInfrastructure types:"
            print "----------------"
            for infrastructureType in infrastructures.keys():
                print infrastructureType

            return 0

        elif (action == "element"):
            if lshw:
                def handler(code, seq, sz,payload):
                    global return_payload
                    return_payload = str(payload)

                p = auxiliary.protocol.Protocol(None)

                HOST = DaemonLocations.autodetectDaemon[0]
                PORT = DaemonLocations.autodetectDaemon[1]

                p.open(HOST,PORT)
                method = "get_lshw"
                payload = pickle.dumps((argument))
                p.sendRequest(method,payload,handler)
                p.readAndProcess()
            
                for i in  pickle.loads(return_payload):
                    print i,
                print
                
                return 0
            else:
                nodes = self.getNodes("all")
                for specificNodeTypes in nodes.values():
                    for specificNode in specificNodeTypes.values():
                        if (specificNode.getNodeID() == argument):
                            print str(specificNode)
                            return 0

            # the id given is not that of a node, search through the infrastructure ids
            infrastructures = self.getInfrastructures("all")
            for specificInfrastructureTypes in infrastructures.values():
                for specificInfrastructure in specificInfrastructureTypes.values():
                    if (specificInfrastructure.getID() == argument):
                        print str(specificInfrastructure)
                        return 0

            print "id not found"
            return -1

        elif (action == "type"):
            nodes = self.getNodes(argument)

            if (nodes):
                for nodeID in nodes.keys():
                    print nodeID
            else:
                infrastructures = self.getInfrastructures(argument)
                if (infrastructures):
                    for infrastructureID in infrastructures.keys():
                        print infrastructureID
                else:
                    print "type does not exist on the testbed"
                    return -1
            return 0

    def getSensorReadings(self, targetNode, sensorType, printToScreen=True):
        """\brief Prints a node's various temperature sensors, if supported
        \param targetNode (\c string) The id of the node
        """
        nodes = self.getNodes("all", "all")
        for specificNodeTypes in nodes.values():
            for specificNode in specificNodeTypes.values():
                if (specificNode.getNodeID() == targetNode):
                    readings = None
                    serviceProcessor = None
                    nodeInstance = None
                    # sensor readings for computers are sometimes obtained
                    # through a service processor
                    if (specificNode.getNodeType() == "computer"):
                        for sp in self.getNodes("serviceprocessor").values():
                            if (sp.getNodeID() == specificNode.getSPNodeID()):
                                serviceProcessor = sp
                                break
                    try:
                        if serviceProcessor:
                            nodeInstance = \
                                self.getNodeInstance(serviceProcessor)
                        else:
                            nodeInstance = self.getNodeInstance(specificNode)
                        readings = None
                        if nodeInstance: 
                            readings = nodeInstance.getSensorReadings()
                        results = targetNode + ":\n"
                        if readings:
                            if not sensorType == "all":
                                sensors = readings[sensorType]
                                for sensor in sensors.keys():
                                    results = results + "\t" + sensor + \
                                              ": " + str(sensors[sensor]) + "\n"
                            else:
                                for sType in readings.values():
                                    for sensor in sType.keys():
                                        results = results + "\t" + sensor + \
                                              ": " + str(sType[sensor]) + "\n"
                    except Exception, inst:
                        print "Exception: " + str(inst)
                        pass

                    if (readings):
                        if (printToScreen):
                            print results
                        else:
                            return results
                    else:
                        string = targetNode + ": operation not supported"
                        if (printToScreen):
                            print string
                        else:
                            return string
                    return

    def pwr(self,username,cmd,args):
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)

        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.autodetectDaemon[0]
        HOST = "localhost"
        PORT = DaemonLocations.powerDaemon[1] 
        PORT = DaemonLocations.powerDaemon[1] + 100000

        p.open(HOST,PORT)
        method = cmd
        payload = pickle.dumps((username,args))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
        return pickle.loads(return_payload)

    def power(self, nodeid, action, port=None, preferSP=False):
        """\brief A wrapper for the powerSilent function that prints the
        results to the console. See powerSilent (below) for full description.
        \return (\c int)          0 on success, -1 otherwise
        """
        (status, results) = self.powerSilent(nodeid, action, port, preferSP)
        if results:
            print "%s: %s" % (nodeid, results)
        return status

    def powerSilent(self, nodeid, action, port=None, preferSP=False):
        """\brief Performs power actions on nodes on the testbed without 
        printing output to the console. When the port argument is set the node 
        specifies the powerswitch to use with that port number. This facilitates
        direct communication with the powerswitch for occasions when devices 
        need to be configured before they are added to hen.
        \param nodeid (\c string) The id of the node (or powerswitch) to perform
                                  the action on
        \param action (\c string) The action to perform: 
                                  {poweron, poweroff, restart, status}
        \param port   (\c string) Specifies a specific powerswitch port to 
                                  apply the action to. (default = None)
        \param preferSP (\c bool) Specifies whether a nodes' serviceprocessor
                                  should be used instead of through a power
                                  switch. (default = False)
        \return (\c tuple(int, string)) A tuple containing a return code and a 
                                        return description. Return codes are:
                                            -1 = Error
                                             0 = OK
        """
        valid_actions = ['poweron','poweroff','restart','status','info','softpoweron','softpoweroff','softrestart']
        valid_soft_actions = ['softpoweron','softpoweroff','softrestart']
        valid_hard_actions = ['poweron','poweroff','restart']
        if not action in valid_actions:
            return (-1, "Unknown action \"%s\" specified" % str(action))
        if (nodeid == "none"):
            return (-1, "Nodeid not specified")

        # Make sure user has node reserved
        #if (not self.__isSuperUser and self.__reservationsClient):
        #    payload = pickle.dumps((self.__username))
        #    devices = self.__reservationsClient.sendRequest("inuseby", payload)
        #    if (nodeid not in devices):
        #        return (-1, "you do not hold a reservation for this node, operation ignored")

        nodes = self.getNodes("all", "all")
        # Collect a dictionary of power switches, including normal switches
        # that are capable of PoE (power over ethernet), and serviceprocessors
        # that allow remote poweron/off
        powernodes = nodes["powerswitch"]
        switches = nodes["switch"]
        for key in switches.keys():
            if ((switches[key].getSingleAttribute("poe")) == "yes"):
                powernodes[key] = switches[key]
        serviceprocessors = nodes["serviceprocessor"]
        for key in serviceprocessors.keys():
            powernodes[key] = serviceprocessors[key]
        # Node to perform action on
        targetNode = None
        node = None
        # If user specified a port, then act directly on the specified node
        if (port != None) and powernodes.has_key(nodeid):
            targetNode = powernodes[nodeid]
            targetInstance = self.getNodeInstance(targetNode)
            if not targetInstance:
                return (-1, "Can't create powernode instance.")
            try:
                return self.__powerAction(targetInstance,action,port)
            except Exception, e:
                return (-1, "Exception thrown: %s" % str(e))

        # Normal operation from here onwards

        # find the node in question
        for nodeType in nodes.keys():
            if nodeType == "powerswitch":
                continue
            if nodes[nodeType].has_key(nodeid):
                node = nodes[nodeType][nodeid]
                break
            
        # check node requested exists
        if node == None:
            return (-1, "Unknown node "+str(nodeid))

        targets = [] # list of (targetid,port,error state,value)
        # get power nodes for device
        # use powerswitch for normal, and sp for soft commands
        if action not in valid_soft_actions:
            # use hardware power controllers
            try:
                for (powerNodeID,PowerNodePort) in node.getPowerNodes(): 
                    if powerNodeID and powernodes.has_key(powerNodeID):
                        targets.append((powernodes[str(powerNodeID)],str(PowerNodePort),None,None))
            except:
                return (-1, "Could not find power switch for node %s" % str(nodeid))
        else:
            # use service processor
            if node.getSPNodeID() and powernodes.has_key(node.getSPNodeID()):
                targets.append((powernodes[node.getSPNodeID()],"1",None,None))
                
        
        # check we have some targets.
        if len(targets) == 0:
            return (-1, "Could not find power switch for node %s" % str(nodeid))
        # find out if device has any more devices to power
        # this needs additions to correctly support peripherals
        # loop through peripherals for a device
        # check wether this device has control of the peripheral
        # if so add it to the targets list.
        log.debug("power targets "+str(targets))
        for i in range(0,len(targets)):
            log.debug("Trying target "+str(i))
            targetInstance = self.getNodeInstance(targets[i][0])
            
            if not targetInstance:
               (val,res) =  (-1, "Can't create powernode instance.")
            try:
                (val,res) = self.__powerAction(targetInstance,action,targets[i][1])
            except Exception, e:
                res = "Exception thrown: %s" % str(e)
                val = -1
            targets[i] = (targets[i][0],targets[i][1],val,res)

        # build the return string
        correct=""
        incorrect=""
        for target in targets:
            if target[2] == -1:
                if incorrect != "":
                    incorrect = incorrect + ", "
                incorrect = incorrect + str(target[3])
            else:
                if correct != "":
                    correct = correct + ", "
                correct = correct + str(target[3])
        # only return errors if there are errors
        if incorrect != "":
            return (-1,incorrect)
        return (0,correct)

    def __powerAction(self,targetInstance,action,port):
        if action == "poweron" or action == "softpoweron" :
            return targetInstance.poweron(port)
        elif action == "poweroff" or action == "softpoweroff":
            return targetInstance.poweroff(port)
        elif action == "restart" or action == "softrestart" :
            return targetInstance.restart(port)
        elif action == "status":
            return targetInstance.status(port)
        elif action == "info":
            return (0,str(targetInstance.getNodeID())+" "+str(port))
        return (-1, "Unknown action %s" % str(action))
        
    def console(self, nodeID,action,baud,port = None):
        """\brief Connect to the terminal server and get a console for the specified nodeID.
                  All nodes are searched for the specified targert. Then the serial device to which
                  the target node is connected is looked up together with the correct port.
                  A SSH connection is used to connect to the specified target.
                  Note that serial and serviceprocessor devices are not supported.
        \param nodeID (\c string) The id of the node to connect to
        \port port (\c string) The port number on the terminal server if connecting directly.
        \return (\c int) 0 if successful, -1 otherwise
        """
        nodes = self.getNodes("all","all")
        serialDeviceTarget = None
        serialDevicePort = -1
        targetFound = "no"

        if (action == ""):
            if (port == None ):
                print "Trying to get the console for " + nodeID + "..."
            else:
                print "Trying to get the console on " + nodeID + " on port " + port
            print "This may take a few seconds. If you don't see the login prompt"
            print "try to hit <return> a few times until you see it."
            print "To escape: Newline followed by ~~."

        if (port != None):
            serialDeviceTarget = nodeID
            serialDevicePort = port
            targetFound = "yes"
        else:
            # Search all nodes for the target node
            for node in nodes.keys():
                specificNodes = nodes[node]
                for specificNode in specificNodes:
                    currentHenNode = specificNodes[specificNode]
                    if currentHenNode.getNodeID() == nodeID:
                        targetFound = "yes"
                        # Exclude serial and serviceprocessor devices
                        #if ((currentHenNode.getNodeType() == "serial") or (currentHenNode.getNodeType() == "serviceprocessor")):
                        #    print "The node you requested (" + nodeID + ") is not supported!\n"
                        #    return -1
                        # Get the serial device that is connected to our target and the correct port
                        serialDeviceTarget = currentHenNode.getSerialNodeID()
                        serialDevicePort = currentHenNode.getSerialNodePort()

        # Requested target could not be found -> exit
        if (targetFound == "no"):
            print "The node you requested (" + nodeID + ") could not be found!\n"
            return -1

        # Search all nodes for the serial device that is connected to our target
        targetFound = "no"
        for node in nodes.keys():
            specificNodes = nodes[node]
            for specificNode in specificNodes:
                currentHenNode = specificNodes[specificNode]
                if currentHenNode.getNodeID() == serialDeviceTarget:
                    targetFound = "yes"
                    # Get an instance of the device and connect to it via ssh
                    serialDeviceInstance = self.getNodeInstance(currentHenNode)
                    if not serialDeviceInstance:
                        print "Could not create instance of node %s" % \
                                                        str(serialDeviceTarget)
                        return -1
                        
                    serialDevicePort = int(serialDevicePort)
                    serialDeviceInstance.setSSHCommand(self.__configFile.get('CONSOLE', 'SSH_COMMAND'))
                    
                    if action == "getbaud":
                        serialDeviceInstance.getBaudRate(serialDevicePort)
                    elif action == "setbaud":
                    	if baud in ["2400","4800","9600","19200","38400","57600","115200"]:
                        	serialDeviceInstance.setBaudRate(serialDevicePort,baud)
                        else:
                        	print "Please choose a valid baud rate (2400, 4800, 9600, 19200, 38400, 57600, 115200)"
                    else:
                        serialDeviceInstance.connect(serialDevicePort)
        # No device could be found -> exit
        if (targetFound == "no"):
            print "Could not connect, no serial device found!\n"
            return -1

        return 0

    def elementStatus(self, action, theID, elementType, newStatus=None):
        """\brief Gets and sets the status of an element in the testbed
        \param action (\c string) Either 'get' or 'set'.
        \param theID (\c string) The id of the element to get or set the status of
        \param elementType (\c string) Either experiment or physical
        \param newStatus (\c string) If action is 'set', denotes the new status of the element
        \return (\c int) 0 upon success, -1 otherwise
        """
        if (elementType == "physical"):
            nodes = self.getNodes("all", "all")
            infrastructures = self.getInfrastructures("all", "all")

            if (action == "set"):
                self.parser.changePhysicalEntryStatus(theID, newStatus)
                print "status of " + str(theID) + " set to: " + str(newStatus)
                return 0

            elif (action == "get"):
                for specificNodeTypes in nodes.values():
                    for nodeID in specificNodeTypes.keys():
                        if (nodeID == theID):
                            print str(nodeID) + ": " + str(specificNodeTypes[nodeID].getStatus())
                            return 0

                for specificInfrastructureTypes in infrastructures.values():
                    for infrastructureID in specificInfrastructureTypes.keys():
                        if (infrastructureID == theID):
                            print str(infrastructureID) + ": " + str(specificInfrastructureTypes[infrastructureID].getStatus())
                            return 0
            else:
                print "elementStatus: unrecognized action: " + str(action)
                return -1

            print "element " + str(theID) + " not found in testbed"
            return -1

        elif (elementType == "experiment"):

            if (action == "set"):
                self.parser.changeExperimentEntryStatus(theID, newStatus)
                print "status of " + str(theID) + " set to: " + str(newStatus)
                return 0

            elif (action == "get"):
                experiments = self.getExperimentEntries("all")
                for key in experiments:
                    if (theID == key):
                        print str(theID) + ": " + str(experiments[key].getStatus())
                        return 0

            else:
                print "elementStatus: unrecognized action: " + str(action)
                return -1

            print "experiment " + str(theID) + " not found in testbed"
            return -1

        else:
            print "elementStatus: invalid element type given: " + str(elementType)
            return -1


    def dhcpServer(self, action):
        """\brief Performs action on the dhcp server. It retrieves the path and name of the server's
                  control script from the config file. Possible actions are start, stop, restart and
                  create, which creates the dhcpd configuration file from the hen database (the xml
                  files)
        \param action (\c string) Either start, stop, restart or create
        \return (\c int) 0 if successful, -1 otherwise
        """
        if (action == "create"):
            self.__writeDHCPConfigFile()
            print "wrote " + self.__configFile.get('DHCP', 'CONFIG_FILE_PATH')
            return

        serverControlScript = self.__configFile.get('DHCP', 'SERVER_CONTROL_SCRIPT')
        print str(serverControlScript) + " " + action
        returnCode = commands.getstatusoutput(str(serverControlScript) + " " + action)[0]
        if (returnCode != 0):
            print "error while performing " + action + " on dhcpd, error code: " + str(returnCode)
            print "(did you run the command with su privileges?)"
            return -1
        else:
            print "successfully performed the following action on dhcpd: " + action
            return 0

    def dnsServer(self, action):
        """\brief Performs action on the dns server. Possible actions are start, stop, restart and
                  create, which creates the named configuration files from the hen database (the xml
                  files). The function gets the path to the named.conf file from the hen config file
        \param action (\c string) Either start, stop, restart or create
        \return (\c int) 0 if successful, -1 otherwise
        """
        if (action == "restart"):
            pid = (commands.getstatusoutput("ps axf | grep named | awk '{print $1}'")[1].splitlines())[0]
            cmd = "kill -s SIGHUP " + pid
            returnCode = commands.getstatusoutput(cmd)[0]
            if (returnCode != 0):
                print "error while restarting dns server, error code: " + str(returnCode)
                print "(did you run the command with su privileges?)"
                return -1
            print "restarted dns server"
        elif (action == "start"):
            returnCode = commands.getstatusoutput("named -c " + self.__configFile.get('DNS', 'NAMED_CONF_PATH'))[0]
            if (returnCode != 0):
                print "error while starting dns server, error code: " + str(returnCode)
                print "(did you run the command with su privileges?)"
                return -1
            print "started dns server"
        elif (action == "stop"):
            pid = (commands.getstatusoutput("ps axf | grep named | awk '{print $1}'")[1].splitlines())[0]
            cmd = "kill " + pid
            returnCode = commands.getstatusoutput(cmd)[0]
            if (returnCode != 0):
                print "error while stopping dns server, error code: " + str(returnCode)
                print "(did you run the command with su privileges?)"
                return -1
            print "stopped dns server"
        elif (action == "create"):
            self.__writeDNSConfigFiles()
            print "wrote dns config files to " + self.__configFile.get('DNS', 'CONFIG_FILES_PATH')

        return 0

    def redetect(self,nodeID):
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)

        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.autodetectDaemon[0]
        #HOST = "localhost"
        PORT = DaemonLocations.autodetectDaemon[1] 
        #PORT = DaemonLocations.autodetectDaemon[1] + 100000

        p.open(HOST,PORT)
        method = "redetect_target"
        payload = pickle.dumps((nodeID))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
        print pickle.loads(return_payload)

    def redetectComputerNode(self, nodeID):
        """\brief Redetects a computer node's hardware
        \param nodeID (\c string) The id of the node to redetect
        """
        # First we need to boot the node so that it can auto-detect its own hardware; to do so
        # we need to create symlinks to netboot the auto-detect filesystem and kernel
        if (self.__configNetboot.createAutodetectNetbootInfo(nodeID) == -1):
            print "error while creating symbolic links for node " + nodeID
            return -1

        # Now reboot the new node up so it can auto-detect its hardware and update etc/physical/nodeID.xml
        if (self.power(nodeID, "restart") == -1):
            print "error while restarting node " + nodeID
            return -1

        # Wait until etc/physical/nodeID.xml has been updated before removing auto-detect symlinks and powering
        # node off
        attributesBeforeUpdate = commands.getstatusoutput("ls -lT " + self.__physicalPath + "/" + nodeID + ".xml")[1]
        attributesAfterUpdate = attributesBeforeUpdate
        sleepTime = 20
        while(attributesBeforeUpdate == attributesAfterUpdate):
            print "waiting for autodetect to finish (probing every " + str(sleepTime) + " seconds)..."
            time.sleep(sleepTime)
            attributesAfterUpdate = commands.getstatusoutput("ls -lT " + self.__physicalPath + "/" + nodeID + ".xml")[1]

        # Set the permissions of the configuration file just written by the node
        filename = self.__physicalPath + "/" + nodeID + ".xml"
        os.system("chgrp " + self.__testbedGroup + " " + filename)
        os.system("chmod 775 " + filename)

        if (self.__configNetboot.removeNetbootInfo(nodeID) == -1):
            print "error while removing autodetect symbolic links for node " + nodeID
            return -1

        # Power node off
        if (self.power(nodeID, "poweroff") == -1):
            print "error while powering off node " + nodeID
            return -1

        print "redetected " + nodeID

        return 0

    def getUserFiles(self, username, fileNodeType):
        """\brief Gets all files of a specific type for the given user. Only files that are not already part of
                  the testbed are returned.
        \param username (\c string) The login id of the user whose files are to be returned
        \param fileNodeType (\c string) The type of file node to search for
        \return (\list of string) The file names (not path included)
        """
        path = self.__henBaseExportPath + fileNodeType + "s/" + username

        # Retrieve the files of this user that are already part of the testbed
        userFiles = []
        fileNodes = self.getFileNodes(fileNodeType)
        for fileNode in fileNodes.values():
            if (fileNode.getOwner() == username):
                userFiles.append(fileNode.getPath())

        filteredFiles = []
        for theFile in os.listdir(path):
            theFile = self.__henBaseExportPath + fileNodeType + "s/" + username + "/" + theFile
            if (theFile not in userFiles):
                filteredFiles.append(theFile)

        return filteredFiles

#######################################################################################################
#
#  EDIT FUNCTIONS
#
#######################################################################################################
    def elementEdit(self, elementID, parameters, attributes):
        """\brief Edits an element on the testbed. The function figures out whether the element is a node,
                  an infrastructure or a fileNode and calls the appropriate function
        \param elementID (\c string) The id of the element to edit
        \param parameters (\c dictionary) A dictionary whose keys are the parameters' names and whose values are the parameters' values
        \param attributes (\c dictionary) A dictionary whose keys are the attributes' names and whose values are the attributes' values
        \return (\c tuple of int, string) The int is 0 if successful, -1 otherwise. The string is the id of the element edited if
                                          successful, an error message otherwise
        """
        superClassName = self.__findSuperClassName(elementID)

        if (not superClassName):
            return (-1, "HenParser::elementEdit: element not in testbed " + str(elementID))

        return getattr(self, superClassName + "Edit")(elementID, parameters, attributes)

    def nodeEdit(self, nodeID, parameters, attributes):
        """\brief Edits a node object.
        \param nodeID (\c string) The id of the object to edit
        \param parameters (\c dictionary) A dictionary whose keys are the parameters' names and whose values are the parameters' values
        \param attributes (\c dictionary) A dictionary whose keys are the attributes' names and whose values are the attributes' values
        \return (\c tuple of int,string) The int is 0 upon success, -1 otherwise; the string is a message regarding the outcome of the operation
        """
        # Retrieve the existing node
        theNode = None
        nodes = self.getNodes("all", "all")
        for nodeTypes in nodes.values():
            for node in nodeTypes.values():
                if (node.getNodeID() == nodeID):
                    theNode = node
        physicalLocation = theNode.getPhysicalLocation()

        if (not theNode):
            return (-1, "HenManager::nodeEdit: node " + str(nodeID) + " does not exist in the testbed")

        # Change it to the new values
        for parameterName in parameters.keys():

            # Handle general parameters
            try:
                getattr(theNode, 'set' + parameterName[0:1].upper() + parameterName[1:])(parameters[parameterName])
                continue
            except:
                pass

            # Handle physical location
            try:
                getattr(physicalLocation, 'set' + parameterName[0:1].upper() + parameterName[1:])(parameters[parameterName])
                continue
            except:
                pass

            # Handle interfaces
            if (parameterName == "externalMACAddress"):
                self.__editInterface(theNode, "external", "mac", parameters[parameterName])
                continue
            elif (parameterName == "externalIP"):
                self.__editInterface(theNode, "external", "ip", parameters[parameterName])
                continue
            elif (parameterName == "externalSubnet"):
                self.__editInterface(theNode, "external", "subnet", parameters[parameterName])
                continue

            # Handle user management
            if ( (parameterName == "username") or (parameterName == "password") ):
                self.__editUsers(theNode, parameterName, parameters[parameterName])
                continue

        # Handle attributes
        theNode.setAttributes(attributes)

        # This will overwrite the previous entry
        returnValue = self.parser.writeNodePhysicalFile(theNode)
        if (returnValue != 0):
            print "HenManager::nodeEdit: error while editing " + str(nodeID)
            return (-1, "HenManager::nodeEdit: error while editing " + str(nodeID))
        else:
            print "HenManager::nodeEdit: successfully edited " + str(nodeID)
            return (0, "HenManager::nodeEdit: successfully edited " + str(nodeID))

    def infrastructureEdit(self, infrastructureID, parameters, attributes):
        """\brief Edits an infrastructure object.
        \param infrastructureID (\c string) The id of the object to edit
        \param parameters (\c dictionary) A dictionary whose keys are the parameters' names and whose values are the parameters' values
        \param attributes (\c dictionary) A dictionary whose keys are the attributes' names and whose values are the attributes' values
        \return (\c tuple of int,string) The int is 0 upon success, -1 otherwise; the string is a message regarding the outcome of the operation
        """
        # Retrieve the existing infrastructure
        theInfrastructure = None
        infrastructures = self.getInfrastructures("all", "all")
        for infrastructureTypes in infrastructures.values():
            for infrastructure in infrastructureTypes.values():
                if (infrastructure.getID() == infrastructureID):
                    theInfrastructure = infrastructure
        physicalSize = theInfrastructure.getPhysicalSize()

        if (not theInfrastructure):
            return (-1, "HenManager::infrastructureEdit: infrastructure " + str(infrastructureID) + " does not exist in the testbed")

        # Change it to the new values
        for parameterName in parameters.keys():

            # Handle general parameters
            try:
                getattr(theInfrastructure, 'set' + parameterName[0:1].upper() + parameterName[1:])(parameters[parameterName])
                continue
            except:
                pass

            # Handle physical size
            try:
                getattr(physicalSize, 'set' + parameterName[0:1].upper() + parameterName[1:])(parameters[parameterName])
                continue
            except:
                pass

        # Handle attributes
        theInfrastructure.setAttributes(attributes)

        # This will overwrite the previous entry
        returnValue = self.parser.writeInfrastructurePhysicalFile(theInfrastructure)
        if (returnValue != 0):
            return (-1, "HenManager::infrastructureEdit: error while editing " + str(infrastructureID))
        else:
            return (0, "HenManager::infrastructureEdit: successfully edited " + str(infrastructureID))

    def fileNodeEdit(self, fileNodeID, parameters, attributes):
        """\brief Edits a file node object.
        \param fileNodeID (\c string) The id of the object to edit
        \param parameters (\c dictionary) A dictionary whose keys are the parameters' names and whose values are the parameters' values
        \param attributes (\c dictionary) A dictionary whose keys are the attributes' names and whose values are the attributes' values
        \return (\c tuple of int,string) The int is 0 upon success, -1 otherwise; the string is a message regarding the outcome of the operation
        """
        # Retrieve the existing file node
        theFileNode = None
        fileNodes = self.getFileNodes("all", "all")
        for fileNodeTypeDictionary in fileNodes.values():
            for fileNode in fileNodeTypeDictionary.values():
                if (fileNode.getID() == fileNodeID):
                    theFileNode = fileNode

        if (not theFileNode):
            return (-1, "HenManager::fileNodeEdit: file node " + str(fileNodeID) + " does not exist in the testbed")

        # Change it to the new values
        for parameterName in parameters.keys():

            # Handle general parameters
            try:
                getattr(theFileNode, 'set' + parameterName[0:1].upper() + parameterName[1:])(parameters[parameterName])
                continue
            except:
                pass

            # Handle user management
            if ( (parameterName == "username") or (parameterName == "password") ):
                try:
                    self.__editUserManagement(theFileNode, parameterName, parameters[parameterName])
                    continue
                except:
                    pass

        # Handle attributes
        theFileNode.setAttributes(attributes)

        # This will overwrite the previous entry
        returnValue = self.parser.writeFileNodeTestbedFile(theFileNode)
        if (returnValue != 0):
            return (-1, "HenManager::fileNodeEdit: error while editing " + str(fileNodeID))
        else:
            return (0, "HenManager::fileNodeEdit: edited " + str(fileNodeID))

    def __editUsers(self, theElement, parameterName, parameterValue):
        """\brief Sets the username or password property of a node's user management object
        \param theElement (\c Node) The element containing the user management object to edit
        \param parameterName (\c string) Either username or password
        \param parameterValue (\c string) The value of the given parameter
        \return (\c int) 0 if successful, -1 if the parameterName is invalid
        """
        if (not theElement.getUsers()):
            userManagementList = []
            userManagementList.append(UserManagement(None, None))
            theElement.setUserManagement(userManagementList)

        if (parameterName == "username"):
            theElement.getUsers()[0].setUsername(parameterValue)
        elif (parameterName == "password"):
            theElement.getUsers()[0].setPassword(parameterValue)
        else:
            return -1

        return 0

    def __editUserManagement(self, theElement, parameterName, parameterValue):
        """\brief Sets the username or password property of an element's user management object
        \param theElement (\c Node or Infrastructure or FileNode) The element containing the user management object to edit
        \param parameterName (\c string) Either username or password
        \param parameterValue (\c string) The value of the given parameter
        \return (\c int) 0 if successful, -1 if the parameterName is invalid
        """
        if (not theElement.getUserManagement()):
            userManagementList = []
            userManagementList.append(UserManagement(None, None))
            theElement.setUserManagement(userManagementList)

        if (parameterName == "username"):
            theElement.getUserManagement()[0].setUsername(parameterValue)
        elif (parameterName == "password"):
            theElement.getUserManagement()[0].setPassword(parameterValue)
        else:
            return -1

        return 0

    def __editInterface(self, theElement, interfaceType, parameterName, parameterValue):
        """\brief Edits an attribute of an interface on a node
        \param theElement (\c Node) The node whose interface to edit
        \param interfaceType (\c string) Either external, management, infrastructure or experimental
        \param parameterName (\c string) Either mac, ip or subnet
        \param parameterValue (\c string) The value for the parameter
        \return (\c int) 0 if successful, -1 if the parameterName is invalid
        """
        if (not theElement.getInterfaces()):
            interfacesDict = {}
            interfacesDict[interfaceType] = None
            theElement.setInterfaces(interfacesDict)

        if (not theElement.getInterfaces(interfaceType)):
            interfaces = []
            interfaces.append(Interface(None, None, None, None, None, None, interfaceType))
            theElement.getInterfaces()[interfaceType] = interfaces

        if (parameterName == "mac"):
            theElement.getInterfaces(interfaceType)[0].setMAC(parameterValue)
        elif (parameterName == "ip"):
            theElement.getInterfaces(interfaceType)[0].setIP(parameterValue)
        elif (parameterName == "subnet"):
            theElement.getInterfaces(interfaceType)[0].setSubnet(parameterValue)
        else:
            return -1

        return 0

#######################################################################################################
#
#  DELETE FUNCTIONS
#
#######################################################################################################
    def elementDelete(self, elementID, isManager=True):
        """\brief Deletes an element on the testbed. The function figures out whether the element is a node,
                  an infrastructure or a fileNode and calls the appropriate function
        \param elementID (\c string) The id of the element to remove
        \return (\c tuple of int, string) The int is 0 if successful, -1 otherwise. The string is the id of the element removed if
                                          successful, an error message otherwise
        """
        superClassName = self.__findSuperClassName(elementID)

        if (not superClassName):
            return (-1, "HenParser::elementDelete: element not in testbed " + str(elementID))

        if (isManager and superClassName == "fileNode"):
            superClassName = "fileNodeManager"

        return getattr(self, superClassName + "Delete")(elementID)

    def nodeDelete(self, nodeID):
        """\brief Removes a node from the testbed
        \param nodeID (\c string) The id of the node to remove
        \return (\c tuple of int, string) The int is 0 if successful, -1 otherwise. The string is the id of the element removed if
                                          successful, an error message otherwise
        """
        # Retrieve the node
        theNode = None
        nodes = self.getNodes("all", "all")
        for nodeTypes in nodes.values():
            for node in nodeTypes.values():
                if (node.getNodeID() == nodeID):
                    theNode = node

        if (not theNode):
            return (-1, "HenManager::nodeDelete: node " + str(nodeID) + " does not exist in the testbed")

        # Begin by powering off the node, if it is connected to a power switch
        if (theNode.getPowerNodeID()):
            if (self.power(nodeID, "poweroff") == -1):
                return (-1, "HenParser::nodeDelete: error while powering off node " + str(nodeID))

        # If it's a computer, remove its symlinks directory
        if (theNode.getNodeType() == "computer"):
            if (self.__configNetboot.removeNetbootInfo(nodeID, 1) == -1):
                print "HenParser::computerNodeDelete: error while removing netboot directory for node " + nodeID
                return (-1, "HenParser::computerNodeDelete: error while removing netboot directory for node " + str(nodeID))

        # FROM SWITCH DELETE
        # Search for orphaned nodes
        #redetectNodes = []
        #nodes = self.getNodes("all")
        #for specificNodeDictionary in nodes.values():
        #    for node in specificNodeDictionary.values():
        #        # Inspect the node's interfaces, if any
        #        interfaces = node.getInterfaces()
        #        if (interfaces != None):
        #            for interfaceList in interfaces.values():
        #                for interface in interfaceList:
        #                    if (interface.getSwitch() == nodeID):
        #                        if (node.getNodeID() not in redetectNodes):
        #                            redetectNodes.append(node.getNodeID())
        #                        print node.getNodeID() + " has orphaned interface " + interface.getMAC() + " previously connected to port " + \
        #                              interface.getPort() + " of " + nodeID
        #
        #if (len(redetectNodes) != 0):
        #    print "\nThe following should be redetected:"
        #    for node in redetectNodes:
        #        print node

        # Remove its xml description file as well as its dns and dhcp entries
        return self.__deleteNode(nodeID)

    def infrastructureDelete(self, infrastructureID):
        """\brief Removes an infrastructure element from the testbed
        \param infrastructureID (\c string) The id of the infrastructure element to remove
        \return (\c tuple of int, string) A return code and the id of the element deleted
        """
        self.parser.deletePhysicalEntry(infrastructureID)
        os.remove(self.__physicalPath + "/" + infrastructureID + ".xml")
        return (0, str(infrastructureID))

    def fileNodeManagerDelete(self, fileNodeID):
        """\brief Managers only run this function to delete a file node. This function not only deletes its XML description
                  file but also the actual file using rm -rf, so treat it with care.
        \param fileNodeID (\c string) The id of the file node to delete
        """
        fileNodes = self.getFileNodes("all", "all")

        path = None
        for fileNodeTypeDictionary in fileNodes.values():
            for fileNode in fileNodeTypeDictionary.values():
                if (fileNode.getID() == fileNodeID):
                    path = fileNode.getPath()
                    break

        filename = None
        for fileEntry in self.parser.parseTestbedFileEntries():
            filename = fileEntry.getFilename()
            if (filename.find(fileNodeID) != -1):
                break

        returnValue = 0
        # Remove the file's entry from topology.xml
        returnValue += self.parser.deleteTestbedFileEntry(fileNodeID)
        # Remove the file's XML description file
        returnValue = commands.getstatusoutput("rm " + str(filename))[0]
        # Remove the actual file
        returnValue += commands.getstatusoutput("rm -rf " + str(path))[0]

        if (returnValue != 0):
            return (-1, "HenParser::fileNodeManagerDelete: error while deleting " + str(fileNodeID))
        else:
            return (0, "HenParser::fileNodeManagerDelete: deleted " + str(fileNodeID))

    def fileNodeDelete(self, fileNodeID):
        """\brief Changes the status of a file node to 'deleted', this function is meant for regular users
        \param fileNodeID (\c string) The id of the file node to delete
        """
        fileNodes = self.getFileNodes("all", "all")

        returnValue = self.parser.changeTestbedFileEntryStatus(fileNodeID, "deleted")

        if (returnValue != 0):
            return (-1, "HenParser::fileNodeDelete: error while deleting " + str(fileNodeID))
        else:
            return (0, "HenParser::fileNodeDelete: deleted " + str(fileNodeID))

#######################################################################################################
#
#  CREATE FUNCTIONS
#
#######################################################################################################
    def fileNodeCreate(self, fileNodeType, owner, path, architecture, osType, version, mustClone, description, attributes=None, username=None, password=None, status="operational"):
        """\brief Adds a file node object to the testbed
        \param fileNodeType (\c string) The type of the FileNode to create
        \param owner (\c string) The login id of the file's owner
        \param path (\c string) The full path to the file
        \param architecture (\c string) The file's processor architecture
        \param osType (\c string) The file's OS type (linux, freebsd, debian, etc)
        \param version (\c string) The file's version
        \param mustClone (\c string) Whether a file is read only and must be copied before writing to it (yes or no)
        \param description (\c string) The file's description
        \param attributes (\c dictionary) The file's attributes (see henParser.parseAttributes)
        \param username (\c string) The file's login (in case it is a filesystem)
        \param password (\c string) The file's password (in case it is a filesystem)
        \param status (\c string) The file node's status
        \return (\c tuple of int, string) int:0 if successful, -1 otherwise. string: new file id if successful, None otherwise
        """
        # Check that the file is not already part of the testbed
        fileNodes = self.getFileNodes("all")
        for fileNodeTypeDictionary in fileNodes.values():
            for fileNode in fileNodeTypeDictionary.values():
                if (fileNode.getPath() == path):
                    print "file already in testbed"
                    return (-1, None)

        # Check that the file is there and generate its MD5 signature
        md5Signature = generateMD5Signature(path)
        if (md5Signature == -1):
            print "file missing"
            return (-1, None)

        # Get the next available id based on the type of the file node
        nextFileNodeID = self.__getNextFileNodeID(fileNodeType, self.__configFile.get('MAIN', 'TESTBEDFILE_' +  fileNodeType.upper() + '_MINIMUM_NUMBER'))

        # Dynamically import module and create object of the right type
        moduleName = "auxiliary.hen"
        className = fileNodeType[0:1].upper() + fileNodeType[1:] + "FileNode"
        module = __import__(moduleName, globals(), locals(), [className])
        if (username != " " and password != " "):
            userManagement = UserManagement(username, password)
            fileNode = vars(module)[className](nextFileNodeID, path, architecture, osType, version, mustClone, attributes, md5Signature, description, status, owner, userManagement)
        else:
            fileNode = vars(module)[className](nextFileNodeID, path, architecture, osType, version, mustClone, attributes, md5Signature, description, status, owner)

        # Write the file node object
        returnValue = self.parser.writeFileNodeTestbedFile(fileNode)
        returnValue += self.parser.writeTestbedFileEntry("filenode", nextFileNodeID, fileNodeType)

        if (returnValue != 0):
            print "error while creating " + nextFileNodeID
            return (-1, None)
        else:
            print "created " + nextFileNodeID
            return (0, nextFileNodeID)

    def serverNodeCreate(self, rackName, serialID, serialPort, managementMAC, infrastructureMAC, externalMAC, externalIP, externalSubnet, attributes, building=None, floor=None, room=None, rackRow=None, rackStartUnit=None, rackEndUnit=None, rackPosition=None, powerID=None, powerPortID=None, serviceProcessorID=None, status="operational", vendor="", model=""):
        """\brief Adds a server node to the testbed. To do so this it checks that the given mac address
                  does not conflict with any already on the testbed; it then  derives an id for the node
                  and an ip address for its management and infrastructure interfaces; it writes a prelimary xml topology file
                  for the node and adds an entry to the testbed's main topology file; it creates dns and
                  dhcp configuration files and restarts these servers; the function checks that
                  the given power switch, serial and service processor ids exist on the testbed.
        \param rackName (\c string) The node's rack name
        \param serialID (\c string) The id of the serial node that the node is connected to
        \param serialPort (\c string) The port of the serial node that the node is connected to
        \param managementMAC (\c string) The mac address of the node's management interface
        \param infrastructureMAC (\c string) The mac address of the node's infrastructure interface
        \param externalMAC (\c string) The mac address of the node's external interface
        \param externalIP (\c string) The ip address of the node's external interface
        \param externalSubnet (\c string) The subnet address of the node's external interface
        \param attributes (\c dictionary) A dictionary whose keys are attribute names and whose values are attribute values
        \param building (\c string) The building that the node is in
        \param floor (\c string) The floor that the node is in
        \param room (\c string) The room that the node is in
        \param rackRow (\c string) The number of the row that the node is in
        \param rackStartUnit (\c string) The rack start unit for the node
        \param rackEndUnit (\c string) The rack end unit for the node
        \param rackPosition (\c string) One of front, rear, or both, describing the node's position in the rack
        \param powerID (\c string) The id of the power switch that the node is connected to
        \param powerPortID (\c string) The port of the power switch that the node is connected to
        \param serviceProcessorID (\c string) The id of the service processor that the node is connected to, if any
        \param status (\c string) The status of the node
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \return (\c tuple of int,string) int is 0 if successful, -1 otherwise. string gives an error's description or the
                                         the new node's id if successful
        """
        # Initialize variables
        minimumInfrastructureIP = self.__configFile.get('MAIN', 'INFRASTRUCTURE_MINIMUM_IP')
        infrastructureSubnet = self.__configFile.get('MAIN', 'INFRASTRUCTURE_SUBNET_MASK')
        minimumExperimentalIP = self.__configFile.get('MAIN', 'EXPERIMENTAL_MINIMUM_IP')
        experimentalSubnet = self.__configFile.get('MAIN', 'EXPERIMENTAL_SUBNET_MASK')

        if (self.__isMACAddressInTestbed(managementMAC) == True or self.__isMACAddressInTestbed(infrastructureMAC) == True):
            print "Given mac address already belongs to a node in the testbed"
            #return -1
        # Now derive the new node's id and ip address from the physical topology file.
        # Second, create the initial xml description file for the new node with the given
        # parameters. Finally, add a new node entry to the main physical topology file.
        if (serialID != "none" and (not(self.__isNodeInTestbed(serialID)))):
            print "No serial node with the given id exists on the testbed: " + serialID

        nextNodeID = self.__getNextNodeID("server", self.__configFile.get('MAIN', 'SERVER_NODE_MINIMUM_NUMBER'))
        nextExperimentalIPAddress = self.__getNextIPAddress(self.__henExperimentalBaseAddress, minimumExperimentalIP)
        nextInfrastructureIPAddress = self.__getNextIPAddress(self.__henInfrastructureBaseAddress, minimumInfrastructureIP)

        managementInterfaces = []
        infrastructureInterfaces = []
        externalInterfaces = []
        managementInterfaces.append(Interface(managementMAC, nextExperimentalIPAddress, experimentalSubnet, \
                                              None, None, None, "management"))
        infrastructureInterfaces.append(Interface(infrastructureMAC, nextInfrastructureIPAddress, infrastructureSubnet, \
                                                  None, None, None, "infrastructure"))
        externalInterfaces.append(Interface(externalMAC, externalIP, externalSubnet, None, None, None, "external"))

        physicalLocation = PhysicalLocation(building, floor, room, rackRow, rackName, rackStartUnit, rackEndUnit, None, rackPosition)
        serverNode = ServerNode()
        serverNode.setNodeID(nextNodeID)
        serverNode.setNodeType("server")
        serverNode.setVendor(vendor)
        serverNode.setModel(model)
        serverNode.setInterfaces(managementInterfaces, "management")
        serverNode.setInterfaces(infrastructureInterfaces, "infrastructure")
        serverNode.setInterfaces(externalInterfaces, "external")
        serverNode.setSerialNodeID(serialID)
        serverNode.setSerialNodePort(serialPort)
        serverNode.setPhysicalLocation(physicalLocation)
        serverNode.setNetbootable("no")
        serverNode.setInfrastructure("yes")
        serverNode.setSPNodeID(serviceProcessorID)
        serverNode.setPowerNodeID(powerID)
        serverNode.setPowerNodePort(powerPortID)

        serverNode.setAttributes(attributes)
        self.parser.writeNodePhysicalFile(serverNode)
        self.parser.writePhysicalEntry("node", nextNodeID, "server")

        # Generate current dhcp files from XML files and restart dhcp server
        if (self.dhcpServer("create") == -1):
            print "HenParser::serverNodeCreate: error while creating dhcp configuration"
            return (-1, "HenParser::serverNodeCreate: error while creating dhcp configuration")
        if (self.dhcpServer("restart") == -1):
            print "HenParser::serverNodeCreate: error while restarting dhcp server"
            return (-1, "HenParser::serverNodeCreate: error while restarting dhcp server")

        # Generate current dns files from XML files and restart dns server
        if (self.dnsServer("create") == -1):
            print "HenParser::serverNodeCreate: error while creating dns configuration"
            return (-1, "HenParser::serverNodeCreate: error while creating dns configuration")
        if (self.dnsServer("restart") == -1):
            print "HenParser::serverNodeCreate: error while restarting dns server"
            return (-1, "HenParser::serverNodeCreate: error while restarting dns server")

        print "HenParser::serverNodeCreate: created " + nextNodeID + ", you will need to restart it so that it will dhcp"
        return (0, str(nextNodeID))

    def computerNodeCreate(self, netbootable, infrastructure, rackName, macAddress, powerID, powerPort, serialID, serialPort, serviceProcessorID, attributes, building=None, floor=None, room=None, rackRow=None, rackStartUnit=None, rackEndUnit=None, rackPosition=None, status="operational", vendor="", model=""):
        """\brief Adds a computer node to the testbed. To do so this it checks that the given mac address
                  does not conflict with any already on the testbed; it then  derives an id for the node
                  and an ip address for its management interface; it writes a prelimary xml topology file
                  for the node and adds an entry to the testbed's main topology file; it creates dns and
                  dhcp configuration files and restarts these servers; it boots the node so that it will
                  autodetect its hardware and complete the prelimary xml topology; finally it removes the
                  symbolic links used to boot the node and powers the node off. The function checks that
                  the given power switch, serial and service processor ids exist on the testbed.
        \param netbootable (\c string) Either yes or no
        \param infrastructure (\c string) Either yes or no
        \param rackName (\c string) The node's physical location
        \param macAddress (\c string) The mac address of the node's management interface
        \param powerID (\c string) The id of the power switch that the node is connected to
        \param powerPort (\c string) The port of the power switch that the node is connected to
        \param serialID (\c string) The id of the serial node that the node is connected to
        \param serialPort (\c string) The port of the serial node that the node is connected to
        \param serviceProcessorID (\c string) The id of the service processor that the node is connected to, if any
        \param attributes (\c dictionary) A dictionary whose keys are attribute names and whose values are attribute values
        \param building (\c string) The building that the node is in
        \param floor (\c string) The floor that the node is in
        \param room (\c string) The room that the node is in
        \param rackRow (\c string) The number of the row that the node is in
        \param rackStartUnit (\c string) The rack start unit for the node
        \param rackEndUnit (\c string) The rack end unit for the node
        \param rackPosition (\c string) One of front, rear, or both, describing the node's position in the rack
        \param status (\c string) The status of the node
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \return (\c tuple of int,string) int is 0 if successful, -1 otherwise. string gives an error's description or the
                                         the new node's id if successful
        """
        # Initialize variables
        minimumIP = None
        subnet = None
        if (infrastructure == "yes"):
            minimumIP = self.__configFile.get('MAIN', 'INFRASTRUCTURE_MINIMUM_IP')
            subnet = self.__configFile.get('MAIN', 'INFRASTRUCTURE_SUBNET_MASK')
        else:
            minimumIP = self.__configFile.get('MAIN', 'EXPERIMENTAL_MINIMUM_IP')
            subnet = self.__configFile.get('MAIN', 'EXPERIMENTAL_SUBNET_MASK')

        if (self.__isMACAddressInTestbed(macAddress) == True):
            print "Given mac address already belongs to a node in the testbed"
            #return -1

        # Now derive the new node's id and ip address from the physical topology file.
        # Second, create the initial xml description file for the new node with the given
        # parameters. Finally, add a new node entry to the main physical topology file.
        if (powerID != "none" and (not(self.__isNodeInTestbed(powerID)))):
            print "No power switch with the given id exists on the testbed: " + powerID
        if (serialID != "none" and (not(self.__isNodeInTestbed(serialID)))):
            print "No serial node with the given id exists on the testbed: " + serialID
        if (serviceProcessorID != None and serviceProcessorID != "none" and (not(self.__isNodeInTestbed(serviceProcessorID)))):
            print "No power switch with the given id exists on the testbed: " + serviceProcessorID

        nextNodeID = self.__getNextNodeID("computer", self.__configFile.get('MAIN', 'COMPUTER_NODE_MINIMUM_NUMBER'))

        nextIPAddress = None
        if (infrastructure == "yes"):
            nextIPAddress = self.__getNextIPAddress(self.__henInfrastructureBaseAddress, minimumIP)
        else:
            nextIPAddress = self.__getNextIPAddress(self.__henExperimentalBaseAddress, minimumIP)

        interfaces = []
        interfaces.append(Interface(macAddress, nextIPAddress, subnet, None, None, None, "management"))

        physicalLocation = PhysicalLocation(building, floor, room, rackRow, rackName, rackStartUnit, rackEndUnit, None, rackPosition)

        computerNode = ComputerNode()
        computerNode.setNodeID(nextNodeID)
        computerNode.setNodeType("computer")
        computerNode.setVendor(vendor)
        computerNode.setModel(model)
        computerNode.setInterfaces(interfaces, "management")
        computerNode.setPowerNodeID(powerID)
        computerNode.setPowerNodePort(powerPort)
        computerNode.setSerialNodeID(serialID)
        computerNode.setSerialNodePort(serialPort)
        computerNode.setPhysicalLocation(physicalLocation)
        computerNode.setNetbootable(netbootable)
        computerNode.setInfrastructure(infrastructure)
        computerNode.setAttributes(attributes)
        self.parser.writeNodePhysicalFile(computerNode)
        self.parser.writePhysicalEntry("node", nextNodeID, "computer", status)

        # Generate current dhcp files from XML files and restart dhcp server
        if (self.dhcpServer("create") == -1):
            print "HenParser::computerNodeCreate: error while creating dhcp configuration"
            return (-1, "HenParser::computerNodeCreate: error while creating dhcp configuration")
        if (self.dhcpServer("restart") == -1):
            print "HenParser::computerNodeCreate: error while restarting dhcp server"
            return (-1, "HenParser::computerNodeCreate: error while restarting dhcp server")

        # Generate current dns files from XML files and restart dns server
        if (self.dnsServer("create") == -1):
            print "HenParser::computerNodeCreate: error while creating dns configuration"
            return (-1, "HenParser::computerNodeCreate: error while creating dns configuration")
        if (self.dnsServer("restart") == -1):
            print "HenParser::computerNodeCreate: error while restarting dns server"
            return (-1, "HenParser::computerNodeCreate: error while restarting dns server")

        # The node does not have a power switch, so we can't autodetect, create netboot dir and we're done
        if (powerID == "none"):
            if (self.__configNetboot.createNetbootDir(nextNodeID) == -1):
                print "HenParser::computerNodeCreate: error while creating netboot dir for " + nextNodeID
                return (-1, "HenParser::computerNodeCreate: error while creating netboot dir for " + str(nextNodeID))
            print "HenParser::computerNodeCreate: created " + nextNodeID
            return (0, str(nextNodeID))

    # We now need to boot the node so that it can auto-detect its own hardware; to do so
    # we need to create symlinks to netboot the auto-detect filesystem and kernel
        if (self.__configNetboot.createAutodetectNetbootInfo(nextNodeID) == -1):
            print "HenParser::computerNodeCreate: error while creating symbolic links for node " + nextNodeID
            return (-1, "HenParser::computerNodeCreate: error while creating symbolic links for node " + str(nextNodeID))

        # Now reboot the new node up so it can auto-detect its hardware and update etc/physical/nextNodeID.xml
        if (self.power(nextNodeID, "restart") == -1):
            print "HenParser::computerNodeCreate: error while restarting node " + nextNodeID
            return (-1, "HenParser::computerNodeCreate: error while restarting node " + str(nextNodeID))

        # Wait until etc/physical/nextNodeID.xml has been updated before removing auto-detect symlinks and powering
        # node off
        attributesBeforeUpdate = commands.getstatusoutput("ls -lT " + self.__physicalPath + "/" + nextNodeID + ".xml")[1]
        attributesAfterUpdate = attributesBeforeUpdate
        sleepTime = 20
        while(attributesBeforeUpdate == attributesAfterUpdate):
            print "waiting for autodetect to finish (probing every " + str(sleepTime) + " seconds)..."
            time.sleep(sleepTime)
            attributesAfterUpdate = commands.getstatusoutput("ls -lT " + self.__physicalPath + "/" + nextNodeID + ".xml")[1]

        # Set the permissions of the configuration file just written by the node
        filename = self.__physicalPath + "/" + nextNodeID + ".xml"
        os.system("chgrp " + self.__testbedGroup + " " + filename)
        os.system("chmod 775 " + filename)

        if (self.__configNetboot.removeNetbootInfo(nextNodeID) == -1):
            print "HenParser::computerNodeCreate: error while removing autodetect symbolic links for node " + nextNodeID
            return (-1, "HenParser::computerNodeCreate: error while removing autodetect symbolic links for node " + str(nextNodeID))

        # Power node off
        if (self.power(nextNodeID, "poweroff") == -1):
            print "HenParser::computerNodeCreate: error while powering off node " + nextNodeID
            return (-1, "HenParser::computerNodeCreate: error while powering off node " + str(nextNodeID))

        print "HenParser::computerNodeCreate: created " + nextNodeID
        return (0, str(nextNodeID))


    #----------a function from DCNDS branch, not sure if we should keep it in the trunk because it doesn't look related to motes
    def computerNodeDelete(self, nodeID):
        """ \brief Deletes a computer node from the testbed. It does so by first powering the node off; then removing
                   its netboot directory, its xml description file, its entry in the testbed's physical toplogy file;
                   and finally recreating dns and dhcp configuration files and restarting both servers.
        \param nodeID (\c string) The id of the computer node to delete
        \return (\c int) 0 if successful, negative otherwise
        """
        # Begin by powering off the node
        if (self.power(nodeID, "poweroff") == -1):
            print "error while powering off node " + nodeID
            return -1

        # Remove its symlinks directory
        if (self.__configNetboot.removeNetbootInfo(nodeID, 1) == -1):
            print "error while removing netboot directory for node " + nodeID
            return -1

        return self.__deleteNode(nodeID)

    def moteList(self,listing) :
        motes = self.expandNodeListing(listing,"mote")

        if len(motes) == 0 :
            print "No motes found."
            return

        motes.sort()
        motes = map(lambda x: (x.getNodeID(), x.getControllerID(), x.getReference(), x.getVendor(), x.getModel()), motes)

        print ("%12.10s" * 5) % ("nodeid","host","reference","vendor","model")
        print "-" * 60
        
        for i in motes:
            print ("%12.10s" * len(i)) % i

    def moteDetect(self,listing):
        # <hack> faster than trying to connect to all hosts
        if len(listing) == 0 :
            listing = ["computer5-14"]
        # </hack>
        hosts = self.expandNodeListing(listing,"computer")
        motesfound = []
        p = auxiliary.protocol.Protocol(None)
        # detect all
        for host in hosts :
            try :
                p.open(host.getNodeID(), DaemonLocations.moteDaemon[1])
                #ret = pickle.loads(p.doSynchronousCall("motelist", ""))
                ret = p.doSynchronousCall("motelist", "")
                p.close()
            except :
                continue
            #refs = []
            #for value in ret :
            #    payload = pickle.loads(value[2])
            #    refs += payload
            ret = pickle.loads(ret[0][2])
            motesfound += map(lambda x: [x,host.getNodeID()], ret)

        refs_host = map(lambda x: [x.getReference(), x.getControllerID()], self.expandNodeListing(listing,"mote"))
        refs = map(lambda x: x[0], refs_host)
        detect = []
        # figure out which, if any, are new/moved
        for mote in motesfound :
            if mote not in refs_host :
                ref,host = mote
                if ref in refs :
                    detect.append([ref,host,"moved"])
                else :
                    detect.append([ref,host,"new"])
            else :
                # anything left in 'refs_host' is missing!
                refs_host.remove(mote)

        for mote in refs_host :
            ref,host = mote
            detect.append([ref,host,"missing"])

        # print 
        if len(detect) == 0 :
            print "No new, missing or moved motes"
            return
        print ("%12.10s " * 3) % ("reference","host","reason")
        print "-" * 40
        for d in detect :
            print ("%12.10s " * len(d)) % tuple(d)

    def motePs(self,listing):
        motes = self.expandNodeListing(listing,"mote")
        computers = self.expandNodeListing(listing,"computer")
        p = auxiliary.protocol.Protocol(None)
        d = {}
        for c in computers :
            p.open(c.getNodeID(), DaemonLocations.moteDaemon[1])
            ret = p.doSynchronousCall("history", "")
            p.close()

            # 'history' returns [[ref,bin]...]
            ret = pickle.loads(ret[0][2])
            #print ret
            for value in ret :
                d[value[0]] = (value[1],value[2])
        motes.sort()
        err = []
        print ("%12.10s" * 3) % ("nodeid","uid","program")
        print "-" * 40
        for m in motes:
            if d.has_key(m.getReference()):
                print "%12.10s %12.10s     %s" % (m.getNodeID(),d[m.getReference()][1],d[m.getReference()][0])
            else :
                err.append(m.getNodeID())
        if len(err) != 0 :
            print "-" * 30
            for error in err :
                print "%12.10s     %s" % (error, "node not found")

    def expandNodeListing(self,listing,type):
        """
            turns a list of human-readable ranges of nodes (eg: ["mote2-3,5","mote4"]) 
            related to motes or hosts into a list of mote objects
        """
        nodes = []
        # empty case - all motes 
        if type not in ["computer","mote"] :
            print >> sys.stderr, "expandNodeListing called with '%s' as a type, exiting" % type
            sys.exit(-1)

        if len(listing) == 0 :
            return self.getNodes(type).values()
        
        for i in listing :
            nodes += self.getNodeRange(i).values()

        motes     = filter(lambda x : x.getNodeID().startswith("mote"), nodes)
        computers = filter(lambda x : x.getNodeID().startswith("computer"), nodes)

        if type == "mote" :
            for c in computers :
                # this is so crap... must change so that 'getMotes' gives a list or dict of mote objects
                #motes += map(lambda x: self.__getNodeFromTestbed(c.getMotes()[x][0]), c.getMotes())
                motes += map(lambda x: self.__getNodeFromTestbed(x.getPeripheralID()), c.getPeripheralsByType("mote"))

            return motes
        else :
            for m in motes :
                c = self.__getNodeFromTestbed(m.getControllerID())
                if c not in computers :
                    computers.append(c)
            #computers += map(lambda x: self.__getNodeFromTestbed(x.getControllerID()), motes)

            return computers

    def __install_handler(self, code, seq, sz,payload) :
        print payload

    def __async_rpc_loop_forever_thread(self,p):
        try :
            while 1 :
                p.readAndProcess()
        except :
            pass

    def moterpc(self, method, platform, appdir, listing) :
        motes = self.expandNodeListing(listing,"mote")
        computers = {}

        # so we can perform installs host at a time
        for mote in motes:
            host = mote.getControllerID()
            if not computers.has_key(host) :
                computers[host] = []
            computers[host].append(mote)
    
        if method == "install" :   
            # contiki requires stipulating a kernel
            # (embedded in the platform name)
            if platform.startswith('tinyos') :
                kernel = None
            else:
                kernel = platform[len("contiki."):]
        elif method == "log" :
            action = platform
        else :
            pass

        # payload format = [(start|stop), mote id, hen id, log file]+       
        calls = []
        for host in computers :
            hostmotes = computers[host]
            payload = []
            for mote in hostmotes :
                id = mote.getNodeID()
                if method == "install" :
                    payload.append([platform,kernel,id[4:],appdir,mote.getReference(),appdir+("/%s.log" % id),id,os.getlogin()])
                elif method == "log" :
                    payload.append([action,mote.getReference(),id,appdir+("/%s.log" % id)])
                else :
                    pass
            payload = pickle.dumps(payload)
            calls.append([host,payload])

        # make calls
        # spawn threads to read socket
        for call in calls :
            host,payload = call
            p = auxiliary.protocol.Protocol(None)
            p.open(host,DaemonLocations.moteDaemon[1])
            p.sendRequest(method,payload,self.__install_handler)
            rpc_thread = thread.start_new_thread(self.__async_rpc_loop_forever_thread,(p,))
            call.append(p)
            call.append(rpc_thread)

        # ... and now, we wait
        try :
            while 1 :
                time.sleep(1)
        except KeyboardInterrupt :
            pass

        # user annoyed enough to press '^c'
        for call in calls :
            host,payload,proto,rpc_thread = call
            proto.close()
        
    def moteNodeCreate(self,mac,host):
        """\brief Adds a mote node to the testbed. To do so this it checks that the given mac address
                  does not conflict with any already on the testbed; it then  derives an id for the node
                  and an ip address for its management interface; it writes a prelimary xml topology file
                  for the node and adds an entry to the testbed's main topology file; it creates dns and
                  dhcp configuration files and restarts these servers; it boots the node so that it will
                  autodetect its hardware and complete the prelimary xml topology; finally it removes the
                  symbolic links used to boot the node and powers the node off. The function checks that
                  the given power switch, serial and service processor ids exist on the testbed.
        \param mac (\c string)
        \param attributes (\c dictionary) A dictionary whose keys are attribute names and whose values are attribute values
        \return (\c int) 0 if successful, -1 otherwise
        """
        nextNodeID = self.__getNextNodeID("mote", self.__configFile.get('MAIN', 'MOTE_NODE_MINIMUM_NUMBER'))

# read all motes
# find if it existed before
# delete reference in host file
# create file + reference in current host

        # it is possible this mote was connected to another host previously
        # if it was, remove the reference from host xml file and set host=none 
        # in  the mote's xml file
        motes = self.getNodes("mote")
        for m in motes :
            if mac == motes[m].getReference():
                oldhost  = self.getNodes("computer")[motes[m].getControllerID()]
                #oldmotes = oldhost.getMotes()
                oldmotes = oldhost.getPeripherals()
                del oldmotes[m]
                motes[m].setControllerID("none")

                self.parser.writeNodePhysicalFile(motes[m])
                self.parser.writeNodePhysicalFile(oldhost)
                break

        hostnode = self.getNodes("computer")[host]
        if hostnode == None:
            print "%s does not exist" % host
            return -1
        
        #motes = hostnode.getMotes()
        #motes[nextNodeID] = [nextNodeID, "usb"]

        hostnode.addPeripheral(Peripheral(nextNodeID,"mote","usb","",""))

        moteNode = MoteNode()
        moteNode.setNodeID(nextNodeID)
        moteNode.setNodeType("mote")

        moteNode.setVendor("moteiv")
        moteNode.setModel("tmote_sky")
        moteNode.setReference(mac)
        moteNode.setStatus("operational")
        #moteNode.setSingleAttribute("status", "operational")
        moteNode.setControllerID(host)
        
        self.parser.writeNodePhysicalFile(moteNode)
        self.parser.writeNodePhysicalFile(hostnode)
        self.parser.writePhysicalEntry("node", nextNodeID, "mote")

        # Set the permissions of the configuration file just written by the node
        filename = self.__physicalPath + "/" + nextNodeID + ".xml"
        os.system("chgrp " + self.__testbedGroup + " " + filename)
        os.system("chmod 775 " + filename)

        print "created " + nextNodeID

        return 0

    def moteNodeDelete(self, listing):
        """ \brief Deletes a mote node from the testbed. It does so by first powering the node off; then removing
                   its netboot directory, its xml description file, its entry in the testbed's physical toplogy file;
                   and finally recreating dns and dhcp configuration files and restarting both servers.
        \param nodeID (\c string) The id of the mote node to delete
        \return (\c int) 0 if successful, negative otherwise
        """
        motes = self.expandNodeListing(listing,"mote")
        computers = self.getNodes("computer")
        motes.sort()
        for m in motes :
            nodeID = m.getNodeID()
            try :
                host = computers[m.getControllerID()]
                #hostmotes = host.getMotes()
                hostmotes = host.getPeripherals()
                del hostmotes[nodeID]
                self.parser.writeNodePhysicalFile(host)
            except :
                pass
            self.__deleteNode(nodeID)

#--------------------------------------------------
    def serialNodeCreate(self, vendor, model, macAddress, powerID, powerPort, username, password, rackName, attributes, building=None, floor=None, room=None, rackRow=None, rackStartUnit=None, rackEndUnit=None, rackPosition=None, status="operational"):
        """\brief Adds a serial node to the testbed. To do so this it checks that the given mac address
                  does not conflict with any already on the testbed; it then  derives an id for the node
                  and an ip address for its infrastructure interface; it writes a prelimary xml topology file
                  for the node and adds an entry to the testbed's main topology file; finally it creates dns and
                  dhcp configuration files and restarts these servers. The function ensures that the given power switch
                  id exists on the testbed
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param macAddress (\c string) The mac address of the node's infrastructure interface
        \param powerID (\c string) The id of the power switch that the node is connected to
        \param powerPort (\c string) The port of the power switch that the node is connected to
        \param username (\c string) The user name to log into the serial node with
        \param password (\c string) The password to log into the serial node with
        \param rackName (\c string) The node's physical location
        \param attributes (\c dictionary) A dictionary whose keys are attribute names and whose values are attribute values
        \param building (\c string) The building that the node is in
        \param floor (\c string) The floor that the node is in
        \param room (\c string) The room that the node is in
        \param rackRow (\c string) The number of the row that the node is in
        \param rackStartUnit (\c string) The rack start unit for the node
        \param rackEndUnit (\c string) The rack end unit for the node
        \param rackPosition (\c string) One of front, rear, or both, describing the node's position in the rack
        \param status (\c string) The status of the node
        \return (\c tuple of int,string) int is 0 if successful, -1 otherwise. string gives an error's description or the
                                         the new node's id if successful
        """
        if (self.__isMACAddressInTestbed(macAddress) == True):
            print "Given mac address already belongs to a node in the testbed"
            #return -1
        if (powerID != "none" and (not(self.__isNodeInTestbed(powerID)))):
            print "No power switch with the given id exists on the testbed: " + powerID


        minimumIP = self.__configFile.get('MAIN', 'INFRASTRUCTURE_MINIMUM_IP')
        subnet = self.__configFile.get('MAIN', 'INFRASTRUCTURE_SUBNET_MASK')
        nextNodeID = self.__getNextNodeID("serial", self.__configFile.get('MAIN', 'SERIAL_NODE_MINIMUM_NUMBER'))
        nextIPAddress = self.__getNextIPAddress(self.__henInfrastructureBaseAddress, minimumIP)
        user = UserManagement(username, password)
        users = []
        users.append(user)
        interfaces = []
        interfaces.append(Interface(macAddress, nextIPAddress, subnet, None, None, None, "infrastructure"))

        physicalLocation = PhysicalLocation(building, floor, room, rackRow, rackName, rackStartUnit, rackEndUnit, None, rackPosition)

        serialNode = SerialNode()
        serialNode.setNodeID(nextNodeID)
        serialNode.setNodeType("serial")
        serialNode.setVendor(vendor)
        serialNode.setModel(model)
        serialNode.setInterfaces(interfaces, "infrastructure")
        serialNode.setPowerNodeID(powerID)
        serialNode.setPowerNodePort(powerPort)
        serialNode.setUsers(users)
        serialNode.setAttributes(attributes)
        serialNode.setPhysicalLocation(physicalLocation)
        serialNode.setNetbootable("no")
        serialNode.setInfrastructure("yes")
        self.parser.writeNodePhysicalFile(serialNode)
        self.parser.writePhysicalEntry("node", nextNodeID, "serial", status)

    # Generate current dhcp files from XML files and restart dhcp server
        if (self.dhcpServer("create") == -1):
            print "HenParser::SerialNodeCreate: error while creating dhcp configuration"
            return (-1, "HenParser::SerialNodeCreate: error while creating dhcp configuration")
        if (self.dhcpServer("restart") == -1):
            print "HenParser::SerialNodeCreate: error while restarting dhcp server"
            return (-1, "HenParser::SerialNodeCreate: error while restarting dhcp server")

    # Generate current dns files from XML files and restart dns server
        if (self.dnsServer("create") == -1):
            print "HenParser::SerialNodeCreate: error while creating dns configuration"
            return (-1, "HenParser::SerialNodeCreate: error while creating dns configuration")
        if (self.dnsServer("restart") == -1):
            print "HenParser::SerialNodeCreate: error while restarting dns server"
            return (-1, "HenParser::SerialNodeCreate: error while restarting dns server")

        print "HenParser::SerialNodeCreate: created " + nextNodeID
        return (0, str(nextNodeID))

    def switchNodeCreate(self, infrastructure, vendor, model, macAddress, powerID, powerPort, serialID, serialPort, rackName, attributes, building=None, floor=None, room=None, rackRow=None, rackStartUnit=None, rackEndUnit=None, rackPosition=None, status="operational"):
        """\brief Adds a switch node to the testbed. To do so this it checks that the given mac address
                  does not conflict with any already on the testbed; it then  derives an id for the node
                  and an ip address for its infrastructure or management interface; it writes a prelimary xml topology file
                  for the node and adds an entry to the testbed's main topology file; finally it creates dns and
                  dhcp configuration files and restarts these servers. The function ensures that the given power switch
                  and serial ids exist on the testbed
        \param infrastructure (\c string) Either yes or no
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param macAddress (\c string) The mac address of the node's infrastructure or management interface
        \param powerID (\c string) The id of the power switch that the node is connected to
        \param powerPort (\c string) The port of the power switch that the node is connected to
        \param serialID (\c string) The id of the serial node that the node is connected to
        \param serialPort (\c string) The port of the serial node that the node is connected to
        \param rackName (\c string) The node's physical location
        \param attributes (\c dictionary) A dictionary whose keys are attribute names and whose values are attribute values
        \param building (\c string) The building that the node is in
        \param floor (\c string) The floor that the node is in
        \param room (\c string) The room that the node is in
        \param rackRow (\c string) The number of the row that the node is in
        \param rackStartUnit (\c string) The rack start unit for the node
        \param rackEndUnit (\c string) The rack end unit for the node
        \param rackPosition (\c string) One of front, rear, or both, describing the node's position in the rack
        \param status (\c string) The status of the node
        \return (\c tuple of int,string) int is 0 if successful, -1 otherwise. string gives an error's description or the
                                         the new node's id if successful
        """
        if (self.__isMACAddressInTestbed(macAddress) == True):
            print "Given mac address already belongs to a node in the testbed"
            #return -1

        if (powerID != "none" and (not(self.__isNodeInTestbed(powerID)))):
            print "No power switch with the given id exists on the testbed: " + powerID

        if (serialID != "none" and (not(self.__isNodeInTestbed(serialID)))):
            print "No serial node with the given id exists on the testbed: " + serialID


        minimumIP = None
        subnet = None
        if (infrastructure == "yes"):
            minimumIP = self.__configFile.get('MAIN', 'INFRASTRUCTURE_MINIMUM_IP')
            subnet = self.__configFile.get('MAIN', 'INFRASTRUCTURE_SUBNET_MASK')
        else:
            minimumIP = self.__configFile.get('MAIN', 'EXPERIMENTAL_MINIMUM_IP')
            subnet = self.__configFile.get('MAIN', 'EXPERIMENTAL_SUBNET_MASK')

        nextNodeID = self.__getNextNodeID("switch", self.__configFile.get('MAIN', 'SWITCH_NODE_MINIMUM_NUMBER'))
        nextIPAddress = self.__getNextIPAddress(self.__henInfrastructureBaseAddress, minimumIP)
        interfaces = []
        interfaces.append(Interface(macAddress, nextIPAddress, subnet, None, None, None, "infrastructure"))

        physicalLocation = PhysicalLocation(building, floor, room, rackRow, rackName, rackStartUnit, rackEndUnit, None, rackPosition)

        switchNode = SwitchNode()
        switchNode.setNodeID(nextNodeID)
        switchNode.setNodeType("switch")
        switchNode.setVendor(vendor)
        switchNode.setModel(model)
        switchNode.setInterfaces(interfaces, "infrastructure")
        switchNode.setSerialNodeID(serialID)
        switchNode.setSerialNodePort(serialPort)
        switchNode.setPowerNodeID(powerID)
        switchNode.setPowerNodePort(powerPort)
        switchNode.setAttributes(attributes)
        switchNode.setPhysicalLocation(physicalLocation)
        switchNode.setNetbootable("no")
        switchNode.setInfrastructure(infrastructure)
        self.parser.writeNodePhysicalFile(switchNode)
        self.parser.writePhysicalEntry("node", nextNodeID, "switch", status)

        # Generate current dhcp files from XML files and restart dhcp server
        if (self.dhcpServer("create") == -1):
            print "HenParser::switchNodeCreate: error while creating dhcp configuration"
            return (-1, "HenParser::switchNodeCreate: error while creating dhcp configuration")
        if (self.dhcpServer("restart") == -1):
            print "HenParser::switchNodeCreate: error while restarting dhcp server"
            return (-1, "HenParser::switchNodeCreate: error while restarting dhcp server")

        # Generate current dns files from XML files and restart dns server
        if (self.dnsServer("create") == -1):
            print "HenParser::switchNodeCreate: error while creating dns configuration"
            return (-1, "HenParser::switchNodeCreate: error while creating dns configuration")
        if (self.dnsServer("restart") == -1):
            print "HenParser::switchNodeCreate: error while restarting dns server"
            return (-1, "HenParser::switchNodeCreate: error while restarting dns server")

        print "HenParser::switchNodeCreate: created " + nextNodeID
        return (0, str(nextNodeID))

    def powerswitchNodeCreate(self, vendor, model, macAddress, serialID, serialPort, rackName, username, password, attributes, building=None, floor=None, room=None, rackRow=None, rackStartUnit=None, rackEndUnit=None, rackPosition=None, status="operational"):
        """\brief Adds a power switch node to the testbed. To do so this it checks that the given mac address
                  does not conflict with any already on the testbed; it then  derives an id for the node
                  and an ip address for its infrastructure interface; it writes a prelimary xml topology file
                  for the node and adds an entry to the testbed's main topology file; finally it creates dns and
                  dhcp configuration files and restarts these servers. The function ensures that the given
                  serial id exists on the testbed
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param macAddress (\c string) The mac address of the node's infrastructure interface
        \param serialID (\c string) The id of the serial node that the node is connected to
        \param serialPort (\c string) The port of the serial node that the node is connected to
        \param rackName (\c string) The node's physical location
        \param attributes (\c dictionary) A dictionary whose keys are attribute names and whose values are attribute values
        \param building (\c string) The building that the node is in
        \param floor (\c string) The floor that the node is in
        \param room (\c string) The room that the node is in
        \param rackRow (\c string) The number of the row that the node is in
        \param rackStartUnit (\c string) The rack start unit for the node
        \param rackEndUnit (\c string) The rack end unit for the node
        \param rackPosition (\c string) One of front, rear, or both, describing the node's position in the rack
        \param status (\c string) The status of the node
        \return (\c tuple of int,string) int is 0 if successful, -1 otherwise. string gives an error's description or the
                                         the new node's id if successful
        """
        if (self.__isMACAddressInTestbed(macAddress) == True):
            print "Given mac address already belongs to a node in the testbed"
            #return -1

        if (serialID != "none" and (not(self.__isNodeInTestbed(serialID)))):
            print "No serial node with the given id exists on the testbed: " + serialID

        minimumIP = self.__configFile.get('MAIN', 'INFRASTRUCTURE_MINIMUM_IP')
        subnet = self.__configFile.get('MAIN', 'INFRASTRUCTURE_SUBNET_MASK')
        nextNodeID = self.__getNextNodeID("powerswitch", self.__configFile.get('MAIN', 'POWERSWITCH_NODE_MINIMUM_NUMBER'))
        nextIPAddress = self.__getNextIPAddress(self.__henInfrastructureBaseAddress, minimumIP)
        interfaces = []
        interfaces.append(Interface(macAddress, nextIPAddress, subnet, None, None, None, "infrastructure"))
        user = UserManagement(username, password)
        users = []
        users.append(user)

        physicalLocation = PhysicalLocation(building, floor, room, rackRow, rackName, rackStartUnit, rackEndUnit, None, rackPosition)

        powerswitchNode = PowerSwitchNode()
        powerswitchNode.setNodeID(nextNodeID)
        powerswitchNode.setNodeType("powerswitch")
        powerswitchNode.setVendor(vendor)
        powerswitchNode.setModel(model)
        powerswitchNode.setInterfaces(interfaces, "infrastructure")
        powerswitchNode.setUsers(users)
        powerswitchNode.setSerialNodeID(serialID)
        powerswitchNode.setSerialNodePort(serialPort)
        powerswitchNode.setAttributes(attributes)
        powerswitchNode.setPhysicalLocation(physicalLocation)
        powerswitchNode.setNetbootable("no")
        powerswitchNode.setInfrastructure("yes")
        self.parser.writeNodePhysicalFile(powerswitchNode)
        self.parser.writePhysicalEntry("node", nextNodeID, "powerswitch", status)

    # Generate current dhcp files from XML files and restart dhcp server
        if (self.dhcpServer("create") == -1):
            print "HenPaser::powerswitchNodeCreate: error while creating dhcp configuration"
            return (-1, "HenPaser::powerswitchNodeCreate: error while creating dhcp configuration")
        if (self.dhcpServer("restart") == -1):
            print "HenPaser::powerswitchNodeCreate: error while restarting dhcp server"
            return (-1, "HenPaser::powerswitchNodeCreate: error while restarting dhcp server")

    # Generate current dns files from XML files and restart dns server
        if (self.dnsServer("create") == -1):
            print "HenPaser::powerswitchNodeCreate: error while creating dns configuration"
            return (-1, "HenPaser::powerswitchNodeCreate: error while creating dns configuration")
        if (self.dnsServer("restart") == -1):
            print "HenPaser::powerswitchNodeCreate: error while restarting dns server"
            return (-1, "HenPaser::powerswitchNodeCreate: error while restarting dns server")

        print "HenPaser::powerswitchNodeCreate: created " + nextNodeID
        return (0, str(nextNodeID))

    def routerNodeCreate(self, vendor, model, macAddress, powerID, powerPort, serialID, serialPort, rackName, attributes, building=None, floor=None, room=None, rackRow=None, rackStartUnit=None, rackEndUnit=None, rackPosition=None, status="operational"):
        """\brief Adds a router node to the testbed. To do so this it checks that the given mac address
                  does not conflict with any already on the testbed; it then  derives an id for the node
                  and an ip address for its management interface; it writes a prelimary xml topology file
                  for the node and adds an entry to the testbed's main topology file; finally it creates dns and
                  dhcp configuration files and restarts these servers. The function ensures that the given power switch
                  and serial ids exist on the testbed
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param macAddress (\c string) The mac address of the node's management interface
        \param powerID (\c string) The id of the power switch that the node is connected to
        \param powerPort (\c string) The port of the power switch that the node is connected to
        \param serialID (\c string) The id of the serial node that the node is connected to
        \param serialPort (\c string) The port of the serial node that the node is connected to
        \param rackName (\c string) The node's physical location
        \param attributes (\c dictionary) A dictionary whose keys are attribute names and whose values are attribute values
        \param building (\c string) The building that the node is in
        \param floor (\c string) The floor that the node is in
        \param room (\c string) The room that the node is in
        \param rackRow (\c string) The number of the row that the node is in
        \param rackStartUnit (\c string) The rack start unit for the node
        \param rackEndUnit (\c string) The rack end unit for the node
        \param rackPosition (\c string) One of front, rear, or both, describing the node's position in the rack
        \param status (\c string) The status of the node
        \return (\c tuple of int,string) int is 0 if successful, -1 otherwise. string gives an error's description or the
                                         the new node's id if successful
        """
        if (self.__isMACAddressInTestbed(macAddress) == True):
            print "Given mac address already belongs to a node in the testbed"
            #return -1
        if (powerID != "none" and (not(self.__isNodeInTestbed(powerID)))):
            print "No power switch with the given id exists on the testbed: " + powerID

        if (serialID != "none" and (not(self.__isNodeInTestbed(serialID)))):
            print "No serial node with the given id exists on the testbed: " + serialID


        minimumIP = self.__configFile.get('MAIN', 'EXPERIMENTAL_MINIMUM_IP')
        subnet = self.__configFile.get('MAIN', 'EXPERIMENTAL_SUBNET_MASK')
        nextNodeID = self.__getNextNodeID("router", self.__configFile.get('MAIN', 'ROUTER_NODE_MINIMUM_NUMBER'))
        nextIPAddress = self.__getNextIPAddress(self.__henExperimentalBaseAddress, minimumIP)
        interfaces = []
        interfaces.append(Interface(macAddress, nextIPAddress, subnet, None, None, None, "management"))

        physicalLocation = PhysicalLocation(building, floor, room, rackRow, rackName, rackStartUnit, rackEndUnit, None, rackPosition)

        routerNode = RouterNode()
        routerNode.setNodeID(nextNodeID)
        routerNode.setNodeType("router")
        routerNode.setVendor(vendor)
        routerNode.setModel(model)
        routerNode.setInterfaces(interfaces, "management")
        routerNode.setSerialNodeID(serialID)
        routerNode.setSerialNodePort(serialPort)
        routerNode.setPowerNodeID(powerID)
        routerNode.setPowerNodePort(powerPort)
        routerNode.setAttributes(attributes)
        routerNode.setPhysicalLocation(physicalLocation)
        routerNode.setNetbootable("no")
        routerNode.setInfrastructure("no")
        self.parser.writeNodePhysicalFile(routerNode)
        self.parser.writePhysicalEntry("node", nextNodeID, "router", status)

    # Generate current dhcp files from XML files and restart dhcp server
        if (self.dhcpServer("create") == -1):
            print "HenPaser::routerNodeCreate: error while creating dhcp configuration"
            return (-1, "HenPaser::routerNodeCreate: error while creating dhcp configuration")
        if (self.dhcpServer("restart") == -1):
            print "HenPaser::routerNodeCreate: error while restarting dhcp server"
            return (-1, "HenPaser::routerNodeCreate: error while restarting dhcp server")

    # Generate current dns files from XML files and restart dns server
        if (self.dnsServer("create") == -1):
            print "HenPaser::routerNodeCreate: error while creating dns configuration"
            return (-1, "HenPaser::routerNodeCreate: error while creating dns configuration")
        if (self.dnsServer("restart") == -1):
            print "HenPaser::routerNodeCreate: error while restarting dns server"
            return (-1, "HenPaser::routerNodeCreate: error while restarting dns server")

        print "HenPaser::routerNodeCreate: created " + nextNodeID
        return (0, str(nextNodeID))

    def serviceprocessorNodeCreate(self, macAddress, powerID, powerPort, username, password, attributes, status="operational", vendor="", model=""):
        """\brief Adds a service processor node to the testbed. To do so this it checks that the given mac address
                  does not conflict with any already on the testbed; it then  derives an id for the node
                  and an ip address for its infrastructure interface; it writes a prelimary xml topology file
                  for the node and adds an entry to the testbed's main topology file; finally it creates dns and
                  dhcp configuration files and restarts these servers. The function ensures that the given power switch
                  id exists on the testbed
        \param macAddress (\c string) The mac address of the node's infrastructure interface
        \param powerID (\c string) The id of the power switch that the node is connected to
        \param powerPort (\c string) The port of the power switch that the node is connected to
        \param username (\c string) The user name to log into the service processor node with
        \param password (\c string) The password to log into the service processor node with
        \param attributes (\c dictionary) A dictionary whose keys are attribute names and whose values are attribute values
        \param status (\c string) The status of the node
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \return (\c tuple of int,string) int is 0 if successful, -1 otherwise. string gives an error's description or the
                                         the new node's id if successful
        """
        if (self.__isMACAddressInTestbed(macAddress) == True):
            print "Given mac address already belongs to a node in the testbed"
            #return -1
        if (powerID != "none" and (not(self.__isNodeInTestbed(powerID)))):
            print "No power switch with the given id exists on the testbed: " + powerID


        minimumIP = self.__configFile.get('MAIN', 'INFRASTRUCTURE_MINIMUM_IP')
        subnet = self.__configFile.get('MAIN', 'INFRASTRUCTURE_SUBNET_MASK')
        nextNodeID = self.__getNextNodeID("serviceprocessor", self.__configFile.get('MAIN', 'SERVICEPROCESSOR_NODE_MINIMUM_NUMBER'))
        nextIPAddress = self.__getNextIPAddress(self.__henInfrastructureBaseAddress, minimumIP)
        interfaces = []
        interfaces.append(Interface(macAddress, nextIPAddress, subnet, None, None, None, "infrastructure"))
        user = UserManagement(username, password)
        users = []
        users.append(user)

        serviceprocessorNode = ServiceProcessorNode()
        serviceprocessorNode.setNodeID(nextNodeID)
        serviceprocessorNode.setNodeType("serviceprocessor")
        serviceprocessorNode.setInterfaces(interfaces, "infrastructure")
        serviceprocessorNode.setUsers(users)
        serviceprocessorNode.setPowerNodeID(powerID)
        serviceprocessorNode.setPowerNodePort(powerPort)
        serviceprocessorNode.setAttributes(attributes)
        serviceprocessorNode.setNetbootable("no")
        serviceprocessorNode.setInfrastructure("yes")
        serviceprocessorNode.setVendor(vendor)
        serviceprocessorNode.setModel(model)
        self.parser.writeNodePhysicalFile(serviceprocessorNode)
        self.parser.writePhysicalEntry("node", nextNodeID, "serviceprocessor", status)

    # Generate current dhcp files from XML files and restart dhcp server
        if (self.dhcpServer("create") == -1):
            print "HenPaser::serviceprocessorNodeCreate: error while creating dhcp configuration"
            return (-1, "HenPaser::serviceprocessorNodeCreate: error while creating dhcp configuration")
        if (self.dhcpServer("restart") == -1):
            print "HenPaser::serviceprocessorNodeCreate: error while restarting dhcp server"
            return (-1, "HenPaser::serviceprocessorNodeCreate: error while restarting dhcp server")

    # Generate current dns files from XML files and restart dns server
        if (self.dnsServer("create") == -1):
            print "HenPaser::serviceprocessorNodeCreate: error while creating dns configuration"
            return (-1, "HenPaser::serviceprocessorNodeCreate: error while creating dns configuration")
        if (self.dnsServer("restart") == -1):
            print "HenPaser::serviceprocessorNodeCreate: error while restarting dns server"
            return (-1, "HenPaser::serviceprocessorNodeCreate: error while restarting dns server")

        # Restart the service processor so that it will get its dhcp address
        if (self.power(nextNodeID, "restart") == -1):
            print "HenPaser::serviceprocessorNodeCreate: error while restarting service processor node " + nextNodeID
            return (-1, "HenPaser::serviceprocessorNodeCreate: error while restarting service processor node " + str(nextNodeID))

        print "HenPaser::serviceprocessorNodeCreate: created " + nextNodeID
        return (0, str(nextNodeID))

    def sensorNodeCreate(self, dhcp, macAddress, ipAddress, rackName, vendor, model, attributes, status="operational"):
        """\brief Adds a service processor node to the testbed. To do so this it checks that the given mac address
                  (if any) does not conflict with any already on the testbed; it then  derives an id for the node
                  and an ip (if dhcp is set to yes); it writes a prelimary xml topology file
                  for the node and adds an entry to the testbed's main topology file; finally it creates dns and
                  dhcp configuration files and restarts these servers. The function ensures that the given power switch
                  id exists on the testbed
        \param dhcp (\c string) yes or no, based on whether the sensor will dhcp or not
        \param macAddress (\c string) The mac address of the node's infrastructure interface
        \param ipAddress (\c string) The ip address of the node's infrastructure interface
        \param rackName (\c string) The node's physical location
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param attributes (\c dictionary) A dictionary whose keys are attribute names and whose values are attribute values
        \param status (\c string) The status of the node
        \return (\c tuple of int,string) int is 0 if successful, -1 otherwise. string gives an error's description or the
                                         the new node's id if successful
        """
        if (macAddress != None and self.__isMACAddressInTestbed(macAddress) == True):
            print "Given mac address already belongs to a node in the testbed"
            #return -1

        minimumIP = self.__configFile.get('MAIN', 'INFRASTRUCTURE_MINIMUM_IP')
        subnet = self.__configFile.get('MAIN', 'INFRASTRUCTURE_SUBNET_MASK')
        nextNodeID = self.__getNextNodeID("sensor", self.__configFile.get('MAIN', 'SENSOR_NODE_MINIMUM_NUMBER'))

        nextIPAddress = None
        if (dhcp == "yes"):
            nextIPAddress = self.__getNextIPAddress(self.__henInfrastructureBaseAddress, minimumIP)
        else:
            nextIPAddress = ipAddress
        interfaces = []
        interfaces.append(Interface(macAddress, nextIPAddress, subnet, None, None, None, "infrastructure"))

        physicalLocation = PhysicalLocation(None, None, None, None, rackName, None)

        sensorNode = SensorNode()
        sensorNode.setDHCP(dhcp)
        sensorNode.setNodeID(nextNodeID)
        sensorNode.setNodeType("sensor")
        sensorNode.setInterfaces(interfaces, "infrastructure")
        sensorNode.setAttributes(attributes)
        sensorNode.setPhysicalLocation(physicalLocation)
        sensorNode.setInfrastructure("yes")
        sensorNode.setNetbootable("no")
        sensorNode.setVendor(vendor)
        sensorNode.setModel(model)

        self.parser.writeNodePhysicalFile(sensorNode)
        self.parser.writePhysicalEntry("node", nextNodeID, "sensor", status)

    # Generate current dhcp files from XML files and restart dhcp server
        if (dhcp == "yes"):
            if (self.dhcpServer("create") == -1):
                print "error while creating dhcp configuration"
                return -1
            if (self.dhcpServer("restart") == -1):
                print "error while restarting dhcp server"
                return -1

    # Generate current dns files from XML files and restart dns server
        if (self.dnsServer("create") == -1):
            print "error while creating dns configuration"
            return -1
        if (self.dnsServer("restart") == -1):
            print "error while restarting dns server"
            return -1

        print "created " + nextNodeID

        return 0

    def kvmNodeCreate(self, vendor, model, rackID, rackStartUnit, rackEndUnit, rackPosition, attributes, building=None, floor=None, room=None, rackRow=None, status="operational"):
        """\brief Adds a kvm node to the testbed.
        \param vendor (\c string) The node's vendor
        \param model (\c string) The node's model
        \param rackID (\c string) The id of the rack that the node is in
        \param rackStartUnit (\c string) The unit that the node begins at (should be smaller than rackEndUnit)
        \param rackEndUnit (\c string) The unit that the node ends at
        \param rackPosition (\c string) Describes which way the node is racked: front, rear or both (for full-depth nodes)
        \param attributes (\c dictionary) A dictionary whose keys are attribute names and whose values are attribute values
        \param building (\c string) The building that the node is in
        \param floor (\c string) The floor that the node is in
        \param room (\c string) The room that the node is in
        \param rackRow (\c string) The number of the row that the node is in
        \param status (\c string) The status of the node
        \return (\c tuple of int,string) int is 0 if successful, -1 otherwise. string gives an error's description or the
                                         the new node's id if successful
        """
        nextNodeID = self.__getNextNodeID("kvm", self.__configFile.get('MAIN', 'KVM_NODE_MINIMUM_NUMBER'))
        physicalLocation = PhysicalLocation(building, floor, room, rackRow, rackName, rackStartUnit, rackEndUnit, None, rackPosition)

        kvmNode = KVMNode()
        kvmNode.setNodeID(nextNodeID)
        kvmNode.setNodeType("kvm")
        kvmNode.setAttributes(attributes)
        kvmNode.setPhysicalLocation(physicalLocation)
        kvmNode.setInfrastructure("yes")
        kvmNode.setNetbootable("no")
        kvmNode.setVendor(vendor)
        kvmNode.setModel(model)

        self.parser.writeNodePhysicalFile(kvmNode)
        self.parser.writePhysicalEntry("node", nextNodeID, "kvm", status)

        print "created " + nextNodeID

        return 0

    def infrastructureRackCreate(self, vendor, model, description, building, floor, room, rackRow, rowPosition, height, width, depth, rearRightSlots, rearLeftSlots, numberUnits, status, attributes):
        nextInfrastructureID = self.__getNextInfrastructureID("rack", self.__configFile.get('MAIN', 'INFRASTRUCTURE_RACK_MINIMUM_NUMBER'))

        infrastructureRack = InfrastructureRack(nextInfrastructureID, "rack", vendor, model, description, \
                                                building, floor, room, attributes, PhysicalSize(height, width, depth, numberUnits), \
                                                status, rackRow, rowPosition, rearRightSlots, \
                                                rearLeftSlots)

        self.parser.writeInfrastructurePhysicalFile(infrastructureRack)
        self.parser.writePhysicalEntry("infrastructure", nextInfrastructureID, "rack", status)

        print "HenParser::infrastructureRackCreate: created " + nextInfrastructureID

        return (0, str(nextInfrastructureID))

    def infrastructureFloorBoxCreate(self, vendor, model, description, building, floor, room, attributes, status, rackRow, rowPosition, maxCurrent, plug1label, plug1enabled, plug1maxcurrent, plug2label, plug2enabled, plug2maxcurrent, plug3label, plug3enabled, plug3maxcurrent, plug4label, plug4enabled, plug4maxcurrent, rj45port1type, rj45port1label, rj45port1description, rj45port2type, rj45port2label, rj45port2description, rj45port3type, rj45port3label, rj45port3description, rj45port4type, rj45port4label, rj45port4description):

        nextInfrastructureID = self.__getNextInfrastructureID("floorbox", self.__configFile.get('MAIN', 'INFRASTRUCTURE_FLOORBOX_MINIMUM_NUMBER'))

        # Create dictionary of FloorBoxPowerPlug objects
        powerPlugs = []
        enabled = False
        if (plug1enabled == "yes"):
            enabled = True
        powerPlugs.append(FloorBoxPowerPlug(plug1label, plug1maxcurrent, enabled))
        enabled = False
        if (plug2enabled == "yes"):
            enabled = True
        powerPlugs.append(FloorBoxPowerPlug(plug2label, plug2maxcurrent, enabled))
        enabled = False
        if (plug3enabled == "yes"):
            enabled = True
        powerPlugs.append(FloorBoxPowerPlug(plug3label, plug3maxcurrent, enabled))
        enabled = False
        if (plug4enabled == "yes"):
            enabled = True
        powerPlugs.append(FloorBoxPowerPlug(plug4label, plug4maxcurrent, enabled))

        # Create dictionary of FloorBoxRJ45Port objects
        rj45Ports = []
        rj45Ports.append(FloorBoxRJ45Port(rj45port1type, rj45port1label, rj45port1description))
        rj45Ports.append(FloorBoxRJ45Port(rj45port2type, rj45port2label, rj45port2description))
        rj45Ports.append(FloorBoxRJ45Port(rj45port3type, rj45port3label, rj45port3description))
        rj45Ports.append(FloorBoxRJ45Port(rj45port4type, rj45port4label, rj45port4description))

        infrastructureFloorBox = InfrastructureFloorBox(nextInfrastructureID, "floorbox", vendor, model, description, \
                                                building, floor, room, attributes, status, rackRow, rowPosition, maxCurrent, \
                                                powerPlugs, rj45Ports)

        self.parser.writeInfrastructurePhysicalFile(infrastructureFloorBox)
        self.parser.writePhysicalEntry("infrastructure", nextInfrastructureID, "floorbox")

        print "created " + nextInfrastructureID

        return 0

    def experimentCreate(self, topologyFile):
        """\brief Creates an experiment on the testbed given the path to an xml file describing it. This
                  involves the following steps:
                  1) Parse the experiment file, checking for inconsistencies
                  2) Parse the main experiments file, making sure that the id does not already exist
                  3) Check for conflicts between this new experiment and existing ones
                  4) Create the necessary vlans, checking for conflicts with existing vlans
                  5) Create symbolic links and directories to netboot from
                  6) Create a startup file to set the hostname and the ip address of the interfaces
                  7) Copy the given file to the directory containing all experiment on the testbed and rename it
                  8) Add an entry to the main experiments file
                  9) Restart the experimental nodes
        \param topologyFile (\c string) The path to the xml file containing the experiment information
        \return (\c int) 0 if successfull, -1 otherwise
        """
        # 1) Parse the new experiment file, checking for problems (parseUserExperiment takes care of this)
        userExperiment = self.parser.parseUserExperiment(topologyFile)
        computerNodes = self.parser.getNodes("computer", "operational")
        experimentNodes = userExperiment.getExperimentNodes()

        # 2) Make sure that the experiment id for the new experiment is not the same as the experiment id for
        # any current experiments
        experiments = self.getExperimentEntries()
        for key in experiments.keys():
            if (key == userExperiment.getExperimentID()):
                print "experiment id already exists in testbed: " + userExperiment.getExperimentID()
                return -1

        # 3) Parse the current experiments file, check that there are no conflicts between these and the new
        # experiment and write this new experiment to the current experiments file
        if (self.parser.writeExperimentToCurrent(userExperiment) == -1):
            print "experiment conflicts with current experiments"
            return -1

        # 4) Create the experiment vlans on the switches
        # First retrieve the vlan information from the experimental interfaces, storing the information
        # in a list of VLAN objects
        vlanList = []
        for specificNodeTypeDictionary in experimentNodes.values():
            for node in specificNodeTypeDictionary.values():
                for interface in node.getNode().getInterfaces("experimental"):
                    if (interface.getVLAN() != ""):
                        newSwitch = interface.getSwitch()
                        newPort = Port(interface.getPort())
                        newVLANName = interface.getVLAN()

                        if (newVLANName != ""):
                            index = isVLANInList(newVLANName, vlanList)
                            # The vlan does not exist in the list, create it and append it
                            ports = []
                            ports.append(newPort)
                            if (index == -1):
                                switches = {}
                                switches[newSwitch] = ports
                                vlan = VLAN(newVLANName, switches)
                                vlanList.append(vlan)

                            else:
                                # The vlan already exists, add to it
                                vlanList[index].addPorts(ports, newSwitch)

        # Any possible vlan conflicts within the experiment have been resolved by addPorts. createVLAN
        # will ensure no conflicts with vlans currently on the switch
        switchNodes = self.getNodes("switch")
        for switchID in switchNodes.keys():
            for vlan in vlanList:
                vlanPorts = vlan.getPortsOnSwitch(switchID)
                # We now have ports to add on the switch
                if (vlanPorts != None):
                    vlanName = vlan.getName()
                    theSwitch = self.getNodeInstance(switchNodes[switchID])
                    if not theSwitch:
                        return -1
                    res = theSwitch.createVLAN(vlan)
                    if (res != 0):
                        print "returning -1"
                        return -1

        # 5,6) Create the netboot directories, symbolic links and startup script (the startup script includes
        # setting the node's host name and ifconfing the interface according to the IPs in the experiment
        for computerNode in experimentNodes["computer"].values():
            theNode = computerNode.getNode()
            nodeID = theNode.getNodeID()
            command = "hostname " + nodeID
            commandsList = []
            commandsList.append(command)
            self.__configNetboot.createNetbootInfo(nodeID, computerNode.getNetbootInfo())
            self.__configNetboot.createStartupCommands(nodeID, commandsList)
            self.__configNetboot.createStartupInterfaceConfig(nodeID, theNode.getInterfaces("experimental"))

        # 7) Copy the given file to the directory containing all experiment on the testbed and rename it. Do this
        #    only if the paths differ
        currentFile = str(os.getcwd()) + "/" + topologyFile + ".xml"
        newFile = self.__experimentPath + "/" + userExperiment.getExperimentID() + ".xml"
        command = "cp " + topologyFile + " " + newFile

        if (currentFile != newFile):
            if (commands.getstatusoutput(command)[0] != 0):
                print "error while copying topology file " + topologyFile
                return -1

        # 8) Add an entry to the main experiments file
        if (self.parser.writeExperimentEntry(userExperiment.getExperimentID(), newFile) != 0):
            print "error while writing new entry to main experiment topology file"
            return -1

        # 9) Power the nodes on (actually, do restart in case they were already on)
        for computerNode in experimentNodes["computer"].values():
            for node in computerNodes.values():
                if ((node.getNodeID() == computerNode.getNodeID()) and (node.getNetbootable() == "yes") ):
                    self.power(node.getNodeID(), "restart")

        return 0

    def experimentDelete(self, experimentID):
        """\brief Deletes an experiment from the testbed given its id. This involves the following steps:
                  1) Find the experiment's topology file
                  2) Parse the experiment's topology file
                  3) Remove VLANs
                  4) Remove netboot symoblic links and startup scripts
                  5) Turn nodes off
                  6) Remove the experiment topology file
                  7) Remove the experiment's entry from the main experiment topology file
        \param experimentID (\c string) The id of the experiment to delete
        \return (\c int) 0 if successful, -1 otherwise
        """
        computerNodes = self.parser.getNodes("computer", "operational")

        # 1) Find the xml file for the experiment from the main experiment topology file
        topologyFile = None
        experiments = self.getExperimentEntries()
        for key in experiments.keys():
            if (key == experimentID):
                topologyFile = experiments[key]
        if (topologyFile == None):
            print "experiment " + experimentID + " does not exist on the testbed, can't delete it"
            return -1

        # 2) Parse the experiment so that we can undo all the configuration done for it
        userExperiment = self.parser.parseUserExperiment(topologyFile)
        experimentNodes = userExperiment.getExperimentNodes()

        # 3) Remove VLANs. To do so, first create a dictionary whose keys are the unique vlan names and
        # whose vales are lists of the switches that each vlan belongs to, then remove the vlans
        vlanDictionary = {}
        for specificNodeTypeDictionary in experimentNodes.values():
            for node in specificNodeTypeDictionary.values():
                for interface in node.getNode().getInterfaces("experimental"):
                    vlanName = interface.getVLAN()
                    if (vlanName != None and vlanName != ""):
                        if (vlanDictionary.has_key(vlanName)):
                            if (interface.getSwitch() not in vlanDictionary[vlanName]):
                                 vlanDictionary[vlanName].append(interface.getSwitch())
                        else:
                            vlanDictionary[vlanName] = []
                            vlanDictionary[vlanName].append(interface.getSwitch())

        switchNodes = self.getNodes("switch")
        for switchID in switchNodes.keys():
            for vlanName in vlanDictionary.keys():
                for switch in vlanDictionary[vlanName]:
                    if (switch == switchID):
                        theSwitch = self.getNodeInstance(switchNodes[switchID])
                        if not theSwitch:
                            print "Could not create instance for node %s" % \
                                                                str(switchID)
                            return -1
                        if (theSwitch.deleteVLAN(vlanName) != 0):
                            print "henmanager.py::experimentDelete: error while deleting vlan " + vlanName + " from switch " + switchID
                            return -1

        # 4) Remove netboot symbolic links and startup scripts (only computer nodes)
        for computerNode in experimentNodes["computer"].values():
            theNode = computerNode.getNode()
            nodeID = theNode.getNodeID()
            self.__configNetboot.removeNetbootInfo(nodeID, 0)
            self.__configNetboot.deleteStartupFile(nodeID)

        # 5) Turn nodes off (only computer nodes)
        for computerNode in experimentNodes["computer"].values():
            for node in computerNodes.values():
                if ((node.getNodeID() == computerNode.getNodeID()) and (node.getNetbootable() == "yes") ):
                    self.power(node.getNodeID(), "poweroff")

        # 6) Remove the experiment file
        if (commands.getstatusoutput("rm " + topologyFile)[0] != 0):
            print "error while removing experiment file"
            return -1

        # 7) Remove the experiment's entry from the main experiment topology file
        if (self.parser.deleteExperimentEntry(experimentID) != 0):
            print "error while deleting entry from main experiment topology file for experiment " + experimentID

        # 8) Remove any entries in the current experiments file
        if (self.parser.deleteExperimentFromCurrent(experimentID) == -1):
            print "error while deleting experiment from current experiments file"
            return -1

        return 0

    def nodeConnectivity(self, nodeID):
        """ Prints out the devices connected to the interfaces of nodeID
        \param nodeID (\c string) The node id to print the ports off
        """
        node = self.__getNodeFromTestbed(nodeID)
        if node == None:
            print "Unknown node "+nodeID
            return
        
        num_ports = node.getSingleAttribute("numberports")
        if num_ports == None:
            print "no ports"
            return
        nodes = self.getNodes("all")
        ports = node.getInstance().getPorts()
#        print str(ports)

        def sortedDictKeys(adict):
            keys = adict.keys()
            keys.sort()
            return [adict[key] for key in keys]    

        sort_list = {}
        for p in ports:
            sort_list[ports[p].getId()]=ports[p].getName()
                
        for i in sortedDictKeys(sort_list):
            #i = ports[p].getName()
            string = str(i)+" "
            found = False
            items = {}
            if (nodes == None or nodes == -1):
                break

            for specificNodeDictionary in nodes.values():
                for other_node in specificNodeDictionary.values():
                    if (other_node.getNodeID() != node.getNodeID()):
                        peripheral_list = other_node.getPeripherals()
                        interface_list = other_node.getInterfaces("all")
                        
                    for peripheral in peripheral_list.values():
                        #print "peripheral",peripheral
                        if peripheral.getPeripheralID() == node.getNodeID():
                            if peripheral.getPeripheralRemotePort() == str(i):
                                
                                if not items.has_key(str(other_node.getNodeID())):
                                    items[str(other_node.getNodeID())] = 0
                                items[str(other_node.getNodeID())] += 1
                            #else:
                                #print peripheral
                    if interface_list != None:
                        for iface_types in interface_list.values():
                            if iface_types != None:
                                for iface in iface_types:
                                    if iface.getPort() == str(i) and iface.getSwitch() == node.getNodeID():
#                                        string +=  str(other_node.getNodeID()) + " "                                
                                        if not items.has_key(str(other_node.getNodeID())):
                                            items[str(other_node.getNodeID())] = 0
                                        items[str(other_node.getNodeID())] += 1
                        #else:
                        #    print "***",str(peripheral.getPeripheralRemotePort()),str(i)
            for item in items:
                string +=  str(item) + " "
            print string

    def getSupportedHardware(self, elementType = None):
        """ return a dictionary with the
        \appropriate values (vendor, make, model, functions)
        \from the hardware directory
        """
        modelsStruct = {}
        fullHardwareDir = self.__henRoot + "/lib/hardware"
        hardwareDir = "hardware"


        hardwareDirContent = dircache.listdir(fullHardwareDir)
        hardwareTypes = []

        for entry in hardwareDirContent :
            tokens = entry.split(".")
            if (len(tokens)==1) :
                hardwareTypes.append(entry)

        hardwareMakes = {}

        for hardwareType in hardwareTypes :
            files = dircache.listdir(fullHardwareDir + "/" + hardwareType)
            makes = []
            for file in files :
                tokens = file.split(".")
                if (len(tokens)==2) and (tokens[1]=="py") and (tokens[0]!="__init__") and (hardwareType[:-1]!=tokens[0]) and (hardwareType[:-2]!=tokens[0]) :
                    makes.append(tokens[0])

            if (len(makes)>0) :
                hardwareMakes[hardwareType] = makes

        modelsStruct.clear()

        for hardwareType in hardwareTypes :
            makes = hardwareMakes[hardwareType]
            aModel = {}
            for make in makes :
                classes = pyclbr.readmodule(hardwareDir+"."+hardwareType+"."+make)
                for key in classes.keys() :
                    classes[key] = []

                classNames = classes.keys()

                removeFromList = []
                for name in classNames :
                    obj = eval(make+"."+name+".functions")
                    if len(obj)==0 :
                        removeFromList.append(name)
                    else :
                        classes[name] = obj

                for entry in removeFromList :
                    del classes[entry]

                aModel[make] = classes

            modelsStruct[hardwareType] = aModel

        ret = {}
        for i in modelsStruct:
            if (i == "terminalservers"):
                ret["serial"] = modelsStruct[i]
            elif i.endswith("es"):
                ret[i.rstrip("es")] = modelsStruct[i]
            elif i.endswith("s"):
                ret[i.rstrip("s")] = modelsStruct[i]
            else:
                ret[i] = modelsStruct[i]

        if elementType == None:
            return ret
        else:
            return ret[elementType]

    def printSupportedHardware(self):

        hardwareTypes = self.__modelsStruct.keys()

        string = ""

        for hardwareType in hardwareTypes :
            string = string+"TYPE: "+hardwareType
            for make in self.__modelsStruct[hardwareType].keys() :
                string = string+"\n\tMAKE: "+make
                for model in self.__modelsStruct[hardwareType][make]:
                    string = string+"\n\t\tMODEL: "+model+"\tFUNCTIONS:"
                    for func in self.__modelsStruct[hardwareType][make][model] :
                        string = string+" "+func
            string = string+"\n"

        string = string[:-1]
        return string

    def portTest(self,tdr,device_str,interface_str):
        
        switch_str = ""
        port_str = ""

        computer = None
        interface = None
        switch = None
        port = None

        switch_obj = None

        manager = HenManager()
        manager.initLogging()
        nodes = manager.getNodes("all")

        for node_type in nodes:
            for node in nodes[node_type]:
                if nodes[node_type][node].getNodeID() == device_str:
                    computer = nodes[node_type][node]
        
	if computer == None:
	    return "Error(1) : Can't find "+device_str

        if computer != None:
            interfaces = computer.getInterfaces()
            for interface_type in interfaces:
                for iface in interfaces[interface_type]:
                    if iface.getInterfaceID() == interface_str:
                        switch_str = iface.getSwitch()
                        port_str = iface.getPort()

	if switch_str == "" or port_str == "":
	    return "Error(2) : Can't find interface for "+device_str+" "+interface_str
		
        for node_type in nodes:
            for node in nodes[node_type]:
                #print node,switch_str
                if nodes[node_type][node].getNodeID() == switch_str:
                    switch = nodes[node_type][node]

        if switch == None:
	    return "Error(3) : Can't find switch for "+device_str+" "+interface_str
        if switch != None:
            switch_obj = switch.getInstance()

        if switch_obj != None:
           port_internal_id = switch_obj.getPortInternalID(port_str)
           if (switch_obj.getPortStatus(port_str) == 1):
              status = "Up"
           else:
              status = "Down"
           #speed = switch_obj.getPortsSpeedByInternalID([port_internal_id])[0][1]
           if tdr:
	      tdr_responce = switch_obj.getPortTdr(port_str)
	      return "Port connected to "+str(device_str)+" "+str(interface_str)+" is "+str(status)+" and is connected to "+str(switch_str)+" "+str(port_str)+"\n"+str(tdr_responce[1])
	   return "Port connected to "+device_str+" "+interface_str+" is "+status
	else:
	   return "Error(4) : Can't find switch for "+device_str+" "+interface_str
	
    return_payload = None

    def vlan_create(self,vlan_str,user_str):
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)

        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.switchDaemon2[0]
        PORT = DaemonLocations.switchDaemon2[1]

        p.open(HOST,PORT)
        method = "vlan_create_vlan"
        payload = pickle.dumps((vlan_str,user_str))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return str(vlan_str) \
               +" "+str(user_str) \
               +str(return_payload)
    
    def port_list(self,switch_str):
        
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = pickle.loads(payload)
        
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.switchDaemon2[0]
        PORT = DaemonLocations.switchDaemon2[1]

        p.open(HOST,PORT)
        method = "port_list"
        payload = pickle.dumps((switch_str))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return str(switch_str) \
               +" port list is \n" \
               +str(return_payload)   
 
    def port_list_and_vlan(self,switch_str):
        
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = pickle.loads(payload)
        
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.switchDaemon2[0]
        PORT = DaemonLocations.switchDaemon2[1]

        p.open(HOST,PORT)
        method = "port_list_and_vlan"
        payload = pickle.dumps((switch_str))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return str(switch_str) \
               +" vlans on ports list is \n" \
               +str(return_payload)   
                                    
    def vlan_show_interface(self,device_str,interface_str=None):
        
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = pickle.loads(payload)
            
        switch_str = ""
        port_str = ""

        computer = None
        interface = None
        switch = None
        port = None

        switch_obj = None

        manager = HenManager()
        manager.initLogging()
        nodes = manager.getNodes("all")

        for node_type in nodes:
            for node in nodes[node_type]:
                if nodes[node_type][node].getNodeID() == device_str:
                    computer = nodes[node_type][node]
    
        iface_str = []
        switch_str = []
        port_str = []
        
        if computer == None:
            return "Error(1) : Can't find "+device_str

        if computer != None:
            interfaces = computer.getInterfaces()
            
            for interface_type in interfaces:
                for iface in interfaces[interface_type]:
                    #print iface.getInterfaceID(),interface_type
                    if iface.getInterfaceID() == interface_str:
                        iface_str.append(iface.getInterfaceID())
                        switch_str.append(iface.getSwitch())
                        port_str.append(iface.getPort())
                    elif interface_str == None:
                        iface_str.append(iface.getInterfaceID())
                        switch_str.append(iface.getSwitch())
                        port_str.append(iface.getPort())    

        #if switch_str == "" or port_str == "":		
        #    return "Error(2) : Can't find interface for "+device_str+" "+interface_str
        
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.switchDaemon2[0]
        PORT = DaemonLocations.switchDaemon2[1]

        p.open(HOST,PORT)
        method = "vlan_show_port"
        payload = pickle.dumps((device_str,iface_str))
        
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
        return_str = ""   
        
        #print return_payload 
        for i in range(0,len(return_payload)):
            return_str += str(device_str) \
                    +" "+str(iface_str[i]) \
                    +" is " \
                    +str(return_payload[i])+"\n"
        return return_str
        
    def vlan_show_port(self,device_str,*args):
        
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = pickle.loads(payload)

        #device_str = ""
        interface_str = ""
        if len(args) != 1:
            for arg in args:
                interface_str += arg + " "
            interface_str = interface_str.rstrip()
        else:
            interface_str = args[0]
            
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.switchDaemon2[0]
        PORT = DaemonLocations.switchDaemon2[1]

        p.open(HOST,PORT)
        method = "vlan_show_port"
        payload = pickle.dumps((device_str,interface_str))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return str(device_str) \
               +" "+str(interface_str) \
               +" is " \
               +str(return_payload[0])

    def vlan_show_name(self,vlan_str):
        
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)
            
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.switchDaemon2[0]
        PORT = DaemonLocations.switchDaemon2[1]

        p.open(HOST,PORT)
        method = "vlan_show_name"
        payload = pickle.dumps((vlan_str))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return str(vlan_str) \
               +" is on : \n" \
               +str(return_payload)

    def vlan_show_empty(self,switch_str):
        
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)
            
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.switchDaemon2[0]
        PORT = DaemonLocations.switchDaemon2[1]

        p.open(HOST,PORT)
        method = "vlan_show_empty"
        payload = pickle.dumps((switch_str))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return str(switch_str) \
               +" is on : \n" \
               +str(return_payload)

    def vlan_show_user(self,user_str):
        
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)
            
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.switchDaemon2[0]
        PORT = DaemonLocations.switchDaemon2[1]

        p.open(HOST,PORT)
        method = "vlan_show_user"
        payload = pickle.dumps((user_str))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return str(user_str) \
               +" has the following vlans : " \
               +str(return_payload)

    def vlan_next_free_id(self):
        
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)
            
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.switchDaemon2[0]
        PORT = DaemonLocations.switchDaemon2[1]

        p.open(HOST,PORT)
        method = "vlan_next_free_id"
        payload = pickle.dumps(("empty"))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return "the next free id is "+str(return_payload)


    def vlan_add(self,vlan_str,user_str,tagged_str,device_str,*args):    
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)

        interface_str = ""
        if len(args) != 1:
            for arg in args:
                interface_str += arg + " "
            interface_str = interface_str.rstrip()
        else:
            interface_str = args[0]

	p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.switchDaemon2[0]
        PORT = DaemonLocations.switchDaemon2[1]

        p.open(HOST,PORT)
        method = "vlan_add_port"
        #print vlan_str,user_str,tagged_str,device_str,interface_str
        payload = pickle.dumps((vlan_str,user_str,tagged_str,device_str,interface_str))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return str(device_str) \
               +" "+str(interface_str) \
               +" is a " \
               +str(pickle.loads(return_payload))

    def vlan_connect(self,vlan_str,user_str,device_str_1,interface_str_1,device_str_2,interface_str_2):    
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)

        p = auxiliary.protocol.Protocol(None)
        
        HOST = DaemonLocations.switchDaemon2[0]
        PORT = DaemonLocations.switchDaemon2[1]

        p.open(HOST,PORT)
        method = "vlan_connect_ports"
        #print vlan_str,user_str,tagged_str,device_str,interface_str
        payload = pickle.dumps((vlan_str,user_str,device_str_1,interface_str_1,device_str_2,interface_str_2))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return str(device_str_1) \
               +" "+str(interface_str_1) \
               +" is a " \
               +str(pickle.loads(return_payload))

    def vlan_remove(self,vlan_str,user_str,tagged_str,device_str,*args):    
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)

        interface_str = ""
        if len(args) != 1:
            for arg in args:
                interface_str += arg + " "
            interface_str = interface_str.rstrip()
        else:
            interface_str = args[0]

	p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.switchDaemon2[0]
        PORT = DaemonLocations.switchDaemon2[1]

        p.open(HOST,PORT)
        method = "vlan_remove_port"
        #print vlan_str,user_str,tagged_str,device_str,interface_str
        payload = pickle.dumps((vlan_str,user_str,tagged_str,device_str,interface_str))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return str(device_str) \
               +" "+str(interface_str) \
               +" is a " \
               +str(return_payload)

    def vlan_port_mode_set(self,mode,device_str,*args):    
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)

        interface_str = ""
        if len(args) != 1:
            for arg in args:
                interface_str += arg + " "
            interface_str = interface_str.rstrip()
        else:
            interface_str = args[0]

	p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.switchDaemon2[0]
        PORT = DaemonLocations.switchDaemon2[1]

        p.open(HOST,PORT)
        method = "vlan_port_mode_set"
        payload = pickle.dumps((mode,device_str,interface_str))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return str(device_str) \
               +" "+str(interface_str) \
               +" is a " \
               +str(return_payload)

    def vlan_port_mode_get(self,device_str,*args):    
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)

        interface_str = ""
        if len(args) != 1:
            for arg in args:
                interface_str += arg + " "
            interface_str = interface_str.rstrip()
        else:
            interface_str = args[0]

	p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.switchDaemon2[0]
        PORT = DaemonLocations.switchDaemon2[1]

        p.open(HOST,PORT)
        method = "vlan_port_mode_get"
        payload = pickle.dumps((device_str,interface_str))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return str(device_str) \
               +" "+str(interface_str) \
               +" is a " \
               +str(return_payload)

    def convertToDate(self,string):
        dates = string.split("/")
        return datetime.date(int(dates[2]), int(dates[1]), int(dates[0]))
        

    def reservation_update(self, username, reservation_id, op_type, device_list, email):
        def handler(code, seq, sz,payload):
            global return_payload

            return_payload = pickle.loads(payload)
        devices = device_list.split(",")
        #endDate = self.convertToDate(end_date_str)
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.reservationDaemon[0]
        PORT = DaemonLocations.reservationDaemon[1]

        p.open(HOST,PORT)
        method = "update"
        payload = pickle.dumps((username, reservation_id, op_type, devices, email))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
        
        return str(return_payload)        

    def reservation_reserve(self,username,device_list,end_date_str,email):
        def handler(code, seq, sz,payload):
            global return_payload

            return_payload = pickle.loads(payload)
        devices = device_list.split(",")
        endDate = self.convertToDate(end_date_str)
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.reservationDaemon[0]
        PORT = DaemonLocations.reservationDaemon[1]

        p.open(HOST,PORT)
        method = "reserve"
        payload = pickle.dumps((username, devices, endDate, email))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
        
        return str(return_payload)
        
    def reservation_release(self,username,reservation_id):
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = pickle.loads(payload)
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.reservationDaemon[0]
        PORT = DaemonLocations.reservationDaemon[1]

        p.open(HOST,PORT)
        method = "release"
        payload = pickle.dumps((username, reservation_id))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return str(return_payload)
    
    def reservation_renew(self,username,reservation_id,end_date_str):
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = pickle.loads(payload)
        p = auxiliary.protocol.Protocol(None)
        endDate = self.convertToDate(end_date_str)
        HOST = DaemonLocations.reservationDaemon[0]
        PORT = DaemonLocations.reservationDaemon[1]

        p.open(HOST,PORT)
        method = "renew"
        payload = pickle.dumps((username,reservation_id,endDate))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return str(return_payload)
    
    def reservation_whohas(self,device_list):
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = pickle.loads(payload)
        devices = device_list.split(",")
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.reservationDaemon[0]
        PORT = DaemonLocations.reservationDaemon[1]

        p.open(HOST,PORT)
        method = "whohas"
        payload = pickle.dumps((devices))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()

        string = ""
        
        for device in return_payload:
            if device[1] == None:
                string = string + str(device[0]) + " is free\n"
            else:
                string = string + str(device[0]) + " in use by " + str(device[1])+"\n"
            
        return string.rstrip()
    
    def reservation_inuseby(self,username):
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.reservationDaemon[0]
        PORT = DaemonLocations.reservationDaemon[1]
        
        p.open(HOST,PORT)
        method = "inuseby"
        payload = pickle.dumps((username))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
        result = pickle.loads(return_payload)
        string = str(username)+" has "
        if len(result) == 0:
            return string + "no machines."
        for i in result:
            string = string + str(i) + ","
        
        return str(string.rstrip(","))

    def reservation_notinuse(self,options=None):
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.reservationDaemon[0]
        PORT = DaemonLocations.reservationDaemon[1]

        p.open(HOST,PORT)
        method = "notinuse"
        payload = pickle.dumps(())
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
        
        result = pickle.loads(return_payload)
        string = "The following machines are free : "
        dev_list = {}
        if len(result) == 0:
            return string + "No machines are free."
        if (options == None):
            for i in result:
                string = string + str(i) + " , "
        elif (options == "models"):
            
            for i in result:
                node = self.__getNodeFromTestbed(i)
                if node != None:
                    m = node.getVendor() + " " +node.getModel()
                    if m == " ":
                        m = "unknown"
                    if not dev_list.has_key(m):
                        dev_list[m] = []
                    dev_list[m].append(i)
                    
                else:
                    print "unknown node",i
            for k in dev_list.keys():
                string = string + "\n"
                string = string + str(k) + ": "
                for m in dev_list[k] :
                    string = string + str(m) + " , "
                string = string.rstrip(" ,")
        return str(string.rstrip(" ,"))

    def reservation_notinuse_power(self,options):
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.reservationDaemon[0]
        PORT = DaemonLocations.reservationDaemon[1]

        p.open(HOST,PORT)
        method = "notinuse"
        payload = pickle.dumps(())
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
        
        result = pickle.loads(return_payload)
        string = "The following free machines are in the following power state : "
        dev_list = {}
        
        for i in result:
            (status, res) = self.powerSilent(i, options)
            if res:
                print "%s: %s" % (i, res)
        return str(string.rstrip(" ,"))
    
    def reservation_cleanexpired(self):
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = str(payload)
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.reservationDaemon[0]
        PORT = DaemonLocations.reservationDaemon[1]

        p.open(HOST,PORT)
        method = "cleanexpired"
        payload = pickle.dumps(())
        p.sendRequest(method,payload,handler)
        p.readAndProcess()

        result = pickle.loads(return_payload)
        print result
        string = "The following machines are free : "
        if len(result) == 0:
            return string + "No machines are free."
        for i in result:
            string = string + str(i) + " , "
        
        return str(string.rstrip(","))


    def reservation_show(self,username):
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = pickle.loads(payload)
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.reservationDaemon[0]
        PORT = DaemonLocations.reservationDaemon[1]

        p.open(HOST,PORT)
        method = "show"
        payload = pickle.dumps((username))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
            
        return str(return_payload)

    def power(self,username,action,args):
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = pickle.loads(payload)

        p = auxiliary.protocol.Protocol(None)

#        HOST = DaemonLocations.powerDaemon[0]
#        PORT = DaemonLocations.powerDaemon[1]
        HOST = "localhost"
        PORT = 156016

        p.open(HOST,PORT)
        method = action
        payload = pickle.dumps((username, args))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()

        return str(return_payload)

    def get_free(self,obj_class,type):
        
            
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = pickle.loads(payload)

        if obj_class == "ip":
            method = "get_free_ip"
        
        p = auxiliary.protocol.Protocol(None)

        HOST = DaemonLocations.autodetectDaemon[0]
        PORT = DaemonLocations.autodetectDaemon[1]
                
        p.open(HOST,PORT)
        
        payload = pickle.dumps((type))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
                
        return str(return_payload)

    def reload(self):
        def handler(code, seq, sz,payload):
            global return_payload
            return_payload = pickle.loads(payload)
        p = auxiliary.protocol.Protocol(None)
        method = "reload"
        daemons = []
        return_str = ""
        # autodetection daemon
        daemons.append((DaemonLocations.autodetectDaemon[0],DaemonLocations.autodetectDaemon[1]))
        for d in daemons:
            HOST = d[0] #DaemonLocations.autodetectDaemon[0]
            PORT = d[1] #DaemonLocations.autodetectDaemon[1]

            p.open(HOST,PORT)

            payload = pickle.dumps((type))
            p.sendRequest(method,payload,handler)
            p.readAndProcess()
            return_str = return_str + " " + str(return_payload)
            
        return return_str 
    

#######################################################################################################
#
#  PRIVATE FUNCTIONS
#
#######################################################################################################
    def __findSuperClassName(self, elementID):
        """\brief Given an element id, figures out whether the element is a node,
                  an infrastructure or a fileNode.
        \param elementID (\c string) The id of the element whose super class name is to be found
        \return (\c string) The name of the superclass, or None if the element is not part of the testbed
        """
        nodes = self.getNodes("all", "all")
        for nodeType in nodes.values():
            for node in nodeType.values():
                if (node.getNodeID() == elementID):
                    return "node"

        infrastructures = self.getInfrastructures("all", "all")
        for infrastructureType in infrastructures.values():
            for infrastructure in infrastructureType.values():
                if (infrastructure.getID() == elementID):
                    return "infrastructure"

        fileNodes = self.getFileNodes("all", "all")
        for fileNodeType in fileNodes.values():
            for fileNode in fileNodeType.values():
                if (fileNode.getID() == elementID):
                    return "fileNode"

        return None

    def __deleteNode(self, nodeID):
        """\brief Removes a node's physical xml file and its entry from the testbed's main physical topology file. The
                  function then restarts both dhcp and dns servers to reflect these changes.
        \param nodeID (\c string) The id of the node to delete
        \return (\c int) 0 if successful, -1 otherwise
        """
    # Remove the node's configuration (xml) file
        command = "rm " + self.__physicalPath + "/" + nodeID + ".xml"
        if (commands.getstatusoutput(command)[0] != 0):
            print "HenManager::__deleteNode: error while removing xml file for node " + nodeID
            return (-1, "HenManager::__deleteNode: error while removing xml file for node " + str(nodeID))

    # Remove the node's entry from the main physical topology XML file
        self.parser.deletePhysicalEntry(nodeID)

        # save rebooting the dhcp and dns servers for a 'lowly' mote
        if nodeID.find("mote") == 0:
            print nodeID + ": deleted"
            return 0

    # Generate current dhcp files from XML files and restart dhcp server
        if (self.dhcpServer("create") == -1):
            print "HenManager::__deleteNode: error while creating dhcp configuration"
            return (-1, "HenManager::__deleteNode: error while creating dhcp configuration")

        if (self.dhcpServer("restart") == -1):
            print "HenManager::__deleteNode: error while restarting dhcp server"
            return (-1, "HenManager::__deleteNode: error while restarting dhcp server")

    # Generate current dns files from XML files and restart dns server
        if (self.dnsServer("create") == -1):
            print "HenManager::__deleteNode: error while creating dns configuration"
            return (-1, "HenManager::__deleteNode: error while creating dns configuration")

        if (self.dnsServer("restart") == -1):
            print "HenManager::__deleteNode: error while restarting dns server"
            return (-1, "HenManager::__deleteNode: error while restarting dns server")

        print "HenManager::__deleteNode: " + nodeID + ": deleted"
        return (0, str(nodeID))

    def __writeDHCPConfigFile(self):
        """\brief Writes the dhcp config file
        """
        from operatingsystem.dhcp import DHCPConfigWriter

        expSubnet = DHCPConfigSubnetInfo(self.__configFile.get('DHCP', 'EXPERIMENTAL_NET'), \
                                         self.__configFile.get('DHCP', 'EXPERIMENTAL_NET_NETMASK'), \
                                         self.__configFile.get('DHCP', 'EXPERIMENTAL_USE_HOST_DECL_NAMES'), \
                                         self.__configFile.get('DHCP', 'EXPERIMENTAL_NET_NETMASK'), \
                                         self.__configFile.get('DHCP', 'EXPERIMENTAL_NET_BROADCAST_ADDRESS'), \
                                         self.__configFile.get('DHCP', 'EXPERIMENTAL_DOMAIN_NAME'), \
                                         self.__configFile.get('DHCP', 'EXPERIMENTAL_ROUTERS'), \
                                         self.__configFile.get('DHCP', 'EXPERIMENTAL_NEXT_SERVER'), \
                                         "experimental")

        infraSubnet = DHCPConfigSubnetInfo(self.__configFile.get('DHCP', 'INFRASTRUCTURE_NET'), \
                                           self.__configFile.get('DHCP', 'INFRASTRUCTURE_NET_NETMASK'), \
                                           self.__configFile.get('DHCP', 'INFRASTRUCTURE_USE_HOST_DECL_NAMES'), \
                                           self.__configFile.get('DHCP', 'INFRASTRUCTURE_NET_NETMASK'), \
                                           self.__configFile.get('DHCP', 'INFRASTRUCTURE_NET_BROADCAST_ADDRESS'), \
                                           self.__configFile.get('DHCP', 'INFRASTRUCTURE_DOMAIN_NAME'), \
                                           self.__configFile.get('DHCP', 'INFRASTRUCTURE_ROUTERS'), \
                                           self.__configFile.get('DHCP', 'INFRASTRUCTURE_NEXT_SERVER'), \
                                           "infrastructure")

        virtualSubnet = DHCPConfigSubnetInfo(self.__configFile.get('DHCP', 'VIRTUAL_NET'), \
                                         self.__configFile.get('DHCP', 'VIRTUAL_NET_NETMASK'), \
                                         self.__configFile.get('DHCP', 'VIRTUAL_USE_HOST_DECL_NAMES'), \
                                         self.__configFile.get('DHCP', 'VIRTUAL_NET_NETMASK'), \
                                         self.__configFile.get('DHCP', 'VIRTUAL_NET_BROADCAST_ADDRESS'), \
                                         self.__configFile.get('DHCP', 'VIRTUAL_DOMAIN_NAME'), \
                                         self.__configFile.get('DHCP', 'VIRTUAL_ROUTERS'), \
                                         self.__configFile.get('DHCP', 'VIRTUAL_NEXT_SERVER'), \
                                         "virtual")
        subnetList = []
        subnetList.append(expSubnet)
        subnetList.append(infraSubnet)
        subnetList.append(virtualSubnet)


        configInfo = DHCPConfigInfo(self.__configFile.get('DHCP', 'DOMAIN_NAME'), \
                                    self.__configFile.get('DHCP', 'DOMAIN_NAME_SERVERS'), \
                                    self.__configFile.get('DHCP', 'DEFAULT_LEASE_TIME'), \
                                    self.__configFile.get('DHCP', 'MAXIMUM_LEASE_TIME'), \
                                    self.__configFile.get('DHCP', 'AUTHORITATIVE'), \
                                    self.__configFile.get('DHCP', 'DDNS_UPDATE_STYLE'), \
                                    self.__configFile.get('DHCP', 'LOG_FACILITY'), \
                                    subnetList)

        writer = DHCPConfigWriter(configInfo, self.__configFile.get('DHCP', 'CONFIG_FILE_PATH'), self.__henExportPath,  self.__testbedGroup, self.parser)
        writer.writeDHCPConfig()


    def __writeDNSConfigFiles(self):
        """\brief Writes the dns config file
        """
        from operatingsystem.dns import DNSConfigWriter

        configInfo = DNSConfigInfo(self.__configFile.get('DNS', 'TTL'), \
                                   self.__configFile.get('DNS', 'CONTACT'), \
                                   self.__configFile.get('DNS', 'REFRESH_TIME'), \
                                   self.__configFile.get('DNS', 'RETRY_TIME'), \
                                   self.__configFile.get('DNS', 'EXPIRY_TIME'), \
                                   self.__configFile.get('DNS', 'MINIMUM_TIME'), \
                                   self.__configFile.get('MAIN', 'EXPERIMENTAL_BASE_ADDRESS'), \
                                   self.__configFile.get('DNS', 'EXPERIMENTAL_DOMAIN_NAME'), \
                                   self.__configFile.get('DNS', 'EXPERIMENTAL_SERVER_ADDRESS'), \
                                   self.__configFile.get('MAIN', 'INFRASTRUCTURE_BASE_ADDRESS'), \
                                   self.__configFile.get('DNS', 'INFRASTRUCTURE_DOMAIN_NAME'), \
                                   self.__configFile.get('DNS', 'INFRASTRUCTURE_SERVER_ADDRESS'), \
                                   self.__configFile.get('MAIN', 'VIRTUAL_BASE_ADDRESS'), \
                                   self.__configFile.get('DNS', 'VIRTUAL_DOMAIN_NAME'), \
                                   self.__configFile.get('DNS', 'VIRTUAL_SERVER_ADDRESS'))

        writer = DNSConfigWriter(configInfo, self.__configFile.get('DNS', 'CONFIG_FILES_PATH'), self.__testbedGroup, self.parser)
        writer.writeDNSConfig()

    def __getNextInfrastructureID(self, infrastructureType, minimumNumber):
        """\brief Returns a string containing the number of the highest-numbered infrastructure plus 1
        \param infrastructureType (\c string) The type of the infrastructure (rack, etc)
        \param minimumNumber (\c string) The minimum starting number for the infrastructure type given
        \return (\c string) A number representing the next infrastructure number to use for a new infrastructure,
                            or -1 if an error occurs while reading the physical topology file
        """
        highestNumber = int(minimumNumber)
        infrastructures = self.getInfrastructures(infrastructureType)
        if (infrastructures == None or infrastructures == -1):
            return infrastructureType + str(minimumNumber)

        for infrastructure in infrastructures.values():
            infrastructureNumber = int(infrastructure.getID()[len(infrastructureType):])
            if (infrastructureNumber > highestNumber):
                highestNumber = infrastructureNumber

        testInfrastructureID = infrastructureType + str(minimumNumber)
        if ((highestNumber == int(minimumNumber)) and (not(self.__isInfrastructureInTestbed(testInfrastructureID)))):
            return infrastructureType + str(minimumNumber)
        else:
            return infrastructureType + str(highestNumber + 1)

    def __getNextNodeID(self, nodeType, minimumNumber):
        """\brief Returns a string containing the number of the highest-numbered node plus 1
        \param nodeType (\c string) The type of the node (computer, serial, etc)
        \param minimumNumber (\c string) The minimum starting number for the node type given
        \return (\c string) A number representing the next node number to use for a new node,
                            or -1 if an error occurs while reading the physical topology file
        """
        highestNumber = int(minimumNumber)
        nodes = self.getNodes(nodeType)
        if (nodes == None or nodes == -1):
            return nodeType + str(minimumNumber)

        for node in nodes.values():
            nodeID = node.getNodeID()
            # Ignore any nodes whose names don't have the type in them (ibex, etc)
            if (nodeID.find(nodeType) != -1):
                #nodeNumber = int(nodeID[len(nodeType):])
                nodeNumber = int(re.compile("\d+$").search(nodeID).group(0))
                if (nodeNumber > highestNumber):
                    highestNumber = nodeNumber

        testNodeID = nodeType + str(minimumNumber)
        if ((highestNumber == int(minimumNumber)) and (not(self.__isNodeInTestbed(testNodeID)))):
            return nodeType + str(minimumNumber)
        else:
            return nodeType + str(highestNumber + 1)

    def __getNextFileNodeID(self, fileNodeType, minimumNumber):
        """\brief Returns a string containing the number of the highest-numbered fileNode plus 1
        \param fileNodeType (\c string) The type of the fileNode (computer, serial, etc)
        \param minimumNumber (\c string) The minimum starting number for the fileNode type given
        \return (\c string) A number representing the next fileNode number to use for a new fileNode,
                            or -1 if an error occurs while reading the physical topology file
        """
        highestNumber = int(minimumNumber)
        fileNodes = self.getFileNodes(fileNodeType)
        if (fileNodes == None or fileNodes == -1):
            return fileNodeType + str(minimumNumber)

        for fileNode in fileNodes.values():
            fileNodeNumber = int(fileNode.getID()[len(fileNodeType):])
            if (fileNodeNumber > highestNumber):
                highestNumber = fileNodeNumber

        testFileNodeID = fileNodeType + str(minimumNumber)
        if ((highestNumber == int(minimumNumber)) and (not(self.__isFileNodeInTestbed(testFileNodeID)))):
            return fileNodeType + str(minimumNumber)
        else:
            return fileNodeType + str(highestNumber + 1)

    def __getNextIPAddress(self, baseAddress, minimumNumber):
        """\brief Derives what the next available IP address is on the testbed. Returns a string
                  with the IP address or -1 of an error occurs
        \param ipType (\c string) A partial IP address such as 192.168.0
        \param minimumNumber (\c string) Used to derive the minimum IP address. This consists
                                         of the base address concatenated with the minimumNumber
        \return (\c string) A string representing the IP address (-1 if an error occurs)
        """
        nodes = self.getNodes("all")
        increment = False

        if (nodes == None or nodes == -1):
            return baseAddress + "." + minimumNumber

        highestIPAddress = baseAddress + "." + minimumNumber
        for specificNodeDictionary in nodes.values():
            for node in specificNodeDictionary.values():
                for specificInterfaceList in node.getInterfaces("all").values():
                    if (specificInterfaceList):
                        for interface in specificInterfaceList:
                            ipAddress = interface.getIP()
                            if (ipAddress.find(baseAddress) != -1):
                                if (isHigherIPAddress(ipAddress, highestIPAddress)):
                                    highestIPAddress = ipAddress
                                elif (ipAddress == highestIPAddress):
                                    increment = True

        if (increment == True):
            return incrementIPAddress(highestIPAddress)

        if (highestIPAddress == (baseAddress + "." + minimumNumber)):
            return baseAddress + "." + minimumNumber
        else:
            return incrementIPAddress(highestIPAddress)

    def __isMACAddressInTestbed(self, macAddress):
        """ Returns whether the given mac address belongs to any of the nodes currently in the testbed
        \param macAddress (\c string) The mac address to search for
        \return (\c boolean) True if the mac address belongs to a node on the tesbed, False otherwise
        """
        nodes = self.getNodes("all")
        if (nodes == None or nodes == -1):
            return False

        for specificNodeDictionary in nodes.values():
            for node in specificNodeDictionary.values():
                for specificInterfaceList in node.getInterfaces("all").values():
                    if (specificInterfaceList):
                        for interface in specificInterfaceList:
                            if (interface.getMAC().upper() == macAddress.upper()):
                                return True
        return False

    def __isInfrastructureInTestbed(self, infrastructureID):
        """ Returns whether an infrastructure with the given id exists on the testbed
        \param infrastructureID (\c string) The infrastructure id to search for
        \param (\c boolean) True if the infrastructure id is found, False otherwise
        """
        infrastructures = self.getInfrastructures("all")
        if (infrastructures == None or infrastructures == -1):
            return False

        for specificInfrastructureDictionary in infrastructures.values():
            for infrastructure in specificInfrastructureDictionary.values():
                if (infrastructure.getID() == infrastructureID):
                    return True
        return False

    def __isNodeInTestbed(self, nodeID):
        """ Returns whether a node with the given node id exists on the testbed
        \param nodeID (\c string) The node id to search for
        \param (\c boolean) True if the node id is found, False otherwise
        """
        nodes = self.getNodes("all", "all")
        if (nodes == None or nodes == -1):
            return False

        for specificNodeDictionary in nodes.values():
            #for node in specificNodeDictionary.values():
            #    if (node.getNodeID() == nodeID):
            #        return True
            if specificNodeDictionary.has_key(nodeID) :
                return True
        return False

    def __isFileNodeInTestbed(self, fileNodeID):
        """ Returns whether a file node with the given id exists on the testbed
        \param fileNodeID (\c string) The file node id to search for
        \param (\c boolean) True if the file node id is found, False otherwise
        """
        fileNodes = self.getFileNodes("all", "all")
        if (fileNodes == None or fileNodes == -1):
            return False

        for specificFileNodeDictionary in fileNodes.values():
            for fileNode in specificFileNodeDictionary.values():
                if (fileNode.getID() == fileNodeID):
                    return True
        return False

    def __getNodeFromTestbed(self, nodeID):
        """ Returns a node object for the given node id
        \param nodeID (\c string) The node id to search for
        \param (\c Node) Node if the node id is found, None otherwise
        """
        nodes = self.getNodes("all", "all")
        if (nodes == None or nodes == -1):
            return None

        for specificNodeDictionary in nodes.values():
            #for node in specificNodeDictionary.values():
            #    if (node.getNodeID() == nodeID):
            #        return node
            # WTF?!?
            if specificNodeDictionary.has_key(nodeID) :
                return specificNodeDictionary[nodeID]
        return None

    def pingInfrastructureNode(self,n):
        ip = n.getInterfaces("infrastructure")[0].getIP()
        if ((commands.getstatusoutput("ping  -W 2 -q -c 1 "+ip)[0]) != 0):
            #log.debug("PING FAILURE")
            return False
        #log.debug("PING SUCCESS")
        return True