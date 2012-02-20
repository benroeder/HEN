############
# TODO
# Sort out port access modes
# Delete modifyports method


##################################################################################################################
# linksys.py: contains the switch subclass for Linksys switches
#
# CLASSES
# --------------------------------------------------------------------
# LinksysSwitch             The class used to support Linksys switches (derived from the Switch superclass). This class
#                            contains all operations relating to proprietary Linksys SNMP mibs, such as VLAN operations.
# LinksysSuperstackSwitch   The class used to support Linksys superstack switches. This class contains information
#                            specific to this model of switch (number of ports, etc)
#
##################################################################################################################
import commands, os, string
from hardware.switches.switch import Switch
from auxiliary.hen import VLAN, Port, SimplePort, SimpleVlan
from auxiliary.snmp import SNMP
from auxiliary.oid import OID
from pysnmp.proto import rfc1902
from struct import *
from array import *
from auxiliary.hen import MACTableEntry

import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

###########################################################################
#   CLASSES
###########################################################################
class LinksysSwitch(Switch):
    """\brief Subclass for any Linksys switch in the testbed
    This subclass implements methods to retrieve and set information from a switch using SNMP version 1 that
    is proprietary to Linksys (vlans, etc).
    """

    functions = []    

###########################################################################
# Set VLAN Name
###########################################################################  

    def __setVLANName(self, vlan_name, vlan_ifindex):
        # use snmp to set the vlan name
        self.snmp.set(\
            OID.dot1qVlanStaticName + (vlan_ifindex,),\
            rfc1902.OctetString(str(vlan_name)))
        if self.snmp.getErrorStatus():
            log.debug("Error with "+str(mylist[int(self.snmp.getErrorIndex())-1]))
            return -1
        return 0

###########################################################################
# Delete Vlan
###########################################################################  
                                                    
    def deleteVLAN(self, vlan_name):
        # Check whether the vlan exists
        if (not self.__vlanExistsForName(vlan_name)):
            log.debug("trying to delete a vlan that doesn't exist")
            return -1

        vlan_ifindex = self.__getVlanIfIndexFromName(vlan_name)
        if (vlan_ifindex == -1):
            log.debug("can't get ifindex for vlan "+str(vlan_name))
            return -1
        log.debug("vlan ifindex "+str(vlan_ifindex))
        vlan_id = self.__getVlanIdFromIfIndex(vlan_ifindex)
        if (vlan_id == -1):
            log.debug("can't get vlan id for vlan "+str(vlan_name)+" for ifindex "+str(vlan_ifindex))
            return -1
        log.debug("vlan id "+str(vlan_id))
        return self.__deleteVLAN(vlan_name)
    
    def __deleteVLAN(self, vlan_name):
        """\brief Creates a vlan given an name
        \param vlan_name (\c string) vlan name to delete
        \return (\int) 0 if the operation is successful, -1 if it failed.
        """
        # you delete a vlan by using its ifindex.

        # get vlan ifindex from vlan_name
        vlan_ifindex = self.__getVLANInternalID(vlan_name)

        log.debug("Deleting vlan with name "+str(vlan_name)+" and ifindex"+str(vlan_ifindex)+" on switch "+str(self.getSwitchName()))

        # check that we got a sane ifindex
        if vlan_ifindex == -1:
            log.debug("When deleting vlan with name "+str(vlan_id)+" couldn't get ifindex on switch "+str(self.getSwitchName()))
            return -1
        
        # use snmp to delete the vlan
        self.snmp.set( \
            OID.dot1qVlanStaticRowStatus+(vlan_ifindex,) ,\
            rfc1902.Integer32(6) )

        # check to see whether the set worked
        if self.snmp.getErrorStatus():
            log.debug("Error deleting vlan with name "+str(vlan_name)+" and ifindex"+str(vlan_ifindex)+" on switch "+str(self.getSwitchName()))
            return -1
        return 0

    def __deleteVLANByIfindex(self, vlan_ifindex):
        """\brief Creates a vlan given an name
        \param vlan_name (\c string) vlan name to delete
        \return (\int) 0 if the operation is successful, -1 if it failed.
        """
        # you delete a vlan by using its ifindex.
        
        log.debug("Deleting vlan with ifindex "+str(vlan_ifindex)+" on switch "+str(self.getSwitchName()))
        
        # use snmp to delete the new vlan
        self.snmp.set(OID.dot1qVlanStaticRowStatus+(vlan_ifindex,) ,\
                      rfc1902.Integer32(6) )
        
        # check to see whether the set worked
        if self.snmp.getErrorStatus():
            log.debug("Error deleting vlan with and ifindex"+str(vlan_ifindex)+" on switch "+str(self.getSwitchName()))
            return -1
        return 0
    
