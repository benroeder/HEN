#!/usr/bin/env python

#######################
# TODO
# add vlan deletion by name
########################

import sys, os
#sys.path.append("/usr/local/hen/lib")

import logging
import threading
import socket
import pickle
import commands
import re
try:
    import pydot
except:
    pass
import traceback
from daemonizer import Daemonizer
from daemon import Daemon
from henmanager import HenManager
from auxiliary.daemonlocations import DaemonLocations
from auxiliary.hen import Port
from auxiliary.hen import VLAN, VlanOwner
from auxiliary.timer import GracefulTimer


logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)
class SNMPException(Exception):
    def __init__(self,message):
        Exception.__init__(self, message)
class PortNotInVlan(Exception):
    def __init__(self,message):
        Exception.__init__(self, message)
class VlanDoesNotExist(Exception):
    def __init__(self,message):
        Exception.__init__(self, message)
class NodeDoesNotExist(Exception):
    def __init__(self,message):
        Exception.__init__(self, message)
class InterfaceDoesNotExist(Exception):
    def __init__(self,message):
        Exception.__init__(self, message)

class SimpleDevice():
    def __init__(self,hen_obj):
        self.__hen_obj = hen_obj
        self.__obj = None
        self.__working = False
        
    def getInstance(self):
        if self.__obj == None :
            try:
                self.__obj = self.__hen_obj.getInstance()
            except Exception, e:
                print "getInstance exception",e
                self.__working = False
                self.__obj = None
            else:
                self.__working = True
        return self.__obj

    def getInterfaceObj(self,interface_str):
        #print "LOOKING FOR ",interface_str
        interfaces = self.__hen_obj.getInterfaces()
        print interfaces 
        for interface_type in interfaces:
            for iface in interfaces[interface_type]:
                if str(iface.getInterfaceID()) == str(interface_str[0]) or str(iface.getInterfaceID()) == str(interface_str):
#                    print "FFADSD "+iface.getInterfaceID()#+" is "+str(interface_str.decode())
                    return iface
#                else:
#                    print "NOTTTT "+iface.getInterfaceID()+" is "+str(interface_str.decode())

    def getSwitchObj(self,interface_str):
        if self.__hen_obj.getNodeType() == "switch":
            return self.__hen_obj.getNodeID()
        return self.getInterfaceObj(interface_str).getSwitch()
    
    def getSwitchPortString(self,interface_str):
        if self.__hen_obj.getNodeType() == "switch":
            return interface_str
        return self.getInterfaceObj(interface_str).getPort()
    
    def getHenObjId(self):
        return self.__hen_obj.getNodeID()
            
    def __str__(self):
        return str(self.__hen_obj.getNodeID())

class SwitchControl(Daemon):
    """\brief Implements basic switch daemon functionality.
    """
    __version = "Switch Daemon v0.3 (simple)"
    __accept_connections = True
                                        
    def __init__(self):
        Daemon.__init__(self)
        # Initalise variables
        self.__henManager = HenManager()
        self.__vlanOwnerFilename = "/usr/local/hen/etc/switchd/vlan_owner.dat"
        
        #self.__int_to_vlan = {} # (computer_str,interface_str) -> vlan_name
        
        # Register hen rpc methods and handlers
        log.debug("Registering methods")
        self.__registerMethods()
        # Load vlan info
        #log.debug("Loading vlan info")
        #self.__initaliseVlanInfo()
        #self.initiateNodes()
        
        # vlan owners
        log.debug("Loading vlan data")
        self.__vlan_owner_name = {}
        self.__vlan_name_owner = {}
        self.loadVlanOwnerFile()
        
        
        
        # nodes
        log.debug("Loading node data")
        self.__nodes = {}
        self.__switches = []
        self.__switch_instances = {}
        self.loadNodes()
        #self.createSwitchInstances()
        # end
        
        # fetching vlan information from the switches
        log.debug("Fetching vlan info from switches")
        self.__vlan_name_switch_id = {}
        self.__vlan_id_switch_name = {}
        self.fetchVlanInfoFromSwitches()
        #raise Exception("Temp halt")
        # end
        
        
        log.debug("Initalisation complete")
        
    def __registerMethods(self):
        # hm commands
        #self.registerMethodHandler("get_switch_port_vlans_for_name", self.getSwitchPortVlansForName)
        # port commands
        self.registerMethodHandler("port_find_mac", self.portFindMac)
        self.registerMethodHandler("port_tdr", self.portTdr)
        self.registerMethodHandler("port_list", self.portList)
        self.registerMethodHandler("port_list_and_vlan",self.portListAndVlan)
        # vlan commands
        self.registerMethodHandler("vlan_show_name", self.vlanShowName)
        self.registerMethodHandler("vlan_show_user", self.vlanShowUser)
        self.registerMethodHandler("vlan_show_port", self.vlanShowPort)
        self.registerMethodHandler("vlan_show_empty", self.vlanShowEmpty)
        self.registerMethodHandler("vlan_create_vlan", self.vlanCreateVlan)
        #self.registerMethodHandler("vlan_destroy_user", self.vlanDestroyVlan)
        self.registerMethodHandler("vlan_add_port",self.vlanAddPort)
        self.registerMethodHandler("vlan_remove_port",self.vlanRemovePort)
        self.registerMethodHandler("vlan_connect_ports",self.vlanConnectPorts)
        self.registerMethodHandler("vlan_next_free_id",self.vlanNextFreeId)
        self.registerMethodHandler("vlan_port_mode_get",self.vlanPortModeGet)
        self.registerMethodHandler("vlan_port_mode_set",self.vlanPortModeSet)
    # HM COMMANDS  ########################################

    def portTdr(self,prot,seq,ln,payload):
        args = pickle.loads(payload)
        if len(args) != 2:
            code = 400
            reply = str("Incorrect number of arguments")
            self.__sendReply(prot,code,seq,reply)
            return        
        device_str = args[0]
        interface_str = args[1]
        print "running tdr with ",device_str,interface_str
        try:
            device = self.__nodes[device_str]
            switch = self.__nodes[device.getSwitchObj(interface_str)].getInstance()
            res = self.__port_tdr(switch,device.getSwitchPortString(interface_str))
            #print "tdr results",res
            reply = pickle.dumps(res)
            code = 200
            
            self.__sendReply(prot,code,seq,reply)
        except Exception, e:
            code = 400
            reply = "Error with portTdr "+str(e)
            self.__sendReply(prot,code,seq,reply)
            return
        
    def portFindMac(self,prot,seq,ln,payload):
        mac_str = pickle.loads(payload)
        if mac_str == None:
            code = 400
            reply = str("Incorrect argument")+" "+str(mac_str)
            self.__sendReply(prot,code,seq,reply)
            return
        try:
            reply = pickle.dumps(self.__port_find_mac(mac_str))
            code = 200
            self.__sendReply(prot,code,seq,reply)
        except Exception, e:
            code = 400
            #reply = "Error with portFindMac "+str(e)
            log.debug("Error with portFindMac "+str(e))
            reply = pickle.dumps([])
            self.__sendReply(prot,code,seq,reply)
            return
                       
    def portList(self,prot,seq,ln,payload):
        switch_str = pickle.loads(payload)
        if switch_str == None:
            code = 400
            reply = str("Incorrect argument")+" "+str(switch_str)
            self.__sendReply(prot,code,seq,reply)
            return
        try:
            reply = pickle.dumps(self.__port_list(switch_str))
            code = 200
            self.__sendReply(prot,code,seq,reply)
        except Exception, e:
            code = 400
            #reply = "Error with portList "+str(e)
            log.debug("Error with portList "+str(e))
            reply = pickle.dumps([])
            self.__sendReply(prot,code,seq,reply)
            return

    def portListAndVlan(self,prot,seq,ln,payload):
        switch_str = pickle.loads(payload)
        if switch_str == None:
            code = 400
            reply = str("Incorrect argument")+" "+str(switch_str)
            self.__sendReply(prot,code,seq,reply)
            return
        try:
            reply = pickle.dumps(self.__port_list_and_vlan(switch_str))
            code = 200
            self.__sendReply(prot,code,seq,reply)
        except Exception, e:
            code = 400
            #reply = "Error with portList "+str(e)
            log.debug("Error with portListAndVlan "+str(e))
            reply = pickle.dumps([])
            self.__sendReply(prot,code,seq,reply)
            return
                                            
    # getVlanForName  ########################################
    def vlanShowName(self,prot,seq,ln,payload):
        vlan_str = pickle.loads(payload)
        if vlan_str == None:
            code = 400
            reply = str("Incorrect argument")+" "+str(vlan_str)
            self.__sendReply(prot,code,seq,reply)
            return
        try:
            log.debug("Trying to get vlan info for "+str(vlan_str))
            reply = self.__get_vlan_info(vlan_str)
            code = 200
            self.__sendReply(prot,code,seq,reply)
        except Exception, e:
            code = 400
            reply = "Error with vlanShowName "+str(e)
            self.__sendReply(prot,code,seq,reply)
            return

    # getVlanForUser  ########################################
    def vlanShowUser(self,prot,seq,ln,payload):
        user_str = pickle.loads(payload)
        
        reply = ""
        try:
            for vlan in self.__vlan_owner_name[user_str]:
                reply = reply + " " + str(vlan.getName())
            code = 200
            self.__sendReply(prot,code,seq,reply)
        except Exception, e:
            code = 400
            reply = "Error with vlanShowUser "+str(e)
            self.__sendReply(prot,code,seq,reply)
            return

    # vlanNextFreeId ########################################
    def vlanNextFreeId(self,prot,seq,ln,payload):
        
        
        reply = ""
        try:
            reply = str(self.__vlan_get_next_id())
            print "REPLY "+str(reply)
            code = 200
            self.__sendReply(prot,code,seq,reply)
        except Exception, e:
            code = 400
            reply = "Error with vlanNextFreeId "+str(e)
            self.__sendReply(prot,code,seq,reply)
            return

    # show empty vlans  ########################################
    def vlanShowEmpty(self,prot,seq,ln,payload):
        switch_str = pickle.loads(payload)
        
        
        
