#!/usr/local/bin/python
import sys, os, xml.dom.minidom, commands, pydot
#sys.path.append("/usr/local/hen/lib/")
#os.environ['PATH'] = "/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin"

import auxiliary.protocol
from henmanager import HenManager
from auxiliary.switchdb import SwitchDB
from auxiliary.daemonstatus import DaemonStatus
from auxiliary.daemonlocations import DaemonLocations

HOST = DaemonLocations.switchDaemon[0]
PORT = DaemonLocations.switchDaemon[1]

class TopologyCGI:
    
    __prot = None
    __switchStatuses = None
    
    def __init__(self):
        #self.__switchStatuses = {}
        self.__payload = ""
        self.__prot = auxiliary.protocol.Protocol(None)
        if DaemonStatus().switchDaemonIsOnline(3):
            self.runQuery()
        self.createSVG()
    
    def handler(self,code,seq,sz,payload):
        if code != 200:
            print "Error from switchdaemon: code[%s], payload[%s]" % \
                    (str(code), str(payload))
            return
        self.__payload = payload
        # Parse the XML data
        #status_dom = xml.dom.minidom.parseString(payload)
        #statuses = status_dom.getElementsByTagName("nodestatus")
        #for nodestatus in statuses:
        #    nodeid = str(nodestatus.attributes["id"].value)
        #    status = int(nodestatus.attributes["status"].value)
        #    if nodeid.startswith("switch"):
        #        self.__switchStatuses[nodeid] = status
        #status_dom.unlink()
        

    def runQuery(self):
        self.__prot.open(HOST, PORT)
        method = "create_network_svg"
        payload = ""
        self.__prot.sendRequest(method,payload,self.handler)
        self.__prot.readAndProcess()

    def createSVG(self):
        print "Content-Type: image/svg+xml"
        print ""
        print self.__payload
        
    def old(self):
        BASE_URL="cgi-bin/gui/components/network/"
        
        manager = HenManager()
        manager.initLogging()
        
        links = manager.getLinks("all","all")
        graph = pydot.Dot()
    
        switches = manager.getNodes("switch")
        for switch in switches.values():
            if self.__switchStatuses.has_key(switch.getNodeID()):
                if self.__switchStatuses[switch.getNodeID()] == 1:
                    graph.add_node(pydot.Node(switch.getNodeID(),URL=BASE_URL+\
                      "switchinfocgi.py?id="+switch.getNodeID(),\
                      style="filled",color="chartreuse1"))
                else:
                    graph.add_node(pydot.Node(switch.getNodeID(),URL=BASE_URL+\
                      "switchinfocgi.py?id="+switch.getNodeID(),\
                      style="filled",color="firebrick"))
            else:
                graph.add_node(pydot.Node(switch.getNodeID(),URL=BASE_URL+\
                                  "switchinfocgi.py?id="+switch.getNodeID()))
        for linktype in links.values():
            for link in linktype.values():
                members = link.getLinkMembers()
                
                graph.add_edge(pydot.Edge(str(members[0].getDeviceId()),\
                  str(members[1].getDeviceId()),label=link.getLinkId(),\
                  arrowhead="none",headlabel=str(members[1].getDevicePort().\
                  replace('GigabitEthernet ','').replace('Management','M')),\
                  taillabel=str(members[0].getDevicePort().\
                  replace('GigabitEthernet','')),fontsize=8,\
                  tooltip=link.getLinkId(),\
                  URL=BASE_URL+"linkinfocgi.py?id="+link.getLinkId()))
    
        # prog='circo' isn't bad
        print graph.create_svg(prog='dot')

def main():
    topologyCGI = TopologyCGI()

if __name__ == "__main__":
    main()