###########################################################################
# Create VLAN
###########################################################################

    def __createVLAN(self, vlan_id, vlan_name):
        """\brief Creates a vlan given an id
        \param vlan_id (\c int) vlan id to add
        \return (\int) 0 if the operation is successful, -1 if it failed.
        """
        log.debug( str(OID.dot1qVlanStaticRowStatus+(vlan_id,)) )
        # you create a vlan using its tagged id
        snmp_list = []
        snmp_list.append( (OID.dot1qVlanStaticName+(vlan_id,) , rfc1902.OctetString(str(vlan_name)) ))
        snmp_list.append( (OID.dot1qVlanStaticEgressPorts+(vlan_id,) , rfc1902.OctetString(self.getEmptyBitMap(64)) ))
        snmp_list.append( (OID.dot1qVlanForbiddenEgressPorts+(vlan_id,) , rfc1902.OctetString(self.getEmptyBitMap(64)) ))
        snmp_list.append( (OID.dot1qVlanStaticUntaggedPorts+(vlan_id,) , rfc1902.OctetString(self.getEmptyBitMap(64))))
        snmp_list.append( (OID.dot1qVlanStaticRowStatus+(vlan_id,) , rfc1902.Integer32(4) ))
        
        self.snmp.complex_set(snmp_list)
        
        if self.snmp.getErrorStatus():
            log.debug("Error creating vlan with id "+str(vlan_id)+" on switch " +str(self.getSwitchName()))
            return -1
        return 0

    def _creatVLAN(self, vlan_id, vlan_name):
        """\brief Creates a vlan based on its id and name
        \param vlan (\c vlan_id) 802.1Q id for the vlan
        \param vlan (\c vlan_name) name of the vlan
        \return (\c int) 0 if the operation is sucessful, negative otherwise
        """
        # Check whether the vlan exists
        if (self.__vlanExistsForName(vlan_name)):
            log.debug("trying to add a vlan that exists")
            return -1
        if (vlan_name == None or vlan_name == "None"):
            log.debug("can't create a vlan with a None name")
            return -1
        
        # Create the vlan
        if (self.__createVLAN(vlan_id,vlan_name) == -1):
            log.debug("Failed to create vlan for id "+str(vlan_id))
            return -1
        
        # Get ifindex for vlan ID
        vlan_ifindex = self.__getIfindexForVLANID(vlan_id)
        if (vlan_ifindex == -1):
            log.debug("Error getting vlan ifindex for vlan id "+str(vlan_id))
            return -1
        #vlan.setInternalID(vlan_ifindex)

        # Name the vlan
        if (self.__setVLANName(vlan_name,vlan_ifindex) == -1):
            log.debug("Failed to name vlan for id "+str(vlan_id)+" with "+str(vlan_name))
            # roll back earlier creation.
            if (vlan_ifindex != -1):
                if (self.__deleteVLANByIfindex(vlan_ifindex) == -1):
                    log.critical("failed to rolled back vlan creation of vlan "+str(vlan_name)+" with id "+str(vlan_id))
                else:
                    log.critical("successfully rolled back vlan creation of vlan "+str(vlan_name)+" with id "+str(vlan_id))
            else:
                log.critical("failed to get ifindex when rolling back")
            return -1
        return 0
    
    def createVLAN(self, vlan):
        # this method is eventually to be phased out and replaced
        # by the one above. It doesn't seem sense to have all the
        # extra overhead of the vlan object and the port addition
        # here. Make it simple and just create a vlan with a name
        # and an id.
        if (self._createVLAN(vlan.getID(),vlan.getName()) == -1):
            return -1
        
        # long term we should remove this and make stuff simpler
        # need to add roll back support
        for port in vlan.getPortsOnSwitch(self.getSwitchName()):
            if not port.getTagged():
                if (self.__addUntaggedPort(port.getPortNumber(),vlan_ifindex) == -1 ):
                    log.debug("Error added untagged port "+str(port.getPortNumber())+" to vlan "+str(vlan.getName()))
                    return -1
                else:
                    log.debug("Successfully added untagged port "+str(port.getPortNumber())+" to vlan "+str(vlan.getName()))
            else:
                if (self.__addTaggedPort(port.getPortNumber(),vlan_ifindex) == -1 ):
                    log.debug("Error added tagged port "+str(port.getPortNumber())+" to vlan "+str(vlan.getName()))
                    return -1
                else:
                    log.debug("Successfully added tagged port "+str(port.getPortNumber())+" to vlan "+str(vlan.getName()))
                    
        return 0

###########################################################################
# Add ports
###########################################################################

    def addPorts(self,vlan_name, ports):
        vlan_ifindex = self.__getVlanIfIndexFromName(vlan_name)
        if (vlan_ifindex == -1):
            log.debug("Unable to get vlan ifindex for vlan name "+str(vlan_name))
        for port in ports:
            if not port.getTagged():
                if (self.__addUntaggedPort(port.getPortNumber(),vlan_ifindex) == -1 ):
                    log.debug("Error added untagged port "+str(port.getPortNumber())+" to vlan "+str(vlan_name))
                    return -1
                else:
                    log.debug("Successfully added untagged port "+str(port.getPortNumber())+" to vlan "+str(vlan_name))
            else:
                if (self.__addTaggedPort(port.getPortNumber(),vlan_ifindex) == -1 ):
                    log.debug("Error added tagged port "+str(port.getPortNumber())+" to vlan "+str(vlan_name))
                    return -1
                else:
                    log.debug("Successfully added tagged port "+str(port.getPortNumber())+" to vlan "+str(vlan_name))
        return 0


        

###########################################################################
# Delete ports
###########################################################################

    def deletePorts(self,vlan_name, ports):
        vlan_ifindex = self.__getVlanIfIndexFromName(vlan_name)
        if (vlan_ifindex == -1):
            log.debug("Unable to get vlan ifindex for vlan name "+str(vlan_name))
            return -1
        
        for port in ports:
            if not port.getTagged():
                if (self.__deleteUntaggedPort(port.getPortNumber(),vlan_ifindex) == -1 ):
                    log.debug("Error deleting untagged port "+str(port.getPortNumber())+" to vlan "+str(vlan_name))
                    return -1
                else:
                    log.debug("Successfully deleted untagged port "+str(port.getPortNumber())+" to vlan "+str(vlan_name))
            else:
                if (self.__deleteTaggedPort(port.getPortNumber(),vlan_ifindex) == -1 ):
                    log.debug("Error deleting tagged port "+str(port.getPortNumber())+" to vlan "+str(vlan_name))
                    return -1
                else:
                    log.debug("Successfully deleted tagged port "+str(port.getPortNumber())+" to vlan "+str(vlan_name))
        return 0

