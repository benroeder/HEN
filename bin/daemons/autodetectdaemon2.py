#!/usr/bin/env python

# TODO remove reservation client syntax

import sys, os, time
#sys.path.append("/usr/local/hen/lib")

from daemonizer import Daemonizer
from daemon import Daemon
import logging, threading, socket, pickle, datetime
from henmanager import HenManager
#from auxiliary.timer import GracefulTimer
from auxiliary.daemonlocations import DaemonLocations
import commands, re, shutil
from daemonclients.reservationclient import ReservationClient
import xml.dom.minidom
from auxiliary.hen import *

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)


processor_vendor = ""
processor_version = ""
usb_version = 0
memory_count = 0

class ComputerDetector():

    def __init__(self,ip,node,debug):
        self.__node = node
        self.__toGiga = (1.0 / 10 ** 9)
        self.__toGigaBinary = (1.0 / 2 ** 30)
        self.__processor_count = 0
        self.__processor_core_count = {}
        self.__interfaces = {}
        self.__next_interface_id = 0
        self.__ip = ip
	self.__debug = debug
        self.__target = None
        self.__lshw = None
    
        self.__target = ReservationClient()
        #if not self.__debug:
        self.__switchd = ReservationClient()
        self.__if_list = []
        log.info("Detecting "+str(ip))
        self.finished=False
        self.start()

    def getNode(self):
        return self.__node

    def getLshw(self):
        return self.__lshw

    def getInterfaceXML(self):
        string = ""
        for interface_type in self.__node.getInterfaces():
            for interface in self.__node.getInterfaces(interface_type):
                if interface.getTdrSuccess() == False:
                    string += '<interface type="' + str(interface_type) + '" mac="' + str(interface.getMAC()) + \
                              '" switch="' + str(interface.getSwitch()) + '" port="' + str(interface.getPort()) + \
                              '" model="' + str(interface.getModel()) + '" speed="' + str(interface.getSpeed()) + \
                              '" id="' + str(interface.getInterfaceID()) +'" tdrSuccess="' + str(interface.getTdrSuccess()) + \
                              '" tdrOutput="' + str(interface.getTdrOutput()) +'" />\n'
        return string
                    
    def __getText(self,nodelist):
        rc = ""
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc = rc + node.data
        return rc                        

    def __handleLshw(self,lshwdoc):
        nodes = lshwdoc.getElementsByTagName("node")
        self.__handleLshwNodes(nodes)

    def __handleLshwNodes(self,nodes):
        global processor_count, processor_core_count, processor_vendor, processor_version, processor_speed, usb_version, memory_count
        for node in nodes:
            if node.hasAttributes():
                if self.__getText(node.attributes['class'].childNodes) == "system":
                    self.__handleSystemNode(node)
                if self.__getText(node.attributes['class'].childNodes) == "processor":
                    self.__handleProcessorNode(node)
                if self.__getText(node.attributes['class'].childNodes) == "network":
                    self.__handleNetworkNode(node)
                if self.__getText(node.attributes['class'].childNodes) == "bus":
                    self.__handleBusNode(node)
                if self.__getText(node.attributes['class'].childNodes) == "memory":
                    self.__handleMemoryNode(node)
        
        self.__node.setSingleAttribute("numbercorespercpu",0)
        for cpu_id in self.__processor_core_count:
            self.__node.setSingleAttribute("numbercorespercpu",max(self.__node.getSingleAttribute("numbercorespercpu"),self.__processor_core_count[cpu_id]))
        self.__node.setSingleAttribute("numbercpus",self.__processor_count)
        self.__node.setSystemMemory(memory_count * self.__toGigaBinary)
        self.__node.setInterfaces(self.__interfaces)

    def __handleSystemNode(self,node):
        if (self.__getText(node.getElementsByTagName("description")[0].childNodes) == "Rack Mount Chassis"):
            self.__node.setMotherboard(self.__getText(node.getElementsByTagName("product")[0].childNodes))
            self.__node.setModel(self.__getText(node.getElementsByTagName("product")[0].childNodes).replace(' ',''))
            self.__node.setVendor(self.__getText(node.getElementsByTagName("vendor")[0].childNodes))
            try:
                self.__node.setSingleAttribute("serialnumber", self.__getText(node.getElementsByTagName("serial")[0].childNodes))
            except:
                pass
                                    
    def __handleProcessorNode(self,node):
        id = self.__getText(node.attributes['id'].childNodes)
        if (id.startswith("logical")):
            parent = self.__getText(node.parentNode.attributes['id'].childNodes)
            if self.__processor_core_count.has_key(parent):
                self.__processor_core_count[parent] = self.__processor_core_count[parent] + 1
            else:
                self.__processor_core_count[parent] = 1
        else:
            self.__processor_count = self.__processor_count + 1
            try:
                self.__node.setSingleAttribute("cputype",' '.join( str(self.__getText(node.getElementsByTagName("product")[0].childNodes)).split()))
            except:
                pass
            try:
                self.__node.setSingleAttribute("cpuspeed",int(self.__getText(node.getElementsByTagName("size")[0].childNodes)) * self.__toGiga)
            except:
                pass

    def __handleNetworkNode(self,node):
        interface = Interface()
        try:
            for n in node.getElementsByTagName("configuration")[0].getElementsByTagName("setting"):
                if (self.__getText(n.attributes['id'].childNodes) == "ip"):
                    interface.setIP(self.__getText(n.attributes['value'].childNodes))
                if (self.__getText(n.attributes['id'].childNodes) == "subnet"):
                    interface.setSubnet(self.__getText(n.attributes['value'].childNodes))
                if (self.__getText(n.attributes['id'].childNodes) == "module"):
                    if interface.getModel() == None:
                        interface.setModel(self.__getText(n.attributes['value'].childNodes))
                if (self.__getText(n.attributes['id'].childNodes) == "speed"):
                    interface.setSpeed(self.__getText(n.attributes['value'].childNodes))
        except:
            pass
        try:
            interface.setMAC(self.__getText(node.getElementsByTagName("serial")[0].childNodes).upper())
            self.__if_list.append(self.__getText(node.getElementsByTagName("serial")[0].childNodes))
        except:
            interface.setMAC("00:00:00:00:00:00")
        try:
            if interface.getSpeed() == None:
                if self.__getText(node.getElementsByTagName("capacity")[0].childNodes) == "1000000000":
                    interface.setSpeed("1GB/s")
                if self.__getText(node.getElementsByTagName("capacity")[0].childNodes) == "100000000":
                    interface.setSpeed("100MB/s")
                self.__if_list.append(self.__getText(node.getElementsByTagName("capacity")[0].childNodes))
        except:
            pass   
        try:
            interface.setModel(self.__getText(node.getElementsByTagName("product")[0].childNodes))
        except:
            pass
        interface.setIfaceType("experimental")
        if interface.getIP() != None:
            if interface.getIP().startswith("192.168.0."):
                interface.setIfaceType("management")
            elif interface.getIP().startswith("192.168.1."):
                interface.setIfaceType("infrastructure")
            elif interface.getIP().startswith("128.16."):
                interface.setIfaceType("external")
        if not self.__interfaces.has_key(interface.getIfaceType()):
               self.__interfaces[interface.getIfaceType()] = []
        interface.setInterfaceID("interface"+str(self.__next_interface_id))
        self.__next_interface_id = self.__next_interface_id + 1
        self.__interfaces[interface.getIfaceType()].append(interface)
                             
    def __handleBusNode(self,node):
        try:
            if (self.__getText(node.getElementsByTagName("description")[0].childNodes) == "USB Controller"):
                usbVersionMap = {"01":"1.0", "0b":"1.1", "02":"2.0", "09":"2.0"}
                id = self.__getText(node.attributes['id'].childNodes)
                if (id.startswith("usb")):
                    self.__node.setSingleAttribute("usbversion",usbVersionMap[self.__getText(node.getElementsByTagName("version")[0].childNodes)])
            elif (self.__getText(node.getElementsByTagName("description")[0].childNodes) == "Motherboard"):
                #self.__node.setMotherboard(self.__getText(node.getElementsByTagName("product")[0].childNodes))
                pass
        except:
            pass
        
    def __handleMemoryNode(self,node):
        global memory_count
        id = self.__getText(node.attributes['id'].childNodes)
        if (id.startswith("bank")):
            try:
                memory_count = memory_count + int(self.__getText(node.getElementsByTagName("size")[0].childNodes))
            except:
                pass              

    def lshw(self):

        command = "lshw"
        payload = ""
        if not self.__debug:
	   PORT = DaemonLocations.autodetectClientDaemon[1]
	else:
	   PORT = DaemonLocations.autodetectClientDaemon[1] + 100000
        log.info("trying to connect to "+str(self.__ip)+" on "+str(PORT))
        self.__target.connect(self.__ip,PORT)

        #if not self.__debug:
        self.__lshw = self.__target.sendRequest(command,payload)
            #print lshw
        #else:
        #    self.__lshw = "/home/arkell/u0/adam/development/svn/hen_scripts/computer100-lshw.xml"
