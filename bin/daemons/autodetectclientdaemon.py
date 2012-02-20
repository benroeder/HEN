#!/usr/bin/env python

# TODO remove reservation client syntax

import sys, os, time
#sys.path.append("/usr/local/hen/lib")

from daemonizer import Daemonizer
from daemon import Daemon
import logging, threading, socket, pickle, datetime
#from henmanager import HenManager
#from auxiliary.timer import GracefulTimer
from auxiliary.daemonlocations import DaemonLocations
import commands, re, shutil
from daemonclients.reservationclient import ReservationClient

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

class Pinger(threading.Thread):
    def __init__(self):
        self.__iface_list = []
        self.__run = True
        threading.Thread.__init__(self)

    def run(self):
        print "PINGER RUN"
        while(self.__run):
            for iface in self.__iface_list:
                cmd = "ping -c 2 -q -I "+iface+" 1.1.1.1"
                log.info("Running "+cmd)
                print "Pinger running"+cmd
                result = commands.getoutput(cmd)
            time.sleep(5)
    def add_iface(self,iface):
        #if self.__iface_list.count(iface) == 0:
        print "PINGER ADDING INTERFACE",iface
        self.__iface_list.append(iface)
        
    def remove_iface(self,iface):
        if self.__iface_list.count(iface) == 1:
            self.__iface_list.remove(iface)

    def stop_pinger(self):
        self.__run = False

class AutoDetectionClient(Daemon):
    """\brief Implements basic reservation daemon functionality.
    """
    __version = "Auto Detection Client Daemon v0.1 (simple)"
    
    def __init__(self,debug=False):
        Daemon.__init__(self)
	self.__debug = debug
        self.__ifaces = {} # mac -> ethX
        self.__management_iface = None
        self.__management_ip = None
        self.__get_interface_list()
        self.__registerMethods()
        self.__registerWithAutoDetectionDaemon()
        self.__pinger = Pinger()
        print "STARTING PINGER"
        self.__pinger.start()
        self.end = False

    def __registerWithAutoDetectionDaemon(self):
        log.info("Trying to connect with autodetection deamon from "+self.__management_ip)
        if self.__debug:
            HOST = "192.168.0.2"
            PORT = DaemonLocations.autodetectDaemon[1] + 100000
            print "TARGET ",HOST,PORT
        else:
            HOST = DaemonLocations.autodetectDaemon[0]
            PORT = DaemonLocations.autodetectDaemon[1]
        client = ReservationClient()
        success = False
        command = "register_target"    
        payload = str(self.__management_ip)
        retries = 0
        while (retries < 3 and not success):
            try:
                retries += 1
                client.connect(HOST, PORT)
                reply = client.sendRequest(command,payload)
                if  reply == "success":
                    success = True
            except Exception,e:
                print e
                log.warning("Retry "+str(retries)+" sleeping for 10 seconds")
                time.sleep(10)
        client.close()
        if success :
            log.info("Connected.")
        else:
            log.critical("Failed to connect")
            self.stop()
        
                
    def __registerMethods(self):
        self.registerMethodHandler("lshw", self.lshw)
        self.registerMethodHandler("interface_up", self.interface_up)
        self.registerMethodHandler("interface_down", self.interface_down)
        self.registerMethodHandler("interface_test", self.interface_test)
        self.registerMethodHandler("interface_list", self.interface_list)
        self.registerMethodHandler("stop", self.stopDaemon)
        
    def __sendReply(self,prot,code,seq,payload):
        if (code == 0):
            code = 200
        else:
            code = 422 # returnCodes[422] = "error executing command"
        prot.sendReply(code, seq, payload)

    def lshw(self,prot,seq,ln,payload):
        print "Running lshw locally"
        result = commands.getoutput('lshw -xml 2>/dev/null')
        #print "Result of lshw",result
        response = pickle.dumps(result)
        self.__sendReply(prot,"100",seq,response)
        
    def __get_interface_list(self):
    	#if not self.__debug:
           result = commands.getoutput('ifconfig -a 2>/dev/null | grep HW | grep -v 00:00:00:00:00:00')
           print "GET INTERFACE LIST "+str(result)
           man_if = (commands.getoutput('route 2>/dev/null | grep 192.168.0')).split()[-1]
           for line in result.splitlines():
               self.__ifaces[(line.split()[4]).upper()] = line.split()[0]
               if line.split()[0] == man_if:
               	  self.__management_iface = (line.split()[4]).upper()
               	  cmd = "ifconfig "+line.split()[0]+" | grep inet\ addr"
               	  res = commands.getoutput(cmd)
               	  self.__management_ip =(res.split(':')[1]).split()[0]
	#else:
		# debugging
	#	self.__management_iface = "00:00:00:00:00:00"