#        reply = ""
#        try:
#            for vlan in self.__vlan_owner_name[user_str]:
#                reply = reply + " " + str(vlan.getName())
#            code = 200
#            self.__sendReply(prot,code,seq,reply)
#        except Exception, e:
        code = 400
        reply = "Error with vlanShowEmpty not implemented"#+str(e)
        self.__sendReply(prot,code,seq,reply)
        return

    # getPortVlansForName  ########################################
    def vlanShowPort(self,prot,seq,ln,payload):
        args = pickle.loads(payload)
        reply = []
        if len(args) != 2:
            code = 400
            reply.append("Incorrect number of arguments")
            self.__sendReply(prot,code,seq,pickle.dumps(reply))
            return        
        device_str = args[0]
        try:
            device = self.__nodes[device_str]
        except:
            code = 400
            reply.append("Unknown device "+str(device_str))
            self.__sendReply(prot,code,seq,pickle.dumps(reply))
            return        
        
        switch_refresh_limit ={}
        for interface_str in args[1:]:
            #try:
                switch = self.__nodes[device.getSwitchObj(interface_str)].getInstance()
                if switch_refresh_limit.has_key(switch):
                    reply.append(self.__get_port_info(switch,device.getSwitchPortString(interface_str),False))
                else:
                    switch_refresh_limit[switch] = True
                    reply.append(self.__get_port_info(switch,device.getSwitchPortString(interface_str),True))
                code = 200
            #except Exception, e:
            #    code = 400
            #    reply.append("Error with vlanShowPort "+str(e))

        print "REPLY",reply

        self.__sendReply(prot,code,seq,pickle.dumps(reply))
        return

    # vlanAddPort  ########################################
    def vlanAddPort(self,prot,seq,ln,payload):
        args = pickle.loads(payload)
        if len(args) != 5:
            code = 400
            reply = str("Incorrect number of arguments")
            self.__sendReply(prot,code,seq,reply)
            return        
        vlan_str = args[0]
        user_str = args[1]
        tagged_str = args[2]
        device_str = args[3]
        device = None
        interface_str = args[4]
        try:
            device = self.__nodes[device_str]
            switch = (self.__nodes[device.getSwitchObj(interface_str)]).getInstance()            
            reply = self.__vlan_add_port(vlan_str,user_str,tagged_str,switch,device.getSwitchPortString(interface_str))
            code = 200
            log.debug("vlan str "+args[0])
            log.debug("user str "+args[1])
            log.debug("tagged str "+args[2])
            log.debug("device str "+args[3])
            log.debug("interface str "+args[4])
            self.__sendReply(prot,code,seq,pickle.dumps(reply))
        except Exception, e:
            code = 400
            traceback.print_exc()
            reply = "Error with vlanAddPort "+str(e)
            # local debugging
            log.debug(str(reply))
            log.debug("vlan str "+args[0])
            log.debug("user str "+args[1])
            log.debug("tagged str "+args[2])
            log.debug("device str "+args[3])
            log.debug("interface str "+args[4])
            if device != None:
                log.debug("device "+args[3]+" instance "+str(device))
            if device != None:
                log.debug( "switch instance"+str(switch)+" looked up device "+str(device.getSwitchObj(interface_str)))
            self.__sendReply(prot,code,seq,reply)
            return

    # vlanRemovePort  ########################################
    def vlanRemovePort(self,prot,seq,ln,payload):
        args = pickle.loads(payload)
        if len(args) != 5:
            code = 400
            reply = str("Incorrect number of arguments")
            self.__sendReply(prot,code,seq,reply)
            return        
        vlan_str = args[0]
        user_str = args[1]
        tagged_str = args[2]
        device_str = args[3]
        interface_str = args[4]
        try:
            device = self.__nodes[device_str]
            switch = self.__nodes[device.getSwitchObj(interface_str)].getInstance()
            reply = self.__vlan_remove_port(vlan_str,user_str,tagged_str,switch,device.getSwitchPortString(interface_str))
            code = 200
            self.__sendReply(prot,code,seq,reply)
        except Exception, e:
            code = 400
            reply = "Error with vlanRemovePort "+str(e)
            self.__sendReply(prot,code,seq,reply)
            return

    # __moveVlan  #######################################    
    def __moveVlan(self,vlan_str,user_str,device_str,interface_str,vlan_old_str=None):
        log.debug("MOVING VLAN")
        # lookup old settings
        (device, switch_str, switch, switch_obj, port_str) = self.__getDeviceObjects(device_str, interface_str)
        port = self.__get_port(switch_obj,port_str)
        
        log.debug("PORT "+str(port))
        # remove old vlan setting
        if port != None:
            if port.getUntagged() != (None,None):
                if str(port.getUntagged()[1]) != str(1):        
                    reply = self.__vlan_remove_port(port.getUntagged()[0],user_str,"untagged",switch_obj,port_str)
                    print "REMOVING UNTAGGED IN MOVE reply : "+str(reply)
            elif port.getTagged() != []:
                res = res + "; tagged : "
                for t in port.getTagged():
                    if t != (None,None):
                        reply = self.__vlan_remove_port(t[0],user_str,"tagged",switch_obj,port_str)
                        print "REMOVING TAGGED IN MOVE reply : "+str(reply)
        # new vlan setting
        print "TRYING TO ADDED NEW VLAN vs "+str(vlan_str)+" ps "+str(port_str)+" switch obj "+str(switch_obj)
        reply = self.__vlan_add_port(vlan_str,user_str,"untagged",switch_obj,port_str)
        print "REPLY FROM ADDD "+str(reply)
        return reply
    
    # vlanConnectPorts  #######################################
    def vlanConnectPorts(self,prot,seq,ln,payload):
        args = pickle.loads(payload)
        print "ARGS "+str(args)
        if len(args) != 6:
            code = 400
            reply = str("Incorrect number of arguments")
            self.__sendReply(prot,code,seq,reply)
            return
