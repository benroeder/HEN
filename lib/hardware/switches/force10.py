####################
# TODO
# Add roll back support for adding ports
# Add roll back support for creating vlans
# Add more debugging to telnet interface
# Clean up code
# More comments, and fix comments
# Add exception throwing

##################################################################################################################
# force10.py: contains the switch subclass for Force10 switches
#
# CLASSES
# --------------------------------------------------------------------
# Force10Switch             The class used to support Force10 switches (derived from the Switch superclass). This class
#                            contains all operations relating to proprietary Force10 SNMP mibs, such as VLAN operations.
# Force10E1200Switch   The class used to support Force10 superstack switches. This class contains information
#                            specific to this model of switch (number of ports, etc)
#
##################################################################################################################
import commands, os, string
from hardware.switches.switch import Switch
from auxiliary.hen import VLAN, Port, MACTableEntry, SimplePort, SimpleVlan
from auxiliary.snmp import SNMP
from auxiliary.oid import OID
from pysnmp.proto import rfc1902
from pysnmp.entity.rfc3413 import cmdgen, mibvar
from pysnmp.entity import engine, config
from pysnmp.smi import view
from pyasn1.codec.ber import decoder
from pyasn1.type import univ
from struct import *
from array import *
import time

import telnetlib

import logging 

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

###########################################################################################
#   CLASSES
###########################################################################################
class Force10Switch(Switch):
    """\brief Subclass for any Force10 switch in the testbed
    This subclass implements methods to retrieve and set information from a switch using SNMP version 1 that
    is proprietary to Force10 (vlans, etc).
    """

    functions = []
    #INTERNAL_ID_OFFSET = 1107787776
    broken_firmware=True
    DEFAULT_VLAN="Vlan 1"
###########################################################################
# Set VLAN Name
###########################################################################
    
    def __setVLANName(self, vlan):
        # there are currently issues with the force10 firmware
        # that means the vlan name needs to be set via telnet
        
        if not Force10Switch.broken_firmware:
            # use snmp to set the vlan name
            self.__setVLANNameSNMP(vlan)
        else:
            # use telnet to set the vlan name
            self.__setVLANNameTelnet(vlan.getID(),vlan.getName())

    # work around method to set the vlan name
    def __setVLANNameTelnet(self, vlan_id,vlan_name):
        tn = telnetlib.Telnet(self.getIPAddress())
        user = "admin"
        password = "admin"
        TIMEOUT=2
        tn.set_debuglevel(1)
        tn.read_until("Login: ")
        tn.write(user + "\n")
        if password:
            tn.read_until("Password: ",TIMEOUT)
            tn.write(password + "\n")
            
        tn.write("configure\n")
        tn.read_until("Force10(conf)#",TIMEOUT)
        tn.write("interface vlan "+str(vlan_id)+"\n")
        tn.read_until("Force10(conf-if-vl-"+str(vlan_id)+")#",TIMEOUT)
        tn.write("name "+str(vlan_name)+"\n")
        tn.read_until("Force10(conf-if-vl-"+str(vlan_id)+")#",TIMEOUT)
        tn.write("exit\n")
        tn.read_until("Force10(conf)#",TIMEOUT)
        tn.write("exit\n")
        tn.read_until("Force10#",TIMEOUT)
        tn.write("exit\n")

    def __setVLANNameSNMP(self,vlan):
        # use snmp to set the vlan name
        self.snmp.set(\
            OID.dot1qVlanStaticName + (vlan.getInternalID(),),\
            rfc1902.OctetString(str(vlanName)))
        if self.snmp.getErrorStatus():
            log.debug("Error with "+str(mylist[int(self.snmp.getErrorIndex())-1]))
            return -1
        return 0

###########################################################################
# Delete VLAN
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
        return self.__deleteVLAN(vlan_name,vlan_id)
        
    def __deleteVLAN(self,vlan_name,vlan_id):
        log.debug("__deleteVLAN "+str(vlan_name)+" "+str(vlan_id))
        if not Force10Switch.broken_firmware:
            return self.__deleteVLANSNMP(vlan_name)
        else:
            return self.__deleteVLANTelnet(vlan_id)

    # work around method to set the vlan name
    def __deleteVLANTelnet(self, vlan_id):
        tn = telnetlib.Telnet(self.getIPAddress())
        user = "admin"
        password = "admin"
        TIMEOUT=2
        tn.set_debuglevel(1)
        tn.read_until("Login: ")
        tn.write(user + "\n")
        if password:
            tn.read_until("Password: ",TIMEOUT)
            tn.write(password + "\n")
            
        tn.write("configure\n")
        tn.read_until("Force10(conf)#",TIMEOUT)
        tn.write("no interface vlan "+str(vlan_id)+"\n")
        tn.read_until("Force10(conf)#",TIMEOUT)
        tn.write("exit\n")
        tn.read_until("Force10#",TIMEOUT)
        tn.write("exit\n")
        return 0
        
    def __deleteVLANSNMP(self, vlan_name):
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
        self.snmp.set( \
            OID.dot1qVlanStaticRowStatus+(vlan_ifindex,) ,\
            rfc1902.Integer32(6) )

        # check to see whether the set worked
        if self.snmp.getErrorStatus():
            log.debug("Error deleting vlan with and ifindex"+str(vlan_ifindex)+" on switch "+str(self.getSwitchName()))
            return -1
        return 0            

