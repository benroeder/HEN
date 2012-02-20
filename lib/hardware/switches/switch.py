##################################################################################################################
# switch.py: contains the switch superclass
#
# CLASSES
# --------------------------------------------------------------------
# Switch                 The super class for any switch in the testbed. The data structures for the switches are
#                        arranged into the following levels of inheritance: the first level consists of this class;
#                        the second level consists of subclasses based on a particular manufacturer (extreme for
#                        example); and the third level consists of sub-subclasses based on a particular modl of
#                        switch (extreme summit for instance). Any SNMP operations based on standard mibs will be
#                        found here; any SNMP operations based on proprietary mibs will be found in the manufacturer
#                        subclasses; the specific switch model sub-subclasses will contains things like the number and
#                        type of ports, etc.
#
# FUNCTIONS
# --------------------------------------------------------------------
# see https://frostie.cs.ucl.ac.uk/nets/hen/wiki/HenDesignHardwareInterfacesEthernetSwitch for details
#
##################################################################################################################

import commands, os, string, operator
from hardware.device import Device
from array import *
from struct import *

from auxiliary.hen import MACTableEntry, SimplePort
from auxiliary.snmp import SNMP
from auxiliary.oid import OID

from pysnmp.proto import rfc1902
from pysnmp.smi import builder
import logging

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)


###########################################################################################
#   CLASSES
###########################################################################################
class Switch(Device):
    """\brief Superclass for any switch in the testbed
    This class implements methods to retrieve information from a switch using SNMP version 1. In
    addition, it acts as a super class for all types of switches in the testbed
    """
    functions = []
    mask = [128,64,32,16,8,4,2,1,0]
    inv_mask = [127,191,223,239,247,251,254,255]

    def __init__(self, switchNode, minimumVLANInternalID, maximumVLANInternalID, minimumInterfaceInternalID, maximumInterfaceInternalID):
        """\brief Initializes the class
        \param switchNode (\c SwitchNode) The SwitchNode object to obtain information from to initialize the class with
        \param macIDLength (\c int) The length of the id of an snmp result coming from a mac address query. The id is
                                    anything to the left of the equal sign, and its length is the number of dot-separated
                                    terms.
        """
        if (switchNode.getInfrastructure() == "yes"):
            self.__ipAddress = switchNode.getInterfaces("infrastructure")[0].getIP()
        else:
            self.__ipAddress = switchNode.getInterfaces("management")[0].getIP()

        self.__switchName = switchNode.getNodeID()
        self.snmp = SNMP(switchNode.getSNMPwriteCommunity(),self.__ipAddress)

        # cache of static tables
        self.__refresh = True # reload
        self.__dot1dBasePortIfIndex = None
        self.__ifDescr = None
        self.__ifName = None
        self.__dot1qVlanStaticUntaggedPorts = None
        self.__dot1qVlanStaticEgressPorts = None
        self.__dot1qPvid = None
        self.__dot1qTpFdbPort = None
        self.__dot1qTpFdbStatus = None
        self.__dot1qVlanFdbId = None
        self.__dot1qVlanStaticName = None
        
        # ports
        self.__ports = {}
        self.refreshPortInfo()
        # vlans
        self.__vlans = {}
        
