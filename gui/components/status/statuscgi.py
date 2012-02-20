#!/usr/bin/env /usr/local/bin/python
import sys
sys.path.insert(0, "/usr/local/hen/lib")
import cgi
import auxiliary.protocol
from auxiliary.daemonstatus import DaemonStatus
from auxiliary.daemonlocations import DaemonLocations

HOST = DaemonLocations.monitorDaemon[0]
PORT = DaemonLocations.monitorDaemon[1]

class StatusCGI:

    __stage = 0
    __prot = None

    def __init__(self):
        self.__prot = auxiliary.protocol.Protocol(None)
        if DaemonStatus().monitorDaemonIsOnline(3):
            self.runQuery()
        else:
            print "Content-type: text/xml"
            print "Cache-Control: no-store, no-cache, must-revalidate\n\n"
            print "<henstatus>"
            print "<\henstatus>"

    def handler(self,code,seq,sz,payload):
        if self.__stage == 0:
            print "Content-type: text/xml"
            print "Cache-Control: no-store, no-cache, must-revalidate\n\n"
            print "<henstatus>"
        if code == 200:
            print payload
        self.__stage += 1
        if self.__stage == 2:
            print "</henstatus>"

    def runQuery(self):
        self.__prot.open(HOST, PORT)
        method = "get_hoststatuses"
        payload = ""
        self.__prot.sendRequest(method,payload,self.handler)
        self.__prot.readAndProcess()
        method = "get_currentsensorreadings"
        payload = ""
        self.__prot.sendRequest(method,payload,self.handler)
        self.__prot.readAndProcess()

def main():
    statusQuery = StatusCGI()

if __name__ == "__main__":
    main()
