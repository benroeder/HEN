################################################################################
# extreme.py: contains the switch subclass for Extreme switches
#
# CLASSES
# --------------------------------------------------------------------
# ExtremeSwitch              The class used to support Extreme switches (derived 
#                            from the Switch superclass). This class contains 
#                            all operations relating to proprietary Extreme SNMP 
#                            mibs, such as VLAN operations.
# ExtremeSummitSwitch        The class used to support Extreme Summit switches. 
#                            This class contains information specific to this 
#                            model of switch (number of ports, etc)
#
################################################################################
import commands, os, string
from hardware.switches.switch import Switch
from auxiliary.hen import VLAN, Port
from auxiliary.snmp import SNMP
from auxiliary.oid import OID
from pysnmp.proto import rfc1902
from pysnmp.v4.proto.rfc1902 import ObjectName

################################################################################
#   CLASSES
################################################################################
class ExtremeSwitch(Switch):
    """\brief Subclass for any 3com switch in the testbed
    This subclass implements methods to retrieve and set information from a switch using SNMP version 1 that
    is proprietary to Extreme (vlans, etc).
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
        
    def getVLANNames(self):
        """\brief Gets the names of the vlans on the switch, returning a dictionary whose keys are the objects'
        internal ids and whose values are the actual vlan names (see getSNMPResultTable for more info)
        \return (\c dictionary) A dictionary with the names of the vlans
        """
        vlans = {}
        
        extremeVlanStaticNameTable = self.snmp.walk(OID.extremeVlanStaticName)
        for extremeVlanStaticNameTableRow in extremeVlanStaticNameTable:
            vlans[int(extremeVlanStaticNameTableRow[0][0][len(extremeVlanStaticNameTableRow[0][0])-1])] = extremeVlanStaticNameTableRow[0][1]
            
        return vlans

    def getVlanInfo(self):
        vlans = {}
        dot1qVlanStaticNameTable = self.snmp.walk(OID.extremeVlanStaticName)
        dot1qVlanFdbIdTable = self.snmp.walk(OID.extremeVlanStaticExternalID)
        
        for dot1qVlanStaticNameTableRow in dot1qVlanStaticNameTable:
            for dot1qVlanFdbIdTableRow in dot1qVlanFdbIdTable:
                if dot1qVlanStaticNameTableRow[0][0][len(dot1qVlanStaticNameTableRow[0][0])-1] == dot1qVlanFdbIdTableRow[0][0][len(dot1qVlanFdbIdTableRow[0][0])-1] :
                    
                    vlans[dot1qVlanStaticNameTableRow[0][1]]  = (dot1qVlanFdbIdTableRow[0][1],dot1qVlanStaticNameTableRow[0][0][len(dot1qVlanStaticNameTableRow[0][0])-1])

        return vlans
                                                        
    def getFullVLANInfo(self, theVLANName=None):
        """\brief Returns a list of VLAN objects consisting of all of the vlan in the switch. If the theVLANName parameter is set, the function returns a single VLAN object corresponding to the requested vlan
        \param theVLANName (\c string) The name of the VLAN to retrieve
        \return (\c list of VLAN objects) A list of VLAN objects with the requested information or a VLAN object if a vlan name is specified
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
            externalID = (self.snmp.get(OID.extremeVlanStaticExternalID + (v,)))[0][1]
            if self.snmp.getErrorStatus():
                print "unable to get external id of vlan internal ID "+v
                vlans.append(VLAN(vlan_names[v],{},None,v))
            else :
                vlans.append(VLAN(vlan_names[v],{},externalID,v))
                    
        for vlan in vlans:
            ifStackStatus = self.snmp.walk(OID.ifStackStatus)
            for ifStackStatusEntry in ifStackStatus:
                if ifStackStatusEntry[0][0][len(ifStackStatusEntry[0][0])-2] == vlan.getInternalID():
                    vlan.setTaggedID(ifStackStatusEntry[0][0][len(ifStackStatusEntry[0][0])-1])

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
                                        vlan.setTaggedID(vt)
                                        
            switches[self.getSwitchName()] = ports
            vlan.setSwitches(switches)
                                
        return vlans                  


    def addPorts(self,vlanName, ports):
        return self.modifyPorts(vlanName,ports,True)
    
    def deletePorts(self,vlanName, ports):
        return self.modifyPorts(vlanName,ports,False)
    
    def modifyPorts(self, vlanName, ports, addPorts):
        if (ports == None or len(ports) == 0):
            return 0
        
        vlan = self.getFullVLANInfo(vlanName)[0]
        
        for p in  ports:
            # internal and external port ids are the same
            p.setInternalID(p.getPortNumber())
                                          
            if p.getTagged():
                # tagged
                if addPorts:
                    self.snmp.set(OID.ifStackStatus + (vlan.getTaggedID(), p.getInternalID()), rfc1902.Integer(4))
                else:
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
                    self.snmp.set(OID.ifStackStatus + (vlan.getInternalID(), p.getInternalID()), rfc1902.Integer(6))
                if self.snmp.getErrorStatus():
                    print "Error with adding/removing port to untagged vlan"
                    print self.snmp
                    return -1
                
        return 0
            

    def deleteVLAN(self, vlanName):
        """\brief Deletes the vlan indicated by the given vlan name. This function will delete the vlan regardless of whether it contains ports or not and returns the following codes:
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

        # delete ports
        res = self.deletePorts(vlanName,vlan.getPortsOnSwitch(self.getSwitchName()))
        if res != 0:
            print "problem deleting ports in vlan"
            return -3
        
        # First delete any 802.1Q interfaces associated with this vlan
        if vlan.getTaggedID() != None:                
            self.snmp.set(OID.ifStackStatus + (vlan.getInternalID(),vlan.getTaggedID()), rfc1902.Integer(6))
            if self.snmp.getErrorStatus():
                print "unable to delete tagged vlan entry interface"
                print self.snmp
                print -3

                self.snmp.set(OID.extremeVlanTaggedRowStatus + (vlan.getTaggedID(),), rfc1902.Integer32(6))
                
                if self.snmp.getErrorStatus():
                    print "unable to delete tagged interface"
                    print self.snmp
                    print -3
                
        # At this point we have a valid vlan, delete it (this command deletes the
        # vlan regardless of whether it contains ports or not
        self.snmp.set(OID.extremeVlanStaticRowStatus + (vlan.getInternalID(),), rfc1902.Integer(6))
        if self.snmp.getErrorStatus():
            print "Error with deleting vlan : "#+str(mylist[int(self.snmp.getErrorIndex())-1])
            print self.snmp
            return -3
        
        return 0

    def createVLAN(self, vlan):
        """\brief Creates a vlan as specified by a vlan object. See addPorts for rules on how ports are added. The function returns the following error codes:
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
        vlanName = vlan.getName()
        vlanNames = self.getVLANNames()
        for name in vlanNames.values():
            if (str(name) == str(vlanName)):
                return -1
            
        # First we need to get the next available index to use as the vlan's internal id
        vlan.setInternalID(int(self.snmp.get(OID.extremeVlanNextAvailableIndex)[0][1]))
        if self.snmp.getErrorStatus():
            print "Error with getting next static vlan id"
            print self.snmp
            return -2
        else:
            print "Correctly got next static vlan id"
            
        # Now create the vlan using the retrieved available index
        # Table filling
        snmp_set_cmd_list = []
        snmp_set_cmd_list.append((OID.extremeVlanStaticExternalID + (vlan.getInternalID(),), rfc1902.Integer(vlan.getID())))
        snmp_set_cmd_list.append((OID.extremeVlanStaticName + (vlan.getInternalID(),), rfc1902.OctetString(vlan.getName())))
        snmp_set_cmd_list.append((OID.extremeVlanStaticRowStatus + (vlan.getInternalID(),), rfc1902.Integer(4)))

        self.snmp.complex_set(snmp_set_cmd_list)
        if self.snmp.getErrorStatus():
            print "Error creating static vlan "+str(snmp_set_cmd_list[int(self.snmp.getErrorIndex())-1])
            #print self.snmp
            return -3
        else:
            print "Correctly created static vlan"
            
        # Create the vlan's 802.1Q interface
        
        # First we need to get the next available index to use as the interface's internal id
        vlan.setTaggedID(int(self.snmp.get(OID.extremeVlanNextAvailableIndex)[0][1]))
        print "next available vlan id "+str(vlan.getTaggedID())
        
        if self.snmp.getErrorStatus():
            print "Error with getting next available vlan 8021Q id"
            #print self.snmp
            return -1
        else:
            print "Correctly got next available vlan 8021Q id"
            
        snmp_set_cmd_list = []
        snmp_set_cmd_list.append((OID.extremeVlanTaggedType + (vlan.getTaggedID(),), rfc1902.Integer(2)))
        snmp_set_cmd_list.append((OID.extremeVlanTaggedTag + (vlan.getTaggedID(),), rfc1902.Integer(vlan.getInternalID())))
        snmp_set_cmd_list.append((OID.extremeVlanTaggedRowStatus + (vlan.getTaggedID(),), rfc1902.Integer(4)))
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

