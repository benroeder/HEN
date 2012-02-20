import socket
from auxiliary.timer import Timer
import threading, os, logging, time

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

class Switch_Port:
    def __init__(self,switch_id,port,trunk=False):
        self.switch_id = switch_id
        self.port = port
        self.trunk = trunk

    def setTrunk(self,state):
        self.trunk = state
        
    def getTrunk(self):
        return self.trunk

    def setPort(self,port):
        self.port = port
        
    def getPort(self):
        return self.port

    def setSwitchId(self,switch_id):
        self.switch_id = switch_id

    def getSwitchId(self):
        return self.switch_id

    def __str__(self):
        s = str(self.switch_id)+" "+str(self.getPort())
        if self.getTrunk():
            return s + " (trunk)"
        else:
            return s

class FDB_Port:
    def __init__(self,port,time):
        self.time = time
        self.port = port
        self.trunk = False

    def setTrunk(self,state):
        self.trunk = state

    def getTrunk(self):
        return self.trunk
        
    def setTime(self,time):
        self.time = time

    def getTime(self):
        return self.time
    
    def setPort(self,port):
        self.port = port

    def getPort(self):
        return self.port

    def __str__(self):
        s = str(self.port)
        if self.trunk:
            s = s + " (trunk)"
        s = s + " time "+str(self.time)
        return s

class FDB_Location:
    def __init__(self,switch_id,port,time=None):
        self.switch_id = switch_id
        self.ports = []
        self.ports.append(FDB_Port(port,time))

    def setTrunk(self,port):
        for p in self.ports:
            if p.getPort() == port:
                p.setTrunk(True)

    def setSwitchId(self,switch_id):
        self.switch_id = switch_id

    def getSwitchId(self):
        return self.switch_id

    def updatePort(self,port,time):
        for p in self.ports:
            if p.getPort() == port:
                p.setTime(time)
                return
        self.ports.append(FDB_Port(port,time))

    def getPort(self,port=None):
        if port == None:
            return self.ports
        else:
            for p in self.ports:
                if p.getPort() == port:
                    return p
        return None

    def addPort(self,port,time):
        self.ports.append(FDB_Port(port,time))

    def __str__(self):
        s = str(self.switch_id)
        for i in self.ports:
            s = s +" "+ str(i)
        return s
    
class FDB_Entry:
    def __init__(self,mac,switch=None,port=None,time=None):
        self.mac = mac.upper()
        self.device_id = None
        self.interface_id = None
        self.location = {}
        if (switch != None and port != None and time != None):
            self.location[switch] = FDB_Location(switch,port,time)

    def setMac(self,mac):
        self.mac = mac

    def getMac(self):
        return self.mac

    def setDevice(self,device_id):
        self.device_id = device_id

    def getDevice(self):
        return self.device_id

    def setInterfaceID(self,interface_id):
        self.interface_id = interface_id

    def getInterfaceID(self):
        return self.interface_id

    def updateLocation(self,switch_id,port,time):
        if (self.getLocation(switch_id) == None):
            self.location[switch_id] = FDB_Location(switch_id,port,time)
        else:
            if (self.location[switch_id].getPort(port) == None):
                self.location[switch_id].addPort(port,time)
            else:
                self.location[switch_id].updatePort(port,time)

    def getLocations(self):
        return self.location
                                        
    def getLocation(self,switch_id=None):
        if self.location.has_key(switch_id):
            return self.location[switch_id]
        else:
            return None
        
    def setLocation(self,switch_id,port,time):
        if (self.getLocation(switch_id) == None):
            self.location[switch_id] = FDB_Location(switch_id,port,time)
        else:
            self.location[switch_id].setPort(port)

    def setTrunk(self,switch_id,port):
        self.location[switch_id].setTrunk(port)
            
    def __str__(self):
        s = "mac "+str(self.mac)
        if self.device_id != None:
            s = s + " device id "+self.device_id
            if self.interface_id != None:
                s = s + " interface id "+self.interface_id
        for l in self.location.values():
            s = s + "\n\t"+str(l)
        s = s + "\n"
        return s
            