#            self.__lshw = "computer100-lshw.xml"
        
#	if self.__debug:
#            dom = xml.dom.minidom.parse(self.__lshw)
#        else:
#            # write lshw to file
        dom = xml.dom.minidom.parseString(self.__lshw)
        self.__handleLshw(dom)

    def interface_find(self):
        print "INTERFACE FIND"
        self.__switchd.connect("192.168.1.2",90000)
        self.__target.sendRequest("interface_up", pickle.dumps(self.__if_list))
        self.__target.sendRequest("interface_test", pickle.dumps(self.__if_list))
        time.sleep(20)
        
        reply = self.__switchd.sendRequest("port_find_mac", pickle.dumps(self.__if_list))
        for i in range(0,len(reply)):
            for interface_type in self.__node.getInterfaces():
                for interface in self.__node.getInterfaces(interface_type):
                    if interface.getMAC().upper() == reply[i][0].upper():
                        mac_list = reply[i][1].getMacs()
                        found = []
                        for m in mac_list:
                            if found.count(m) == 0:
                                found.append(m)
                        if len(found) == 1:
                            interface.setPort(reply[i][1].getName())
                            interface.setName(reply[i][1].getName())
                            interface.setSwitch(reply[i][1].getSwitch())
                                    
        self.__switchd.close()
        
    def interface_tdr(self):
        self.__switchd.connect("192.168.1.2",90000)
        for interface_type in self.__node.getInterfaces():
            for interface in self.__node.getInterfaces(interface_type):
                if interface.getSwitch() == None or interface.getName() == None:
                    pass
                dev = ([interface.getMAC()])
                new_payload = pickle.dumps(dev)
                self.__target.sendRequest("interface_down", new_payload)
                dev = (interface.getSwitch(),interface.getName())
                new_payload = pickle.dumps(dev)
                try:
                    tdr_res = pickle.loads(self.__switchd.sendRequest("port_tdr", new_payload))
                
                    if tdr_res[0]:
                        interface.setTdrSuccess(True)
                        #print str(interface.getSwitch()),str(interface.getName())+" tdr ok"
                    else:
                        interface.setTdrSuccess(False)
                        interface.setTdrOutput(tdr_res[1])
                        #print str(interface.getSwitch()),str(interface.getName())+" tdr failed : \n"+str(tdr_res[1])
                except:
                    print "problem running tdr for ",str(interface.getSwitch()),str(interface.getName())
                    pass
                print interface
        payload = pickle.dumps(())
        self.__target.sendRequest("interface_down", payload)
        self.__switchd.close()
        
    def start(self):
        self.lshw()
        self.interface_find()
        if not self.__debug:
            #self.interface_find()
            self.interface_tdr()
            time.sleep(5)
        
        payload = pickle.dumps((""))
        self.__target.sendAsyncRequest("stop", payload)
        
        print "finished detecting",self.__ip
        self.finished=True
        