###########################################################################
# Create VLAN
###########################################################################

    def __createVLAN2(self, vlan_id, vlan_name):
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
    

    def __createVLAN(self, vlan_id):
        """\brief Creates a vlan given an id
        \param vlan_id (\c int) vlan id to add
        \return (\int) 0 if the operation is successful, -1 if it failed.
        """
        log.debug( str(OID.dot1qVlanStaticRowStatus+(vlan_id,)) )
        # you create a vlan using its tagged id
        self.snmp.set( \
            OID.dot1qVlanStaticRowStatus+(vlan_id,) ,\
            rfc1902.Integer32(4) )
        
        if self.snmp.getErrorStatus():
            log.debug("Error creating vlan with id "+str(vlan_id)+" on switch "+str(self.getSwitchName()))
            return -1
        return 0

    def __setVLANName2(self, vlan_name, vlan_ifindex):
        # use snmp to set the vlan name
        print "vlan_name "+str(vlan_name)
        print "vlan_ifindex "+str(vlan_ifindex)
        self.snmp.set(OID.dot1qVlanStaticName + (vlan_ifindex,),\
                      rfc1902.OctetString(str(vlan_name)))
        if self.snmp.getErrorStatus():
            log.debug("Error with "+str(mylist[int(self.snmp.getErrorIndex())-1]))
            return -1
        return 0

    def addUntaggedPort(self,port_str,vlan_str):
       self.refreshVlanInfo()
       vlan_obj = self.getVlanByName(vlan_str)
       port_obj = self.getPortByName(port_str)
       if vlan_obj == None or port_obj == None:
           print "error with addUntaggedPort in force10.py"
           print "port_str",port_str
           print "vlan_str",vlan_str
           print "vlan_obj",str(vlan_obj)
           print "port_obj",str(port_obj)
           print "vlan_obj id",str(vlan_obj.getLocalId())
           print "port_obj id",str(port_obj.getId())
           return -1
       log.debug("port obj"+str(port_obj))
       log.debug("vlan obj"+str(vlan_obj))
       snmp_list = []
       snmp_list.append(self.__modUntaggedPort(vlan_obj.getLocalId(),port_obj.getId(),True))
       snmp_list.append(self.__modTaggedPort(vlan_obj.getLocalId(),port_obj.getId(),True))
       
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
           print "error with addUntaggedPort in force10.py"
           print "port_str",port_str
           print "vlan_str",vlan_str
           print "vlan_obj",str(vlan_obj)
           print "port_obj",str(port_obj)
           print "vlan_obj id",str(vlan_obj.getLocalId())
           print "port_obj id",str(port_obj.getId())
           return -1
       log.debug("port obj"+str(port_obj))
       log.debug("vlan obj"+str(vlan_obj))
       snmp_list = []
       #snmp_list.append(self.__modUntaggedPort(vlan_obj.getLocalId(),port_obj.getId(),True))
       snmp_list.append(self.__modTaggedPort(vlan_obj.getLocalId(),port_obj.getId(),True))
       
       self.snmp.complex_set(snmp_list)
       
       if self.snmp.getErrorStatus():
           log.debug("Problem with adding port "+str(port_obj.getId())+" to vlan")
           return -1
       return 0

    def removeUntaggedPort(self,port_str,vlan_str):
       #self.refreshVlanInfo()
       vlan_ifindex = self.__getVlanIfIndexFromName(vlan_str)
       vlan_id = self.__getVlanIdFromIfIndex(vlan_ifindex)
       return self.__deleteUntaggedPortTelnet(port_str,vlan_id)

    def removeTaggedPort(self,port_str,vlan_str):
       #self.refreshVlanInfo()
       vlan_ifindex = self.__getVlanIfIndexFromName(vlan_str)
       vlan_id = self.__getVlanIdFromIfIndex(vlan_ifindex)
       return self.__deleteTaggedPortTelnet(port_str,vlan_id)

    def rubbish(self):
       vlan_obj = self.getVlanByName(vlan_str)
       vlan_default_obj = self.getVlanByName("Vlan 1")
       port_obj = self.getPortByName(port_str)
       if vlan_obj == None or port_obj == None:
           print "error with addUntaggedPort in force10.py"
           print "port_str",port_str
           print "vlan_str",vlan_str
           print "vlan_default_obj",str(vlan_default_obj)
           print "vlan_obj",str(vlan_obj)
           print "port_obj",str(port_obj)
           print "vlan_obj id",str(vlan_obj.getLocalId())
           print "port_obj id",str(port_obj.getId())
           return -1
       log.debug("port obj : "+str(port_obj))
       log.debug("vlan obj : "+str(vlan_obj))
       log.debug("vlan_default_obj : "+str(vlan_default_obj))
       snmp_list = []
       snmp_list.append(self.__modTaggedPort(vlan_obj.getLocalId(),port_obj.getId(),False))
       snmp_list.append(self.__modUntaggedPort(vlan_obj.getLocalId(),port_obj.getId(),False))
       
       # try moving deleted vlan to the default one as we delete it.
       #snmp_list.append(self.__modUntaggedPort(vlan_default_obj.getLocalId(),port_obj.getId(),True))
       #snmp_list.append(self.__modTaggedPort(vlan_default_obj.getLocalId(),port_obj.getId(),True))
       # alternative thing to try, is just moving it to the defualt.
       self.snmp.complex_set(snmp_list)
       print "SNMP LIST "+str(snmp_list)
       if self.snmp.getErrorStatus():
           log.debug("Problem with removing port "+str(port_obj.getId())+" to vlan")
           return -1
       return 0 

    def __addUntaggedPort(self,port_name,vlan_ifindex):
        port_ifindex = self.__getPortInternalID(port_name)
        if (port_ifindex == -1):
            log.debug("Can't get port ifindex for port name "+str(port_name))
            return -1

        print vlan_ifindex
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
        snmp_list.append((OID.dot1qVlanStaticUntaggedPorts + (vlan_ifindex,), upl))
        snmp_list.append((OID.dot1qVlanStaticEgressPorts + (vlan_ifindex,) , epl))

        self.snmp.complex_set(snmp_list)
        if self.snmp.getErrorStatus():
            log.debug("Problem with adding port "+str(port_name)+" to vlan")
            return -1
        return 0

    def __modUntaggedPort(self,vid,pid,mod):
       # if mod is True, turn the port on
       # False, turn the port off
       # None, get the status
       log.debug("full "+self.snmp.get(OID.dot1qVlanStaticUntaggedPorts \
                           + (int(vid),))[0][1])
       upl = self.snmp.get(OID.dot1qVlanStaticUntaggedPorts \
                           + (int(vid),))[0][1]
       log.debug("upl "+str(upl)) 
       if self.snmp.getErrorStatus():
           log.debug("unable to get untagged ports")
           return -1
       if mod != None:
           log.debug("ifmap "+str(self.portIfIndexMapRev[pid]))
           upl = self.__setPortList(upl,self.portIfIndexMapRev[pid],mod)
           log.debug("new upl "+str(upl))
       snmp_entry = (OID.dot1qVlanStaticUntaggedPorts + (int(vid),), upl)
       print "SNMP ENTRY "+str(snmp_entry)
       return snmp_entry
                                                                                           
    def __modTaggedPort(self,vid,pid,mod):
       # get Static Egress Ports Map
       epl = self.snmp.get(OID.dot1qVlanStaticEgressPorts + (int(vid),))[0][1]
       if self.snmp.getErrorStatus():
           log.debug("unable to get tagged ports")
           return -1
       epl = self.__setPortList(epl,self.portIfIndexMapRev[pid],mod)
       snmp_entry = (OID.dot1qVlanStaticEgressPorts + (int(vid),) , epl)
       return snmp_entry
                                                                   
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
                                                                                                                                                                                                                                                                                                                                                                                   

    def __addUntaggedPort(self,port_name,vlan_ifindex):
        port_ifindex = self.__getPortInternalID(port_name)
        log.debug("PORT IF INDEX "+str(port_ifindex))
        if (port_ifindex == -1):
            log.debug("Can't get port ifindex for port name "+str(port_name))
            return -1

        print vlan_ifindex
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
        print "success 1"
        if (vlan_name == None or vlan_name == "None"):
            log.debug("can't create a vlan with a None name")
            return -1
        print "success 2"
                                                                            
        # Create the vlan
        if (self.__createVLAN2(vlan_id,vlan_name) == -1):
            log.debug("Failed to create vlan for id "+str(vlan_id))
            return -1
        print "success 3"
        
        # Get ifindex for vlan ID
        vlan_ifindex = self.__getIfindexForVLANID(vlan_id)
        if (vlan_ifindex == -1):
            log.debug("Error getting vlan ifindex for vlan id "+str(vlan_id))
            return -1                                    
        print "success 4"
        
        # Name the vlan
        if (self.__setVLANName2(vlan_name,vlan_ifindex) == -1):
            log.debug("Failed to name vlan for id "+str(vlan_id)+" with "+str(vlan_name))
            # roll back earlier creation.
            if (vlan_ifindex != -1):
                if (self.__deleteVLANByIfindex(vlan_ifindex) == -1):
                    log.critical("failed to rolled back vlan creation of vlan "+str(vlan_name)+" with id "+str(vlan_id))
                else:
                    log.critical("successfully rolled back vlan creation of vlan "+str(vlan_name)+" with id "+str(vlan_id))
            else:
                log.critical("failed to get ifindex when rolling back")
            print "success 5"
            return -1
        print "success 6"
        return 0
        
    def createVLAN(self, vlan):
        """\brief Creates a vlan as specified by a vlan object. See addPorts for rules on how ports are
                  added. The function returns the following error codes:
                  -1: if the operation failed
                   0: if the operation succeeds
        \param vlan (\c VLAN) A VLAN object representing the vlan to be added
        \return (\c int) 0 if the operation is sucessful, negative otherwise
        """   
        # Check whether the vlan exists
        if (self.__vlanExistsForName(vlan.getName())):
            log.debug("trying to add a vlan that exists")
            return -1
        if (vlan.getName() == None or vlan.getName() == "None"):
            log.debug("can't create a vlan with a None name")
            return -1
        
        # Create the vlan
        if (self.__createVLAN(vlan.getID()) == -1):
            log.debug("Failed to create vlan for id "+str(vlan.getID()))
            return -1

        # Get ifindex for vlan ID
        vlan_ifindex = self.__getIfindexForVLANID(vlan.getID()) 
        if (vlan_ifindex == -1):
            log.debug("Error getting vlan ifindex for vlan id  (b)"+str(vlan.getID()))
            return -1
        vlan.setInternalID(vlan_ifindex)

        # Name the vlan
        if (self.__setVLANName(vlan) == -1):
            log.debug("Failed to name vlan for id "+str(vlan.getID())+" with "+str(vlan.getName()))
            # roll back earlier creation.
            if (vlan_ifindex != -1):
                if (self.__deleteVLANByIfindex(vlan_ifindex) == -1):
                    log.critical("failed to rolled back vlan creation of vlan "+str(vlan.getName())+" with id "+str(vlan.getID()))
                else:
                    log.critical("successfully rolled back vlan creation of vlan "+str(vlan.getName())+" with id "+str(vlan.getID()))
            else:
                log.critical("failed to get ifindex when rolling back")
            return -1  
        
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
            return -1
        
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
# Remove untagged ports
###########################################################################

    def __deleteUntaggedPort(self,port_name,vlan_ifindex):
        # there are currently issues with the force10 firmware
        # that means the vlan name needs to be set via telnet
        
        if not Force10Switch.broken_firmware:
            # use snmp to set the vlan name
            self.__deleteUntaggedPortSNMP(port_name,vlan_ifindex)
        else:
            # use telnet to set the vlan name
            # need to lookup vlan index for vlan ifindex
            vlan_id = self.__getVlanIdFromIfIndex(vlan_ifindex)
            if vlan_id == -1:
                log.debug("Couldn't get vlan id for vlan ifindex "+str(vlan_ifindex))
                return -1
            self.__deleteUntaggedPortTelnet(port_name,vlan_id)

    def __deleteUntaggedPortTelnet(self,port_name,vlan_id):
        tn = telnetlib.Telnet(self.getIPAddress())
        user = "admin"
        password = "admin"
        TIMEOUT=2
        tn.set_debuglevel(1)
        tn.read_until("Login: ")
        tn.write(user + "\n")
        if password:
            tn.read_until("Password: ",TIMEOUT)
            tn.write(password + "\n")
            
        tn.write("configure\n")
        tn.read_until("Force10(conf)#",TIMEOUT)
        tn.write("interface vlan "+str(vlan_id)+"\n")
        tn.read_until("Force10(conf-if-vl-"+str(vlan_id)+")#",TIMEOUT)
        tn.write("no untagged "+str(port_name)+"\n")
        tn.read_until("Force10(conf-if-vl-"+str(vlan_id)+")#",TIMEOUT)
        tn.write("exit\n")
        tn.read_until("Force10(conf)#",TIMEOUT)
        tn.write("exit\n")
        tn.read_until("Force10#",TIMEOUT)
        tn.write("exit\n")
        return 0 
    
    def __deleteUntaggedPortSNMP(self,port_name,vlan_ifindex):
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
        # there are currently issues with the force10 firmware
        # that means the vlan name needs to be set via telnet
        
        if not Force10Switch.broken_firmware:
            # use snmp to set the vlan name
            self.__deleteTaggedPortSNMP(port_name,vlan_ifindex)
        else:
            # use telnet to set the vlan name
            # need to lookup vlan index for vlan ifindex
            vlan_id = self.__getVlanIdFromIfIndex(vlan_ifindex)
            if vlan_id == -1:
                log.debug("Couldn't get vlan id for vlan ifindex "+str(vlan_ifindex))
                return -1
            self.__deleteTaggedPortTelnet(port_name,vlan_id)

    def __deleteTaggedPortTelnet(self,port_name,vlan_id):
        tn = telnetlib.Telnet(self.getIPAddress())
        user = "admin"
        password = "admin"
        TIMEOUT=2
        tn.set_debuglevel(1)
        tn.read_until("Login: ")
        tn.write(user + "\n")
        if password:
            tn.read_until("Password: ",TIMEOUT)
            tn.write(password + "\n")
            
        tn.write("configure\n")
        tn.read_until("Force10(conf)#",TIMEOUT)
        tn.write("interface vlan "+str(vlan_id)+"\n")
        tn.read_until("Force10(conf-if-vl-"+str(vlan_id)+")#",TIMEOUT)
        tn.write("no tagged "+str(port_name)+"\n")
        tn.read_until("Force10(conf-if-vl-"+str(vlan_id)+")#",TIMEOUT)
        tn.write("exit\n")
        tn.read_until("Force10(conf)#",TIMEOUT)
        tn.write("exit\n")
        tn.read_until("Force10#",TIMEOUT)
        tn.write("exit\n")
        return 0


    def __deleteTaggedPortSNMP(self,port_name,vlan_ifindex):
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

    def getVlanList(self):
        vlan_names = self.getVLANNames()
        vlan_ids_table = self.getDot1qVlanFdbId()
        self.clearVlans()
        for vlan_id in vlan_ids_table:
            vid = vlan_id[0][0][-1]
            sv = SimpleVlan(vlan_names[vid],str(vlan_id[0][1]),str(vid),self.getNodeID())
            self.addVlan(sv)

    def refreshVlanInfo(self):
        """\brief Refreshes both the port list and vlan list for the switch
    """
        untaggedPorts = self.getDot1qVlanStaticUntaggedPorts()
        taggedPorts = self.getDot1qVlanStaticEgressPorts()
        pvidPorts = self.getDot1qPvid()

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
        #vlans['1'] = rfc1902.OctetString('Default VLAN')

        #for i in vlans:
        #    log.debug( i,vlans[i] )
        return vlans

    def getFullVLANInfo(self, theVLANName=None):
        """\brief Returns a list of VLAN objects consisting of all of the vlans in the switch. If the theVLANName parameter is set, the function returns a single VLAN object corresponding to the requested vlan
        \param theVLANName (\c string) The name of the VLAN to retrieve  
        \return (\c list of VLAN objects) A list of VLAN objects with the requested information or a VLAN object if a vlan name is specified
        """
        vlans = []

        portIfIndexTable = self.getDot1dBasePortIfIndex()
        ifDescrTable = self.getIfDescr()
        untaggedPorts = self.getDot1qVlanStaticUntaggedPorts()
        taggedPorts = self.getDot1qVlanStaticEgressPorts()
        pvidPorts = self.getDot1qPvid()
        vlan_names = self.getVLANNames()
        vlan_ids = self.getDot1qVlanFdbId()
        #log.debug( untaggedPorts )
        #log.debug( taggedPorts )
        #log.debug( pvidPorts )

        vlan_list = {} # key -> (name, untagged list, tagged list, pvid list)

        for vid in vlan_names:
            if not vlan_list.has_key(vid):
                vlan_list[vid] = (None,[],[],[])
            vlan_list[vid] = (vlan_names[vid],[],[],[])
        # put untagged ports into list
        for up in untaggedPorts:
            pl = self.__parsePortList(up[0][1],False)
            vid = up[0][0][len(up[0][0])-1]
            if not vlan_list.has_key(vid):
                vlan_list[vid] = (None,[],[],[])
            vlan_list[vid] = (vlan_list[vid][0],pl, vlan_list[vid][2], vlan_list[vid][3])
        # put tagged ports into list
        for tp in taggedPorts:
            pl = self.__parsePortList(tp[0][1],True)
            vid = tp[0][0][len(tp[0][0])-1]
            if not vlan_list.has_key(vid):
                vlan_list[vid] = (None,[],[],[])
            vlan_list[vid] = (vlan_list[vid][0],vlan_list[vid][1],pl, vlan_list[vid][3])
        # put pvid ports into list
        for pp in pvidPorts:
            pl = self.__parsePortList(pp[0][1],False)
            vid = pp[0][0][len(pp[0][0])-1]
            if not vlan_list.has_key(vid):
                vlan_list[vid] = (None,[],[],[])
            vlan_list[vid] = (vlan_list[vid][0],vlan_list[vid][1],vlan_list[vid][2],pl)
        for v in vlan_list:
            #if v == 1107787777:
            #    continue
            #log.debug( "vlan ",v," ",vlan_list[v][0] )
            #log.debug( "\t untagged" )
            for port in vlan_list[v][1]:
                found = False
                for portIfIndexTableRow in portIfIndexTable:
                    if portIfIndexTableRow[0][0][len(portIfIndexTableRow[0][0])-1] == port.getInternalID():
                        #print portIfIndexTableRow[0][0][len(portIfIndexTableRow[0][0])-1],port.getInternalID()
                        for ifDescrTableRow in ifDescrTable:
                            if ifDescrTableRow[0][0][len(ifDescrTableRow[0][0])-1] == portIfIndexTableRow[0][1]:
                                port.setPortNumber(ifDescrTableRow[0][1])
                                port.setInternalID(portIfIndexTableRow[0][1])
                                found = True
                                break
                    if found : break
                            
                #log.debug( "\t\t",port, )
            #log.debug( "\t tagged" )
            
            for port in vlan_list[v][2]:
                found = False
                for portIfIndexTableRow in portIfIndexTable:
                    if portIfIndexTableRow[0][0][len(portIfIndexTableRow[0][0])-1] == port.getInternalID():
                        for ifDescrTableRow in ifDescrTable:
                            if ifDescrTableRow[0][0][len(ifDescrTableRow[0][0])-1] == portIfIndexTableRow[0][1]:
                                port.setPortNumber(ifDescrTableRow[0][1])
                                port.setInternalID(portIfIndexTableRow[0][1])
                                found = True
                                break
                    if found : break
                
                #log.debug( "\t\t",port,)
            #log.debug( "\t pvid")
            
            for port in vlan_list[v][3]:
                found = False
                for portIfIndexTableRow in portIfIndexTable:
                    if portIfIndexTableRow[0][0][len(portIfIndexTableRow[0][0])-1] == port.getInternalID():
                        for ifDescrTableRow in ifDescrTable:
                            if ifDescrTableRow[0][0][len(ifDescrTableRow[0][0])-1] == portIfIndexTableRow[0][1]:
                                port.setPortNumber(ifDescrTableRow[0][1])
                                port.setInternalID(portIfIndexTableRow[0][1])
                                found = True
                                break
                    if found : break
                
                #log.debug( "\t\t",port,)

        # consider what to do with ports in both tagged and untagged state

        for v in vlan_list:
            switches = {}
            tmp_vlan = VLAN(vlan_list[v][0])
            tmp_vlan.setInternalID(v)
            for vid in vlan_ids:
                if vid[0][0][len(vid[0][0])-1] == v:
                    tmp_vlan.setID(vid[0][1])
                    tmp_vlan.setTaggedID(vid[0][1])
                    break
            switches[self.getSwitchName()] = vlan_list[v][1] + vlan_list[v][2] + vlan_list[v][3] 
            tmp_vlan.setSwitches(switches)
            vlans.append(tmp_vlan)

        for vlan in vlans:
            if (vlan.getName() == theVLANName):
                return [vlan]                    
        return vlans
    