#        connect : [vlan name] [user name] [element] [interface] [element] [interface]
        vlan_str = args[0]
        user_str = args[1]
        device_str_1 = args[2]
        device_str_2 = args[4]
        device_1 = None
        device_2 = None
        switch_1 = None
        switch_2 = None
        interface_str_1 = args[3]
        interface_str_2 = args[5]
        reply_1 = "nothing"
        reply_2 = "nothing"
        try:
            reply_1 = self.__moveVlan(vlan_str,user_str,device_str_1,interface_str_1)
            reply_2 = self.__moveVlan(vlan_str,user_str,device_str_2,interface_str_2)
            code = 200
            log.debug("success in creating connected ports")
            log.debug("vlan str "+args[0])
            log.debug("user str "+args[1])
            log.debug("element 1 "+args[2])
            log.debug("interface str 1 "+args[3])
            log.debug("element 2 "+args[4])
            log.debug("interface str 2 "+args[5])
            log.debug("reply 1"+str(reply_1))
            log.debug("reply 2"+str(reply_2))
            self.__sendReply(prot,code,seq,pickle.dumps(str(reply_1+"\n"+reply_2)))
            return
        except Exception, e:
            code = 400
            traceback.print_exc()
            reply = "Error with vlanConnectPort "+str(e)
            # local debugging
            log.debug(str(reply))
            log.debug("vlan str "+args[0])
            log.debug("user str "+args[1])
            log.debug("element 1 "+args[2])
            log.debug("interface str 1 "+args[3])
            log.debug("element 2 "+args[4])
            log.debug("interface str 2 "+args[5])
            if device_1 != None:
                log.debug("device "+args[2]+" instance "+str(device_1))
            if device_1 != None:
                log.debug( "switch instance"+str(switch_1)+" looked up device "+str(device_1.getSwitchObj(interface_str_1)))
            if device_2 != None:
                log.debug("device "+args[4]+" instance "+str(device_2))
            if device_2 != None:
                log.debug( "switch instance"+str(switch_2)+" looked up device "+str(device_2.getSwitchObj(interface_str_2)))
            self.__sendReply(prot,code,seq,reply)
            return

        
    # vlanPortModeGet  ########################################
    def vlanPortModeGet(self,prot,seq,ln,payload):
        args = pickle.loads(payload)
        if len(args) != 2:
            code = 400
            reply = str("Incorrect number of arguments")
            self.__sendReply(prot,code,seq,reply)
            return
        device_str = args[0]
        interface_str = args[1]
        try:
            device = self.__nodes[device_str]
            switch = self.__nodes[device.getSwitchObj(interface_str)].getInstance()
            reply = str(switch.getPortVlanMode(device.getSwitchPortString(interface_str)))
            code = 200
            self.__sendReply(prot,code,seq,reply)
        except Exception, e:
            code = 400
            reply = "Error with vlanPortModeGet "+str(e)
            self.__sendReply(prot,code,seq,reply)
            return
        
    # vlanPortModeSet  ########################################
    def vlanPortModeSet(self,prot,seq,ln,payload):
        args = pickle.loads(payload)
        if len(args) != 3:
            code = 400
            reply = str("Incorrect number of arguments")
            self.__sendReply(prot,code,seq,reply)
            return
        mode_str = args[0]
        if (not(mode_str == "general" or mode_str == "access" or mode_str == "trunk")):
            code = 400
            reply = str("Incorrect mode : ")+str(mode_str)
            self.__sendReply(prot,code,seq,reply)
            return
                                            
        device_str = args[1]
        interface_str = args[2]
        try:
            device = self.__nodes[device_str]
            switch = self.__nodes[device.getSwitchObj(interface_str)].getInstance()
            reply = str(switch.setPortVlanMode(device.getSwitchPortString(interface_str),mode_str))
            code = 200
            self.__sendReply(prot,code,seq,reply)
        except Exception, e:
            code = 400
            reply = "Error with vlanPortModeSet "+str(e)
            self.__sendReply(prot,code,seq,reply)
            return


    # HELPER METHODS ########################################

    def loadVlanOwnerFile(self):
        f = open(self.__vlanOwnerFilename,'r')
        
        for l in f.readlines():
            v = VlanOwner()
            v.fromFileString(l.rstrip('\n'))
            if not self.__vlan_owner_name.has_key(v.getOwner()):
                self.__vlan_owner_name[v.getOwner()] = []
            self.__vlan_owner_name[v.getOwner()].append(v)
            self.__vlan_name_owner[v.getName()] = v
            f.close()
        

    def saveVlanOwnerFile(self):
        f = open(self.__vlanOwnerFilename,'w')

        for v in self.__vlan_name_owner.values():
            f.write(v.toFileString()+"\n")
        f.close()

    def fetchVlanInfoFromSwitches(self):
        self.__vlan_name_switch_id = {}
        self.__vlan_id_switch_name = {}
        for switch in self.__switches:
            try:
                switch_obj = switch.getInstance()
                switch_obj.refreshVlanInfo()
                ports = switch_obj.getPorts()
                #print "ports "+str(ports)
                for port in ports.values():
                    temp = {}
                    u = port.getUntagged()
                    if u != (None,None):
                        temp[u[0]] = u[1]
                    ts = port.getTagged()
                    if ts != []:
                        for t in ts:
                            if t != (None,None):
                                temp[t[0]] = t[1]
                    p = port.getPvid()
                    if p != (None,None):
                        temp[p[0]] = p[1]
                    for temp_k in temp:
                        self.__allocate_id(temp_k, temp[temp_k], switch)
            except Exception, e:
                print "Switch "+str(switch)+" failed to fetch vlan info"
                print "exception",e 
                
        for i in self.__vlan_name_switch_id:
            print i,
            for j in self.__vlan_name_switch_id[i]:
                print j,
                print self.__vlan_name_switch_id[i][j],
            print 
        
        vlan_id_keys = self.__vlan_id_switch_name.keys()
        vlan_id_keys = sorted(vlan_id_keys)
        for i in vlan_id_keys:
            print i,
            for j in self.__vlan_id_switch_name[i]:
                print j,
                print self.__vlan_id_switch_name[i][j],
            print 
            
    def loadNodes(self):
        n = self.__henManager.getNodes("all", "all")
        for nT in n.keys():
            for node in n[nT].values():
                sn = SimpleDevice(node)
                self.__nodes[node.getNodeID()] = sn
                if nT == "switch" and node.getStatus() == "operational":
                    if self.__henManager.pingInfrastructureNode(node):
                        self.__switches.append(sn)
                    else:
                        log.debug("node "+node.getNodeID()+" is not pingable.")
    
    def createSwitchInstances(self):
        # pre load all switch instances
        for s in self.__switches:
            s.getInstance()

    def __port_find_mac(self, macs_str):
        res = []
        log.debug("Searching for macs "+str(macs_str))
        for switch in self.__switches:
            print "Trying",switch,
            try:
                switch_obj = switch.getInstance()
                switch_obj.refreshPortInfo()
                switch_obj.resetPortsMacInfo()
                switch_obj.addMacsToPorts()
                ports = switch_obj.getPorts() 
                #print "",len(ports),
                for port in ports.values():
                    #print "",len(port.getMacs())
                    for mac in port.getMacs():
                        
                        for mac_str in macs_str:
                            if mac_str.upper() == mac.upper():
                                print "FOUND ",mac_str,port
                                res.append((mac,port))
