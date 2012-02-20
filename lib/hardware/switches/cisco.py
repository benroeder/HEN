#################################################################################################################
# cisco.py: contains the switch subclass for Cisco switches
#
# CLASSES
# --------------------------------------------------------------------
# CiscoSwitch                The class used to support Cisco switches (derived from the Switch superclass). This class
#                            contains all operations relating to proprietary Cisco SNMP mibs, such as VLAN operations.
# CiscoCatalystSwitch        The class used to support Cisco catalyst switches. This class contains information
#                            specific to this model of switch (number of ports, etc)
#
##################################################################################################################
import commands, os, string
from hardware.switches.switch import Switch
from auxiliary.hen import VLAN, MACTableEntry, Port, convertHexCharacterToInt, convertIntToHexCharacter, SimpleVlan
from auxiliary.snmp import SNMP
from auxiliary.oid import OID
from array import *
from struct import *
from pysnmp.proto import rfc1902

###########################################################################################
#   SNMP CISCO OIDs
###########################################################################################
# CISCO-VTP-MIB.my OIDs for Catalyst switch
VLAN_STATUS_TABLE = "1.3.6.1.4.1.9.9.46.1.3.1.1.2.1"
VLAN_TYPES_TABLE = "1.3.6.1.4.1.9.9.46.1.3.1.1.3.1"
VLAN_NAMES_TABLE = "1.3.6.1.4.1.9.9.46.1.3.1.1.4.1"
# CISCO-VLAN-MEMBERSHIP.my OIDs for Catalyst switch
VLAN_TO_PORTS_TABLE = "1.3.6.1.4.1.9.9.68.1.2.2.1.2"

SWITCH_DB_ADDRESSES_TABLE = "1.3.6.1.2.1.17.4.3.1.1"
SWITCH_DB_PORTS_TABLE = "1.3.6.1.2.1.17.4.3.1.2"
SWITCH_DB_STATUS_TABLE = "1.3.6.1.2.1.17.4.3.1.3"
PORT_IDS_TABLE = "1.3.6.1.2.1.17.1.4.1.2"
IFNAME_TABLE = "1.3.6.1.2.1.31.1.1.1.1"

VLAN_PORTS_TABLE = "1.3.6.1.4.1.9.9.68.1.2.1.1.2"

# Adding VLANs
VLAN_EDIT_TABLE = "1.3.6.1.4.1.9.9.46.1.4.2"
VLAN_EDIT_OPERATION = "1.3.6.1.4.1.9.9.46.1.4.1.1.1.1"
VLAN_EDIT_BUFFER_OWNER = "1.3.6.1.4.1.9.9.46.1.4.1.1.3.1"
VLAN_EDIT_ROW_STATUS = "1.3.6.1.4.1.9.9.46.1.4.2.1.11.1"
VLAN_EDIT_TYPE = "1.3.6.1.4.1.9.9.46.1.4.2.1.3.1"
VLAN_EDIT_NAME = "1.3.6.1.4.1.9.9.46.1.4.2.1.4.1"
VLAN_EDIT_DOT_10_SAID = "1.3.6.1.4.1.9.9.46.1.4.2.1.6.1"

# Adding Ports
VLAN_VM_VLAN = "1.3.6.1.4.1.9.9.68.1.2.2.1.2"