# Informational commands
            
    def getSwitchName(self,use_snmp=False):
        """\brief Retrieves the switch's name
        \param use_snmp (\c boolean) if True read value from switch.
        \return (\c string) The switch's name
        """

        if use_snmp:
            return self.snmp.get(OID.sysName)[0][1]
        else:
            return self.__switchName
        
    def setSwitchName(self,name,commit=False):
        """\brief Sets the switch's name, and commits to the hardware if commit is True
        \param name (\c string) The switch's name
        \param commit (\c boolean) If True apply to hardware
        \return (\c int) Returns 0 if successful, -1 if unsuccessful
        """
        self.__switchName = name
        if commit:
            self.snmp.set(OID.sysName,rfc1902.OctetString(name))
            return self.snmp.getErrorStatus()
        return

    def getPorts(self):
        return self.__ports

    def getPort(self,local_id):
        return self.__ports[local_id]

    def getPortByName(self,i):
        for port in self.__ports:
            if str(self.__ports[port].getName()) == str(i):
                return self.__ports[port]
        return None
    
    def addPort(self,port):
        self.__ports[port.getId()] = port

    def clearPorts(self):
        self.__ports = {}

    def resetPortsVlanInfo(self):
        for port in self.__ports:
            self.__ports[port].setUntagged((None,None))
            self.__ports[port].setPvid((None,None))
            self.__ports[port].setTagged([])

    def resetPortsMacInfo(self):
        for port in self.__ports:
            self.__ports[port].setMacs([])

    def getPortsVlanMode(self):
        return None

    def getPortVlanMode(self,pid):
        return 0
    
    def setPortVlanMode(self,pid,mode):
        return 0
                    
    
    def refreshPortInfo(self):
        """\brief Refreshes the port list for the switch`
        """
        self.clearPorts()
        #log.debug("Creating ports")
        ifname_table = self.getPortNames()
        iftype_table = self.snmp.walk(OID.ifType)
        portsvlanmode_table = self.getPortsVlanMode()
        
        ethernet_ports = []
        for iftype in iftype_table:
            if str(iftype[0][1]) == "6":
                ethernet_ports.append(iftype[0][0][-1])
        
        for ifname in ifname_table:
            if int(ifname[0][0][-1]) in ethernet_ports:
                sp = SimplePort(ifname[0][1],ifname[0][0][-1],self.getNodeID())
                self.addPort(sp)

        if portsvlanmode_table != None:
            for portmode in portsvlanmode_table:
                sp = self.getPort(portmode[0][0][-1])
                sp.setVlanMode(int(portmode[0][1]))
                
    def getVlans(self):
        return self.__vlans

    def getVlan(self,ident):
        return self.__vlans[ident]

    def getVlanByName(self,name):
        for v_id in self.__vlans:
            if str(self.__vlans[v_id].getName()) == name:
                log.debug("Vlan name "+str(name)+" id "+str(v_id)+" "+str(self.__vlans[v_id]))
                return self.__vlans[v_id]
        return None
    
    def addVlan(self,vlan):
        self.__vlans[vlan.getLocalId()] = vlan

    def clearVlans(self):
        self.__vlans = {}

    def getNodeID(self):
        return self.__switchName
    
    def setIPAddress(self, i):
        """\brief Sets the ip address of the switch's management interface and updates the snmp command accordingly
        \param i (\c string) The ip address of the switch's management interface
        """
        self.__ipAddress = i
        self.snmp.setIpAddress(i)

    def getIPAddress(self):
        """\brief Gets the ip address of the switch's management interface
        \return (\c string) The ip address of the switch's management interface
        """ 
        return self.__ipAddress

    def getNumberofPorts(self):
        """\brief Retrieves the number of ports on the switch
        \return (\c string) The number of ports on the switch
        """
        return self.snmp.get(OID.dot1dBaseNumPorts)[0][1]

    def getSwitchDescription(self):
        """\brief Retrieves the switch's description
        \return (\c string) The switch's description
        """
        return self.snmp.get(OID.sysDescr)[0][1]

    def setSwitchDescription(self,s):
        """\brief Retrieves the switch's description
        \return (\c int) Returns 0 if successful, -1 if unsuccessful
        """
        self.snmp.set(OID.sysDescr,rfc1902.OctetString(s))
        return self.snmp.getErrorStatus()

    def getSwitchUptime(self):
        """\brief Retrieves the switch's uptime
        \return (\c string) The switch's uptime
        """
        return str(self.snmp.get(OID.sysUpTimeInstance)[0][1])
    
    def getSwitchContact(self):
        """\brief Retrieves the switch's contact
        \return (\c string) The switch's contact
        """
        return self.snmp.get(OID.sysContact)[0][1]

    def setSwitchContact(self,s):
        """\brief Retrieves the switch's contact
        \param s (\c string) The switch's contact
        \return (\c int) Returns 0 if successful, -1 if unsuccessful
        """
        self.snmp.set(OID.sysContact,rfc1902.OctetString(s))
        return self.snmp.getErrorStatus()

    def getSwitchLocation(self):
        """\brief Retrieves the switch's location
        \return (\c string) The switch's location
        """
        return self.snmp.get(OID.sysLocation)[0][1]
    
    def setSwitchLocation(self,s):
        """\brief Retrieves the switch's location
        \param s (\c string) The switch's location
        \return (\c int) Returns 0 if successful, -1 if unsuccessful
        """
        self.snmp.set(OID.sysLocation,rfc1902.OctetString(s))
        return self.snmp.getErrorStatus()

    def getSerialNumber(self):
        """\brief returns the serial number of the device 
        \return A string of the serial number
        """
        return ""