#                            else:
#                                print "NOT FOUND",mac_str.upper(),mac.upper(),str(switch)
            except Exception, e:
                if (switch_obj == None):
                    log.debug("Switch "+str(switch)+" is offline.")
                else:
                    log.debug("Error in __port_find_mac "+str(e)+" switch "+str(switch))
                pass
        return res
    
    def __port_tdr(self,switch_obj,switch_port_str):
        
        try:
            output = switch_obj.getPortTdr(switch_port_str)
            res = pickle.dumps(output)
            
            #print "tdr result "+res
        except Exception, e:
            print e
        if res == None :
            return "Unknown Port"
        return str(res)

    def __port_list(self,switch_str):
        return_str = ""
        for switch in self.__switches:
            if switch.getHenObjId() == switch_str:
                try:
                    #log.debug("trying to get instance of "+str(switch))
                    switch_obj = switch.getInstance()
                    ports = switch_obj.getPorts()
                    port_keys = ports.keys()
                    port_keys = sorted(port_keys)
                    for port in port_keys:
                        return_str += str(ports[port].getName()) +" "#("+str(ports[port].getId())+")\n"
                    return return_str
                except:
                    log.debug("Failed to get switch object instance")
                    return_str = "error collecting port information."
        return "error getting port information."
                
    def __port_list_and_vlan(self,switch_str):
        return_str = ""
        for switch in self.__switches:
            if switch.getHenObjId() == switch_str:
                try:
                    #log.debug("trying to get instance of "+str(switch))
                    switch_obj = switch.getInstance()
                    #log.debug("refreshingVlanInfo for "+str(switch))
                    switch_obj.refreshVlanInfo()
                    ports = switch_obj.getPorts()
                    port_keys = ports.keys()
                    port_keys = sorted(port_keys)
                    for port in port_keys:
                        return_str += str(ports[port].getName()) +" "#("+str(ports[port].getId())+") "
                        if ports[port].getUntagged() != (None,None):
                            return_str = return_str + "untagged : "+str(ports[port].getUntagged()[0])
                        if ports[port].getTagged() != []:
                            return_str = return_str + "; tagged : "
                            for t in ports[port].getTagged():
                                if t != (None,None):
                                    return_str = return_str + " "+str(t[0])
                                    if t[1] != None:
                                        return_str = return_str + " (" + str(t[1]) + ")"
                            if ports[port].getPvid() != (None,None):
                                return_str = return_str + "; pvid : "+str(ports[port].getPvid()[0])
                        
                        return_str += "\n" 
                    return return_str
                except Exception, e:
                    raise e
                    log.debug("Failed to get switch object instance")
                    return_str = "error collecting port information."
        return "error getting port information."        
                  
    #def __port_tdr(self,switch_obj,switch_port_str):
    #    switch_obj.refreshVlanInfo()
    #    res = switch_obj.getPortByName(switch_port_str)
    #    if res == None :
    #        return "Unknown Port"
    #    return str(res)

    def __get_vlan_info(self,vlan_str):
        res = ""
        for switch in self.__switches:
            try:
                #log.debug("trying to get instance of "+str(switch))
                switch_obj = switch.getInstance()
                #log.debug("refreshingVlanInfo for "+str(switch))
                switch_obj.refreshVlanInfo()
                ports = switch_obj.getPorts()
                output = switch_obj.getVlanByName(vlan_str)
                if output != None:
                    res += str(output.toString(ports))
            except Exception,e:
                log.debug(e)
                pass
        if res == "" :
            return "Unknown vlan"
        return str(res)

    def __get_port(self,switch_obj,port_str,vlan_refresh=True):
            # this is an expensive operation so allow for the suppression of it.
            if vlan_refresh:
                print switch_obj
                switch_obj.refreshVlanInfo()
            ports = switch_obj.getPorts()
            for port in ports.values():
                if str(port.getName()) == str(port_str):
#                    print "FOUND PORT "+str(port_str)
                    return port
#                else:
#                    print "NOT FOUND PORT "+str(port_str)+" is not "+str(port.getName())
            return None


    def __get_port_info(self,switch_obj,port_str,vlan_refresh=True):
        res = ""
        try:
            output = self.__get_port(switch_obj,port_str,vlan_refresh)
            if output != None:
                print "FOUND SOMETING "+str(output)
                if output.getUntagged() != (None,None):
                    res = res + "untagged : "+str(output.getUntagged()[0])
                if output.getTagged() != []:
                    res = res + "; tagged : "
                    for t in output.getTagged():
                        if t != (None,None):
                            res = res + " "+str(t[0])
                            if t[1] != None:
                                res = res + " (" + str(t[1]) + ")"
                if output.getPvid() != (None,None):
                    res = res + "; pvid : "+str(output.getPvid()[0])
        except Exception, e:
            print e
            pass
        if res == "" :
            print "DAMNNNN"+str(port_str)
            return "Unknown port"
        return str(res)

    def __allocate_id(self,vlan_str,vlan_id,switch_str):
        print "ALLOCATING ID ",vlan_str,vlan_id,switch_str
        if not self.__vlan_name_switch_id.has_key(vlan_str):
            self.__vlan_name_switch_id[vlan_str] = {}
        if not self.__vlan_name_switch_id[vlan_str].has_key(switch_str):
            self.__vlan_name_switch_id[vlan_str][switch_str] = {}
        self.__vlan_name_switch_id[vlan_str][switch_str] = vlan_id
                    
        if not self.__vlan_id_switch_name.has_key(vlan_id):
            self.__vlan_id_switch_name[vlan_id] = {}
        if not self.__vlan_id_switch_name[vlan_id].has_key(switch_str):
            self.__vlan_id_switch_name[vlan_id][switch_str] = {}
        self.__vlan_id_switch_name[vlan_id][switch_str] = vlan_str  

    def __vlan_get_next_id(self):
        for i in range(100,4095):
            if not self.__vlan_id_switch_name.has_key(str(i)):                
                return i
        return -1

    def __vlan_create(self,vlan_str,user_str,switch_obj):
        log.debug("creating vlan "+vlan_str+" for user "+user_str)
        # find free vlan_id

        switch_str = str(switch_obj.getNodeID())
        vlan_id = self.__vlan_get_next_id()
        if vlan_id == -1:
            raise Exception("Out of vlan ids")
        ret = switch_obj._creatVLAN(vlan_id,vlan_str)
        #if ret:
        self.__allocate_id(str(vlan_str), str(vlan_id), switch_str)
        print "RETURN VALUE FROM VLAN CREATE "+str(ret)
        return ret
    
    def __vlan_add_port(self,vlan_str,user_str,tagged_str,switch_obj,switch_port_str):
        print "vlan_str",vlan_str
        print "user_str",user_str
        print "tagged_str",tagged_str
        print "switch_obj",str(switch_obj)
        print "switch_port_str",switch_port_str

        #check to see if vlan exists
        #switch_obj.refreshVlanInfo() 
        if (switch_obj.getVlanByName(vlan_str) == None):
            reply = self.__vlan_create(vlan_str,user_str,switch_obj)

            if reply != 0:
                print "0",reply
                return "failure, creating vlan "+str(vlan_str)+" for user "+str(user_str)
        
        if tagged_str == "tagged":
            print "1"
            reply = switch_obj.addTaggedPort(switch_port_str,vlan_str)
        elif tagged_str == "untagged":
            print "2"
            reply = switch_obj.addUntaggedPort(switch_port_str,vlan_str)
            print "2 : "+str(reply)
        else:
            print "3"
            return "failure, incorrect tag type "+str(tagged_str)
        if reply == 0:
            reply = "success"
        else:
            reply = "failure"
        return str(reply)

    def __vlan_remove_port(self,vlan_str,user_str,tagged_str,switch_obj,switch_port_str):
        #print "vlan_str",vlan_str
        #print "user_str",user_str
        print "tagged_str",tagged_str
        #print "switch_obj",str(switch_obj)
        #print "switch_port_str",switch_port_str
        if tagged_str == "tagged":
            reply = switch_obj.removeTaggedPort(switch_port_str,vlan_str)
        elif tagged_str == "untagged":
            reply = switch_obj.removeUntaggedPort(switch_port_str,vlan_str)
        else:
            return "failure, incorrect tag type ",tagged_str
        if reply == 0:
            reply = "success"
        else:
            reply = "failure"
        return str(reply)