###########################################################################################
#   CLASSES
###########################################################################################
class CiscoSwitch(Switch):
    """\brief Subclass for any Cisco switch in the testbed
    This subclass implements methods to retrieve and set information from a switch using SNMP version 1 that
    is proprietary to Cisco (vlans, etc).
    """


    functions = []    

    def getVLANNames(self):
        """\brief Gets the names of the vlans on the switch, returning a dictionary whose keys are the objects' internal ids and whose values are the actual vlan names (see \getSNMPResultTable for more info)
        \return (\c dictionary) A dictionary with the names of the vlans
                                                  """
        vlans = {}
        dot1qVlanStaticNameTable = self.snmp.walk(OID.ciscoVtpVlanName)
        
        for dot1qVlanStaticNameTableRow in dot1qVlanStaticNameTable:
            if str(dot1qVlanStaticNameTableRow[0][1]) == "trnet-default":
                pass
            elif str(dot1qVlanStaticNameTableRow[0][1]) == "token-ring-default":
                pass
            elif str(dot1qVlanStaticNameTableRow[0][1]) == "fddi-default":
                pass
            elif str(dot1qVlanStaticNameTableRow[0][1]) == "fddinet-default":
                pass
            else:
                vlans[dot1qVlanStaticNameTableRow[0][0][len(dot1qVlanStaticNameTableRow[0][0])-1]] = dot1qVlanStaticNameTableRow[0][1]
        # Do we want to clean up and only return ethernet vlans ?
        # OID.ciscoVtpVlanType
        
        return vlans

    def getVlanInfo(self):
        vlans = {}
        dot1qVlanStaticNameTable = self.snmp.walk(OID.ciscoVtpVlanName)
        #dot1qVlanFdbIdTable = self.snmp.walk(OID.dot1qVlanFdbId)
        
        for dot1qVlanStaticNameTableRow in dot1qVlanStaticNameTable:
            if str(dot1qVlanStaticNameTableRow[0][1]) == "trnet-default":
                pass
            elif str(dot1qVlanStaticNameTableRow[0][1]) == "token-ring-default":
                pass
            elif str(dot1qVlanStaticNameTableRow[0][1]) == "fddi-default":
                pass
            elif str(dot1qVlanStaticNameTableRow[0][1]) == "fddinet-default":
                pass
            else:
                vlans[dot1qVlanStaticNameTableRow[0][1]]  = (dot1qVlanStaticNameTableRow[0][0][len(dot1qVlanStaticNameTableRow[0][0])-1],dot1qVlanStaticNameTableRow[0][0][len(dot1qVlanStaticNameTableRow[0][0])-1])

        return vlans



    def getFullVLANInfo(self, theVLANName=None):
        """\brief Returns a list of VLAN objects consisting of all of the vlans in the switch. If the theVLANName parameter is set, the function returns a single VLAN object corresponding to the requested vlan
        \param theVLANName (\c string) The name of the VLAN to retrieve
        \return (\c list of VLAN objects) A list of VLAN objects with the reque\sted information or a VLAN object if a vlan name is specified

        """
        vlans = []

        vlan_names = self.getVLANNames()
        port_ids = self.getPortIDs()

        if theVLANName != None:
            vn = {}
            for v in vlan_names.keys():
                if vlan_names.get(v) == theVLANName:
                    vn[v] = theVLANName
                    vlan_names = vn
        
        for v in vlan_names:
            if str(v) == "trnet-default":
                pass
            elif str(v) == "token-ring-default":
                pass
            elif str(v) == "fddi-default":
                pass
            elif str(v) == "fddinet-default":
                pass
            else:
                vlans.append(VLAN(vlan_names[v],{},None,v))

        # get untagged vlan (port based)
        portMapTable = self.snmp.walk(OID.ciscoVmMembershipSummaryMemberPorts)
        for vlan in vlans:
            ports = []
            temp_ports = []
            switches = {}
            # getting port based vlans
            for portMapRow in portMapTable:
                if (portMapRow[0][0][len(portMapRow[0][0])-1] == vlan.getInternalID()):                    
                    ports = self.__parsePortList(portMapRow[0][1],False)
            # getting 802.1Q tagged/untagged vlans
            
            switches[self.getSwitchName()] = ports
            vlan.setSwitches(switches)

        
        return vlans

    def __parsePortList(self,pl,tagged):

        raw_ports = array('B')
        for i in range(0,len(pl)):
            raw_ports.extend(unpack('B',pl[i]))
            
            
        mask = [128,64,32,16,8,4,2,1,0]
        port_number = 0
        ports = []
        port_ids = self.getPortIDs()
        port_names = self.getPortNames()
        for port in raw_ports:
            for slot in range(0,8):
                port_number = port_number + 1
                if (port & Switch.mask[slot] == Switch.mask[slot]):
                    for port_id in port_ids:
                        if (port_id[0][0][len(port_id[0][0])-1] == rfc1902.Integer32(port_number)):
                            for port_name in port_names:
                                if (port_name[0][0][len(port_name[0][0])-1] == port_id[0][1]):
                                    ports.append(Port(port_name[0][1],tagged,port_number))
        return ports
        
    def refreshVlanInfo(self):
        """\brief Refreshes both the port list and vlan list for the switch
        """
        untaggedPorts = self.snmp.walk(OID.ciscoVmMembershipSummaryMemberPorts)
        taggedPorts = self.snmp.walk(OID.dot1qVlanStaticEgressPorts)
        pvidPorts = self.snmp.walk(OID.dot1qPvid)
        self.getVlanList()
        
        # put untagged ports into list
        for up in untaggedPorts:
            try:
                vlan = self.getVlan(str(up[0][0][-1]))
                plp = self.__simpleParsePortList(up[0][1])
                vlan.setUntagged(plp)
                for p in plp:
                    port = self.getPort(p)
                    port.setUntagged((vlan.getName(),vlan.getId()))
            except:
                pass
            

        # put tagged ports into list
        for tp in taggedPorts:
            vlan = self.getVlan(str(tp[0][0][-1]))
            plp = self.__simpleParsePortList(tp[0][1])
            vlan.setTagged(plp)
            for p in plp:
                port = self.getPort(p)
                a = port.getTagged()
                a.append((vlan.getName(),vlan.getId()))
                port.setTagged(a)
                
        for pp in pvidPorts:
            vlan = self.getVlan(str(pp[0][1]))
            if (pp[0][0][-1] <= self.getNumberofPorts()):
                pvid_list = vlan.getPvid()
                pvid_list.append(pp[0][0][-1])
                vlan.setPvid(pvid_list)
                port = self.getPort(pp[0][0][-1])
                #port.setPvid((pp[0][1],vlan_list[vid][0]))
                port.setUntagged((vlan.getName(),vlan.getId()))
                
    def getVlanList(self):
        vlan_names = self.getVLANNames()
        self.clearVlans()
        for vid in vlan_names:
            sv = SimpleVlan(vlan_names[vid],str(vid),str(vid),self.getNodeID())
            self.addVlan(sv)
            
    def __simpleParsePortList(self,pl):
        ports = []
        raw_ports = array('B')
        for i in range(0,len(pl)):
            ports = []
            raw_ports.extend(unpack('B',pl[i]))
            mask = [128,64,32,16,8,4,2,1,0]
            port_number = 0
            for port in raw_ports:
                for slot in range(0,8):
                    port_number = port_number + 1
                    if (port & Switch.mask[slot] == Switch.mask[slot]):
                        ports.append(port_number)
                    if (port_number == self.getNumberofPorts()):
                        return ports
        return ports

    def DELETEgetVLANNames(self):
        """\brief Gets the names of the vlans on the switch, returning a dictionary whose keys are the objects'
                  internal ids and whose values are the actual vlan names
        \return (\c dictionary) A dictionary with the names of the vlans
        """
        cmd = self.getSNMPwalkCommand() + VLAN_NAMES_TABLE
        print cmd

    def DELETEgetVLANGlobalIDs(self):
        """\brief Gets the VLAN's global ID and returns a dictionary whose keys represent the
                  vlans' internal ids and whose values represent the vlans' global ids
        \return (\c dictionary) A dictionary containing the results
        """
        # TODO: We assume that the internal and external ID are the same
	cmd = self.getSNMPwalkCommand() + VLAN_NAMES_TABLE
	return self.getSNMPResultTable(cmd).keys()

    def getPortInternalID(self, portNumber):
        """\brief Given a port's external number, this function returns its internal
        number. If the port is not found -1 is returned
        We assume that the internal number is NOT the ifIndex
        \param portNumber (\c string) The port number whose internal port is to be searched ('Fa0/1')
        \return (\c string) The port's internal id, or -1 if unsuccessful
        """        
        # Get the ifName (e.g. Fa0/2)
        portIfNameTable = self.getIfName()

        for portIfNameTableRow in portIfNameTable:
            for (oid,val) in portIfNameTableRow:
                if (val == str(portNumber)):
                    #print oid,val
                    return oid[len(oid)-1]                
        return -1

    def DELETEgetVLANIDFromName(self, vlanName):
        cmd = self.getSNMPwalkCommand() + VLAN_NAMES_TABLE
        vlanNames = self.getSNMPResultTable(cmd)
        for vlanID in vlanNames.keys():
            if (vlanNames[vlanID] == vlanName):
                return vlanID
        return -1

    def DELETE__resetEditMode(self):
        cmd = self.getSNMPsetCommand() + VLAN_EDIT_OPERATION + " integer 4"
        status = commands.getstatusoutput(cmd)[0]
        

    def DELETEdeleteVLAN(self, vlanName):
        """\brief Deletes a vlan based on the VLAN Name given. The function returns the following codes:
        -1: if the vlan name is not set
        -2: if there was an error deleting the new vlan
        0: if successful
        \param vlanName (\c string) The VLAN Name
        \return (\c int) 0 if successful, negative otherwise
        """
        if (vlanName == None):
            return -1
        
        vlanID = self.getVLANIDFromName(vlanName)
        if (vlanID == -1):
            # Look up failed, no such name
            return -2

        # 1) Check if the vlan exists
        cmd = self.getSNMPgetCommand() + VLAN_STATUS_TABLE + "." + str(vlanID)
        result = self.getSNMPResultValue(cmd)
        if (result == -1):
            # vlanID does not exist
            return -2

        # 2) Check if no one is working
        cmd = self.getSNMPwalkCommand() + VLAN_EDIT_TABLE
        result = self.getSNMPResultTable(cmd)
        if (result != {}):
            # Somebody is using the edit buffer, returning
            print "using buffer.."
            return -2

        # 3) Start Edit Mode
        cmd = self.getSNMPsetCommand() + VLAN_EDIT_OPERATION + " i 2"
        status = commands.getstatusoutput(cmd)[0]
        if (status != 0):
            return -2

        # 4) Move all the ports from this VLAN to the default VLAN
        cmd = self.getSNMPwalkCommand() + VLAN_VM_VLAN
        vlanPorts = self.getSNMPResultTable(cmd)
        movePorts = []
        for port in vlanPorts:
            if (vlanPorts[port] == vlanID):
                movePorts.append(port)
        for port in movePorts:
            cmd = self.getSNMPsetCommand() + VLAN_VM_VLAN + "." + str(port) + " i 1"
            status = commands.getstatusoutput(cmd)[0]
            if (status != 0):
                self.__resetEditMode()
                return -2
        
        # 5) Write 'destroy' to row status
        cmd = self.getSNMPsetCommand() + VLAN_EDIT_ROW_STATUS + "." + str(vlanID) + " i 6"
        status = commands.getstatusoutput(cmd)[0]
        if (status != 0):
            self.__resetEditMode()
            return -2

        # 6) Apply the Modifications
        cmd = self.getSNMPsetCommand() + VLAN_EDIT_OPERATION + " i 3"
        status = commands.getstatusoutput(cmd)[0]
        if (status != 0):
            self.__resetEditMode()
            return -2

        # 6) Leave Edit Mode
        self.__resetEditMode()

        return 0


    def DELETEcreateVLAN(self, vlan):
        """\brief Creates a vlan based on the VLAN object given. The function returns the following codes:
        -1: if the vlan name, its external id or its switches are not set
        -2: if there was an error creating the new vlan
        -3: if there was an error setting the new vlan's external id
        -4: if the switches dictionary does not have a key equal to the switch's id
        0: if successful
        \param vlan (\c VLAN object) A VLAN object to create the vlan from
        \return (\c int) 0 if successful, negative otherwise
        """

        if (vlan.getName() == None or vlan.getID() == None or vlan.getSwitches() == None):
            return -1


        # check to see if this switch is in the vlan
        if (not vlan.getSwitches().has_key(self.getSwitchID())):
            return -4

        vlanID = vlan.getID()
        vlanName = vlan.getName()

        # 1) Check current VLANs, if ID or name already exist stop creating
        cmd = self.getSNMPgetCommand() + VLAN_STATUS_TABLE + "." + str(vlanID)
        result = self.getSNMPResultValue(cmd)
        if (result != -1):
            # vlanID already exists
            return -2
        checkVlanID = self.getVLANIDFromName(vlanName)
        if (checkVlanID != -1):
            return -2

        # 2) Check if no one is working on the edit buffer
        cmd = self.getSNMPwalkCommand() + VLAN_EDIT_TABLE
        result = self.getSNMPResultTable(cmd)
        if (result != {}):
            # Somebody is using the edit buffer, returning
            return -2

        # 3) Start Edit Mode
        cmd = self.getSNMPsetCommand() + VLAN_EDIT_OPERATION + " i 2"
        status = commands.getstatusoutput(cmd)[0]
        if (status != 0):
            self.__resetEditMode()
            return -2

        # 4) Set the Owner of the Buffer
        cmd = self.getSNMPsetCommand() + VLAN_EDIT_BUFFER_OWNER + " s \"hen\""
        status = commands.getstatusoutput(cmd)[0]
        if (status != 0):
            self.__resetEditMode()
            return -2

        # 5) create a row and set the type and the name
        cmd = self.getSNMPsetCommand() + VLAN_EDIT_ROW_STATUS + "." + str(vlanID) + " i 4"
        status = commands.getstatusoutput(cmd)[0]
        if (status != 0):
            self.__resetEditMode()
            return -2
        cmd = self.getSNMPsetCommand() + VLAN_EDIT_NAME + "." + str(vlanID) + " s \"" + vlanName + "\""
        status = commands.getstatusoutput(cmd)[0]
        if (status != 0):
            self.__resetEditMode()
            return -2
        cmd = self.getSNMPsetCommand() + VLAN_EDIT_TYPE + "." + str(vlanID) + " i 1"
        status = commands.getstatusoutput(cmd)[0]
        if (status != 0):
            self.__resetEditMode()
            return -2
        
        # 6) Set the vtpVlanEditDot10Said. This is the VLAN number + 100000 translated to hexadecimal.
        dot10Said = 100000 + int(vlanID)
        dot10SaidHex = "%08x" % (dot10Said)
        cmd = self.getSNMPsetCommand() + VLAN_EDIT_DOT_10_SAID + "." + str(vlanID) + " x " + str(dot10SaidHex)
        status = commands.getstatusoutput(cmd)[0]
        if (status != 0):
            self.__resetEditMode()
            return -2
        
        # 7) Apply the Modifications
        cmd = self.getSNMPsetCommand() + VLAN_EDIT_OPERATION + " i 3"
        status = commands.getstatusoutput(cmd)[0]
        if (status != 0):
            self.__resetEditMode()
            return -2
        
        # 8) Leave Edit Mode
        self.__resetEditMode()
        

        # 9) Add the ports
        if (vlan.getPortsOnSwitch(self.getSwitchID()) != None):
            self.addPorts(vlan.getName(),vlan.getPortsOnSwitch(self.getSwitchID()))
        else:
            return -4

        return 0



    def DELETEaddPorts(self, vlanName, ports):
        
        vlanID = self.getVLANIDFromName(vlanName)
        if (vlanID == -1):
            # Look up failed, no such name
            return -2

        # Get the membership for all ports (is checked later)
        cmd = self.getSNMPwalkCommand() + VLAN_VM_VLAN
        vlanPorts = self.getSNMPResultTable(cmd)

        # Get the ifName (e.g. Fa0/2)
        cmd = self.getSNMPwalkCommand() + IFNAME_TABLE
        macTableIfName = self.getSNMPResultTable(cmd)

        # Get the ifIndex of the port
        for p in range(0,len(ports)):
            port = ports[p]
            portName = port.getPortNumber()

            portIndex = -1
            for x in macTableIfName:
                if (macTableIfName[x] == portName):
                    portIndex = x
                    break

            if (portIndex == -1):
                # Port could not be found
                continue

            if (not vlanPorts.has_key(portIndex)):
                # Port is not available (maybe a trunk port, trunk ports are not in that list)
                continue
            
            if (vlanPorts[portIndex] != "1"):
                # Port is not available
                continue

            # Set the port membership to our VLAN
            cmd = self.getSNMPsetCommand() + VLAN_VM_VLAN + "." + str(portIndex) + " i " + str(vlanID)
            status = commands.getstatusoutput(cmd)[0]
            if (status != 0):
                # Could not add port
                continue
        
        return 0


    def DELETEdeletePorts(self, vlanName, ports):
        """\brief Delete static ports from the given vlan and assign it to the default VLAN 1 again.
        The function returns the following codes
                  -3: if static port failed to be deleted
                   0: if successful
        \param vlanName (\c string) The vlan to delete ports from
        \param ports (\c list of Port objects) The ports to delete
        \return (\c int) 0 if successful, negative otherwise
        """        
        # First retrieve the vlan's internal id from its name
        vlanID = self.getVLANIDFromName(vlanName)
        if (vlanID == -1):
            # Look up failed, no such name
            return -3

        # Get the membership for all ports (is checked later)
        cmd = self.getSNMPwalkCommand() + VLAN_VM_VLAN
        vlanPorts = self.getSNMPResultTable(cmd)

        # Get the ifName (e.g. Fa0/2)
        cmd = self.getSNMPwalkCommand() + IFNAME_TABLE
        macTableIfName = self.getSNMPResultTable(cmd)

        # Delete ports one at a time
        for port in ports:
            portName = port.getPortNumber()
            portIndex = -1
            for x in macTableIfName:
                if (macTableIfName[x] == portName):
                    portIndex = x
                    break

            if (portIndex == -1):
                # Port could not be found
                continue

            if (not vlanPorts.has_key(portIndex)):
                # Port is not available (maybe a trunk port, trunk ports are not in that list)
                continue
            
            if (vlanPorts[portIndex] != vlanID):
                # Port does not belong to this VLAN
                continue

            # Set the port membership to the default VLAN 1
            cmd = self.getSNMPsetCommand() + VLAN_VM_VLAN + "." + str(portIndex) + " i 1"
            status = commands.getstatusoutput(cmd)[0]
            if (status != 0):
                # Could not move port
                continue

        return 0


    def DELETEgetFullVLANInfo(self, theVLANName=None):

        vlans = []
        vlanNames = self.getVLANNames()
        vlanIDs = self.getVLANGlobalIDs()
        
        for vlanID in vlanIDs:

            vlanName = vlanNames[vlanID]
            ports = self.__getVLANPorts(vlanID)

            switches = {}
            switches[self.getSwitchID()] = ports

            vlan = VLAN(vlanName, switches, vlanID)
            vlans.append(vlan)

        if (not theVLANName):
            return vlans

        for vlan in vlans:
            if (vlan.getName() == theVLANName):
                return vlan
            
        return -1


    def DELETE__getVLANPorts(self, vlanID):
        cmd = self.getSNMPgetCommand() + VLAN_PORTS_TABLE + "." + vlanID

        allPortsBitmap = self.getSNMPResultValueRemoveLF(cmd).replace(" ", "")

        # Get the IfIndex corresponding port number
        cmd = self.getSNMPwalkCommand() + PORT_IDS_TABLE
        macTableIfIndex = self.getSNMPResultTable(cmd)
        
        # Get the ifName (e.g. Fa0/2
        cmd = self.getSNMPwalkCommand() + IFNAME_TABLE
        macTableIfName = self.getSNMPResultTable(cmd)

        # Process each set of 4 bits (one character in the string) at a time
        ports = []
        for x in range(0, len(allPortsBitmap)):
            # The next loop runs 4 times, once for each of the 4 bits in the character
            # The mask takes on the values: 1000, 0100, 0010, 0001. The & of the character
            # and the mask will return 0 if the bit is zero, or 8, 4, 2, or 1 if the bit
            # is 1, so testing with != 0 will return a boolean for the bit's value
            mask = 0x8
            for y in range(0, 4):
                bit = (convertHexCharacterToInt(allPortsBitmap[x]) & mask) != 0
                mask = mask >> 1
                if (bit):
                    # The port number is the bit number (y + 1) plus the number of characters
                    # of four bits that came before it (x * 4)
                    portNumber = str((x * 4) + y + 1)

                    # Get the IfIndexcorresponding port number
                    ifIndex = macTableIfIndex[portNumber]
                    
                    # Get the ifName (e.g. Fa0/2)
                    ifName = macTableIfName[ifIndex]

                    # TODO Check the (un)tagged status of the port
                    p = Port(ifName)
                    ports.append(p)

        return ports


