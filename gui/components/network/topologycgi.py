#!/usr/local/bin/python
import sys, os, xml.dom.minidom, commands, pydot
sys.path.append("/usr/local/hen/lib/")
os.environ['PATH'] = "/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin"

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

    def runQuery(self):
        self.__prot.open(HOST, PORT)
        method = "create_network_svg"
        payload = ""
        self.__prot.sendRequest(method,payload,self.handler)
        self.__prot.readAndProcess()

    def createSVG(self):
        print "Content-Type: image/svg+xml"
        print ""
        data = self.__payload
        if data == "":
            print "<svg width=\"885pt\" height=\"290pt\" viewBox = \"0 0 885 290\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\">"
             
            print "</svg>"
        else:
            print data
        

def main():
    topologyCGI = TopologyCGI()

if __name__ == "__main__":
    main()
