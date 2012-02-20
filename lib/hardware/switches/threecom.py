##################################################################################################################
# threecom.py: contains the switch subclass for 3com switches
#
# CLASSES
# --------------------------------------------------------------------
# ThreecomSwitch             The class used to support 3com switches (derived from the Switch superclass). This class
#                            contains all operations relating to proprietary 3com SNMP mibs, such as VLAN operations.
# ThreecomSuperstackSwitch   The class used to support 3com superstack switches. This class contains information
#                            specific to this model of switch (number of ports, etc)
#
##################################################################################################################
import commands, os, string
from hardware.switches.switch import Switch
from auxiliary.hen import VLAN, Port
from auxiliary.snmp import SNMP
from auxiliary.oid import OID
from pysnmp.proto import rfc1902
from pyasn1.codec.ber import encoder
import logging

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)


###########################################################################################
#   CLASSES
###########################################################################################
class ThreecomSwitch(Switch):
    """\brief Subclass for any 3com switch in the testbed
    This subclass implements methods to retrieve and set information from a switch using SNMP version 1 that
    is proprietary to 3com (vlans, etc).
    """

    functions = [] 

    def __init__(self, switchNode, minimumVLANInternalID, maximumVLANInternalID, minimumInterfaceInternalID, maximumInterfaceInternalID):
        """\brief Initializes the class
        \param switchNode (\c SwitchNode) The SwitchNode object to obtain information from to initialize the class with
        \param minimumVLANInternalID (\c int) The minimum number for a vlan's internal id
        \param maximumVLANInternalID (\c int) The maximum number for a vlan's internal id        
        \param minimumInterfaceInternalID (\c int) The minimum number for an interface's internal id
        \param maximumInterfaceInternalID (\c int) The maximum number for an interface's internal id        
        """
        Switch.__init__(self, switchNode, minimumVLANInternalID, maximumVLANInternalID, minimumInterfaceInternalID, maximumInterfaceInternalID)
        self.snmp = SNMP(self.getCommunity(),self.getIPAddress(),SNMP.SNMPv1)
     
    def getVLANNames(self):
        """\brief Gets the names of the vlans on the switch, returning a dictionary whose keys are the objects'
                  internal ids and whose values are the actual vlan names (see getSNMPResultTable for more info)
        \return (\c dictionary) A dictionary with the names of the vlans
        """
        vlans = {}
                
        threecomVlanStaticNameTable = self.snmp.walk(OID.threecomVlanStaticName)
        for threecomVlanStaticNameTableRow in threecomVlanStaticNameTable:
            
            vlans[threecomVlanStaticNameTableRow[0][0][len(threecomVlanStaticNameTableRow[0][0])-1]] = threecomVlanStaticNameTableRow[0][1]
            
        return vlans

    def getVlanInfo(self):
        vlans = {}
        dot1qVlanStaticNameTable = self.snmp.walk(OID.threecomVlanStaticName)
        dot1qVlanFdbIdTable = self.snmp.walk(OID.threecomVlanStaticExternalID)
        
        for dot1qVlanStaticNameTableRow in dot1qVlanStaticNameTable:
            for dot1qVlanFdbIdTableRow in dot1qVlanFdbIdTable:
                if dot1qVlanStaticNameTableRow[0][0][len(dot1qVlanStaticNameTableRow[0][0])-1] == dot1qVlanFdbIdTableRow[0][0][len(dot1qVlanFdbIdTableRow[0][0])-1] :
                    
                    vlans[dot1qVlanStaticNameTableRow[0][1]]  = (dot1qVlanFdbIdTableRow[0][1],dot1qVlanStaticNameTableRow[0][0][len(dot1qVlanStaticNameTableRow[0][0])-1])

        return vlans
        
    def getFullVLANInfo(self, theVLANName=None):
        """\brief Returns a list of VLAN objects consisting of all of the vlans in the switch. If
                  the theVLANName parameter is set, the function returns a single VLAN object
                  corresponding to the requested vlan
        \param theVLANName (\c string) The name of the VLAN to retrieve                  
        \return (\c list of VLAN objects) A list of VLAN objects with the requested information or
                                          a VLAN object if a vlan name is specified
        """
        vlans = []
        
        vlan_names = self.getVLANNames()

        port_ids = self.getPortIDs()

        # If only wanting information about one vlan, only get that information.
        if theVLANName != None:
            vn = {}
            for v in vlan_names:
                if vlan_names[v] == theVLANName:
                    vn[v] = theVLANName
            vlan_names = vn
        
        for v in vlan_names:
            externalID = (self.snmp.get(OID.threecomVlanStaticExternalID + (v,)))[0][1]
            if self.snmp.getErrorStatus():
                print "unable to get external id of vlan internal ID "+v
                vlans.append(VLAN(vlan_names[v],{},None,v))
            else :
                vlans.append(VLAN(vlan_names[v],{},externalID,v,externalID))

        for vlan in vlans:
            epl = []
            upl = []
            switches = {}
            ports = []
            remove = []
            table2 = table = self.getVLANToInterfacesTable()
            for t in table:
                if t == vlan.getInternalID():
                    for tt in table[t]:
                        for pi in port_ids:
                            if pi[0][1] ==  rfc1902.Integer32(tt):
                                ports.append(Port(pi[0][0][len(pi[0][0])-1],False,tt))
                                remove.append(tt)
                    # remove found ports from the list
                    for r in remove:
                        table[t].remove(r)
                    # ports left in table[t] at this point are tagged vlans
                    for vt in table[t]:
                        for ids in table2:
                            if vt == ids:
                                for pi in port_ids:
                                    if pi[0][1] == rfc1902.Integer32(table2[ids][0]):
                                        ports.append(Port(pi[0][0][len(pi[0][0])-1],True,table2[ids][0]))
                        #vlan.setTaggedID(vt)
                        #vlan.setID(vt)
            switches[self.getSwitchName()] = ports
            vlan.setSwitches(switches)