###########################################################################
    def vlanCreateVlan(self,prot,seq,ln,payload):
        args = pickle.loads(payload)
        if len(args) != 2:
            code = 400
            reply = str("Incorrect number of arguments")
            self.__sendReply(prot,code,seq,reply)
            return
        vlan_str = args[0]
        user_str = args[1]
        try:            
            code = 200
            v = VlanOwner(vlan_str,user_str)

            if not self.__vlan_owner_name.has_key(v.getOwner()):
                self.__vlan_owner_name[v.getOwner()] = []
            self.__vlan_owner_name[v.getOwner()].append(v)
            self.__vlan_name_owner[v.getName()] = v
            self.saveVlanOwnerFile()
            reply = str("Trying to create ")+str(v)
            self.__sendReply(prot,code,seq,reply)
            return
                                            
        except Exception, e:
            code = 400
            reply = "Error with createVlanForUser "+str(e)
            self.__sendReply(prot,code,seq,reply)
            return
                                
    # OLDER STUFF  ########################################

    # Add Port to Vlan by Name ################################################
    def addPortToVlanByName(self,prot,seq,ln,payload):
        args = pickle.loads(payload)
        if len(args) != 3:
            code = 400
            reply = str("Incorrect number of arguments")
            self.__sendReply(prot,code,seq,reply)
            return        
        computer_str = args[0]
        interface_str = args[1]
        vlan_str = args[2]
        try:
            (code,reply) = self.__addPortToVlan(computer_str,interface_str,vlan_str,None)
        except Exception, e:
            code = 400
            reply = "Error with addPortToVlanByName "+str(e)
            traceback.print_exc(file=sys.stdout)
            self.__sendReply(prot,code,seq,reply)
            return
        self.__sendReply(prot,code,seq,reply)
        
    def __addPortToVlan(self, computer_str, interface_str, vlan_str, vlan_id):
        (computer, switch_str, switch, switch_obj, port_str) = self.__getDeviceObjects(computer_str, interface_str)
        (vlan_name,old_vlan_id,port_obj) = self.__findVlanOfPort(switch_obj,switch_str,port_str)
        
        if (old_vlan_id != 1):
            log.info("need to delete this port")
            (code, reply) = self.__deletePortFromVlan(computer_str, interface_str, vlan_name)

        if (self.__vlans[switch_str] == None):
            try:
                self.__vlans[switch_str] = switch_obj.getFullVLANInfo()
            except Exception, e:
                raise SNMPException("Snmp exception getFullVLANInfo from switch"+str(switch_str)) 
            
        if (vlan_str != None):
            # adding by vlan string
            if not self.__switchHasVlanByName(vlan_str,switch_str):
                self.__createNewVlanByName(vlan_str,switch_obj,switch_str)
        else:
            log.info("Adding vlan based on vlan id "+str(vlan_id)+" on switch "+str(switch_str))
            if not self.__switchHasVlanById(vlan_id,switch_str):
                self.__createNewVlanById(vlan_id,switch_obj,switch_str)
                vlan_str = self.__getVlanNameFromId(switch_str,vlan_id)
        try:
            result = switch_obj.addPorts(vlan_str,[Port(port_str,False,port_str)])
        except Exception, e:
            raise SNMPException("Snmp exception addPorts from switch"+str(switch_str)) 
        
        if result == 0:
            # write to log file ?
            log.info("Added port "+str(port_str)+" to vlan "+str(vlan_str))
            code = 200       
            reply = "success"
        else:
            log.critical("Failed to add port "+str(port_str)+" to vlan "+str(vlan_str))
            code = 400
            reply = "failure"    
        return (code,reply)

    # Delete Port From Vlan ################################################
    def deletePortFromVlan(self,prot,seq,ln,payload):
        args = pickle.loads(payload)
        if len(args) != 3:
            code = 400
            reply = str("Incorrect number of arguments")
            self.__sendReply(prot,code,seq,reply)
            return        
        computer_str = args[0]
        interface_str = args[1]
        vlan_str = args[2]
        try:
            (code,reply) = self.__deletePortFromVlan(computer_str, interface_str, vlan_str)
            self.__sendReply(prot,code,seq,reply)
            return
        except Exception, e:
            code = 400
            reply = "Error with deletePortFromVlan "+str(e)
            self.__sendReply(prot,code,seq,reply)
            return

    def __deletePortFromVlan(self, computer_str, interface_str, vlan_str):
        (computer, switch_str, switch, switch_obj, port_str) = self.__getDeviceObjects(computer_str, interface_str)
        #log.debug("Trying to delete port from vlan "+str(switch_str)+" "+ str( port_str))
        try:
            vlans = switch_obj.getFullVLANInfo()
        except Exception, e:
            raise SNMPException("Snmp exception getFullVlanInfo from switch"+str(switch_str))
        
        vlan = None
        vlan_found = False
        for v in vlans:
            if v.getName() == vlan_str:
                vlan = v
                vlan_found = True
                break
            
        if not vlan_found:
            raise VlanDoesNotExist("Vlan "+str(vlan_str)+" does not exist.")
        
        ports = vlan.getPortsOnSwitch(switch_str)
        port_found = False
        for p in ports:
            if str(p.getPortNumber()) == port_str:
                port_found = True
                break
            
        if port_found:
            try:
                result = switch_obj.deletePorts(vlan.getName(),[Port(port_str,False,port_str)])
            except Exception, e:
                raise SNMPException("Snmp exception deletePorts from switch"+str(switch_str)) 
        else:
            raise PortNotInVlan("Port "+str(port_str)+" not in vlan "+str(vlan_str))
        
        if result == 0:
            # write to log file ?
            log.info("Deleted port "+str(port_str)+" from vlan "+str(vlan_str))
            code = 200       
            reply = "success"
        else:
            log.critical("Failed to delete port "+str(port_str)+" from vlan "+str(vlan_str))
            code = 400
            reply = "failure"    
        return (code,reply)
    
    # List Ports on Vlan on Switch ########################################

    def listPortsOnVlanOnSwitch(self,prot,seq,ln,payload):
        args = pickle.loads(payload)
        if len(args) != 2:
            code = 400
            reply = str("Incorrect number of arguments")
            self.__sendReply(prot,code,seq,reply)
            return        
        switch_str = args[0]
        vlan_str = args[1]
        try:
            switch_obj = self.__getSwitchInstance(switch_str)
            vlan_obj = switch_obj.getFullVLANInfo(vlan_str)
        except Exception, e:
            code = 400
            reply = "Error with listPortsOnVlanOnSwitch "+str(e)
            self.__sendReply(prot,code,seq,reply)
            return
        
        reply = ""
        for i in vlan_obj:
            reply += str(i)
        code = 200
        self.__sendReply(prot,code,seq,reply)
        retur                                               
    # List Vlans on Switch ########################################

    def listVlansOnSwitch(self,prot,seq,ln,payload):
        args = pickle.loads(payload)
        if len(args) != 1:
            code = 400
            reply = str("Incorrect number of arguments")
            self.__sendReply(prot,code,seq,reply)
            return
        switch_str = args[0]
        try:
            switch_obj = self.__getSwitchInstance(switch_str)
        except Exception, e:
            code = 400
            reply = "Error with listVlansOnSwitch "+str(e)
            self.__sendReply(prot,code,seq,reply)
            return
        try:
            vlan_obj = switch_obj.getFullVLANInfo()
        except Exception, e:
            code = 400
            reply = "Error with listVlansOnSwitch "+str(e)
            self.__sendReply(prot,code,seq,reply)
            return
        
        reply = ""
        for i in vlan_obj:
            vlan_name = self.__rewriteVlan(i.getName())
            reply += str(vlan_name)+" "+str(i.getID())+"\n"
        code = 200
        self.__sendReply(prot,code,seq,reply)
                                                                    
    # get Vlan Id For Port ########################################
    def getVlanIdForPort(self,prot,seq,ln,payload):
        args = pickle.loads(payload)
        if len(args) != 2:
            code = 400
            reply = str("Incorrect number of arguments")
            self.__sendReply(prot,code,seq,reply)
            return
                            
        computer_str = args[0]
        interface_str = args[1]
        try:
            
            (computer, switch_str, switch, switch_obj, port_str) = self.__getDeviceObjects(computer_str, interface_str)
            #(vlan_name,vlan_id,port_obj) = self.__findVlanOfPort_new(switch_obj,switch_str,port_str)
            reply = self.__get_port_info(switch_obj,switch_str,port_str)
                       
            code = 200
            self.__sendReply(prot,code,seq,reply)
        except Exception, e:
            code = 400
            reply = "Error with getVlanIdForPort "+str(e)
            self.__sendReply(prot,code,seq,reply)
            return

    # get Vlan Id For Switch Port ########################################
    def getSwitchPortVlansForName(self,prot,seq,ln,payload):
        args = pickle.loads(payload)
        if len(args) != 2:
            code = 400
            reply = str("Incorrect number of arguments")
            self.__sendReply(prot,code,seq,reply)
            return
                            
        switch_str = args[0]
        port_str = args[1]
        try:
            
            
            (switch,switch_obj) = self.__getSwitchInstance(switch_str)
            
            reply = self.__get_port_info(switch_obj,switch_str,port_str)
                       
            code = 200
            self.__sendReply(prot,code,seq,reply)
        except Exception, e:
            code = 400
            reply = "Error with getVlanIdForSwitchPort "+str(e)
            self.__sendReply(prot,code,seq,reply)
            return
        
    # get Vlan Name For Port ########################################        
    def getVlanNameForPort(self,prot,seq,ln,payload):
        args = pickle.loads(payload)
        if len(args) != 2:
            code = 400
            reply = str("Incorrect number of arguments")
            self.__sendReply(prot,code,seq,reply)
            return
                            
        computer_str = args[0]
        interface_str = args[1]
        try:
            if self.__int_vlan_map.has_key((computer_str, interface_str)):
                vlan_name = self.__int_vlan_map((computer_str, interface_str))
            else:
                (computer, switch_str, switch, switch_obj, port_str) = self.__getDeviceObjects(computer_str, interface_str)
                (vlan_name,vlan_id,port_obj) = self.__findVlanOfPort(switch_obj,switch_str,port_str)
            code = 200
            reply = str(vlan_name)
            self.__sendReply(prot,code,seq,reply)
        except Exception, e:
            code = 400
            reply = "Error with getVlanNameForPort "+str(e)
            self.__sendReply(prot,code,seq,reply)
            return
        
    # create New Vlan By Name ########################################        
    def createVlanByName(self,prot,seq,ln,payload):
         args = pickle.loads(payload)
         if len(args) != 2:
             code = 400
             reply = str("Incorrect number of arguments")
             self.__sendReply(prot,code,seq,reply)
             return
         vlan_str = args[0]
         switch_str = args[1]
         try:
              (switch,switch_obj) = self.__getSwitchInstance(switch_str)
              if not self.__switchHasVlanByName(vlan_str,switch_str):
                  result = self.__createNewVlanByName(vlan_str,switch_obj,switch_str)
                  if result == 0:
                      reply = "vlan "+str(vlan_str)+" created on switch "+str(switch_str)
                      code = 200
                  else:
                      reply = "failed to create vlan "+str(vlan_str)+" on switch "+str(switch_str)
                      code = 400
              else:
                  reply = "vlan "+str(vlan_str)+" already exists on switch "+str(switch_str)
                  code = 400
         except Exception, e:
             code = 400
             reply = "Error with createNewVlanByName "+str(e)
             self.__sendReply(prot,code,seq,reply)
             return
         self.__sendReply(prot,code,seq,reply)
         return                                                                    

    def __createNewVlanByName(self,vlan_str,switch_obj,switch_str):
        log.info("Creating new vlan "+str(vlan_str)+" on "+str(switch_str))
        switches = {}
        switches[switch_str] = []
        v = VLAN(vlan_str,switches,self.__getNextFreeVlanId(switch_str))
        result = switch_obj.createVLAN(v)
        self.__reload_vlan_info(switch_str,switch_obj)
        log.info("result from create vlan "+str(result))
        return result

    # delete New Vlan By Name ########################################        

    def deleteVlanByName(self,prot,seq,ln,payload):
         args = pickle.loads(payload)
         if len(args) != 2:
             code = 400
             reply = str("Incorrect number of arguments")
             self.__sendReply(prot,code,seq,reply)
             return
         vlan_str = args[0]
         switch_str = args[1]
         try:
              (switch,switch_obj) = self.__getSwitchInstance(switch_str)
              if self.__switchHasVlanByName(vlan_str,switch_str):
                  result = self.__deleteVlan(vlan_str,switch_obj,switch_str)
                  if result == 0:
                      reply = "vlan "+str(vlan_str)+" deleted from switch "+str(switch_str)
                      code = 200
                  else:
                      reply = "failed to delete vlan "+str(vlan_str)+" on switch "+str(switch_str)
                      code = 400
              else:
                  reply = "vlan "+str(vlan_str)+" does not exists on switch "+str(switch_str)
                  code = 400
         except Exception, e:
             code = 400
             reply = "Error with deleteVlanByName "+str(e)
             traceback.print_exc(file=sys.stdout)
             self.__sendReply(prot,code,seq,reply)
             return
         self.__sendReply(prot,code,seq,reply)
         return                                                                    

    def __deleteVlan(self,vlan_str,switch_obj,switch_str):
        log.info("Deleting vlan "+str(vlan_str)+" on "+str(switch_str))
        self.__reload_vlan_info(switch_str,switch_obj)
        result = switch_obj.deleteVLAN(vlan_str)
        self.__reload_vlan_info(switch_str,switch_obj)
        log.info("result from vlan "+str(result))


    
    # Old stuff
  
    def __initaliseVlanInfo(self):
        if self.__nodes == None:
            self.__getNodes()
        for node_type in self.__nodes:
            if node_type == "switch":
                for node in self.__nodes[node_type]:
                    # Gets switch objects and basic info
                    if str(self.__nodes[node_type][node].getNodeID()) == "switch14":
                        log.debug("Getting switch instance for "+str(self.__nodes[node_type][node].getNodeID()))
                        (switch,switch_obj) = self.__getSwitchInstance(self.__nodes[node_type][node].getNodeID())
                        self.__reload_vlan_info(switch.getNodeID(),switch_obj)
                    
    def __sendReply(self,prot,code,seq,payload):
        if (code == 0):
            code = 200
        else:
            code = 422 # returnCodes[422] = "error executing command"
        prot.sendReply(code, seq, payload)

    def __getNodes(self):
        self.__nodes = self.__henManager.getNodes("all")

    def __getComputer(self, computer_str):
        if self.__nodes == None:
            self.__getNodes()
            
        for node_id in self.__nodes:
            if node_id == computer_str:
                return self.__nodes[node_id]
        raise NodeDoesNotExist("Node "+str(computer_str)+" does not exist.")

    def __getSwitchLocation(self, computer, interface_str):
        interf = computer.getInterfaceObj(interface_str)
        if interf != None:
            return (interf.getSwitch(),interf.getPort())
        return (None,None)
    
    def __rewriteVlan(self,vlan):
        if vlan == "Default VLAN" or vlan == "DEFAULT_VLAN" or vlan == "Vlan 1" or vlan == "default":
            return "Default"
        return vlan
    
    def __reload_vlan_info(self, switch_str, switch_obj):
        self.__vlan_info[switch_str] = switch_obj.getVlanInfo()
        if self.__vlan_info[switch_str] == None:
            print "ERRROR no vlan content for switch",switch_str
        for i in self.__vlan_info[switch_str]:
            print i,self.__vlan_info[switch_str][i]

    def enableTestMode(self,prot,seq,ln,payload):
        self.__test_mode = True
        self.__minimum_id = 20
        self.__maximum_id = 30
        code = 200
        self.__sendReply(prot,code,seq,"")

    def disableTestMode(self,prot,seq,ln,payload):
        self.__test_mode = False
        self.__minimum_id = 200
        self.__maximum_id = 500
        code = 200
        self.__sendReply(prot,code,seq,"")
    
    def clearVlans(self,prot,seq,ln,payload):
        (switch_str) = pickle.loads(payload)
        (switch,switch_obj) = self.__getSwitchInstance(switch_str)
        
        
        for i in self.__vlan_info[switch_str]:
            if self.__vlan_info[switch_str][i][0] < self.__minimum_id:
                pass
            elif self.__vlan_info[switch_str][i][0] > self.__maximum_id:
                pass
            else:
                log.info("Deleting vlan "+str(i)+" on "+str(switch_str))
                self.__deleteVlan(i,switch_obj,switch_str)
        code = 200
        self.__sendReply(prot,code,seq,"")

    def __findVlanOfPort(self,switch_obj,switch_str,port_str):
        vlans = switch_obj.getFullVLANInfo()
        for vlan in vlans:
            ports = vlan.getPortsOnSwitch(switch_str)
            for port in ports:
                if str(port.getPortNumber()) == port_str:
                    return (vlan.getName(),vlan.getID(),port)
        return (None,None)


    def addPortToVlanById(self,prot,seq,ln,payload):
        (computer_str, interface_str, vlan_id) = pickle.loads(payload)
        log.info("trying to use vlan id "+str(vlan_id))
        (code,reply) = self.__addPortToVlan(computer_str,interface_str,None,int(vlan_id))
        self.__sendReply(prot,code,seq,reply)
    
    def __switchHasVlanByName(self,vlan_str,switch_str):
        log.info("checking if "+str(switch_str)+" has vlan "+str(vlan_str))
        if self.__vlan_info[switch_str] == None:
            (switch, switch_obj) =  self.__getSwitchInstance(switch_str)
            self.__reload_vlan_info(switch.getNodeID(),switch_obj)
        
        for vlan in self.__vlan_info[switch_str]:
            if vlan == vlan_str:
                log.info(str(switch_str)+" does have vlan "+str(vlan_str))
                return True
        log.info(str(switch_str)+" does not have vlan "+str(vlan_str))
        return False

    def __getVlanNameFromId(self,switch_str,vlan_id):
         log.info("getting vlan name from id "+str(vlan_id)+" on switch "+str(switch_str))
         for vlan in self.__vlans[switch_str]:
             if vlan.getID() == vlan_id:
                 log.info(str(switch_str)+" does have vlan id "+str(vlan_id)+" name is "+str(vlan.getName()))
                 return vlan.getName()
         log.info(str(switch_str)+" does not have name for vlan id "+str(vlan_id))
         raise VlanDoesNotExist("no vlan for id "+str(vlan_id)+" on switch "+str(switch_str))
                                                         

    def __switchHasVlanById(self,vlan_id,switch_str):
        log.info("checking if "+str(switch_str)+" has vlan id "+str(vlan_id))
        for vlan in self.__vlans[switch_str]:
            if vlan.getID() == vlan_id:
                log.info(str(switch_str)+" does have vlan id "+str(vlan_id))
                return True
        log.info(str(switch_str)+" does not have vlan id "+str(vlan_id))
        return False    

    def testGetNextFreeVlanId(self,prot,seq,ln,payload):
        (switch_str) = pickle.loads(payload)
        code = 200
        reply = self.__getNextFreeVlanId(switch_str)
        self.__sendReply(prot,code,seq,str(reply))

    def __getNextFreeVlanId(self,switch_str=None):
        log.info("Getting next free vlan id")
        vlan_id_list = []
        #self.__minimum_id = 20
        #self.__maximum_id = 30
        last = self.__minimum_id
        if switch_str != None:
            for i in self.__vlan_info[switch_str]:
                if self.__vlan_info[switch_str][i][0] < self.__minimum_id:
                    pass
                elif self.__vlan_info[switch_str][i][0] > self.__maximum_id:
                    pass
                else:
                    vlan_id_list.append(self.__vlan_info[switch_str][i][0])
        else:
            for switch_str in self.__vlan_info:
                for i in self.__vlan_info[switch_str]:
                    if self.__vlan_info[switch_str][i][0] < self.__minimum_id:
                        pass
                    elif self.__vlan_info[switch_str][i][0] > self.__maximum_id:
                        pass
                    else:
                        vlan_id_list.append(self.__vlan_info[switch_str][i][0])
                        
        vlan_id_list.sort()
        
        for i in vlan_id_list:
#            print i
            if last+1 < i:
                log.info("Next free vlan id is "+str(last+1))
                return last+1
            last = i
        log.info("Next free vlan id is "+str(self.__minimum_id)+" min id")
        return self.__minimum_id
        

    def __createNewVlanById(self,vlan_id,switch_obj,switch_str):
        log.info("Creating new id "+str(vlan_id)+" on "+str(switch_str))
        switches = {}
        switches[switch_str] = []
        v = VLAN(None,switches,vlan_id)
        result = switch_obj.createVLAN(v)
        self.__reload_vlan_info(switch_str,switch_obj)
        log.info("result from create vlan id "+str(vlan_id)+" on switch "+str(switch_str)+" is "+str(result))

    def __getVlanId(self,vlan_str,switch_str):
        return self.__vlan_info[switch_str][vlan_str][0]

    def listEmptyVlansOnSwitch(self,prot,seq,ln,payload):
        (switch_str) = pickle.loads(payload)
        (switch,switch_obj) = self.__getSwitchInstance(switch_str)
        if switch == None:
            code = 400
            reply = "No such switch "+switch_str
            self.__sendReply(prot,code,seq,reply)
            return
        vlan_obj = (switch_obj.getFullVLANInfo())
        reply = ""
        for i in vlan_obj:
            if len(i.getPortsOnSwitch(switch_str)) == 0:
                vlan_name = self.__rewriteVlan(i.getName())
                reply += str(vlan_name)+" "+str(i.getID())+"\n"
        code = 200
        self.__sendReply(prot,code,seq,reply)

    def clearEmptyVlansOnSwitch(self,prot,seq,ln,payload):
        (switch_str) = pickle.loads(payload)
        (switch,switch_obj) = self.__getSwitchInstance(switch_str)
        if switch == None:
            code = 400
            reply = "No such switch "+switch_str
            self.__sendReply(prot,code,seq,reply)
            return
        vlan_obj = (switch_obj.getFullVLANInfo())
        reply = "Deleted the following empty vlans\n"
        for i in vlan_obj:
            if len(i.getPortsOnSwitch(switch_str)) == 0:
                vlan_name = self.__rewriteVlan(i.getName())
                reply += str(vlan_name)+" "+str(i.getID())+"\n"
                log.info("Deleting vlan "+str(i.getID())+" on "+str(switch_str))
                self.__deleteVlan(str(i.getName()),switch_obj,switch_str)
                                                
        code = 200
        self.__sendReply(prot,code,seq,reply)


    def initiateNodes(self):
        """\brief Creates a {nodeid:(node,nodeinstance)} dictionary for sensor
        readings, and a {nodeid:node} dictionary for host ping checking.
        """
        log.debug("Creating NodeInstance map")
        self.__nodeInstances = {}
        
        nodes = self.__henManager.getNodes("all", "all")
        
        for nodeType in nodes.keys():
            if nodeType != "switch" :
                continue
            nodeTypes = nodes[nodeType]
            for node in nodeTypes.values():
                if node.getStatus() == "dead" or node.getStatus() == "maintanence" :
                    continue