###########################################################################
# Add untagged ports
###########################################################################

    def __addUntaggedPort(self,port_name,vlan_ifindex):
        port_ifindex = self.__getPortInternalID(port_name)
        if (port_ifindex == -1):
            log.debug("Can't get port ifindex for port name "+str(port_name))
            return -1

        # get Static Untagged Ports Map
        upl = self.snmp.get(OID.dot1qVlanStaticUntaggedPorts + (vlan_ifindex,))[0][1]
        if self.snmp.getErrorStatus():
            log.debug("unable to get untagged ports")
            return -1
        #log.debug(self.printPortMap(upl,False))

        # get Static Egress Ports Map
        epl = self.snmp.get(OID.dot1qVlanStaticEgressPorts + (vlan_ifindex,))[0][1]
        if self.snmp.getErrorStatus():
            log.debug("unable to get tagged ports")
            return -1
        #log.debug( self.printPortMap(epl,True) )
        
        upl = self.__setPortList(upl,port_ifindex,True)
        epl = self.__setPortList(epl,port_ifindex,True)

        snmp_list = []
        snmp_list.append((OID.dot1qVlanStaticEgressPorts + (vlan_ifindex,) , epl))
        snmp_list.append((OID.dot1qVlanStaticUntaggedPorts + (vlan_ifindex,), upl))        
        self.snmp.complex_set(snmp_list)
        if self.snmp.getErrorStatus():
            log.debug("Problem with adding port "+str(port_name)+" to vlan")
            return -1
        return 0

###########################################################################
# vlan modification ports - -new
###########################################################################

    def addUntaggedPort(self,port_str,vlan_str):
        self.refreshVlanInfo()
        vlan_obj = self.getVlanByName(vlan_str)
        port_obj = self.getPortByName(port_str)
        if vlan_obj == None or port_obj == None:
            print "error with addUntaggedPort in linksys.py"
            print "port_str",port_str
            print "vlan_str",vlan_str
            print "vlan_obj",str(vlan_obj)
            print "port_obj",str(port_obj)
            return -1
        snmp_list = []
        snmp_list.append(self.__modUntaggedPort(vlan_obj.getLocalId(),port_obj.getId(),True))
        snmp_list.append(self.__modTaggedPort(vlan_obj.getLocalId(),port_obj.getId(),True))
        
        self.snmp.complex_set(snmp_list)
        if self.snmp.getErrorStatus():
            log.debug("Problem with adding port "+str(port_obj.getId())+" to vlan")
            return -1
        return 0
    
    def removeUntaggedPort(self,port_str,vlan_str):
        vlan_obj = self.getVlanByName(vlan_str)
        port_obj = self.getPortByName(port_str)
        if vlan_obj == None or port_obj == None:
            return -1
        snmp_list = []
        snmp_list.append(self.__modUntaggedPort(vlan_obj.getLocalId(),port_obj.getId(),False))
        snmp_list.append(self.__modTaggedPort(vlan_obj.getLocalId(),port_obj.getId(),False))
        
        self.snmp.complex_set(snmp_list)
        if self.snmp.getErrorStatus():
            log.debug("Problem with adding port "+str(port_obj.getId())+" to vlan")
            return -1
        return 0

    def addTaggedPort(self,port_str,vlan_str):
        self.refreshVlanInfo()
        vlan_obj = self.getVlanByName(vlan_str)
        port_obj = self.getPortByName(port_str)
        if vlan_obj == None or port_obj == None:
            return -1
        snmp_list = []
        snmp_list.append(self.__modTaggedPort(vlan_obj.getLocalId(),port_obj.getId(),True))
        
        self.snmp.complex_set(snmp_list)
        if self.snmp.getErrorStatus():
            log.debug("Problem with adding port "+str(port_obj.getId())+" to vlan")
            return -1
        return 0
    
    def removeTaggedPort(self,port_str,vlan_str):
        vlan_obj = self.getVlanByName(vlan_str)
        port_obj = self.getPortByName(port_str)
        if vlan_obj == None or port_obj == None:
            return -1
        snmp_list = []
        snmp_list.append(self.__modTaggedPort(vlan_obj.getLocalId(),port_obj.getId(),False))
        snmp_list.append(self.__modUntaggedPort(vlan_obj.getLocalId(),port_obj.getId(),None))
        
        self.snmp.complex_set(snmp_list)
        if self.snmp.getErrorStatus():
            log.debug("Problem with removing port "+str(port_obj.getId())+" from vlan")
            return -1
        return 0

    def getPortsVlanMode(self):
        return self.getLinksysGeneralPortAccess()

    def getLinksysGeneralPortAccess(self,run=False):
        if self._linksysGeneralPortAccess == None or self._refresh or run:
            self._linksysGeneralPortAccess = self.snmp.walk(OID.linksysGeneralPortAccess)
        return self._linksysGeneralPortAccess
                                        

    def getPortVlanMode(self,pid):
        port = self.getPortByName(pid)
        return str(SimplePort.VLANMODE[port.getVlanMode()])
        
    def setPortVlanMode(self,pid,mode):
        port = self.getPortByName(pid)
        
        return 0
    
    def __modUntaggedPort(self,vid,pid,mod):
        # if mod is True, turn the port on
        # False, turn the port off
        # None, get the status
        upl = self.snmp.get(OID.dot1qVlanStaticUntaggedPorts \
                            + (int(vid),))[0][1]
        if self.snmp.getErrorStatus():
            log.debug("unable to get untagged ports")
            return -1
        if mod != None:
            upl = self.__setPortList(upl,pid,mod)
        snmp_entry = (OID.dot1qVlanStaticUntaggedPorts + (int(vid),), upl)
        return snmp_entry

    def __modTaggedPort(self,vid,pid,mod):
        # get Static Egress Ports Map
        epl = self.snmp.get(OID.dot1qVlanStaticEgressPorts + (int(vid),))[0][1]
        if self.snmp.getErrorStatus():
            log.debug("unable to get tagged ports")
            return -1
        epl = self.__setPortList(epl,pid,mod)
        snmp_entry = (OID.dot1qVlanStaticEgressPorts + (int(vid),) , epl)
        return snmp_entry
    