class DetectorDaemon(threading.Thread):
    def __init__(self,d,debug):
    	self.__debug = debug
        self.__device_list = d
        self.__run = True
        self.__nodes = {}
        self.__running = []
        self.__man_ips = {}
        self.__inf_ips = {}
        self.__symlinksRoot = "/export/machines/"
        if self.__debug:
            self.__etcRoot = "/usr/local/hen/etc/daemons/autodetectiond/debug/"
        else:
            self.__etcRoot = "/usr/local/hen/etc/daemons/autodetectiond/"

        self.load_data()
        self.show_stats()
        
        threading.Thread.__init__(self)
    def show_stats(self):
        count = 0
        string = "Number of free management ips :"
        for i in self.__man_ips:
            if self.__man_ips[i] == "free":
                count = count + 1
        string = string + str(count)
        log.info(string)
        count = 0
        string = "Number of free infrastructure ips :"
        for i in self.__inf_ips:
            if self.__inf_ips[i] == "free":
                count = count + 1
        string = string + str(count)
        log.info(string)

    def load_data(self):
        log.info("Loading Data")
        self.__manager = HenManager()
        for i in range(1,254):
            self.__man_ips["192.168.0."+str(i)] = "free"
            self.__inf_ips["192.168.1."+str(i)] = "free"
            
        n = self.__manager.getNodes("all","all")
        for nt in n:
            for node in n[nt].values():
                try:
                    man_ip = node.getInterfaces("management")
                    inf_ip = node.getInterfaces("infrastructure")
                    if man_ip != []:
                        self.__nodes[man_ip[0].getIP()] = node
                        self.__man_ips[str(man_ip[0].getIP())] = node.getNodeID()
                    if inf_ip != []:
                        self.__nodes[inf_ip[0].getIP()] = node
                        self.__inf_ips[str(inf_ip[0].getIP())] = node.getNodeID()
                except:
                    pass
        self.show_stats()

    def getFreeIp(self,type_str):
        if type_str == "infrastructure":
            for i in self.__inf_ips:
                if self.__inf_ips[i] == "free":
                    return i
            return "no free infrastructure ip"
        elif type_str == "management":
            for i in self.__man_ips:
                if self.__man_ips[i] == "free":
                    return i
            return "no free infrastructure ip"
        else:
            return "unknown ip type "+type_str
        
    def writeXML(self,node,old=False):
        xmlstring = self.__manager.parser.writeNodePhysicalFileString(node,self.__debug)
        print xmlstring
        filename=self.__etcRoot+node.getNodeID()+".xml"
        if old:
            filename=filename+".old"
        try:
            if not self.__debug:
                theFile = open(filename, "w")
                theFile.write(xmlstring)
                theFile.close()
            else:
                print "Would write to file ",filename
                print xmlstring
        except Exception, e:
            log.info("error while writing xml file for "+str(node.getNodeID()))
            log.info(str(e))
            return -1

    def readLshw(self,node_str):
        filename=self.__etcRoot+node_str+"-lshw.xml"
        try:
            theFile = open(filename, "r")
            xmlstring = theFile.readlines()
            theFile.close()
        except Exception, e:
            log.info("error while reading lshw file for "+str(node_str))
            log.info(str(e))
            return (["error while reading lshw file for "+str(node_str)])
        
        return xmlstring
    
    def writeLshw(self,node,xmlstring):
        filename=self.__etcRoot+node.getNodeID()+"-lshw.xml"
        try:
            theFile = open(filename, "w")
            theFile.write(xmlstring)
            theFile.close()
        except Exception, e:
            log.info("error while writing to lshw file for "+str(node.getNodeID()))
            log.info(str(e))
            return -1
        
    def writeInterfaces(self,node,detector):
        filename=self.__etcRoot+node.getNodeID()+"-interfaces.xml"
        xmlstring = detector.getInterfaceXML()
        try:
            if not self.__debug:
                theFile = open(filename, "w")
                theFile.write(xmlstring)
                theFile.close()
            else:
                print "would write : "+filename+" : "+xmlstring
        except Exception, e:
            log.info("error while writing to interfaces file for "+str(node.getNodeID()))
            log.info(str(e))
            return -1

    def power_target(self,target,action):
        log.info("power "+str(action)+" "+str(target))
        if not self.__debug:
            self.__manager.powerSilent(target, "power"+action)
        else:
            print "would power"+str(action)+" "+str(target)

    def cleanup_target(self,device):
        log.info("cleanup "+str(device))
        if not self.__debug:
            os.system("rm " + self.__symlinksRoot + device + "/*")
            os.system("rm " + self.__symlinksRoot + device + "/pxelinux.cfg/*")
        else:
            print "would run : rm " + self.__symlinksRoot + device + "/*"
            print "would run : rm " + self.__symlinksRoot + device + "/pxelinux.cfg/*"

    def setup_target(self,target,autodetect=False):
        log.info("setup "+str(target))

        mac = ""
        n = self.__manager.getNodes("all","all")
        for nt in n:
            for node in n[nt].values():
                if (node.getNodeID() == target):
                    man_ip = node.getInterfaces("management")
                    mac = "01-"+str(man_ip[0].getMAC().replace(':','-').lower())
        if autodetect:
            pxestring = "default autodetect\n"
        else:
            pxestring = "default linux\n"
        pxestring = pxestring + "label autodetect\n"
        pxestring = pxestring + "\tkernel kernel.autodetect\n"
        pxestring = pxestring + "\tappend ip=dhcp root=/dev/ram initrd=initrd.autodetect console=ttyS0\n"
        pxestring = pxestring + "label linux\n"
        pxestring = pxestring + "\tkernel kernel\n"
        pxestring = pxestring + "\tappend ip=dhcp root=/dev/nfs nfsroot=192.168.0.250:/cs/research/nets/hen/export0/machines/"+str(target)+"/filesystem,nfsvers=3 console=ttyS0\n"
        pxestring = pxestring + "serial 0 9600\n"

        startupstring = "#!/bin/bash\n"
        startupstring = startupstring + "hostname "+target+"\n"
        
        default_str = "default"
        mac_str = str(mac)
        target_str = self.__symlinksRoot + target
        autodetect_kernel_str = "kernel.autodetect"
        autodetect_initrd_str = "initrd.autodetect"
        loader_str = "loader"
        autodetect_initrd = "../../filesystems/adam/autodetect.img"
        autodetect_kernel = "../../kernels/adam/autodetect-vmlinuz-2.6.36.2"
        loader = "../../loaders/pxelinux.0"
        if not self.__debug:
            pxeFile = open(target_str+"/pxelinux.cfg/"+default_str, "w")
            pxeFile.write(pxestring)
            pxeFile.close()
            startupFile = open(target_str+"/startup.sh","w")
            startupFile.write(startupstring)
            startupFile.close()
            os.system("cd "+target_str+" ; chmod +x "+target_str+"/startup.sh")
            os.system("cd "+target_str+" ; ln -s " + loader + " " + loader_str)
            os.system("cd "+target_str+"/pxelinux.cfg/ ; ln -s " + default_str + " " + mac_str)
            os.system("cd "+target_str+" ; ln -s " + autodetect_kernel + " " + autodetect_kernel_str)
            os.system("cd "+target_str+" ; ln -s " + autodetect_initrd + " " + autodetect_initrd_str)
        else:
            print "would write :\n"+pxestring+"\n to : "+default_str
            print "would write :\n"+startupstring+"\n to :"+target_str+"/startup.sh"
            print "would run : ln -s " + default_str + " " + mac_str
            print "would run : ln -s " + loader + " " + loader_str
            print "would run : ln -s " + autodetect_kernel + " " + autodetect_kernel_str
            print "would run : ln -s " + autodetect_initrd + " " + autodetect_initrd_str
        
    def run(self):
        while(self.__run):
            for device in self.__device_list:
                self.__device_list.remove(device)
                if not self.__nodes.has_key(device):
                    print "new device",
                    node = ComputerNode()
                    if self.__debug:
                        node.setNodeID("computerDEBUG")
                    print node 
                else:
                    node = self.__nodes[device]                      
                    self.writeXML(node,True)
                self.__running.append(ComputerDetector(device,node,self.__debug))
            for run_device in self.__running:
                if run_device.finished:
                    self.__running.remove(run_device)
                    if run_device.getNode().getNodeID() == None:
                        print "NULL NODE"
                        print node
                        print device
                        print self.__nodes
                    self.writeXML(run_device.getNode(),False)
                    if not self.__debug:
                        self.writeLshw(run_device.getNode(),run_device.getLshw())
                        
                    self.writeInterfaces(run_device.getNode(),run_device)
                    self.power_target(run_device.getNode().getNodeID(),"off")
                    # Remove old files    
                    self.cleanup_target(run_device.getNode().getNodeID())
                    # Setup symlinks    
                    self.setup_target(run_device.getNode().getNodeID(),False)
                                            
            time.sleep(5)
    

