#!/usr/local/bin/python
import sys,__builtin__
sys.path.append("/usr/local/hen/lib")

from daemonizer import Daemonizer
from daemon import Daemon
import logging, traceback, pickle, string, hashlib, time, threading, socket
from auxiliary.timer import GracefulTimer
from auxiliary.daemonlocations import DaemonLocations
from ConfigParser import SafeConfigParser

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

class PowerControl(Daemon):
    """\brief Implements basic power daemon functionality. 
    Current version does not implement authentication. It does not use SSL for connections. This might be needed
    in the future if the power daemon and hmd are not on the same machine, and to avoid letting firewall config 
    errors compromise the power daemon.
    """
    __computerToSwitch = {}
    __configuredPortState = {}
    __phases = {}
    __switch = {}
    __switchInstances = {}
    __configFile = None
    __interPhaseDelay = 0
    __intraPhaseDelay = 0
    __power_check_timer = None
    
    def __init__(self, configFilePath='/usr/local/hen/etc/configs/powerdaemon/powerdaemon.cfg'):
        """\brief Registers the methods this daemon offers.
        """
        Daemon.__init__(self)
        self.__registerMethods()
        self.__configFile = SafeConfigParser()
        try:
            self.__configFile.read(configFilePath)
            self.__configFile.get('MAIN', 'HEN_CONFIG_FILE')
            self.__power_check_timer = GracefulTimer(string.atoi(\
                 self.__configFile.get('MAIN', 'POWER_CHECK_INTERVAL')), \
                 self.checkPowerState).start()

            self.__interPhaseDelay = string.atoi(self.__configFile.get('MAIN', \
                                                           'INTER_PHASE_DELAY'))
            self.__intraPhaseDelay = string.atoi(self.__configFile.get('MAIN', \
                                                           'INTRA_PHASE_DELAY'))
            
            if (self.__interPhaseDelay<=0 or self.__intraPhaseDelay<=0):
                log.debug("Delays are wrong: inter phase is %d, intra phase is %d",self.__interPhaseDelay,self.__intraPhaseDelay)
            
        except Exception,e:
            log.error("Error while loading config file "+configFilePath+":"+str(e))
            sys.exit()
        self.loadConfig()
        
    def __registerMethods(self):
        self.registerMethodHandler("set_config", self.setConfig)
        self.registerMethodHandler("get_config_version", self.getConfigVersion)
        self.registerMethodHandler("get_port_name_list",self.getPortNameList)
        self.registerMethodHandler("set_port_state",self.setPortState)
        self.registerMethodHandler("get_port_state",self.getPortState)
        self.registerMethodHandler("get_conf_port_state",self.getConfiguredPortState)
        self.registerMethodHandler("get_switch_names",self.getSwitchNames)
        self.registerMethodHandler("get_port_to_switch",self.getPortToSwitch)
        self.registerMethodHandler("get_current",self.getCurrent)
    
    def checkPowerState(self):
        log.debug("Checking power state")
        #check power off first
        for device in self.__configuredPortState:
            if self.__configuredPortState[device]=="on":
                #this will be dealt with using the phases
                continue
            if self.checkDevicePower(device,"off")==0:
                log.error("Device "+device+" power should be off")
                (res,msg) = self.setPortStateBackend(device, "off")
                log.debug("Shutdown success:%d, message %s",self.checkDevicePower(device, "off"),msg)
                break
        
        phase_ids = self.__phases.keys()
        phase_ids.sort()
        for phase_id in phase_ids:
            boot = 0
            for device in self.__phases[phase_id]:
                if (self.checkDevicePower(device,"on"))==0:
                    log.error("Device "+device+" should be on")
                    (res,msg) = self.setPortStateBackend(device, "on")
                    log.debug("Powerup success:%d, message %s",self.checkDevicePower(device, "on"),msg)
                    boot = 1
                    time.sleep(self.__intraPhaseDelay)
                    break
            if (boot==1):
                time.sleep(self.__interPhaseDelay)
        
    def saveConfig(self):
        try:
            #save stuff to file
            log.debug("Saving hen configuration to "+self.__configFile.get('MAIN', 'HEN_CONFIG_FILE'))

	    sys.modules["__builtin__"] = __builtin__

            f = open(self.__configFile.get('MAIN', 'HEN_CONFIG_FILE'),"w")
            pickle.dump(self.version,f);
	    pickle.dump(self.__switch,f);
	    pickle.dump(self.__computerToSwitch,f);
            pickle.dump(self.__configuredPortState,f);
            pickle.dump(self.__phases,f);
        except Exception,e:
            log.error("Could not save config file "+self.__configFile.get('MAIN', 'HEN_CONFIG_FILE')+" because "+str(e))
            

    def loadConfig(self):
        try:
            #save stuff to file
            log.debug("Loading hen configuration from "+self.__configFile.get('MAIN', 'HEN_CONFIG_FILE'))
            f = open(self.__configFile.get('MAIN', 'HEN_CONFIG_FILE'),"r")
            self.version = pickle.load(f);
            self.__switch = pickle.load(f);
            self.__computerToSwitch = pickle.load(f);
            self.__configuredPortState = pickle.load(f);
            self.__phases = pickle.load(f);

	    for k in self.__switch.keys():
		self.__switchInstances[k] = self.__switch[k].getInstance();	    

            #log.debug(str(self.__computerToSwitch))            
            log.debug("Config version "+str(self.version))
        except Exception,e:
            log.error("Could not load config file "+self.__configFile.get('MAIN', 'HEN_CONFIG_FILE')+" because "+str(e))
	    self.version = ""

    def setConfigHandler(self,nodes):
        """\brief Parses state from the hen manager. 
        The payload is a pickled version of all the nodes in the hardware hen config. In the future 
        it must support delta updates and versioning
        """
        try:
            self.__switch = {}
            self.__computerToSwitch = {}
            self.__configuredPortState = {}
            self.__phases = {}
            
            for powerswitch in nodes["powerswitch"].values():
		pInstance = powerswitch.getInstance()
                self.__switch[powerswitch.getNodeID()] = powerswitch
		self.__switchInstances[powerswitch.getNodeID()] = pInstance
                
	    switches = nodes["switch"]
	    for key in switches.keys():
		if ((switches[key].getSingleAttribute("poe")) == "yes"):
		    self.__switch[key] = switches[key]
		    self.__switchInstances[key] = switches[key].getInstance()

	    serviceprocessors = nodes["serviceprocessor"]
	    for key in serviceprocessors.keys():
		self.__switch[key] = serviceprocessors[key]
		self.__switchInstances[key] = serviceprocessors[key].getInstance()

            for n in nodes.keys():
                if n != "powerswitch":
                    for obj in nodes[n].values():
                        try:
                            if (obj.getPowerNodes() is None):
                                log.debug("%s : no powerswitch specified",obj.getNodeID())
                                continue
                            
			    for (switch,port) in obj.getPowerNodes():
				if not self.__switch.has_key(switch):
				    log.debug("PowerSwitch %s required by %s does not exist",str(switch),str(obj.getNodeID()))
				    continue
                                
				if (not self.__computerToSwitch.has_key(obj.getNodeID())):
				    self.__computerToSwitch[obj.getNodeID()] = [(switch,port)]
                                else:
	                            self.__computerToSwitch[obj.getNodeID()].append((switch,port))
                                    
                                #deal with configured states
                            if (not (obj.getAttributes() is None) and obj.getAttributes().has_key("enforce_power_state")):
                                power = obj.getAttributes()["enforce_power_state"]
                                self.__configuredPortState[obj.getNodeID()] = power
                                if (power=="on"):
                                    self.__configuredPortState[obj.getNodeID()] = power
                                    if (obj.getAttributes().has_key("phase")):
                                        phase = string.atoi(obj.getAttributes()["phase"])
                                    else:
                                        phase = 100
                                        log.debug("Device "+obj.getNodeID()+" has no assigned power phase. Setting default value: 100")

                                    if (self.__phases.has_key(phase)):
                                        self.__phases[phase].append(obj.getNodeID());
                                    else:
                                        self.__phases[phase] = [obj.getNodeID()];
                                elif (power=="off"):
                                    self.__configuredPortState[obj.getNodeID()] = power
                                else:
                                    log.debug("Device "+obj.getNodeID()+" has assigned an invalid power state:"+power)
                        except Exception,e:
                            	traceback.print_exc()
			    	return (0,str(e))
            log.debug("Config version "+str(self.version)+" initialized succesfully")
            self.saveConfig()
	    return (1,"")
        except Exception,e:
            	traceback.print_exc()
		return (0,str(e))


    def getPortMapping(self, portname):
        """\brief Implements the namespace for powerd; 
        Besides the typical power computerX commands, it allows the client to directly specify a switch and port by using direct://switch:port
        """
        if portname[0:9]=="direct://" :
            i = portname.index(":",9)
            if (self.__switchInstances.has_key(portname[9:i])):
                return [(portname[9:i],portname[i+1:])]
            else:
                return None
        else:
            if (self.__computerToSwitch.has_key(portname)):
                return self.__computerToSwitch[portname]
            else:
                return None
    
    def getPortNameList(self,prot,seq,ln,payload):
        """\brief Implements the get_port_name_list rpc, replying with all the device names in the namespace that are configured 
        Other entries can be accessed by using the direct://switch:port interface
        \param payload - Nothing
        """
        payload = ""
        for i in self.__computerToSwitch.keys():
            payload = payload + i+"\n"
        prot.sendReply(200, seq, payload)    
        
    def setPortState(self,prot,seq,ln,payload):
        """\brief Implements the set_port_state rpc, setting the state of the port to the desired value 
        Other entries can be accessed by using the direct://switch:port interface
        \param payload Contains the name of the device and the desired state (poweron and poweroff are currently supported), separated by comma
        """
        try:
            (portname, state) = payload.split(",")
        except Exception,e:
            prot.handleError(404,seq,"Expected port,state")
            return
        
        (ret, msg) = self.setPortStateBackend(portname,state)
        
        prot.sendReply(ret,seq,msg)
        

    def setPortStateBackend(self, portname, state):
        #if (self.__configuredPortState.has_key(portname)):
        #   return (404,"Device "+portname+" is configured to be "+\
        # self.__configuredPortState[portname]+"; this is enforced "+\
        # "continuously; if you want to change this behavior please "+\
        # "edit the config files")

        toConfigure = self.getPortMapping(portname)

        if toConfigure==None:
            return (404,"Required port " + portname + "not present")
        else:
            if (state=="on"):
            #check to see if the switches won't be overloaded
                for (switchID,port) in toConfigure:
		    if self.__switchInstances.has_key(switchID):
			switch = self.__switchInstances[switchID]
		    else:
			switch = None

                    if (switch is None or port is None):
                        return (404,"Switch or port not configured properly")
                    else:
                        try:
                            max = switch.getPowerswitchNode().getAttributes()["amp_threshold"]
                            current = switch.getCurrent()
                            if (current>=max):
                                return (404,"Switch "+switch.getPowerswitchNode().getNodeID()+" has already reached its maximum power")
                        except Exception,e:
                            log.debug("Error while checking for current limit:"+str(e))

            for (switchID,port) in toConfigure:
		if self.__switchInstances.has_key(switchID):
			switch = self.__switchInstances[switchID]
		else:
			switch = None
                if (switch==None or port==None):
                    return (404,"Switch or port not configured properly")
                else:
                    if (state=="on"):
                        if (switch.status(port)=="off"):
                            switch.poweron(port)
                    elif (state=="off"):
                        if (switch.status(port)=="on"):
                            switch.poweroff(port)
                    elif state=="restart":
                        pass
                    else:
                        return (404,"Allowed actions for set_port_status are on, off and restart, you supplied: " + state)
    
                    return (200,"OK");
        
    
    def getPortState(self,prot,seq,ln,payload):
        """\brief Implements the get_port_state rpc by using getPortStateBackend to find switch status and replying with the values for the ports assigned to the specific device
        Other entries can be accessed by using the direct://switch:port interface
        \param payload Contains the name of the device or direct address
        """
        status = self.getPortStateBackend(payload)
        
        if (status!=None):
            prot.sendReply(200,seq,",".join(status));
        else:
            prot.handleError(404,seq,"Required port " + payload + " not present")

    def getPortStateBackend(self,device):
        """\brief Finds out the power state(s) of the given device by querying the proper switch(es)
        \param payload Contains the name of the device or direct address
        """
        toConfigure = self.getPortMapping(device)
        
        if (toConfigure!=None):
            state = []
            for (switchID,port) in toConfigure:
		if self.__switchInstances.has_key(switchID):
			switch = self.__switchInstances[switchID]
		else:
			switch = None

                if (switch==None or port==None):
                    log.error("Switch or port not configured properly")
                    continue
                else:
                    real_status = switch.status(port)
                    state.append(real_status)
                
            return state
        else:
            return None
        
    def checkDevicePower(self,device,power):
        status = self.getPortStateBackend(device)
        for s in status:
            if (s!=power):
                return 0
        return 1
        
    def getConfiguredPortState(self,prot,seq,ln,payload):
        """\brief Implements the get_conf_port_state rpc by return the local (cached) state of the switch, which is not necesarrily the same with the real state
        \param payload Contains the name of the device or direct address
        """
        if self.__configuredPortState.has_key(payload):
            state = self.__configuredPortState[payload]
            prot.sendReply(200,seq,state);
        else:
            prot.handleError(404,seq,"Required port " + payload + " not present in configured ports")

 
    def getSwitchNames(self,prot,seq,ln,payload):
        """\brief Implements the get_switch_list rpc, replying with all the switch names currently configured
        \param payload - Nothing
        """        
        payload = ""
        for i in self.__switch.keys():
            payload = payload + i+"\n"
        prot.sendReply(200, seq, payload)    
    
    def getPortToSwitch(self,prot,seq,ln,payload):
        """\brief Implements the get_port_to_switch rpc, replying with the switch a certain device belongs to
        \param payload - device name or direct identifier
        """        
        toConfigure = self.getPortMapping(payload)
        switch_names = ""

        if (toConfigure!=None):
            for (switchID,port) in toConfigure:
	    	if self.__switchInstances.has_key(switchID):
			switch = self.__switchInstances[switchID]
	    	else:
			switch = None

                if (switch==None or port==None):
                    prot.handleError(404,seq,"Switch or port not configured properly")
                    return
                else:
                    if (switch_names==""):
                        switch_names = switch.getPowerswitchNode().getNodeID()
                    else:
                        switch_names = switch_names+","+switch.getPowerswitchNode().getNodeID()
            prot.sendReply(200,seq,switch_names);
        else:
            prot.handleError(404,seq,"Required port " + payload + " not present")
    
    def getCurrent(self,prot,seq,ln,payload):
        """\brief Implements the get_current rpc
        \param payload - switch name
        Currently does nothing
        """        
        if (self.__switchInstances.has_key(payload)):
            try:
                prot.sendReply(200,seq,str(self.__switchInstances[payload].getCurrent()))
            except Exception,e:
                prot.handleError(404,seq,str(e))
        else:
            prot.handleError(404, seq, "Switch "+payload+ " does not exist")    

    def getConfigVersion(self,prot,seq,ln,payload):
        """\brief Implements the get_switch_list rpc, replying with all the switch names currently configured
        \param payload - Nothing
        """        
        prot.sendReply(200, seq, str(self.version))    

    def stopDaemon(self,prot,seq,ln,payload):
        """\brief Stops the daemon and all threads
        This method will first stop any more incoming queries, then wait for
        any update tasks to complete, before stopping itself.
        """
        log.debug("stopDaemon called.")
        prot.sendReply(200, seq, "Accepted stop request.")
        log.debug("Sending stopDaemon() response")
        self.acceptConnections(False)
        log.debug("Stopping power check timer")
        self.__power_check_timer.stop()
        log.debug("Stopping PowerDaemon (self)")
        self.stop()

    def startUpdateTimers(self):
        self.__power_check_timer = GracefulTimer(\
            string.atoi(self.__configFile.get('MAIN', 'POWER_CHECK_INTERVAL')),\
            self.checkPowerState, True)
        self.__power_check_timer.start()
        
class PowerDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    __bind_addr = DaemonLocations.powerDaemon[0]
    __port = DaemonLocations.powerDaemon[1]
    __sockd = None
    __powercontrol = None

    def __init__(self, doFork):
        Daemonizer.__init__(self, doFork)

    def run(self):
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        self.__sockd.settimeout(2) # 2 second timeouts
        log.debug("Creating PowerDaemon")
        self.__powercontrol = PowerControl()
        log.debug("Starting PowerDaemon")
        self.__powercontrol.startUpdateTimers()
        self.__powercontrol.start()
        while self.__powercontrol.isAlive():
            if self.__powercontrol.acceptingConnections():
                # allow timeout of accept() to avoid blocking a shutdown
                try:
                    (s,a) = self.__sockd.accept()
                    log.info("New connection established from " + str(a))
                    self.__powercontrol.addSocket(s)
                except:
                    pass
            else:
                log.debug(\
                      "PowerDaemon still alive, but not accepting connections")
                time.sleep(2)
        log.debug("Closing socket.")
        self.__sockd.shutdown(socket.SHUT_RDWR)
        self.__sockd.close()
        while threading.activeCount() > 1:
            cThreads = threading.enumerate()
            log.debug("Waiting on " + str(threading.activeCount()) + \
                      " active threads...")
            time.sleep(2)
        log.debug("PowerDaemon Finished.")
        # Now everything is dead, we can exit.
        sys.exit(0)

def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    WORKDIR = '/var/hen/powerdaemon'
    PIDDIR = '/var/run/hen'
    LOGDIR = '/var/log/hen/powerdaemon'
    LOGFILE = 'powerdaemon.log'
    PIDFILE = 'powerdaemon.pid'
    GID = 17477 # schooley
    UID = 17477 # schooley
    powerd = PowerDaemon(False) # False = no forking
    powerd.setWorkingDir(WORKDIR)
    powerd.setPIDDir(PIDDIR)
    powerd.setLogDir(LOGDIR)
    powerd.setLogFile(LOGFILE)
    powerd.setPidFile(PIDFILE)
    powerd.setUid(UID)
    powerd.setGid(GID)
    powerd.start()

if __name__ == "__main__":
    main()