class CiscoCatalystSwitch(CiscoSwitch):
    """\brief Sub-subclass used to support Cisco Catalyst switches. This class contains information
              specific to this model of switch (number of ports, etc)          
    """
    functions = ["switch"]

    def __init__(self, switchNode):
        """\brief Initializes the class
        \param switchNode (\c SwitchNode) The SwitchNode object to obtain information from to initialize the class with
        """
        CiscoSwitch.__init__(self, switchNode, 2, 4094, 10000, 100000)

    def getFullMACTable(self):
        """\brief Gets the full learned mac table from the switch, returning a list of MACTableEntry objects.
        \return (\c list) A list of MACTableEntry objects with the results.
        """
        result = []
        community = self.snmp.getCommunity()
        for v in self.getVLANNames():
            self.snmp.setCommunity(str(community)+"@"+str(v))
            self.__getFDBTable(result)
        self.snmp.setCommunity(str(community))

        dot1dBasePortIfIndexTable = self.getDot1dBasePortIfIndex()
        ifNameTable = self.getPortNames()

        for r in result:
            for entry in dot1dBasePortIfIndexTable:
                if (str(entry[0][0][len(entry[0][0])-1]) == str(r.getPort())):
                    for entry2 in ifNameTable:
                        if (str(entry2[0][0][len(entry2[0][0])-1]) == str(entry[0][1])):
                            r.setPort(entry2[0][1])
        return result
    
    def __getFDBTable(self,result):
        portsTable = self.snmp.walk(OID.dot1dTpFdbPort)
        learnedTypeTable = self.snmp.walk(OID.dot1dTpFdbStatus)
        
        for learnedTypeTableRow in learnedTypeTable:
            for learnedname, learnedval in learnedTypeTableRow:
                if learnedval == rfc1902.Integer32('3'):
                    learnedname = rfc1902.ObjectName((learnedname.prettyPrint()).replace(OID.dot1dTpFdbStatus.prettyPrint(),OID.dot1dTpFdbPort.prettyPrint()))
                    for portTableRow in portsTable:
                        for portname, portval in portTableRow:
                            if learnedname == portname:
                                result.append(MACTableEntry(("%02x:%02x:%02x:%02x:%02x:%02x" % (int(learnedname[11]),int(learnedname[12]),int(learnedname[13]),int(learnedname[14]),int(learnedname[15]),int(learnedname[16]))).replace("0x","").upper(),portval,'3',self.getSwitchName()))

        #return result
        return 
        for key in learnedTypeTable.keys():
            if (learnedTypeTable[key] == str(3)):
                mac = MACTableEntry((macAddressesTable[key]).replace(' ',':',5).upper(),portsTable[key],learnedTypeTable[key])
                mac.setSwitch(self.getSwitchID())
                result.append(mac)
                #print mac
                
        
    def DELETEgetFullMACTable(self):
        """\brief Returns a list of MACTableEntry objects representing the full mac table of the
                  switch (the switch's database).
        \return (\c list) A list of MACTableEntry objects
        """
        
        originalCmd = self.getCommunity()
        table = []

        # Get the VLAN ids
        vlanIDs = CiscoSwitch.getVLANGlobalIDs(self)
        for vlanID in vlanIDs:
            newcmd = str(originalCmd) + "@" + vlanID
            self.setCommunity(newcmd)

            # Get the MAC Address Table
            cmd = self.getSNMPwalkCommand() + SWITCH_DB_ADDRESSES_TABLE
            macTableMAC = self.getSNMPResultTable(cmd)
            # Get the port numbers
            cmd = self.getSNMPwalkCommand() + SWITCH_DB_PORTS_TABLE
            macTablePort = self.getSNMPResultTable(cmd)
            # Get the status (e.g. 3 = learned)
            cmd = self.getSNMPwalkCommand() + SWITCH_DB_STATUS_TABLE
            macTableStatus = self.getSNMPResultTable(cmd)
            # Get the IfIndexcorresponding port number
            cmd = self.getSNMPwalkCommand() + PORT_IDS_TABLE
            macTableIfIndex = self.getSNMPResultTable(cmd)
            # Get the ifName (e.g. Fa0/2)
            cmd = self.getSNMPwalkCommand() + IFNAME_TABLE
            macTableIfName = self.getSNMPResultTable(cmd)

            # Should be correct?: len(macTableMAC) == len(macTablePort) == len (macTableStatus)
            for key in macTableMAC.keys():
                if (macTableStatus[key] == str(3)):
                    ifIndex = int(macTableIfIndex[macTablePort[key]]);

                    # We could map to the name as well, uncomment to get name
                    #for name in macTableIfName.keys():
                    #    if (int(name) == ifIndex):
                    #        ifName = macTableIfName[name]

                    # We now decrement the ifIndex by 1 to get the correct port
                    # TODO: Is this always correct?
                    ifIndex = ifIndex - 1
                    mac = MACTableEntry((macTableMAC[key]).replace(' ',':',5).upper(),ifIndex,macTableStatus[key])
                    table.append(mac)
                    
        self.setCommunity(originalCmd)
        return table


    def DELETEgetSNMPResultValueRemoveLF(self, command):
        """\brief Runs an snmp command and retrieves a value from the result. The value is anything to the
                  right of the equal sign, Remove the linefeed before.
        \param command (\c string) The SNMP command to run
        \return (\c string) The result's value
        """        
        result = commands.getstatusoutput(command)

	status = result[0]
	output = result[1]

        if (status == 0):
            # Remove the linefeeds in the result
            lines = output.splitlines()
            output = ""
            for line in lines:
                line.rstrip('\n')
                output = output + line

            return self.parseSNMPResultValue(output)
        else:
            return -1