class AutoDetectionServer(Daemon):
    """\brief Implements basic reservation daemon functionality.
    """
    __version = "Auto Detection Client Daemon v0.1 (simple)"
    
    def __init__(self,debug):
    	self.__debug = debug
        Daemon.__init__(self)
        self.__registerMethods()
        self.device_list = []
        self.__detector_daemon = DetectorDaemon(self.device_list,self.__debug)
        self.__detector_daemon.start()

        
    def __registerMethods(self):
        self.registerMethodHandler("register_target", self.register_target)
        self.registerMethodHandler("redetect_target", self.redetect_target)
        self.registerMethodHandler("get_lshw", self.get_lshw)
        self.registerMethodHandler("get_free_ip", self.get_free_ip)
        self.registerMethodHandler("reload", self.system_reload)
                
    def __sendReply(self,prot,code,seq,payload):
        if (code == 0):
            code = 200
        else:
            code = 422 # returnCodes[422] = "error executing command"
        prot.sendReply(code, seq, payload)

    def get_lshw(self,prot,seq,ln,payload):
        node_str = pickle.loads(payload)
        return_str = pickle.dumps(self.__detector_daemon.readLshw(node_str))
        self.__sendReply(prot,"100",seq,return_str)

    def get_free_ip(self,prot,seq,ln,payload):
        type_str = pickle.loads(payload)
        return_str = pickle.dumps(self.__detector_daemon.getFreeIp(type_str))
        self.__sendReply(prot,"100",seq,return_str)

    def system_reload(self,prot,seq,ln,payload):
        type_str = pickle.loads(payload)
        return_str = pickle.dumps("Reload not implemented")
        self.__detector_daemon.load_data()
        self.__sendReply(prot,"100",seq,return_str)

    def redetect_target(self,prot,seq,ln,payload):
        host = pickle.loads(payload)
        log.info("Redetect "+str(host))
        
        reply = "Redetect of "+str(host)+" requested."

        self.__detector_daemon.power_target(host,"off")
        self.__detector_daemon.cleanup_target(host)
        self.__detector_daemon.setup_target(host,True)
        self.__detector_daemon.power_target(host,"on")
        response = pickle.dumps(reply)
        self.__sendReply(prot,"100",seq,response)

    def register_target(self,prot,seq,ln,payload):
        log.info("Register Received from "+str(payload))
        reply = "success"
	#if not self.__debug:
        self.device_list.append(payload)
	#else:
	#   self.device_list.append("127.0.0.1")
        response = pickle.dumps(reply)
        self.__sendReply(prot,"100",seq,response)

    def stopDaemon(self,prot,seq,ln,payload):
        """\brief Stops the daemon and all threads
        This method will first stop any more incoming queries, then wait for
        any update tasks to complete, before stopping itself.
        """
        log.info("stopDaemon called.")
        prot.sendReply(200, seq, "Accepted stop request.")
        log.debug("Sending stopDaemon() response")
        self.acceptConnections(False)
        log.info("Stopping AutoDetectionClientDaemon (self)")
        self.stop()

class AutoDetectionDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    __bind_addr = DaemonLocations.autodetectDaemon[0]
    __port = DaemonLocations.autodetectDaemon[1]
    __sockd = None
    __autoDetectionClient = None
    
    def __init__(self, doFork, debug):
        self.__debug = debug
        if self.__debug:
            self.__bind_addr = "192.168.0.2"
            self.__port = self.__port + 100000
        Daemonizer.__init__(self, doFork)

    def run(self):
        log.debug("Creating Auto Detection Client Daemon")
        
        self.__autoDetectionServer = AutoDetectionServer(self.__debug)
        # Creating socket
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        self.__sockd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        self.__sockd.settimeout(2) # 2 second timeouts
        log.info("Starting Auto Detection Server Daemon")
        self.__autoDetectionServer.start()
        while self.__autoDetectionServer.isAlive():
            if self.__autoDetectionServer.acceptingConnections():
                # allow timeout of accept() to avoid blocking a shutdown

                try:
                    (s,a) = self.__sockd.accept()
                    log.debug("New connection established from " + str(a))
                    self.__autoDetectionServer.addSocket(s)
                except socket.timeout:	
                    pass

            else:
                log.warning(\
                      "Auto Detection Server Daemon still alive, but not accepting connections")
                time.sleep(2)
        
	log.info("Closing socket.")
	self.stop()

    def stop(self):
        
        self.__sockd.shutdown(socket.SHUT_RDWR)
        self.__sockd.close()
        self.__autoDetectionServer.stop()
	count = 0
        while threading.activeCount() > 1 and count < 3:
            cThreads = threading.enumerate()
            log.warning("Waiting on " + str(threading.activeCount()) + \
                        " active threads...")
            time.sleep(2)
	    count += 1
        log.info("Auto Detection Server Daemon Finished.")
        # Now everything is dead, we can exit.
        sys.exit(0)