###########################################################################
# Get Mac table
###########################################################################
    
    def getFullMACTable(self,simple=False):
        if simple:
            return self.__getSimpleMACTable()
        else:
            return self.__getFullMACTable()
        
    def __getFullMACTable(self):
        """\brief Gets the full learned mac table from the switch, returning a  list of MACTableEntry objects.
        \return (\c list) A list of MACTableEntry objects with the results.
        """
        portsTable = self.getDot1qTpFdbPort()
        learnedTypeTable = self.getDot1qTpFdbStatus()
        portIfIndexTable = self.getDot1dBasePortIfIndex()
        ifDescrTable = self.getPortNames()

        # get mac table
        result = []
        for learnedTypeTableRow in learnedTypeTable:
            for learnedname, learnedval in learnedTypeTableRow:
                if learnedval == rfc1902.Integer32('3'):
                    learnedname = rfc1902.ObjectName((learnedname.prettyPrint()).replace(OID.dot1qTpFdbStatus.prettyPrint(),OID.dot1qTpFdbPort.prettyPrint()))
                    for portTableRow in portsTable:
                        for portname, portval in portTableRow:
                            if learnedname == portname:
                                result.append(MACTableEntry(("%02x:%02x:%02x:%02x:%02x:%02x" % (int(learnedname[14]),int(learnedname[15]),int(learnedname[16]),int(learnedname[17]),int(learnedname[18]),int(learnedname[19]))).replace("0x","").upper(),portval,'3',self.getSwitchName()))

        # Translate ids to names
        for port in result:
            #log.debug( port.getPort())
            for portIfIndexTableRow in portIfIndexTable:
                
                if portIfIndexTableRow[0][0][len(portIfIndexTableRow[0][0])-1] == port.getPort():
                    for ifDescrTableRow in ifDescrTable:
                        if ifDescrTableRow[0][0][len(ifDescrTableRow[0][0])-1] == portIfIndexTableRow[0][1]:
                            port.setPort(ifDescrTableRow[0][1])
                                
        return result

    def addMacsToPorts(self):
        """\brief Gets the full learned mac table from the switch, returning a  list of MACTableEntry objects.
        \return (\c list) A list of MACTableEntry objects with the results.
        """
        portsTable = self.getDot1qTpFdbPort()
        learnedTypeTable = self.getDot1qTpFdbStatus()
        portIfIndexTable = self.getDot1dBasePortIfIndex()
        ifDescrTable = self.getPortNames()

        self.resetPortsMacInfo()
        # get mac table
        result = []
        for learnedTypeTableRow in learnedTypeTable:
            for learnedname, learnedval in learnedTypeTableRow:
                if learnedval == rfc1902.Integer32('3'):
                    for portTableRow in portsTable:
                        for portname, portval in portTableRow:
                            if learnedname[-6:] == portname[-6:]:
                                #print portname, portval#', rubbish
                                mac = ("%02x:%02x:%02x:%02x:%02x:%02x" %
                                       (int(learnedname[14]),
                                        int(learnedname[15]),
                                        int(learnedname[16]),
                                        int(learnedname[17]),
                                        int(learnedname[18]),
                                        int(learnedname[19])))
                                mac = mac.replace("0x","").upper()
                                port = self.getPort(self.portIfIndexMap[portval])
                                mac_list = port.getMacs()
                                mac_list.append(mac)
                                port.setMacs(mac_list)
                                
    def __getSimpleMACTable(self):
        """\brief Gets the full learned mac table from the switch, returning a  list of MACTableEntry objects.
        \return (\c list) A list of MACTableEntry objects with the results.
        """
        portsTable = self.getDot1qTpFdbPort()
        learnedTypeTable = self.getDot1qTpFdbStatus()
        portIfIndexTable = self.getDot1dBasePortIfIndex()
        ifDescrTable = self.getPortNames()

        # get mac table
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
                                result.append((mac,portval))
        # Translate ids to names
        for i in range(0,len(result)):
            #log.debug( port.getPort())
            for portIfIndexTableRow in portIfIndexTable:
                
                if portIfIndexTableRow[0][0][len(portIfIndexTableRow[0][0])-1] == result[i][1]:
                    for ifDescrTableRow in ifDescrTable:
                        if ifDescrTableRow[0][0][len(ifDescrTableRow[0][0])-1] == portIfIndexTableRow[0][1]:
                            result[i] = (result[i][0],str(ifDescrTableRow[0][1]))
        return result

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
            log.debug("Error getting ifindex for vlan id (a)"+str(vlan_id))
            return -1
        
        for dot1qVlanFdbIdRow in dot1qVlanFdbIdTable:
            #print ">",str(dot1qVlanFdbIdRow[0][1]),str(vlan_id)
            if (int(dot1qVlanFdbIdRow[0][1]) == int(vlan_id)):
                #print " > FOUND ",str(dot1qVlanFdbIdRow[0][0][len(dot1qVlanFdbIdRow[0][0])-1])
                return int(dot1qVlanFdbIdRow[0][0][len(dot1qVlanFdbIdRow[0][0])-1])
        return -1                                   

    def __getVlanIfIndexFromName(self, vlan_name):
        dot1qVlanStaticNameTable = self.getDot1qVlanStaticName()
        for dot1qVlanStaticNameRow in dot1qVlanStaticNameTable:
            #print ">>> ",str(dot1qVlanStaticNameRow[0][1]),str(vlan_name)
            if (str(dot1qVlanStaticNameRow[0][1]) == str(vlan_name)):
                #print ">>>> found ",str(dot1qVlanStaticNameRow[0][0][len(dot1qVlanStaticNameRow[0][0])-1])
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
        ifDescrTable = self.getIfDescr()
        portIfIndexTable = self.getDot1dBasePortIfIndex()
        for ifDescrTableRow in ifDescrTable:
            if (str(ifDescrTableRow[0][1]) == str(port)):
                ifindex=ifDescrTableRow[0][0][len(ifDescrTableRow[0][0])-1]
                for portIfIndexTableRow in portIfIndexTable:
                    if (str(ifindex) == str(portIfIndexTableRow[0][1])):
                        return int(portIfIndexTableRow[0][0][len(portIfIndexTableRow[0][0])-1])
        return -1
    
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
        return rfc1902.OctetString(str(s))

    def __parsePortList(self,pl,tagged):
        ports = []
        mask = [128,64,32,16,8,4,2,1,0]
        port_number = 0
        for i in range(0,len(pl)):
            port = (unpack('B',pl[i]))[0]
            if port != 0:
                if (port & Switch.mask[0] == Switch.mask[0]):
                    ports.append(Port(port_number+1,tagged,port_number+1))
                if (port & Switch.mask[1] == Switch.mask[1]):
                    ports.append(Port(port_number+2,tagged,port_number+2))
                if (port & Switch.mask[2] == Switch.mask[2]):
                    ports.append(Port(port_number+3,tagged,port_number+3))
                if (port & Switch.mask[3] == Switch.mask[3]):
                    ports.append(Port(port_number+4,tagged,port_number+4))
                if (port & Switch.mask[4] == Switch.mask[4]):
                    ports.append(Port(port_number+5,tagged,port_number+5))
                if (port & Switch.mask[5] == Switch.mask[5]):
                    ports.append(Port(port_number+6,tagged,port_number+6))
                if (port & Switch.mask[6] == Switch.mask[6]):
                    ports.append(Port(port_number+7,tagged,port_number+7))
                if (port & Switch.mask[7] == Switch.mask[7]):
                    ports.append(Port(port_number+8,tagged,port_number+8))
            port_number = port_number + 8
        return ports

    def __simpleParsePortList(self,pl):
        ports = []
        mask = [128,64,32,16,8,4,2,1,0]
        port_number = 0
        for i in range(0,len(pl)):
            port = (unpack('B',pl[i]))[0]
            if port != 0:
                if (port & Switch.mask[0] == Switch.mask[0]):
                    ports.append(self.portIfIndexMap[port_number+1])
                if (port & Switch.mask[1] == Switch.mask[1]):
                    ports.append(self.portIfIndexMap[port_number+2])
                if (port & Switch.mask[2] == Switch.mask[2]):
                    ports.append(self.portIfIndexMap[port_number+3])
                if (port & Switch.mask[3] == Switch.mask[3]):
                    ports.append(self.portIfIndexMap[port_number+4])
                if (port & Switch.mask[4] == Switch.mask[4]):
                    ports.append(self.portIfIndexMap[port_number+5])
                if (port & Switch.mask[5] == Switch.mask[5]):
                    ports.append(self.portIfIndexMap[port_number+6])
                if (port & Switch.mask[6] == Switch.mask[6]):
                    ports.append(self.portIfIndexMap[port_number+7])
                if (port & Switch.mask[7] == Switch.mask[7]):
                    ports.append(self.portIfIndexMap[port_number+8])
            port_number = port_number + 8
        return ports

    def __slowparsePortList(self,pl,tagged):
        ports = []
        raw_ports = array('B')
        for i in range(0,len(pl)):
            ports = []
            raw_ports.extend(unpack('B',pl[i]))            
            mask = [128,64,32,16,8,4,2,1,0]
            port_number = 0
            for port in raw_ports:
                if port != 0:
                    for slot in range(0,8):
                        port_number = port_number + 1
                        if (port & Switch.mask[slot] == Switch.mask[slot]):
                            ports.append(Port(port_number,tagged,port_number))
                else:
                    port_number = port_number + 8
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

    def getPortStatus(self, portNumber):
        """\brief Gets the operational status of a port: up (1), down (2)
        \param portNumber (\c string) The port whose status is to be retrieved
        \return (\c string) The port status
        """
        ifDescrTable = self.getIfDescr()
        for ifDescrTableRow in ifDescrTable:
            if (str(ifDescrTableRow[0][1]) == str(portNumber)):
                ifindex=ifDescrTableRow[0][0][len(ifDescrTableRow[0][0])-1]
                return self.snmp.get(OID.ifOperStatus+(ifindex,))[0][1]
        return "unknown"

    def getPortTdr(self, port_name):
    	tn = telnetlib.Telnet(self.getIPAddress())
        user = "admin"
        password = "admin"
        TIMEOUT=2
        #tn.set_debuglevel(1)
        tn.read_until("Login: ")
        tn.write(user + "\n")
        if password:
            tn.read_until("Password: ",TIMEOUT)
            tn.write(password + "\n")

        tn.write("tdr-cable-test "+str(port_name)+"\n")
        tn.read_until("Force10#",TIMEOUT)
        tn.write("exit\n")
	time.sleep(10)
	tn = telnetlib.Telnet(self.getIPAddress())
        user = "admin"
        password = "admin"
        TIMEOUT=2
        #tn.set_debuglevel(1)
        tn.read_until("Login: ")
        tn.write(user + "\n")
        if password:
            tn.read_until("Password: ",TIMEOUT)
            tn.write(password + "\n")
	
        tn.write("show tdr "+str(port_name)+"\n\n")
        (code,obj,string_return) = tn.expect(["Error","Time"],TIMEOUT)
	output = tn.read_until("Force10#",TIMEOUT)
        tn.write("exit\n")
	
	s = "TDR result :"
	if code != 1:
	   s = "\nError running TDR test"
	if code == 1:
	   for i in output.split('\n'):
	       if i.find("Pair") != -1:
	       	  s = s + "\n" + i.lstrip()
        # 4 OK's and 4 Terminated means success
        if s.count("OK") == 4 and s.count("Terminated") == 4:
            return (True,s)
	return (False,s)