# operational commands

## Ports

    def enablePort(self, portNumber):
        """\brief Enables a port. Returns 0 upon success, -1 otherwise
        \param portNumber (\c string) The port to enable
        \return (\c int) 0 if succesful, -1 otherwise
        """
        internalID = int(self.getPortInternalID(portNumber))
        self.snmp.set(OID.ifAdminStatus+(internalID,),rfc1902.Integer(1))
        return self.snmp.getErrorStatus()

    def getPortStatus(self, portNumber):
        """\brief Gets the operational status of a port: up (1), down (2) 
        \param portNumber (\c string) The port whose status is to be retrieved
        \return (\c string) The port status
        """
        internalID = int(self.getPortInternalID(portNumber))
        return self.snmp.get(OID.ifOperStatus+(internalID,))[0][1]


    def getPortAdminStatus(self, portNumber):
        """\brief Gets the status of a port: up (1), down (2) or testing (3)
        \param portNumber (\c string) The port whose status is to be retrieved
        \return (\c string) The port status
        """
        internalID = int(self.getPortInternalID(portNumber))
        return self.snmp.get(OID.ifAdminStatus+(internalID,))[0][1]

    def disablePort(self, portNumber):
        """\brief Disables a port. Returns 0 upon success, -1 otherwise
        \param portNumber (\c string) The port to disable
        \return (\c int) 0 if succesful, -1 otherwise
        """
        internalID = int(self.getPortInternalID(portNumber))
        self.snmp.set(OID.ifAdminStatus+(internalID,),rfc1902.Integer(2))
        return self.snmp.getErrorStatus()
             
    def getPortIDs(self):
        """\brief Gets the internal ids for each of the ports on the switch. This function
                  returns a dictionary with the results
        \return (\c dictionary) A dictionary with the results (see getSNMPResultTable for more information)
        """
        return self.getDot1dBasePortIfIndex()

    def getPortNames(self):
        if self.__ifName == None:
            self.__ifName = self.snmp.walk(OID.ifName)
        return self.__ifName

    def getDot1dBasePortIfIndex(self):
        if self.__dot1dBasePortIfIndex == None:
            self.__dot1dBasePortIfIndex = self.snmp.walk(OID.dot1dBasePortIfIndex)
        return self.__dot1dBasePortIfIndex

    def getIfDescr(self):
        if self.__ifDescr == None:
            self.__ifDescr = self.snmp.walk(OID.ifDescr)
        return self.__ifDescr
                            

    def getPortInternalID(self, portNumber):
        """\brief Given a port's external number, this function returns its internal
                  number. If the port is not found -1 is returned
        \param portNumber (\c string) The port number whose internal port is to be searched
        \return (\c string) The port's internal id, or -1 if unsuccessful
        """
        varBindTable = self.getPortIDs()
        for tableRow in varBindTable:
            for name, val in tableRow:
                #print name,val
                if name is None:
                    continue
                if name[len(name)-1] == rfc1902.Integer32(portNumber):
                    return val 
        return -1

    def getFullMACTable(self):
        """\brief Gets the full learned mac table from the switch, returning a list of MACTableEntry objects.
        \return (\c list) A list of MACTableEntry objects with the results.
        """
        portsTable = self.snmp.walk(OID.dot1dTpFdbPort)
        learnedTypeTable = self.snmp.walk(OID.dot1dTpFdbStatus)

        result = []

        for learnedTypeTableRow in learnedTypeTable:
            for learnedname, learnedval in learnedTypeTableRow:
                if learnedval == rfc1902.Integer32('3'):
                    learnedname = rfc1902.ObjectName((learnedname.prettyPrint()).replace(OID.dot1dTpFdbStatus.prettyPrint(),OID.dot1dTpFdbPort.prettyPrint()))
                    for portTableRow in portsTable:
                        for portname, portval in portTableRow:
                            if learnedname == portname:
                                result.append(MACTableEntry(("%02x:%02x:%02x:%02x:%02x:%02x" % (int(learnedname[11]),int(learnedname[12]),int(learnedname[13]),int(learnedname[14]),int(learnedname[15]),int(learnedname[16]))).replace("0x","").upper(),portval,'3',self.__switchName))
                                
        return result

        for key in learnedTypeTable.keys():
            if (learnedTypeTable[key] == str(3)):
                mac = MACTableEntry((macAddressesTable[key]).replace(' ',':',5).upper(),portsTable[key],learnedTypeTable[key])
                mac.setSwitch(self.getSwitchID())
                result.append(mac)
                #print mac

    def getInterfaceDescriptionTable(self):
        """\brief Gets the table of interface descriptions
        \return (\c dictionary) A dictionary with the results (see getSNMPResultTable for more information)
        """
        result = {}
        interfaceTable = self.getIfDescr()
        for interfaceTableRow in interfaceTable:
            for name, val in interfaceTableRow:
                result[name[len(name)-1]] = val

        return result

    def setCommunity(self, c):
        """\brief Sets the community and updates the snmp commands accordingly
        \param c (\c string) The community
        """
        self.snmp.setCommunity(c)


    def getCommunity(self):
        """\brief Gets the community
        \return (\c string) The community
        """
        return self.snmp.getCommunity()