def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    DEBUG = False
    FORK = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "--debug":
            DEBUG=True
            FORK=False
            print "RUNNING IN DEBUG MODE"

    if not DEBUG:
        WORKDIR = '/var/hen/autodetectdaemon'
        PIDDIR = '/var/run/hen'
        LOGDIR = '/var/log/hen/autodetectdaemon'
    else:
        WORKDIR = '/tmp/var/hen/autodetectdaemon/debug'
        PIDDIR = '/tmp/var/run/hen/debug'
        LOGDIR = '/tmp/var/log/hen/autodetectdaemon/debug'
    LOGFILE = 'autodetectdaemon.log'
    PIDFILE = 'autodetectdaemon.pid'
    if DEBUG:
        GID = int(commands.getoutput('id -g'))
        UID = int(commands.getoutput('id -u'))
    else:
        UID = int(commands.getoutput('id -u'))
        GID = 3000 # hen
    autodetectiond = AutoDetectionDaemon(FORK,DEBUG)
    autodetectiond.setUid(UID)
    autodetectiond.setGid(GID)
    autodetectiond.setWorkingDir(WORKDIR)
    autodetectiond.setPIDDir(PIDDIR)
    autodetectiond.setLogDir(LOGDIR)
    autodetectiond.setLogFile(LOGFILE)
    autodetectiond.setPidFile(PIDFILE)
                        
    try:
        autodetectiond.start()
    except KeyboardInterrupt:
        autodetectiond.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()