###########################################################################
# Remove untagged ports
###########################################################################

    def __deleteUntaggedPort(self,port_name,vlan_ifindex):
        port_ifindex = self.__getPortInternalID(port_name)
        if (port_ifindex == -1):
            log.debug("Can't get port ifindex for port name "+str(port_name))
            return -1

        # get Static Untagged Ports Map
        upl = self.snmp.get(OID.dot1qVlanStaticUntaggedPorts + (vlan_ifindex,))[0][1]
        if self.snmp.getErrorStatus():
            log.debug( "unable to get untagged ports")
            return -1
        #log.debug(self.printPortMap(upl,False))

        # get Static Egress Ports Map
        epl = self.snmp.get(OID.dot1qVlanStaticEgressPorts + (vlan_ifindex,))[0][1]
        if self.snmp.getErrorStatus():
            log.debug( "unable to get tagged ports" )
            return -1
        #log.debug( self.printPortMap(epl,True) )
        
        upl = self.__setPortList(upl,port_ifindex,False)
        epl = self.__setPortList(epl,port_ifindex,False)

        snmp_list = []
        snmp_list.append((OID.dot1qVlanStaticUntaggedPorts + (vlan_ifindex,), upl))
        snmp_list.append((OID.dot1qVlanStaticEgressPorts + (vlan_ifindex,) , epl))
        
        self.snmp.complex_set(snmp_list)
        if self.snmp.getErrorStatus():
            log.debug("Problem with deleting port "+str(port_name)+" to vlan")
            return -1
        return 0

###########################################################################
# Add tagged ports
###########################################################################

    def __addTaggedPort(self,port_name,vlan_ifindex):
        port_ifindex = self.__getPortInternalID(port_name)
        if (port_ifindex == -1):
            log.debug("Can't get port ifindex for port name "+str(port_name))
            return -1

        # get Static Tagged Ports Map
        upl = self.snmp.get(OID.dot1qVlanStaticUntaggedPorts + (vlan_ifindex,))[0][1]
        if self.snmp.getErrorStatus():
            log.debug("unable to get tagged ports")
            return -1
        #log.debug(self.printPortMap(upl,False))

        # get Static Egress Ports Map
        epl = self.snmp.get(OID.dot1qVlanStaticEgressPorts + (vlan_ifindex,))[0][1]
        if self.snmp.getErrorStatus():
            log.debug("unable to get tagged ports")
            return -1
        #log.debug( self.printPortMap(epl,True) )
        
        upl = self.__setPortList(upl,port_ifindex,False)
        epl = self.__setPortList(epl,port_ifindex,True)

        snmp_list = []
        snmp_list.append((OID.dot1qVlanStaticEgressPorts + (vlan_ifindex,) , epl))
        snmp_list.append((OID.dot1qVlanStaticUntaggedPorts + (vlan_ifindex,), upl))        
        self.snmp.complex_set(snmp_list)
        if self.snmp.getErrorStatus():
            log.debug("Problem with adding port "+str(port_name)+" to vlan")
            return -1
        return 0

###########################################################################
# Delete Tagged ports
###########################################################################

    def __deleteTaggedPort(self,port_name,vlan_ifindex):
        port_ifindex = self.__getPortInternalID(port_name)
        if (port_ifindex == -1):
            log.debug("Can't get port ifindex for port name "+str(port_name))
            return -1

        if self.snmp.getErrorStatus():
            log.debug( "unable to get tagged ports")
            return -1
        #log.debug(self.printPortMap(upl,False))

        # get Static Egress Ports Map
        epl = self.snmp.get(OID.dot1qVlanStaticEgressPorts + (vlan_ifindex,))[0][1]
        if self.snmp.getErrorStatus():
            log.debug( "unable to get tagged ports" )
            return -1
        #log.debug( self.printPortMap(epl,True) )
        
        epl = self.__setPortList(epl,port_ifindex,False)

        snmp_list = []
        snmp_list.append((OID.dot1qVlanStaticEgressPorts + (vlan_ifindex,) , epl))
        
        self.snmp.complex_set(snmp_list)
        if self.snmp.getErrorStatus():
            log.debug("Problem with deleting port "+str(port_name)+" to vlan")
            return -1
        return 0
    