## VLANS

    def getVLANToInterfacesTable(self):
        """\brief Gets the mappings between VLANS and interfaces (ports)
        \return (\c dictionary) A dictionary with the results (see getSNMPResultVLANTable for more information)
        """
        table = {}
        ifStackStatusTable = self.snmp.walk(OID.ifStackStatus)
        for ifStackStatusTableRow in ifStackStatusTable:
            if (table.has_key(ifStackStatusTableRow[0][0][len(ifStackStatusTableRow[0][0])-2]) == False):
                table[ifStackStatusTableRow[0][0][len(ifStackStatusTableRow[0][0])-2]] = []
            table[ifStackStatusTableRow[0][0][len(ifStackStatusTableRow[0][0])-2]].append(ifStackStatusTableRow[0][0][len(ifStackStatusTableRow[0][0])-1])
        return table

    def getVlanInfo(self):
        vlans = {}
        dot1qVlanStaticNameTable = self.snmp.walk(OID.dot1qVlanStaticName)
        dot1qVlanFdbIdTable = self.snmp.walk(OID.dot1qVlanFdbId)
        
        for dot1qVlanStaticNameTableRow in dot1qVlanStaticNameTable:
            for dot1qVlanFdbIdTableRow in dot1qVlanFdbIdTable:
                if dot1qVlanStaticNameTableRow[0][0][len(dot1qVlanStaticNameTableRow[0][0])-1] == dot1qVlanFdbIdTableRow[0][0][len(dot1qVlanFdbIdTableRow[0][0])-1] :
                    
                    vlans[dot1qVlanStaticNameTableRow[0][1]]  = (int(dot1qVlanFdbIdTableRow[0][1]),dot1qVlanStaticNameTableRow[0][0][len(dot1qVlanStaticNameTableRow[0][0])-1])

        return vlans
        
    def setMinimumVLANInternalID(self, m):
        print "not implemented"
        
    def getMinimumVLANInternalID(self):
        print "not implemented"

    def setMaximumVLANInternalID(self, m):
        print "not implemented"

    def getMaximumVLANInternalID(self):
        print "not implemented"

    def getVLANNames(self):
        print "not implemented"

    def getFullVLANInfo(self, theVLANName=None):
        print "not implemented"

    def createVLAN(self, vlan):
        print "not implemented"
                    
    def addPorts(self, vlanName, ports):
        print "not implemented"

    def deletePorts(self, vlanName, ports):
        print "not implemented"
                
    def deleteVLAN(self, vlanName):
        print "not implemented"
                
    def populateVLAN(self, vlanName):
        print "not implemented"        

    def getEmptyBitMap(self,num_ports=None):
        s = ""
        if num_ports == None:
            num_ports = int(self.snmp.get(OID.dot1dBaseNumPorts)[0][1])

        for i in range(0,divmod(num_ports,8)[0]):
            s = s + pack('B',0)
        return s
                                                
    def printPortMap(self, portList, Tagged=False):

        bitfield = array('B')
        
        for i in range(0,len(portList)):
            bitfield.extend(unpack('B',portList[i]))
                 
        s = "u"
        if Tagged:
            s = "t"
        for port in bitfield:
            for slot in range(0,8):
                if slot == 0:
                    s = s + " "
                if (port & Switch.mask[slot] == Switch.mask[slot]):
                    s = s + "1"
                else:
                    s = s + "0"
        return s

    def getPortTdr(self, port_str):
        return (False,"TDR testing not supported")