class SwitchDB:
    __update_lock = threading.Lock()
    
    def __init__(self,hen_manager):
        log.debug("SwitchDB created")
        self.fdb = {}
        self.switch_ports = {}
        self.links = []
        self.switches = []
        self.__hen_manager = hen_manager
        # load switches
        self.loadSwitches()
        # load links
        self.loadLinks()
        
    def loadLinks(self):
        log.debug("loading links")
        self.links = self.__hen_manager.getLinks("all","all")
        for linktype in self.links.values():
            for link in linktype.values():
                for member in link.getLinkMembers():
                    log.debug("got port, set it to trunk"+str(member))
                    #if member.getDeviceId() == "switch10":
                    try:
                        
                        self.switch_ports[member.getDeviceId()][str(member.getDevicePort())].setTrunk(True)
                        self.switch_ports[member.getDeviceId()][str(member.getDevicePort())].setSwitchId(member.getDeviceId())
                        self.switch_ports[member.getDeviceId()][str(member.getDevicePort())].setPort(member.getDevicePort())
                    except Exception,e :
                        print "Unknown port "+str(e)
        #for switch in self.switch_ports.values():
        #    for p in switch.values():
        #        print p
            
    def loadSwitches(self):
        log.debug("loading switches")
        self.switches = self.__hen_manager.getNodes("switch","operational")
        for switch in self.switches.values():
            #log.debug("getting switch information for "+str(switch))
            try:
                swi = switch.getInstance()
            except Exception, e:
                log.debug("error getting switch instance")
                log.debug(e)
                continue
            
            #if(swi.getSwitchName() == "switch10"):
            
            log.debug("running on "+str(swi.getSwitchName()))
            if ((swi.getSwitchName() == "switch14") or (swi.getSwitchName() == "switch6")):
                ports=swi.getPortNames()
            else:
                ports=swi.getPortIDs()
            name = swi.getSwitchName()
            self.switch_ports[name] = {}
            try:
                for p in ports:        
                    self.switch_ports[name][str(p[0][1])] = Switch_Port(name,str(p[0][1]))
                #log.debug("adding port "+str(p[0][1]))
            except Exception, e:
                print "loadSwitches error :"+str(e)
                pass

            for switch in self.switch_ports.values():
                print p
            
       
    def addFDB(self,switch_id,fdb):
        self.__update_lock.acquire()
        log.debug("adding fdb from "+str(switch_id))
        current_time = time.time()
        for mac_entry in fdb:
            log.debug("trying to add "+str(mac_entry))
            if self.fdb.has_key(mac_entry.getMAC()):
                self.fdb[mac_entry.getMAC()].updateLocation(mac_entry.getSwitch(),mac_entry.getPort(),current_time)
            else:
                self.fdb[mac_entry.getMAC()] = FDB_Entry(mac_entry.getMAC(),mac_entry.getSwitch(),mac_entry.getPort(),current_time)
                
                obj = self.__get_device_id(mac_entry.getMAC())
                self.fdb[mac_entry.getMAC()].setDevice(obj[0])
                self.fdb[mac_entry.getMAC()].setInterfaceID(obj[1])

            if (self.isTrunk(mac_entry.getSwitch(),mac_entry.getPort())):
                print "FOUND TRUNK"
                self.fdb[mac_entry.getMAC()].setTrunk(mac_entry.getSwitch(),mac_entry.getPort())
        self.__update_lock.release()
        log.debug("finished adding fdb from "+str(switch_id))

    def isTrunk(self,switch,port):
        try:
            for p in self.switch_ports.values():
                for pp in p.values():
                    if ((str(pp.getSwitchId()) == str(switch)) and (str(pp.getPort()) == str(port))): 
                        return pp.getTrunk()
                    elif ((str(pp.getSwitchId()) == "switch6") and (str(switch) == "switch6")):
                        print "pp is "+str(pp)+" port "+str(port)
        except Exception, e:
            print "isTrunk exception "+e
            pass
        return False
    
    def findMAC(self,mac):
        log.debug("looking for "+str(mac))
        s = ""
        if self.fdb.has_key(mac.upper()):
            fdb_entry = self.fdb[mac.upper()]
            locations = fdb_entry.getLocations()
            for location in locations.values():
                s = s + str(location.getSwitchId())
                for port in location.getPort():
                    s = s + " " + str(port.getPort())
                    if port.getTrunk():
                        s = s + "(T)"
                s = " "
            return s
        else:
            return "unknown"

    def findUniqueMACs(self, macs):
        """\brief Uses the switches' dabatabases to discover which ports interfaces are plugged into
        \param macs (\c list of strings) The macs of the interfaces to discover
        \return (\c dictionary of string,string tuples) A dictionary whose keys are the mac addresses,
                and whose values are tuples consisting of the switch id and the port name.
        """
        result = {}
        for m in macs:
            mac = m.upper()
            try:
                if self.fdb.has_key(mac):
                    print "found mac "+mac
                    for location in self.fdb[mac].getLocations().values():
                        for port in location.getPort():
                            if port.getTrunk() == False:
                                result[mac] = (location.getSwitchId(),port.getPort())
                            else:
                                print "we think this is a trunk",mac,location
                else:
                    print "did not find mac "+mac
                    result[mac] = ("unknown","unknown")
            except Exception, e:
                print "exception stuff"+str(e)
                pass
        #result["00:11:22:33:44:55"] = ("switch13", "GigabitEthernet 2/13")
        #result["00:11:22:33:44:66"] = ("switch1", "GigabitEthernet 2/13")
        #result["00:11:22:33:44:77"] = ("switch2", "GigabitEthernet 2/13")

        return result
    
    def showMACs(self):
        s = ""
        for mac_entry in self.fdb.keys():
            s = s + " " + str(mac_entry)
        return s

    def showBlackList(self):
        s = ""
        for mac_list in self.__portsBlackList.values():
                for mac_entry in mac_list:
                    s = s + " "+ str(mac_entry)
        return s

    def __str__(self):
        s = "Switch DB"
        for i in self.fdb.values():
            s = s + str(i)
        return s

    def __get_device_id(self,mac):
        try:
            nodes_dict = self.__hen_manager.getNodes("all","all")
        except Exception, e:
            print "trouble getting nodes"

        for nodetype in nodes_dict:
            for node in nodes_dict[nodetype].values():
                try:
                    interface_dict = node.getInterfaces()
                    for interface_type in interface_dict:
                        if interface_dict[interface_type] != None :
                            for interface in interface_dict[interface_type]:
                                if (str(interface.getMAC().upper().strip()) == str(mac.upper().strip())):
                                    
                                    return [node.getNodeID(),interface.getInterfaceID()]
                except Exception, e:
                    print "oops"+str(e)
        return [None,None]