###########################################################################
# VLAN Information
###########################################################################
    
    def getVLANNames(self):
        """\brief Gets the names of the vlans on the switch, returning a dictionary whose keys are the objects' internal ids and whose values are the actual vlan names (see \getSNMPResultTable for more info)
        \return (\c dictionary) A dictionary with the names of the vlans
        """
        vlans = {}
        dot1qVlanStaticNameTable = self.getDot1qVlanStaticName()
        for dot1qVlanStaticNameTableRow in dot1qVlanStaticNameTable:
            #log.debug( dot1qVlanStaticNameTableRow[0][1] )
            
            vlans[dot1qVlanStaticNameTableRow[0][0][len(dot1qVlanStaticNameTableRow[0][0])-1]] = dot1qVlanStaticNameTableRow[0][1]
            
        # default vlan does not show up in linksys tables, hard code it here
        vlans['1'] = rfc1902.OctetString('Default VLAN')

        #for i in vlans:
        #    log.debug( i,vlans[i] )
        return vlans
                                                                        
    def getFullVLANInfo(self, theVLANName=None):
        """\brief Returns a list of VLAN objects consisting of all of the vlans in the switch. If the theVLANName parameter is set, the function returns a single VLAN object corresponding to the requested vlan
        \param theVLANName (\c string) The name of the VLAN to retrieve  
        \return (\c list of VLAN objects) A list of VLAN objects with the requested information or a VLAN object if a vlan name is specified
        """
        vlans = []
        
        untaggedPorts = self.getDot1qVlanStaticUntaggedPorts(True)
        taggedPorts = self.getDot1qVlanStaticEgressPorts(True)
        pvidPorts = self.getDot1qPvid(True)
        vlan_names = self.getVLANNames()
        vlan_ids = self.getDot1qVlanFdbId(True)

        #log.debug( untaggedPorts )
        #log.debug( taggedPorts )
        #log.debug( pvidPorts )

        vlan_list = {} # key -> (name, untagged list, tagged list, pvid list)

        for vid in vlan_names:
            if not vlan_list.has_key(str(vid)):
                vlan_list[str(vid)] = (None,[],[],[])
            vlan_list[str(vid)] = (vlan_names[vid],[],[],[])
            #log.debug("initial vlan list "+str(vlan_list[str(vid)]))

        # put untagged ports into list
        for up in untaggedPorts:
            vid = str(up[0][0][len(up[0][0])-1])
            if not vlan_list.has_key(vid):
                vlan_list[vid] = (None,[],[],[])
                #log.debug("adding new vlan (untagged) "+str(vlan_list[vid]))
            vlan_list[vid] = (vlan_list[vid][0],self.__parsePortList(up[0][1],False), vlan_list[vid][2], vlan_list[vid][3])

        # put tagged ports into list
        for tp in taggedPorts:
            vid = str(tp[0][0][len(tp[0][0])-1])
            if not vlan_list.has_key(vid):
                vlan_list[vid] = (None,[],[],[])
                #log.debug("adding new vlan (tagged) "+str(vlan_list[vid]))
            vlan_list[vid] = (vlan_list[vid][0],vlan_list[vid][1],self.__parsePortList(tp[0][1],True), vlan_list[vid][3])

        # Remove PVID support - Adam 18/02/2008
        # put pvid ports into list
        #for pp in pvidPorts:
        #    vid = str(pp[0][1])
        #    if not vlan_list.has_key(vid):
        #        #log.debug("adding new vlan (vpid) "+str(vlan_list[vid]))
        #        vlan_list[vid] = (None,[],[],[])

        #    temp_port = Port(pp[0][0][len(pp[0][0])-1],
        #                      False,
        #                      pp[0][0][len(pp[0][0])-1])
        #    if (pp[0][0][len(pp[0][0])-1] > self.getNumberofPorts()):
        #        pass
        #    else:
        #        vlan_list[vid][3].append(temp_port)
        #        vlan_list[vid] = (vlan_list[vid][0],
        #                          vlan_list[vid][1],
        #                          vlan_list[vid][2],
        #                          vlan_list[vid][3])
            
        # consider what to do with ports in both tagged and untagged state

        for v in vlan_list:
            switches = {}
            tmp_vlan = VLAN(vlan_list[v][0])
            tmp_vlan.setInternalID(v)
            tmp_vlan.setID(v)
            tmp_vlan.setTaggedID(v)
            switches[self.getSwitchName()] = vlan_list[v][1] + vlan_list[v][2] + vlan_list[v][3] 
            tmp_vlan.setSwitches(switches)
            vlans.append(tmp_vlan)

        for vlan in vlans:
            if (vlan.getName() == theVLANName):
                return [vlan]                    
        return vlans


    def getVlanList(self):
        vlan_names = self.getVLANNames()
        self.clearVlans()
        for vid in vlan_names:
            sv = SimpleVlan(vlan_names[vid],str(vid),str(vid),self.getNodeID())
            self.addVlan(sv)
            
    def refreshVlanInfo(self):
        """\brief Refreshes both the port list and vlan list for the switch
        """
        untaggedPorts = self.getDot1qVlanStaticUntaggedPorts(True)
        taggedPorts = self.getDot1qVlanStaticEgressPorts(True)
        pvidPorts = self.getDot1qPvid(True)

        self.resetPortsVlanInfo()
        self.getVlanList()
        
        # put untagged ports into list
        for up in untaggedPorts:
            vlan = self.getVlan(str(up[0][0][-1]))
            plp = self.__simpleParsePortList(up[0][1])
            vlan.setUntagged(plp)
            for p in plp:
                port = self.getPort(p)
                port.setUntagged((vlan.getName(),vlan.getId()))
                
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