####
# Caching code
####

    def getDot1qVlanStaticUntaggedPorts(self,run=False):
        if self.__dot1qVlanStaticUntaggedPorts == None or self.__refresh or run:
            self.__dot1qVlanStaticUntaggedPorts = self.snmp.walk(OID.dot1qVlanStaticUntaggedPorts)
        return self.__dot1qVlanStaticUntaggedPorts

    def getDot1qVlanStaticEgressPorts(self,run=False):
        if self.__dot1qVlanStaticEgressPorts == None or self.__refresh or run:
            self.__dot1qVlanStaticEgressPorts = self.snmp.walk(OID.dot1qVlanStaticEgressPorts)
        return self.__dot1qVlanStaticEgressPorts

    def getDot1qPvid(self,run=False):
        if self.__dot1qPvid == None or self.__refresh or run:
            self.__dot1qPvid = self.snmp.walk(OID.dot1qPvid)
        return self.__dot1qPvid

    def getDot1qTpFdbPort(self,run=False):
        if self.__dot1qTpFdbPort == None or self.__refresh or run:
            self.__dot1qTpFdbPort = self.snmp.walk(OID.dot1qTpFdbPort)
        return self.__dot1qTpFdbPort

    def getDot1qTpFdbStatus(self,run=False):
        if self.__dot1qTpFdbStatus == None or self.__refresh or run:
            self.__dot1qTpFdbStatus = self.snmp.walk(OID.dot1qTpFdbStatus)
        return self.__dot1qTpFdbStatus

    def getDot1qVlanStaticName(self,run=False):
        if self.__dot1qVlanStaticName == None or self.__refresh or run:
            self.__dot1qVlanStaticName = self.snmp.walk(OID.dot1qVlanStaticName)
        return self.__dot1qVlanStaticName

    def getDot1qVlanFdbId(self,run=False):
        if self.__dot1qVlanFdbId == None or self.__refresh or run:
            self.__dot1qVlanFdbId = self.snmp.walk(OID.dot1qVlanFdbId)
        return self.__dot1qVlanFdbId