#            print vlan
        return vlans
    
    def createVLAN(self, vlan):
        """\brief Creates a vlan as specified by a vlan object. See addPorts for rules on how ports are
                  added. The function returns the following error codes:
                  -1: if a vlan with the same external id already exists on the switch
                  -2: if a vlan with the same name already exists on the switch                  
                  -3: if there was an error creating the vlan using the retrieved index
                  -4: if the vlan id is invalid (not in the range 2-4094) or is already assigned to another vlan
                  -5: if the vlan name is invalid or couldn't be set
                  -6: if the vlan couldn't be activated
                  -7: if the operation to create and association an 802.1Q interface with the vlan failed
                  -8: if any of the operations to add ports to the vlan failed
                   0: if the operation succeeds
        \param (\c VLAN) A VLAN object representing the vlan to be added
        \return (\c int) 0 if the operation is sucessful, negative otherwise
        """

        # Now make sure that there isn't a vlan with the same name already on the switch
        log.debug("STUFF")
        vlanName = vlan.getName()
        vlanNames = self.getVLANNames()
        for name in vlanNames.values():
            if (str(name) == str(vlanName)):
                return -1

        # First we need to get the next available index to use as the vlan's internal id
        vlan.setInternalID(int(self.snmp.get(OID.threecomVlanNextAvailableIndex)[0][1]))
        if self.snmp.getErrorStatus():
            print "Error with getting next static vlan id"
            print self.snmp
            return -2
        else:
            print "Correctly got next static vlan id"
        
	# Now create the vlan using the retrieved available index
        # Table filling
        snmp_set_cmd_list = []
                
        snmp_set_cmd_list.append((OID.threecomVlanStaticRowStatus + (vlan.getInternalID(),), rfc1902.Integer(5)))
        snmp_set_cmd_list.append((OID.threecomVlanStaticExternalID + (vlan.getInternalID(),), rfc1902.Integer(vlan.getID())))        
        snmp_set_cmd_list.append((OID.threecomVlanStaticName + (vlan.getInternalID(),), rfc1902.OctetString(vlan.getName())))
        snmp_set_cmd_list.append((OID.threecomVlanStaticRowStatus + (vlan.getInternalID(),), rfc1902.Integer(1)))
        
        self.snmp.complex_set(snmp_set_cmd_list)
        if self.snmp.getErrorStatus():
            print "Error creating static vlan "+str(snmp_set_cmd_list[int(self.snmp.getErrorIndex())-1])
            #print self.snmp
            return -3
        else:
            print "Correctly created static vlan"

        # Create the vlan's 802.1Q interface
        
        # First we need to get the next available index to use as the interface's internal id
        vlan.setTaggedID(int(self.snmp.get(OID.threecomVlanNextAvailableIndex)[0][1]))
        print "next available vlan id "+str(vlan.getTaggedID())
        
        if self.snmp.getErrorStatus():
            #print "Error with getting next available vlan 8021Q id"
            log.critical("Error with getting next available vlan 8021Q id")
            #print self.snmp
            return -1
        else:
            print "Correctly got next available vlan 8021Q id"


        self.snmp.set(OID.threecomVlanTaggedRowStatus + (vlan.getTaggedID(),), rfc1902.Integer(5))
        if self.snmp.getErrorStatus():
            print "Error doing create and wait on tagged row creation"
            #print self.snmp
            return -1
        else:
            print "Correctly did create and wait on tagged row creation"
            
        snmp_set_cmd_list = []
        snmp_set_cmd_list.append((OID.threecomVlanTaggedType + (vlan.getTaggedID(),), rfc1902.Integer(2)))
        snmp_set_cmd_list.append((OID.threecomVlanTaggedTag + (vlan.getTaggedID(),), rfc1902.Integer(vlan.getID())))
        snmp_set_cmd_list.append((OID.threecomVlanTaggedRowStatus + (vlan.getTaggedID(),), rfc1902.Integer(4)))
        
        self.snmp.complex_set(snmp_set_cmd_list)
        if self.snmp.getErrorStatus():
            print "Error with creating 8021Q interface "+str(snmp_set_cmd_list[int(self.snmp.getErrorIndex())-1])
            print self.snmp
            return -7
        else:
            print "correctly created 8021Q interface"

        # Create an interface associated with the vlan using create and go (4)
        self.snmp.set(OID.ifStackStatus + (vlan.getInternalID(), vlan.getTaggedID()), rfc1902.Integer(4))
        if self.snmp.getErrorStatus():
            print "Error setting up ifStackStatus"
            print self.snmp
            return -1
        else:
            print "Correctly setup ifStackStatus"
        
	# Now add the ports to the vlan
        if (self.addPorts(vlan.getName(), vlan.getPortsOnSwitch(self.getSwitchName())) < 0):
            return -8

        return 0

    def addPorts(self,vlanName, ports):
        return self.modifyPorts(vlanName,ports,True)
    
    def deletePorts(self,vlanName, ports):
        return self.modifyPorts(vlanName,ports,False)
    
    def modifyPorts(self, vlanName, ports, addPorts):
        if (ports == None or len(ports) == 0):
            return 0

        vlan = None
        try:
            vlan = self.getFullVLANInfo(vlanName)[0]
        except Exception, e:
            print e
            
        for p in  ports:
            #get correct internal id
            print p
            p.setInternalID(self.getPortInternalID(p.getPortNumber()))
            if p.getTagged():
                # tagged
                if addPorts:
                    self.snmp.set(OID.ifStackStatus + (vlan.getTaggedID(), p.getInternalID()), rfc1902.Integer(4))
                else:
                    print vlan.getTaggedID()
                    print p.getInternalID()
                    self.snmp.set(OID.ifStackStatus + (vlan.getTaggedID(), p.getInternalID()), rfc1902.Integer(6))
                if self.snmp.getErrorStatus():
                    print "Error with adding/removing port to tagged vlan"
                    print self.snmp
                    return -1
            else:
                # untagged
                if addPorts:
                    self.snmp.set(OID.ifStackStatus + (vlan.getInternalID(), p.getInternalID()), rfc1902.Integer(4))
                else:
                    print vlan
                    print vlan.getTaggedID()
                    print p
                    print p.getInternalID()
                                    
                    self.snmp.set(OID.ifStackStatus + (vlan.getInternalID(), p.getInternalID()), rfc1902.Integer(6))
                if self.snmp.getErrorStatus():
                    print "Error with adding/removing port to untagged vlan"
                    print self.snmp
                    return -1
                                                    
        return 0
    

    def deleteVLAN(self, vlanName):
        """\brief Deletes the vlan indicated by the given vlan name. This function will
                  delete the vlan regardless of whether it contains ports or not and returns
                  the following codes:
                  -1: if the vlan does not exist on the switch
                  -2: if the operation to delete the vlan's 802.1Q failed
                  -3: if the snmpset command to delete the vlan fails
                   0: if successful
        \param vlanName (\c string) The name of the vlan to delete
        \return (\c int) 0 if successful, negative otherwise
        """
        vi = self.getFullVLANInfo(vlanName)
        if len(vi) == 1:
            vlan = vi[0]
        else:
            return -1
        if (vlan.getInternalID() == -1):
            return -1

        # First delete any 802.1Q interfaces associated with this vlan

        if vlan.getTaggedID() != None:
            if (self.__delete8021QInterface(vlan.getTaggedID()) < 0):
                print "error deleting tagged vlan"
                return -2
                        
        # At this point we have a valid vlan, delete it (this command deletes the
        # vlan regardless of whether it contains ports or not
        self.snmp.set(OID.threecomVlanStaticRowStatus + (vlan.getInternalID(),), rfc1902.Integer(6))
        if self.snmp.getErrorStatus():
            print "Error with deleting vlan : "#+str(mylist[int(self.snmp.getErrorIndex())-1])
            print self.snmp
            return -3

        return 0

    def __delete8021QInterface(self,id):
        print "MISSING"
        return 1

    def getSerialNumber(self):
        serial = self.snmp.get(OID.threecomStackUnitSerialNumber)[0][1]
        if self.snmp.getErrorStatus():
            print "error getting serial number"
            return "unknown"
        return serial

class ThreecomSuperstackSwitch(ThreecomSwitch):
    """\brief Sub-subclass used to support 3com superstack switches. This class contains information
              specific to this model of switch (number of ports, etc)
    """
    functions = ["switch"]
    def __init__(self, switchNode):
        """\brief Initializes the class
        \param switchNode (\c SwitchNode) The SwitchNode object to obtain information from to initialize the class with
        """
        functions = ["switch"]
        ThreecomSwitch.__init__(self, switchNode, 2, 4094, 10000, 100000)
        
    def getFullMACTable(self):
        """\brief Returns a list of MACTableEntry objects representing the full mac table of the
                  switch (the switch's database).
        \return (\c list of MACTableEntry objects) A list of MACTableEntry objects
        """
        originalCommunity = self.snmp.getCommunity()
        table = []
        macs = []
      
        vlans = self.getFullVLANInfo()
        
        
        for vlan in vlans:
            community = str(originalCommunity) + "@" + str(vlan.getID())
            self.snmp.setCommunity(community)
            macs = Switch.getFullMACTable(self)
            for mac in macs:
                table.append(mac)
        self.snmp.setCommunity(originalCommunity)
        return table