###########################################################################
# Index and Name Manipulation
###########################################################################

    def __vlanExistsForName(self, vlan_name):
        log.debug("Getting vlan id from name "+str(vlan_name))
        vlanNames = self.getVLANNames()
        if vlan_name != None:
            for name in vlanNames.values():
                if (str(name) == str(vlan_name)):
                    return True
        return False

    def __getIfindexForVLANID(self, vlan_id):
        dot1qVlanFdbIdTable = self.getDot1qVlanFdbId()
        if self.snmp.getErrorStatus():
            log.debug("Error getting ifindex for vlan id "+str(vlan_id))
            return -1
        
        for dot1qVlanFdbIdRow in dot1qVlanFdbIdTable:
            if (int(dot1qVlanFdbIdRow[0][1]) == int(vlan_id)):
                return int(dot1qVlanFdbIdRow[0][0][len(dot1qVlanFdbIdRow[0][0])-1])
        return -1                                   

    def __getVlanIfIndexFromName(self, vlan_name):
        dot1qVlanStaticNameTable = self.getDot1qVlanStaticName()
        for dot1qVlanStaticNameRow in dot1qVlanStaticNameTable:
            if (str(dot1qVlanStaticNameRow[0][1]) == str(vlan_name)):
                return dot1qVlanStaticNameRow[0][0][len(dot1qVlanStaticNameRow[0][0])-1]
        return -1

    def __getVlanIdFromIfIndex(self,ifindex):
        dot1qVlanFdbIdTable = self.getDot1qVlanFdbId()
        for dot1qVlanFdbIdRow in dot1qVlanFdbIdTable :
            
            if (str(dot1qVlanFdbIdRow[0][0][len(dot1qVlanFdbIdRow[0][0])-1]) == str(ifindex)):
                return int(dot1qVlanFdbIdRow[0][1])
        return -1
    
    def __getPortInternalID(self, port):
        """\brief Given a port's name, returns its internal id number. This overrides the definition found
                  in the Switch super class
        \param port (\c string) The name of the port
        \return (\c int) The port's internal id number
        """
        # the linksys uses the port number as the internal id
        return port
    
    def __getVLANInternalID(self, vlanName):
        """\brief Retrieves a vlan's internal id given its name. The function returns
                  the following codes:
                  -1: if the vlan does not exist on the switch
                   0: if successful
        \param vlanName (\c string) The name of the vlan
        \return (\c string) The internal id of the vlan if found, negative otherwise
        """
        ## Optimisation could be done here to ensure lookups are faster.
        ## Use a dictionary of id to name.
        
        internalID = None

        # no default vlan in the snmp tables for the linksys
        if (vlanName == "Default VLAN"):
            return "1"

        dot1qVlanStaticNameTable = self.getDot1qVlanStaticName()
        for dot1qVlanStaticNameTableRow in dot1qVlanStaticNameTable:
            if dot1qVlanStaticNameTableRow[0][1] == rfc1902.OctetString(vlanName):
                internalID = dot1qVlanStaticNameTableRow[0][0][len(dot1qVlanStaticNameTableRow[0][0])-1]

        if (internalID == None):
            return -1

        return internalID
        
###########################################################################
# Manipuate Port list
###########################################################################
    
    def __setPortList(self,pl,internal_port,enable):
        #log.debug("internal_port "+str(internal_port)+" enabled "+str(enable))
        #log.debug("start "+str(self.printPortMap(pl,enable)) )
        raw_ports = array('B')
        for i in range(0,len(pl)):
            raw_ports.extend(unpack('B',pl[i]))
                        
        port_number = 0
        
        for i in range(0,len(raw_ports)):
            for slot in range(0,8):
                port_number = port_number + 1
                if (port_number == int(internal_port)):
                    if enable:
                        #log.debug("setting port "+str(i)+" " +str(slot)+" to on")
                        raw_ports[i] = (raw_ports[i] | Switch.mask[slot])
                    else:
                        #log.debug("setting port "+str(i)+" " +str(slot)+" to off")
                        raw_ports[i] = (raw_ports[i] & Switch.inv_mask[slot])
        s = ""
        for i in range(0,len(raw_ports)):
            s = s + pack('B',raw_ports[i])

        #log.debug( "end   "+str(self.printPortMap(s,enable)) )
        return rfc1902.OctetString(s)

    def __parsePortList(self,pl,tagged):
        ports = []
        raw_ports = array('B')
        #log.debug("port list in __parsePortList "+str(pl))
        for i in range(0,len(pl)):
            ports = []
            raw_ports.extend(unpack('B',pl[i]))            
            mask = [128,64,32,16,8,4,2,1,0]
            port_number = 0
            for port in raw_ports:
                for slot in range(0,8):
                    port_number = port_number + 1
                    if (port & Switch.mask[slot] == Switch.mask[slot]):
                        ports.append(Port(port_number,tagged,port_number))
                if (port_number == self.getNumberofPorts()):
                    return ports
        return ports

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
                                        