class ExtremeSummitSwitch(ExtremeSwitch):
    """\brief Sub-subclass used to support Extreme Summit switches. This class 
    contains information specific to this model of switch (number of ports, etc)
    """
    functions = ["switch"]

    SENSOR_DESCRIPTIONS = {'temperature':{ \
                                      'chassistemp':75.000 
                                      }, \
                       'alarm':{ \
                                   'fan1':2, \
                                   'fan2':2, \
                                   'overtemp':2 \
                                   }}

    def __init__(self, switchNode):
        """\brief Initializes the class
        \param switchNode (\c SwitchNode) The SwitchNode object to obtain 
        information from to initialize the class with
        """
        ExtremeSwitch.__init__(self, switchNode,1,2,3,4)

    def getSensorDescriptions(self):
        """\brief Returns the dictionary of sensorname:critical-value pairs.
        """
        return self.SENSOR_DESCRIPTIONS
    
    def getSensorReadings(self):
        """\brief Returns a dictionary of the form:
                        {sensorclass:{sensorname:reading}}.
                        
        The reading will either be a numeric value (no units of measurements are
        given in the value) or -1 for sensors that could not be read.
        """
        # Grab the chassis temperature
        sensorResults = self.getEmptySensorDictionary()
        tempClass = self.getSensorClassFromName( \
                               self.SENSOR_DESCRIPTIONS, "chassistemp")
        tempReading = self.snmp.get(OID.extremeCurrentTemperature)[0][1]
        if not self.snmp.getErrorStatus() and tempClass:
            (sensorResults[tempClass])["chassistemp"] = int(tempReading)
        # Grab the overtemp alarm status
        overtempClass = self.getSensorClassFromName( \
                               self.SENSOR_DESCRIPTIONS, "overtemp")
        overtempReading = self.snmp.get(OID.extremeOverTemperatureAlarm)[0][1]
        if not self.snmp.getErrorStatus() and tempClass:
            if overtempReading != 2:
                (sensorResults[overtempClass])["overtemp"] = 1 # ALARM
            else:
                (sensorResults[overtempClass])["overtemp"] = 0 # OK
        # Grab the fan alarm statuses
        fantable = self.snmp.walk(OID.extremeFanStatusTable)        
        for fantablerow in fantable:
            fanName = "fan" + \
                            str(fantablerow[0][0][len(fantablerow[0][0])-1])
            fanClass = self.getSensorClassFromName( \
                               self.SENSOR_DESCRIPTIONS, fanName)
            if fanClass:
                if fantablerow[0][1] != rfc1902.Integer32('1'):
                    (sensorResults[fanClass])[fanName] = 1 # ALARM
                else:
                    (sensorResults[fanClass])[fanName] = 0 # OK
        return sensorResults

    def getSerialNumber(self):
        serial = self.snmp.get(OID.extremeSystemID)[0][1]
        if self.snmp.getErrorStatus():
            print "error getting serial number"
            return "unknown"
        return serial

                                            