###########################################################################
# Other
##############y#############################################################

    def getPortInternalID(self, port):
        return self.__getPortInternalID(port)
        
class Force10E1200Switch(Force10Switch):
    """\brief Sub-subclass used to support Force10 E1200 switches. This class contains information
              specific to this model of switch (number of ports, etc)
    """
    functions = ["switch"]

    SENSOR_DESCRIPTIONS = {'temperature':{ \
                                      'fantray0':75.000, \
                                      'fantray1':75.000, \
                                      'card0':75.000, \
                                      'card1':75.000, \
                                      'card2':75.000, \
                                      'card3':75.000, \
                                      'card4':75.000, \
                                      'card5':75.000, \
                                      'card6':75.000, \
                                      'card7':75.000, \
                                      'card8':75.000, \
                                      'card9':75.000, \
                                      'card10':75.000, \
                                      'card11':75.000, \
                                      'card12':75.000, \
                                      'card13':75.000, \
                                      'card14':75.000 \
                                      }}

    def __init__(self, switchNode):
        """\brief Initializes the class
        \param switchNode (\c SwitchNode) The SwitchNode object to obtain information from to initialize the class with
        """
        Force10Switch.__init__(self, switchNode, 2, 4094, 10000, 100000)
        portIfIndexTable = self.getDot1dBasePortIfIndex()
        self.portIfIndexMap = {}
        self.portIfIndexMapRev = {}
        for portIfIndexTableRow in portIfIndexTable:
            self.portIfIndexMap[portIfIndexTableRow[0][0][-1]] = portIfIndexTableRow[0][1]
            self.portIfIndexMapRev[portIfIndexTableRow[0][1]] = portIfIndexTableRow[0][0][-1]
            
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
        sensorResults = self.getEmptySensorDictionary()
        temperatureTable = self.snmp.walk(OID.force10chSysCardUpperTemp)
        if not self.snmp.getErrorStatus():
            for temperatureTableRow in temperatureTable:
                phySlotNum = temperatureTableRow[0][0][\
                                               len(temperatureTableRow[0][0])-1]
                phySlotTemp = temperatureTableRow[0][1]
                sensorName = ""
                if (phySlotNum == 8):
                    sensorName = "fantray0"
                elif (phySlotNum == 9):
                    sensorName = "fantray1"
                elif (phySlotNum < 8):
                    sensorName = "card"+str(phySlotNum -1)
                elif (phySlotNum > 9):
                    sensorName = "card"+str(phySlotNum -3)
                sensorClass = self.getSensorClassFromName( \
                                   self.SENSOR_DESCRIPTIONS, sensorName)
                if sensorClass:
                    (sensorResults[sensorClass])[sensorName] = int(phySlotTemp)
        return sensorResults

    def getSerialNumber(self):
        serial = self.snmp.get(OID.force10chSerialNumber)[0][1]
        if self.snmp.getErrorStatus():
            log.debug( "error getting serial number" )
            return "unknown"
        return serial
    
    def getNumberofPorts(self):
        raise Exception("Should calculate this")
        return 480