###########################################################################
# Monitoring
###########################################################################

    def getPortsPacketCount(self, ports):
        """\brief Returns the packet counts for the given ports
        \param ports (\c list of string) The names of the ports
        \return (\c list of tuples of string, int) A list of tuples, each consisting of the port's name and its
                                                   its packet count in bytes
        """
        ifDescrTable = self.getIfDescr()
        ifPortCountTable = self.snmp.walk(OID.ifInOctects)

        results = []
        for port in ports:
            for ifDescrTableRow in ifDescrTable:
                if (ifDescrTableRow[0][1] == port.getPortNumber()):
                    for ifPortCountTableRow in ifPortCountTable:
                        if (ifDescrTableRow[0][0][10] == ifPortCountTableRow[0][0][10]):
                            results.append((port.getPortNumber(), int(ifPortCountTableRow[0][1])))
        return results
                            
    def getPortsPacketCountByInternalID(self, portInternalIDs):
        """\brief Returns the packet counts given the ports' internal id numbers
        \param ports (\c list of int) The ports' internal id numbers
        \return (\c list of tuples of int, int) A list of tuples, each consisting of the port's id and its
                                                packet count in bytes
        """        
        results = []
        for portInternalID in portInternalIDs:
            inPacketCount = int(self.snmp.get(OID.ifInUcastPkts + (portInternalID,))[0][1])
            outPacketCount = int(self.snmp.get(OID.ifOutUcastPkts + (portInternalID,))[0][1])            
            results.append((portInternalID, inPacketCount, outPacketCount))
        return results

    def getPortsSpeedByInternalID(self, portInternalIDs):
        """\brief Returns the port speeds given the ports' internal id numbers
        \param ports (\c list of int) The ports' internal id numbers
        \return (\c list of tuples of int, int) A list of tuples, each consisting of the port's id and its
                                                speed in bytes per second
        """                
        results = []
        for portInternalID in portInternalIDs:
            result = self.snmp.get(OID.ifSpeed + (portInternalID,))
            results.append((portInternalID, int(result[0][1])))
        return results

###########################################################################
# Other
###########################################################################

    def getPortInternalID(self, port):
        return self.__getPortInternalID(port)
        
###########################################################################
# Old
###########################################################################
        
#    def modifyPorts(self, vlanName, ports, addPorts):
#        """\brief Adds ports to a vlan. The function will not add ports that are already assigned
#                  to existing vlans. A tagged port will not be added if it already exists as an untagged
#                  port on the switch or if it already exists as a tagged port on the given vlan. An untagged
#                  port will not be added if it already belongs to a vlan or if it already belongs to a vlan
#                  as tagged. The function returns the following codes:
#                  -1: if the vlan does not exist on the switch
#                  -2: if the snmpset command fails for a tagged port (the other ports are still added)
#                  -3: if the snmpset command fails for an untagged port (the other ports are still added)                  
#                   0: if successful
#        \param vlanName (\c string) The name of the vlan to add ports to
#        \param port (\c list of Port objects) A list of Port objects representing the ports to add
#        \return (\c int) 0 if successful, negative otherwise
#        """
#        epl = None
#        upl = None
#        snmp_list = []
#        
#        if (ports == None or len(ports) == 0):
#            return 0
#            
#        internalID = self.__getVLANInternalID(vlanName)
#        if (internalID == -1):
#            return -1
#                
#        # Now translate the port number of the ports to be added into their internal id on the switch
#        results = self.getPortIDs()
#        for key in results:
#            for port in ports:
#                if (str(key) == str(port.getPortNumber())):
#                    port.setInternalID(str(results[key]))
#        
#        if len(ports) != 0:
#            pl = self.snmp.get(OID.dot1qVlanStaticUntaggedPorts + (internalID,))
#            if self.snmp.getErrorStatus():
#                print "unable to get untagged ports"
#                print self.snmp
#            else:
#                upl = pl[0][1]
#                #print self.printPortMap(upl,False)
#
#            pl = self.snmp.get(OID.dot1qVlanStaticEgressPorts + (internalID,))
#            if self.snmp.getErrorStatus():
#                print "unable to get tagged ports"
#                print self.snmp
#            else:
#                epl = pl[0][1]
#                #print self.printPortMap(epl,True)
#        
#        for newPort in ports:            
#            snmp_list.append((OID.linksysGeneralPortAccess + (newPort.getInternalID() , ), rfc1902.Integer32(1)))
#            if (newPort.getTagged()):
#                # Tagged Ports
#                if addPorts == True:
#                    epl = self.__setPortList(epl,newPort.getInternalID(),"on")
#                    upl = self.__setPortList(upl,newPort.getInternalID(),"off")
#                else:
#                    snmp_list.append((OID.dot1qPvid + (newPort.getInternalID(),), rfc1902.Unsigned32(1)))
#                    epl = self.__setPortList(epl,newPort.getInternalID(),"off")
#                    upl = self.__setPortList(upl,newPort.getInternalID(),"off")
#                
#            else:
#                # Untagged Ports
#                if addPorts == True:
#                    #snmp_list.append((OID.dot1qPvid + (newPort.getInternalID(),), rfc1902.Unsigned32(internalID)))
#                    upl = self.__setPortList(upl,port.getInternalID(),"on")
#                    epl = self.__setPortList(epl,port.getInternalID(),"on")
#                else:
#                    #snmp_list.append((OID.dot1qPvid + (newPort.getInternalID(),), rfc1902.Unsigned32(1)))
#                    upl = self.__setPortList(upl,port.getInternalID(),"off")
#                    epl = self.__setPortList(epl,port.getInternalID(),"off")
#
#        if snmp_list != []:
#            self.snmp.complex_set(snmp_list)
#        if self.snmp.getErrorStatus():
#            print "Error with complex set"
#            print self.snmp
#            #print self.snmp.showError()
#
#        snmp_list = []
#        
#        if upl != None:
#            snmp_list.append((OID.dot1qVlanStaticUntaggedPorts + (internalID,) , upl))
#
#        if epl != None:
#            snmp_list.append((OID.dot1qVlanStaticEgressPorts +(internalID,) , epl))
#
#        #print self.printPortMap(upl,False)
#        #print self.printPortMap(epl,True)      
#
#        if snmp_list != []:
#           self.snmp.complex_set(snmp_list)
#            if self.snmp.getErrorStatus():
#                print "Error with complex set"
#                print self.snmp
#                print self.snmp.showError()
#                
#        return 0

