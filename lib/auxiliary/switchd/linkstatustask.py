import threading, logging, time, commands
from henmanager import HenManager

# length of time a worker thread will sleep before checking for work
LINK_STATUS_SLEEP_TIME = 2

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

class LinkStatusTask(threading.Thread):
    __linkid = None
    __link = None
    __hm = None
    __switchdb = None
    __newlink = None
    __stop = None

    def __init__(self, linkid, link, hm, swdb, doneEvent):
        threading.Thread.__init__(self)
        self.__linkid = linkid
        self.__link = link
        self.__hm = hm
        self.__switchdb = swdb
        self.__workdone = doneEvent
        self.__stop = threading.Event()

    def __del__(self):
        del self.__linkid
        del self.__link
        del self.__hm
        if self.__newlink:
            del self.__newlink

    def __checkPortState(self,switch_id,port):
        try:
            switch = None
            switch_nodes = self.__hm.getNodes("switch","all")
            for snk in switch_nodes.keys():
                if snk == switch_id:
                    switch = switch_nodes[snk].getInstance()
                    if not self.__switchdb.getHostStatus(switch_id):
                        log.critical(str(switch_id)+" not reachable.")
                        return False
            if switch == None:
                log.critical(str(switch_id)+" not found.")
                return False
            state = switch.getPortStatus(port)
            if (state == 1):
                log.debug("Port state : up "+str(switch_id)+" "+str(port))
                return True
            else:
                log.debug("Port state : down "+str(switch_id)+" "+str(port))
                return False
        except Exception,e:
            log.critical("Error getting port state for "+str(switch_id)+"\n")
            
        log.debug("Port state : UNKNOWN "+str(switch_id)+" "+str(port))
        return False
            
    def run(self):
        try:
            log.debug("link "+str(self.__link))
            link_up = True
            for i in range(0,len(self.__link[2])):
                (switch,port,up) = (self.__link[2])[i]
                up = self.__checkPortState(switch,port)
                self.__link[2][i] = (switch,port,up)
                if not up:
                    link_up = False
            self.__newlink = (self.__link[0],link_up,self.__link[2])
            #log.debug(str(self.__switchMacTable))
        except Exception, e:
            log.debug(str(e))
        self.__workdone.set()
        while not self.__stop.isSet():
            self.__stop.wait(LINK_STATUS_SLEEP_TIME)

    def getLinkState(self):
        self.__stop.set()
        return self.__newlink
