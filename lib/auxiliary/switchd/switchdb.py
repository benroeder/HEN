from auxiliary.timer import GracefulTimer
from hardware.device import Device
import threading
import os
import logging
import commands
import time
import datetime
import pydot
import sys, traceback


logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# The maximum number of writes held in memory before a flush must be invoked.
MAX_Q_SIZE = 100
# The number of seconds between automatic flushes.
AUTO_FLUSH_TIME = 10
# The maximum number of sensor readings to keep in memory for trend analysis.
MAX_SENSOR_HISTORY = 5

COMPRESS_COMMAND = '/usr/bin/gzip '
MOVE_COMMAND = '/bin/mv '

class SwitchDB:
    HOSTONLINE = 1
    HOSTOFFLINE = 0

    __hm = None
    __db_dir = None
    __status_lock = None
    __flush_lock = None
    __update_lock = None
    __writebuf_lock = None
    __open_file_lock = None
    __writes_since_flush = None
    __node_fds = None
    __node_locks = None
    __write_buf = None
    __flush_timer = None
    # history format: {nodeid:{sensorid:[(type, time, val, status),..],..},..}
    __sensor_history = None
    __sensor_max = None

    # fdb format: {mac:(name,{(nodeid,port):[trunk,time]}
    __fdb = None
    # links format :
    __links = None
    __links_map_lock = None
    __links_map = None
    #
    __graph = None
    
    # host status dictionary. Format: {nodeid:status, ...}
    #        Where status is: 0 = OK, 1 = OFFLINE
    __host_status = None

    def __init__(self):
        self.__writes_since_flush = 0
        self.__status_lock = threading.RLock()
        self.__flush_lock = threading.RLock()
        self.__update_lock = threading.RLock()
        self.__writebuf_lock = threading.RLock()
        self.__open_file_lock = threading.RLock()
        self.__links_map_lock = threading.RLock()
        self.__node_fds = {}
        self.__node_locks = {}
        self.__write_buf = {}
        self.__sensor_history = {}
        self.__sensor_max = {}
        self.__fdb = {}
        self.__links = {}
        self.__graph = None
        self.__host_status = {}

    def setHenManager(self,hm):
        self.__hm = hm

    def getStorageStats(self):
        stats = {}
        stats["__sensor_history length"] = len(self.__sensor_history)
        histCount = 0
        for sensorDict in self.__sensor_history.values():
            histCount += len(sensorDict.keys())
        stats["Total history entries"] = histCount
        stats["__sensor_max length"] = len(self.__sensor_max)
        stats["__write_buf length"] = len(self.__write_buf)
        stats["__host_status length"] = len(self.__host_status)
        stats["__node_locks length"] = len(self.__node_locks)
        stats["__node_fds length"] = len(self.__node_fds)
        stats["__writes_since_flush"] = self.__writes_since_flush
        return stats

    def startTimer(self):
        log.debug("SwitchDB: Starting flush timer")
        self.__flush_timer = GracefulTimer(AUTO_FLUSH_TIME, self.flushWrites)
        self.__flush_timer.start()

    def stopTimer(self):
        """\brief Stop the write flush timer.
        """
        log.debug("SwitchDB: stopping flush timer")
        self.__flush_timer.stop()
        self.flushWrites()

    def locateMac(self,m,unique=False):
        mac = m.upper()
        if self.__fdb.has_key(mac):
            res = []  
            for i in self.__fdb[mac][1]:
                if unique:
                    if self.__fdb[mac][1][i][0] == False:
                        res.append(i)
                else:
                    res.append(i)
            if unique:
                if (len(res) == 1):
                    return res
                else:
                    return None
            else:
                return res
        return None

    def setDBDirectory(self, dbDir):
        if len(dbDir) <= 0:
            log.critical("setDBDirectory(): No directory provided, using \"/\"")
            dbDir = "/"
        if dbDir[len(dbDir) - 1] != "/":
            dbDir = dbDir + "/"
        log.debug("setDBDirectory(): Creating dir [" + dbDir + "]")
        if not os.path.exists(dbDir):
            os.mkdir(dbDir)
        log.info("SwitchDB: Using DB directory [" + dbDir + "]")
        self.__db_dir = dbDir

    def setHostStatus(self, nodeid, status):
        self.__status_lock.acquire()
        self.__host_status[nodeid] = status
        self.__status_lock.release()

    def getHostStatus(self, nodeid):
        if self.__host_status.has_key(nodeid):
            return self.__host_status[nodeid]
        else:
            return -1

    def getHostStatuses(self):
        return self.__host_status

    def getHostHistory(self, nodeid):
        history = {}
        if self.__sensor_history.has_key(nodeid):
            return str(self.__sensor_history[nodeid])

    def getLinks(self):
        return self.__links

    def fromMacGetId(self,mac):
        if self.__hm == None:
            log.critical("HM not set in switchdb")
            return None
        try:
            nodes_dict = self.__hm.getNodes("all","all")
        except:
            log.critical("Unable to get nodes from hm")
            return None
        for nodetype in nodes_dict:
            for node in nodes_dict[nodetype].values():
                interface_dict = node.getInterfaces()
                for interface_type in interface_dict:
                    if interface_dict[interface_type] != None :
                        for interface in interface_dict[interface_type]:
                            if (str(interface.getMAC().upper().strip()) == str(mac.upper().strip())):
                                return (node.getNodeID(),interface.getInterfaceID())
        return None #("unknown","unknown")

    def isExternal(self,switch,port):
        # fix this
        #return False
        if self.__links == None:
            return False
        for link in self.__links.values():
            if link[0] != "external":
                continue
            try:
                for member in link[2]:
                    #if switch == "switch10":
                    #    log.debug("SWITCH10 "+str((member,switch,port)))
                    if ((str(switch) == str(member[0])) and (str(port) == str(member[1]))):
                        return True
                    return False
            except Exception, e:
                print "error in isExternal ",e
                traceback.print_exc(file=sys.stdout)
                return False

    def isLink(self,switch,port):
        # fix this
        #return False
        if self.__links == None:
            return False
        for link in self.__links.values():
            for member in link[2]:
                #if switch == "switch10":                    
                #    log.debug("SWITCH10 "+str((member,switch,port))) 
                if ((str(switch) == str(member[0])) and (str(port) == str(member[1]))):
                    return True
        return False

    def writeFdbEntry(self,nodeid,mac,port,time):
        self.__update_lock.acquire()
        if not self.__fdb.has_key(mac):
            self.__fdb[mac] = (self.fromMacGetId(mac),{})
        if (self.__fdb[mac][1]).has_key((nodeid,port)):
            del (self.__fdb[mac][1])[(nodeid,port)]
        
        if (self.isExternal(nodeid,port) != True):
            (self.__fdb[mac][1])[(nodeid,port)] = (self.isLink(nodeid,port),time)
        if (len(self.__fdb[mac][1]) == 0):
            del self.__fdb[mac]
        self.__update_lock.release()

    def cleanFdb(self,timeout=300):
        self.__update_lock.acquire()
        log.debug("Running fdb clean up")
        old_time = time.time() - timeout
        # remove all items created more than timeout seconds ago
        for mac in self.__fdb.keys():
            if self.__fdb[mac][0] != None:
                if (self.__fdb[mac][0][1]) != None :
                    for (switch,port) in (self.__fdb[mac][1].keys()):
                        if (self.__fdb[mac][1])[(switch,port)][1] < old_time:
                            log.debug("timing out port entry")
                            del (self.__fdb[mac][1])[(switch,port)]
                    if len(self.__fdb[mac][1]) == 0:
                        log.debug("timing out mac entry "+mac)
                        del self.__fdb[mac]
        log.debug("Finished fdb clean up")
        self.__update_lock.release()
                        
    def loadLinksDb(self):
        if self.__hm == None:
            log.critical("HM not set in switchdb")
            return False
        try:
            links = self.__hm.getLinks("all","all")
        except:
            log.critical("Unable to get links from hm")
            return False
        log.debug("Loading links")
        for linktype in links.values():
            for link in linktype.values():
                self.__links[link.getLinkId()] = (link.getLinkType(),None,[])
                
                for member in link.getLinkMembers():
                    (self.__links[link.getLinkId()])[2].append((member.getDeviceId(),member.getDevicePort(),False))
                log.debug(self.__links[link.getLinkId()])
        #self.__createNetworkSvg()

    def setLink(self,linkid,link):
        self.__links[linkid] = link
        #self.__createNetworkSvg()
        #self.dumpLinkdb()
        
    def dumpLinkdb(self):
        s = "links db\n"
        for link_id in self.__links.keys():
            s = s + str(self.__links[link_id])+"\n"
        log.debug(s)
        #return s
        
    def dumpFdb(self,unique=False):
        s = "switchdb fdb\n"
        for mac in self.__fdb.keys():
            s = s + str(mac)
            if self.__fdb[mac][0] != None:
                s = s + " "+str(self.__fdb[mac][0][0])
                if (self.__fdb[mac][0][1]) != None :
                    s = s + "."+str(self.__fdb[mac][0][1])
            for (switch,port) in (self.__fdb[mac][1].keys()):
                if unique:
                    if not (self.__fdb[mac][1])[(switch,port)][0]:
                        s = s + " ("+str(switch)+"."+str(port)+")"
                else:
                    if not (self.__fdb[mac][1])[(switch,port)][0]:
                        s = s + " ("+str(switch)+"."+str(port)+")"
                    else:
                        s = s + " ("+str(switch)+"."+str(port)+"(T))"
            s = s +"\n"
            log.debug(s)
        return s

    def createNetworkSvg(self):
        self.__links_map_lock.acquire()    
        _map = self.__links_map
        if _map == None:
            _map = "<svg></svg>"
        self.__links_map_lock.release()
        return _map

    def networkMapGeneration(self):
        nm = "digraph G {\n"
        #add external connection
        nm += "external";
        
        nm += "}\n"
        self.__links_map_lock.acquire()
        try:
            self.__links_map = commands.getstatusoutput("dot -Tsvg < "+str(nm))[0]
            
        except:
            log.critical("Error creating network map")
            pass
        self.__links_map_lock.release()
        return
    
    def OldnetworkMapGeneration(self):
        # each call to pydot is leaking about 1M, damn
        #return
        if self.__graph == None:
            self.__graph = pydot.Dot()
        # special node to reperesent external connection
        self.__graph.add_node(pydot.Node("external"))
        BASE_URL="cgi-bin/gui/components/network/"
        
        for hostid in self.__host_status.keys():
            if self.__host_status[hostid] == SwitchDB.HOSTONLINE:
                self.__graph.add_node(pydot.Node(hostid,URL=BASE_URL+\
                                          "switchinfocgi.py?id="+hostid,\
                                          style="filled",color="chartreuse1"))
            else:
                self.__graph.add_node(pydot.Node(hostid,URL=BASE_URL+\
                                          "switchinfocgi.py?id="+hostid,\
                                          style="filled",color="firebrick"))
                
        for linkid in self.__links.keys():
            (s1,p1,u1) = (None,None,None)
            (s2,p2,u2) = (None,None,None)
            c = "black"
            if self.__links[linkid][0] == "external":
                # ignore external links for now
                (s1,p1,u1) = self.__links[linkid][2][0]
                (s2,p2,u2) = ("external"," ",True)
                
            elif self.__links[linkid][0] == "direct":
                (s1,p1,u1) = self.__links[linkid][2][0]
                (s2,p2,u2) = self.__links[linkid][2][1]
            else:
                continue

            
            if self.__links[linkid][1] == True:
                c = "black"
            else:
                c = "red"
                
            p1 = p1.replace('GigabitEthernet ','')
            p1 = p1.replace('ManagementEthernet','M')
            p2 = p2.replace('GigabitEthernet ','')
            p2 = p2.replace('ManagementEthernet','M')

            if u1 == False:
                p1 = "down "+p1
            if u2 == False:
                p2 = "down "+p2
            e = pydot.Edge(s1,\
                           s2,\
                           label=linkid,\
                           arrowhead="none",\
                           headlabel=p2,\
                           taillabel=p1,\
                           color=c,\
                           fontsize=8,\
                           tooltip=linkid,\
                           URL=BASE_URL+"linkinfocgi.py?id="+linkid)
            self.__graph.add_edge(e)
                
            
        self.__links_map_lock.acquire()        
        try:
            self.__links_map = str(self.__graph.create_svg(prog='dot'))
            print str(self.__graph.to_string())
        except:
            log.critical("Error creating network map")
            pass
        del(self.__graph)
        self.__links_map_lock.release()

    def dumpUnknownFdb(self):
        for mac in self.__fdb.keys():
            s = "Unknown : "+str(mac)
            if self.__fdb[mac][0] != None:
                continue
            for (switch,port) in (self.__fdb[mac][1].keys()):
                s = s + " ("+str(switch)+"."+str(port)+")"
            log.debug(s)
    
            
    def flushWrites(self):
        """\brief Flush any writes to disk.
        """
        #log.debug("flushWrites(): Acquiring update lock.")
        self.__update_lock.acquire()
        #log.debug("flushWrites() has update lock.")
        if self.__writes_since_flush > 0:
            #log.debug("flushWrites(): Acquiring file locks.")
            for fileLock in self.__node_locks.values():
                fileLock.acquire()
            log.debug("flushWrites(): Flushing write buffers")
            for nodeid in self.__node_fds.keys():
                nodefd = self.__node_fds[nodeid]
                while len(self.__write_buf[nodeid]) > 0:
                    writeStr = self.__write_buf[nodeid].pop(0)
                    os.write(nodefd, writeStr)
            self.__writes_since_flush = 0
            #log.debug("flushWrites(): Releasing file locks.")
            for fileLock in self.__node_locks.values():
                fileLock.release()
        #log.debug("flushWrites(): Releasing update lock.")
        self.__update_lock.release()
        #log.debug("flushWrites() releases update lock.")        