class LinksysSrw2048Switch(LinksysSwitch):
    """\brief Sub-subclass used to support Linksys srw2048 switches. This class contains information
              specific to this model of switch (number of ports, etc)
    """
    functions = ["switch"]
    def __init__(self, switchNode):
        """\brief Initializes the class
        \param switchNode (\c SwitchNode) The SwitchNode object to obtain information from to initialize the class with
        """
        self._linksysGeneralPortAccess = None
        self._refresh = False
        LinksysSwitch.__init__(self, switchNode, 2, 4094, 10000, 100000)

    def getNumberofPorts(self):
        """\brief return the correct number of ports on the switch, the switch reports 56 ports are avaiable when there are only 48.
        \return (\c int) number of ports
        """
        return 48

    def getFullMACTable(self,simple=False):
        if simple:
            log.debug("Simple verision")
            return self.__getSimpleMACTable()
        else:
            log.debug("Old verision")
            return self.__getFullMACTable()
        
    def __getFullMACTable(self):
        """\brief Gets the full learned mac table from the switch, returning a list of MACTableEntry objects.
        \return (\c list) A list of MACTableEntry objects with the results.
        """
        portsTable = self.getDot1qTpFdbPort(True)
        learnedTypeTable = self.getDot1qTpFdbStatus(True)
        result = []
        
        for learnedTypeTableRow in learnedTypeTable:
            for learnedname, learnedval in learnedTypeTableRow:
                if learnedval == rfc1902.Integer32('3'):
                    learnedname = rfc1902.ObjectName((learnedname.prettyPrint()).replace(OID.dot1qTpFdbStatus.prettyPrint(),OID.dot1qTpFdbPort.prettyPrint()))
                    for portTableRow in portsTable:
                        for portname, portval in portTableRow:
                            if learnedname == portname:
                                
                                result.append(MACTableEntry(("%02x:%02x:%02x:%02x:%02x:%02x" % (int(learnedname[14]),int(learnedname[15]),int(learnedname[16]),int(learnedname[17]),int(learnedname[18]),int(learnedname[19]))).replace("0x","").upper(),portval,'3',self.getSwitchName()))

        return result

    def addMacsToPorts(self):
        portsTable = self.getDot1qTpFdbPort(True)
        learnedTypeTable = self.getDot1qTpFdbStatus(True)
        
        self.resetPortsMacInfo()
        for learnedTypeTableRow in learnedTypeTable:
            for learnedname, learnedval in learnedTypeTableRow:
                if learnedval == rfc1902.Integer32('3'):
                    learnedname = rfc1902.ObjectName((learnedname.prettyPrint()).replace(OID.dot1qTpFdbStatus.prettyPrint(),OID.dot1qTpFdbPort.prettyPrint()))
                    for portTableRow in portsTable:
                        for portname, portval in portTableRow:
                            if learnedname == portname:
                                mac = ("%02x:%02x:%02x:%02x:%02x:%02x" %
                                       (int(learnedname[14]),
                                        int(learnedname[15]),
                                        int(learnedname[16]),
                                        int(learnedname[17]),
                                        int(learnedname[18]),
                                        int(learnedname[19])))
                                mac = mac.replace("0x","").upper()
                                port = self.getPort(portval)
                                mac_list = port.getMacs()
                                mac_list.append(mac)
                                port.setMacs(mac_list)

        
    def __getSimpleMACTable(self):
        """\brief Gets the full learned mac table from the switch, returning a list of MACTableEntry objects.
        \return (\c list) A list of MACTableEntry objects with the results.
        """
        portsTable = self.getDot1qTpFdbPort(True)
        learnedTypeTable = self.getDot1qTpFdbStatus(True)
        result = []
        
        for learnedTypeTableRow in learnedTypeTable:
            for learnedname, learnedval in learnedTypeTableRow:
                if learnedval == rfc1902.Integer32('3'):
                    learnedname = rfc1902.ObjectName((learnedname.prettyPrint()).replace(OID.dot1qTpFdbStatus.prettyPrint(),OID.dot1qTpFdbPort.prettyPrint()))
                    for portTableRow in portsTable:
                        for portname, portval in portTableRow:
                            if learnedname == portname:
                                mac = ("%02x:%02x:%02x:%02x:%02x:%02x" %
                                       (int(learnedname[14]),
                                        int(learnedname[15]),
                                        int(learnedname[16]),
                                        int(learnedname[17]),
                                        int(learnedname[18]),
                                        int(learnedname[19])))
                                mac = mac.replace("0x","").upper()
                                result.append((mac,str(portval)))
        return result



        