#                elif node.getNodeID() != "switch14" :
#                    continue
        
                
                try:
                    self.__nodeInstances[node.getNodeID()] = \
                                                           (node, node.getInstance())
                    log.debug("Created instance for node [%s]" % \
                              str(node.getNodeID()))
                except Exception, e:
                    log.debug("Creating node instance failed for node [%s]: %s" % (str(node.getNodeID()), str(e)))
        log.debug("initiateNodes() completed. NodeInstances[%s]" % (str(len(self.__nodeInstances.keys()))))
        counter = 0
        for nodeid in self.__nodeInstances.keys():
            log.debug("[%s] %s" % (str(counter), nodeid))
            counter += 1

    
    ## Internal methods
        
    def acceptingConnections(self):
        """\brief To question whether the daemon is accepting connections"""
        return self.__accept_connections
    
    def setDBDirectory(self, dbDir):
        self.__switchdb.setDBDirectory(dbDir)
        
    ## Library functions

    # Given a switch name, return a switch object
    def __getSwitchInstance(self,switch_str):
        if self.__switch_instances.has_key(switch_str):
            return self.__switch_instances[switch_str]
        if self.__nodes == None:
            self.__getNodes()
        for node_id in self.__nodes:
            if node_id == switch_str:
                switch = self.__nodes[node_id]
