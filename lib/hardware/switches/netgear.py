##### WARNING NOT TESTED FULLY ######

##################################################################################################################
# netgear.py: contains the switch subclass for netgear switches
#
# CLASSES
# --------------------------------------------------------------------
# Netgear                           The class used to support NETGEAR switches (derived from the Switch superclass). This class
#                              contains all operations relating to proprietary NETGEAR SNMP mibs, such as VLAN operations.
# Procurve                     The class used to support NETGEAR Procurve switches. This class contains information
#                              specific to this model of switch (number of ports, etc)
#
##################################################################################################################
import commands, os, string, math
from hardware.switches.switch import Switch
from auxiliary.snmp import SNMP
from auxiliary.oid import OID
from pysnmp.proto import rfc1902
from auxiliary.hen import VLAN, MACTableEntry, Port

###########################################################################################
#   CLASSES
###########################################################################################
class NetgearSwitch(Switch):
    """\brief Subclass for any NETGEAR switch in the testbed
    This subclass implements methods to retrieve and set information from a switch using SNMP version 1 that
    is proprietary to NETGEAR (vlans, etc).
    """

    def getVLANNames(self):
        """\brief Gets the names of the vlans on the switch, returning a dictio\nary whose keys are the objects'
        internal ids and whose values are the actual vlan names (see getSNMPRes\ultTable for more info)
        \return (\c dictionary) A dictionary with the names of the vlans
        """
        vlans = {}
        
        netgearVlanStaticNameTable = self.snmp.walk(OID.netgearVlanStaticName)
        for netgearVlanStaticNameTableRow in netgearVlanStaticNameTable:
            vlans[int(netgearVlanStaticNameTableRow[0][0][len(netgearVlanStaticNameTableRow[0][0])-1])] = netgearVlanStaticNameTableRow[0][1]
        
        return vlans
                                                    
    def getFullVLANInfo(self, theVLANName=None):
        """\brief Returns a list of VLAN objects consisting of all of the vlans\ in the switch. If the theVLANName parameter is set, the function returns a sin\gle VLAN object corresponding to the requested vlan
        \param theVLANName (\c string) The name of the VLAN to retrieve
        \return (\c list of VLAN objects) A list of VLAN objects with the reque\sted information or a VLAN object if a vlan name is specified
        """
        vlans = []
        vlan_names = self.getVLANNames()
        port_ids = self.getPortIDs()
        
        # If only wanting information about one vlan, only get that information.
        if theVLANName != None:
            vn = {}
            for v in vlan_names.keys():
                if vlan_names.get(v) == theVLANName:
                    vn[v] = theVLANName
                    vlan_names = vn
                    
        # Create VLAN objects from vlan names
        for v in vlan_names:
            vlans.append(VLAN(vlan_names[v],{},v,v))

        portGeneralAccessTable = self.snmp.walk(OID.netgearGeneralPortAccess)
        portVlanTaggedTypeTable = self.snmp.walk(OID.netgearVlanTaggedType)
        for vlan in vlans:
            ports = []
            temp_ports = []
            switches = {}
     
            for portGeneralAccessTableRow in portGeneralAccessTable:
                #print portGeneralAccessTableRow
                if (portGeneralAccessTableRow[0][1] == rfc1902.Integer32(vlan.getID())):
                    vid = portGeneralAccessTableRow[0][1]
                    pid = portGeneralAccessTableRow[0][0][len(portGeneralAccessTableRow[0][0])-1]
                    #print vlan.getID(),vid,pid
                    temp_ports.append(Port(pid,False,pid))
            for portVlanTaggedTypeRow in portVlanTaggedTypeTable:
                vid = portVlanTaggedTypeRow[0][0][len(portVlanTaggedTypeRow[0][0])-1]
                pid = portVlanTaggedTypeRow[0][0][len(portVlanTaggedTypeRow[0][0])-2]
                vlanType = portVlanTaggedTypeRow[0][1]
                #print portVlanTaggedVlanRow
                if (vid == rfc1902.Integer32(vlan.getID())):
                    if (vlanType == rfc1902.Integer32(1)):
                        temp_ports.append(Port(pid,False,pid))
                    elif (vlanType == rfc1902.Integer32(2)):
                        temp_ports.append(Port(pid,True,pid))
                    else:
                        print "unknown vlan type ",pid,vid,vlanType

                temp_ports.sort()
                # clean list
                if (len(temp_ports) > 0):
                    ports.insert(0,temp_ports[0])
                    temp_ports.remove(ports[0])
                    while (len(temp_ports) > 0):
                        if ports[0] == temp_ports[0]:
                            temp_ports.remove(ports[0])
                        elif (ports[0].getInternalID() == temp_ports[0].getInternalID() and ports[0].getPortNumber() == temp_ports[0].getPortNumber() ):
                            if (ports[0].getTagged() == True and temp_ports[0].getTagged() == False):
                                ports[0].setTagged(False)
                                temp_ports.remove(temp_ports[0]) 
                        else:
                            ports.insert(0,temp_ports[0])
                            temp_ports.remove(ports[0])
            switches[self.getSwitchName()] = ports
            vlan.setSwitches(switches)
        return vlans

    def createVLAN(self, vlan):
        vlanName = vlan.getName()
        vlanNames = self.getVLANNames()
        for name in vlanNames.values():
            if (str(name) == str(vlanName)):
                return -1

        self.snmp.set( OID.netgearVlanStaticRowStatus + (vlan.getID(),) , rfc1902.Integer32(5))
        if self.snmp.getErrorStatus():
            print "Error with creating vlan row"
            print self.snmp
            return -2
                                            
        self.snmp.set( OID.netgearVlanStaticName + (vlan.getID(),) , rfc1902.OctetString(vlan.getName()))
        
        if self.snmp.getErrorStatus():
            print "Error with setting vlan name"
            print self.snmp
            return -3
        # Now add the ports to the vlan
        if (self.addPorts(vlan.getName(), vlan.getPortsOnSwitch(self.getSwitchName())) < 0):
            return -4
        
        return 0

    def deleteVLAN(self,vlanName):
        vlanNames = self.getVLANNames()
        for vlanId in vlanNames:
            
            if vlanNames[vlanId] == vlanName:
                self.snmp.set(OID.netgearVlanStaticRowStatus + (vlanId,), rfc1902.Integer32(6))
                if self.snmp.getErrorStatus():
                    print "error deleting vlan"
                    return -1
                else:
                    return 0
        return -2

    def addPorts(self,vlanName, ports):
        return self.modifyPorts(vlanName,ports,True)
    
    def deletePorts(self,vlanName, ports):
        return self.modifyPorts(vlanName,ports,False)
    
    def modifyPorts(self,vlanName, ports, addPorts):
        if (ports == None or len(ports) == 0):
            return 0
        
        vlan = self.getFullVLANInfo(vlanName)[0]
        for port in  ports:
            # internal and external port ids are the same
            port.setInternalID(port.getPortNumber())
            
            if port.getTagged():
                # tagged
                if addPorts:
                    self.snmp.set(OID.netgearVlanTaggedRowStatus + (port.getInternalID(),vlan.getID(),),rfc1902.Integer32(5))
                    if self.snmp.getErrorStatus():
                        print "error creating (un)tagged row"
                        return -2
                    self.snmp.set(OID.netgearVlanTaggedType + (port.getInternalID(),vlan.getID(),),rfc1902.Integer32(2))
                    if self.snmp.getErrorStatus():
                        print "error setting row tagged type"
                        return -2
                else:
                    self.snmp.set(OID.netgearVlanTaggedRowStatus + (port.getInternalID(),vlan.getID(),),rfc1902.Integer32(6))
                    if self.snmp.getErrorStatus():
                        print "error deleting (un)tagged row"
                        return -2
                    
            else:
                # untagged
                if addPorts:
                    # set pvid
                    self.snmp.set(OID.netgearGeneralPortAccess + (port.getInternalID(),),rfc1902.Integer32(vlan.getID()))
                    # set untagged
                    if self.snmp.getErrorStatus():
                        print "error setting general access on port"
                        return -1
                    self.snmp.set(OID.netgearVlanTaggedRowStatus + (port.getInternalID(),vlan.getID(),),rfc1902.Integer32(5))
                    if self.snmp.getErrorStatus():
                        print "error creating (un)tagged row"
                        return -2
                    self.snmp.set(OID.netgearVlanTaggedType + (port.getInternalID(),vlan.getID(),),rfc1902.Integer32(1))
                    if self.snmp.getErrorStatus():
                        print "error setting row tagged type"
                        return -2
                else:
                    # clear untagged
                    self.snmp.set(OID.netgearGeneralPortAccess + (port.getInternalID(),),rfc1902.Integer32(1))
                    if self.snmp.getErrorStatus():
                        print "error setting pvid to default"
                        return -2
                    self.snmp.set(OID.netgearVlanTaggedRowStatus + (port.getInternalID(),vlan.getID(),),rfc1902.Integer32(6))
                    if self.snmp.getErrorStatus():
                        print "error deleting untagged row"
                        return -2
        return 0
                        

class NetgearFsm700sSwitch(NetgearSwitch):
    """\brief Sub-subclass used to support NETGEAR Procurve switches. This class contains information
              specific to this model of switch (number of ports, etc)          
    """

    def __init__(self, switchNode):
        """\brief Initializes the class
        \param switchNode (\c SwitchNode) The SwitchNode object to obtain infor\mation from to initialize the class with
        """
        NetgearSwitch.__init__(self, switchNode, 2, 4094, 10000, 100000)
                        