#		self.__management_ip = "192.168.0.23"
            
    def interface_list(self,prot,seq,ln,payload):
        iface_list = []
	if not self.__debug:
           for i in self.__ifaces:
               iface_list.append(i)
	else:
	   iface_list.append("11:11:11:11:11:11")
	   iface_list.append("11:11:11:11:11:22")
        response = pickle.dumps(iface_list)
        self.__sendReply(prot,"100",seq,response)

    def interface_down(self,prot,seq,ln,payload):
        interfaces = pickle.loads(payload)
        result = []
        for interface in interfaces:
            try:
                if interface.upper() != self.__management_iface:
                    self.__pinger.remove_iface(self.__ifaces[interface.upper()])
                    cmd = "ifconfig "+self.__ifaces[interface.upper()]+" down"
                    log.info("Running "+cmd)
                    res = commands.getoutput(cmd)
                    result.append((interface.upper(),True))
                else:
                    result.append((interface.upper(),False))
            except:
                result.append((interface.upper(),False))
        response = pickle.dumps(result)
        self.__sendReply(prot,"100",seq,response)

    def interface_up(self,prot,seq,ln,payload):
        interfaces = pickle.loads(payload)
        result = []
        for interface in interfaces:
            try:
                if interface.upper() != self.__management_iface:
                    cmd = "ifconfig "+self.__ifaces[interface.upper()]+" up"
                    log.info("Running "+cmd)
                    res = commands.getoutput(cmd)
                    log.info("Ran "+cmd+" with result "+str(res))
                    result.append((interface.upper(),True))
                else:
                    result.append((interface.upper(),False))
            except:
                result.append((interface.upper(),False))
        response = pickle.dumps(result)
        self.__sendReply(prot,"100",seq,response)

    def interface_test(self,prot,seq,ln,payload):
        interfaces = pickle.loads(payload)
        print "TESTING INTERFACES"+str(interfaces),self.__ifaces
        for i in self.__ifaces:
            print "IFACE",i,self.__ifaces[i]
        result = []
        for interface in interfaces:
            if self.__ifaces.has_key(interface.upper()):
                print "FOUND",i,self.__ifaces[i]
#            try:
                print "ADDING INTERFACE TO PINGER",interface,self.__pinger
                self.__pinger.add_iface(self.__ifaces[interface.upper()])
                print "ADDED INTERFACE TO PINGER",interface
                result.append((interface.upper(),True))
#            except Exception, e:
#                print e
#                result.append((interface.upper(),False))
        print result
        response = pickle.dumps(result)
        self.__sendReply(prot,"100",seq,response)

    def stop_pinger(self):
    	print "running stop"
        self.__pinger.stop_pinger()

    def stopDaemon(self,prot,seq,ln,payload):
        """\brief Stops the daemon and all threads
        This method will first stop any more incoming queries, then wait for
        any update tasks to complete, before stopping itself.
        """
        #self.__pinger.stop_pinger()
        log.info("stopDaemon called.")
        prot.sendReply(200, seq, "Accepted stop request.")
        log.debug("Sending stopDaemon() response")
        self.acceptConnections(False)
        log.info("Stopping AutoDetectionClientDaemon (self)")
        self.end = True
        
class AutoDetectionClientDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    __bind_addr = DaemonLocations.autodetectClientDaemon[0]
    __port = DaemonLocations.autodetectClientDaemon[1]
    __sockd = None
    __autoDetectionClient = None
    
    def __init__(self, doFork,debug):
    	self.__debug = debug
	if self.__debug:
	   self.__port = self.__port + 100000
	   self.__bind_addr = "192.168.0.2"
        Daemonizer.__init__(self, doFork)
	

    def run(self):
        log.debug("Creating Auto Detection Client Daemon")
        
        self.__autoDetectionClient = AutoDetectionClient(self.__debug)
        # Creating socket
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        self.__sockd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print "Binding to port: " + str(self.__port)+" on address "+str(self.__bind_addr)
        self.__sockd.bind(("0.0.0.0", self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        self.__sockd.settimeout(2) # 2 second timeouts
        log.info("Starting Auto Detection Client Daemon")
        self.__autoDetectionClient.start()
        while self.__autoDetectionClient.isAlive() and not self.__autoDetectionClient.end:
            #print "outer loop"
            if self.__autoDetectionClient.acceptingConnections():
                try:
                    try:
                        (s,a) = self.__sockd.accept()
                        log.debug("New connection established from " + str(a))
                        self.__autoDetectionClient.addSocket(s)
                    except socket.timeout:
                        pass
                except KeyboardInterrupt:
                    break
                
            else:
                log.warning(\
                      "Auto Detection Client Daemon still alive, but not accepting connections")
                time.sleep(2)
        log.info("Closing socket.")
        self.__sockd.shutdown(socket.SHUT_RDWR)
        self.__sockd.close()
        self.__autoDetectionClient.stop_pinger()
        self.__autoDetectionClient.stop()
        while threading.activeCount() > 1:
            cThreads = threading.enumerate()
            log.warning("Waiting on " + str(threading.activeCount()) + \
                        " active threads...")
            time.sleep(2)
        log.info("Auto Detection Client Daemon Finished.")
        # Now everything is dead, we can exit.
        sys.exit(0)

def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    DEBUG = False
    FORK = True
    if len(sys.argv) > 1:
        if sys.argv[1] == "--debug":
            DEBUG=True
            FORK=False
            print "RUNNING IN DEBUG MODE"

    if DEBUG:
        GID = int(commands.getoutput('id -g'))
        UID = int(commands.getoutput('id -u'))
    else:
        GID = 1 # daemons
    	UID = 0 # root
    if not DEBUG:
        WORKDIR = '/var/hen/autodetectclientdaemon'
        PIDDIR = '/var/run/hen'
        LOGDIR = '/var/log/hen/autodetectclientdaemon'
    else:
        WORKDIR = '/tmp/var/hen/autodetectclientdaemon/debug'
        PIDDIR = '/tmp/var/run/hen/debug'
        LOGDIR = '/tmp/var/log/hen/autodetectclientdaemon/debug'
    LOGFILE = 'autodetectclientdaemon.log'
    PIDFILE = 'autodetectclientdaemon.pid'
    autodetectionclientd = AutoDetectionClientDaemon(FORK,DEBUG)
    autodetectionclientd.setUid(UID)
    autodetectionclientd.setGid(GID)
    autodetectionclientd.setWorkingDir(WORKDIR)
    autodetectionclientd.setPIDDir(PIDDIR)
    autodetectionclientd.setLogDir(LOGDIR)
    autodetectionclientd.setLogFile(LOGFILE)
    autodetectionclientd.setPidFile(PIDFILE)
    #try:
    autodetectionclientd.start() 
    #except Exception, e:
    #	print e
    #	sys.exit(1)

if __name__ == "__main__":
    main()