#                if (switch.getStatus() == "operational" ): #and switch_str =="switch14"):
                switch_obj = switch.getInstance()
#                else:
#                    log.debug("Not creating an instance of "+str(switch_str))
#                   return (None,None)
                self.__switch_instances[switch_str] = (switch,switch_obj)
                return (switch, switch_obj)
        return (None,None)

    def __getDeviceObjects(self,computer_str, interface_str):
        computer = self.__getComputer(computer_str)
                
        if computer == None:
            log.info("Computer "+str(computer_str)+" doesn't exist.")
            return (None, None, None, None, None)

        (switch_str, port_str) = self.__getSwitchLocation(computer,interface_str)
        if switch_str == "":
            log.info("Switch not found for computer "+str(computer_str)+" interface "+str(interface_str))
            return (None, None, None, None, None)
        
        (switch, switch_obj) = self.__getSwitchInstance(switch_str)
        
        if switch_obj == None:
            log.info("Can't create switch instance for "+str(switch_str))
            return (None, None, None, None, None)

        return (computer, switch_str, switch, switch_obj, port_str)


    def stopDaemon(self,prot,seq,ln,payload):
        """\brief Stops the daemon and all threads
        This method will first stop any more incoming queries, then wait for
        any update tasks to complete, before stopping itself.
        """
        log.info("stopDaemon called.")
        prot.sendReply(200, seq, "Accepted stop request.")
        log.debug("Sending stopDaemon() response")
        self.acceptConnections(False)
        log.debug("Attempting to acquire update lock")
        self.__update_lock.acquire()
        log.debug("Stopping update timer")
        self.__update_timer.stop()
        log.debug("Releasing update lock")
        self.__update_lock.release()
        log.info("Stopping SwitchDaemon (self)")
        self.stop()

class SwitchDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    __bind_addr = DaemonLocations.switchDaemon2[0]  
    __port = DaemonLocations.switchDaemon2[1]
    
    __sockd = None
    __switchcontrol = None

    def __init__(self, doFork):
        Daemonizer.__init__(self, doFork)

    def run(self):
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + str(self.__bind_addr) + ":" + str(self.__port))
        self.__sockd.listen(10)
        self.__sockd.settimeout(2) # 2 second timeouts
        log.debug("Creating SwitchDaemon")
        self.__switchcontrol = SwitchControl()
        log.info("Starting SwitchDaemon")
        self.__switchcontrol.start()
        while self.__switchcontrol.isAlive():
            if self.__switchcontrol.acceptingConnections():
                # allow timeout of accept() to avoid blocking a shutdown
                try:
                    (s,a) = self.__sockd.accept()
                    log.debug("New connection established from " + str(a))
                    self.__switchcontrol.addSocket(s)
                except KeyboardInterrupt:
                    self.__switchcontrol.stop()
                except:
                    pass
                
            else:
                log.warning(\
                      "SwitchDaemon still alive, but not accepting connections")
                time.sleep(2)
        log.debug("Closing socket.")
        self.__sockd.shutdown(socket.SHUT_RDWR)
        self.__sockd.close()
        log.info("SwitchDaemon Finished.")
        # Now everything is dead, we can exit.
        sys.exit(0)


def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    WORKDIR = '/var/hen/switchdaemon'
    PIDDIR = '/var/run/hen'
    LOGDIR = '/var/log/hen/switchdaemon'
    LOGFILE = 'switchdaemon2.log'
    PIDFILE = 'switchdaemon2.pid'
    DBDIR = '%s/switchdb' % WORKDIR    
    GID = 18122 # adam
    UID = 18122 # adam
    switchd = SwitchDaemon(False)
    switchd.setWorkingDir(WORKDIR)
    switchd.setPIDDir(PIDDIR)
    switchd.setLogDir(LOGDIR)
    switchd.setLogFile(LOGFILE)
    switchd.setPidFile(PIDFILE)
    switchd.setUid(UID)
    switchd.setGid(GID)
    switchd.start()

if __name__ == "__main__":
    main()
