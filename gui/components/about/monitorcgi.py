#!/usr/bin/env /usr/local/bin/python
import sys
sys.path.insert(0, "/usr/local/hen/lib")
import cgi
import auxiliary.protocol
from auxiliary.daemonstatus import DaemonStatus
from auxiliary.daemonlocations import DaemonLocations

HOST = DaemonLocations.henstatusDaemon[0]
PORT = DaemonLocations.henstatusDaemon[1]

class HenStatusCGI:

    __prot = None

    def __init__(self):
        self.__prot = auxiliary.protocol.Protocol(None)
        if DaemonStatus().henStatusDaemonIsOnline(3):
            self.runQuery()
        else:
            self.__printNothing()

    def handler(self,code,seq,sz,payload):
            if code != 200:
                self.__printNothing()
            else:
                print payload

    def __printNothing(self):
        print "Content-type: text/xml"
        print "Cache-Control: no-store, no-cache, must-revalidate\n\n"
        print "<processmanagement>"
        print "<\processmanagement>"

    def runQuery(self):
        self.__prot.open(HOST, PORT)
        method = "get_henstatus"
        payload = ""
        self.__prot.sendRequest(method,payload,self.handler)
        self.__prot.readAndProcess()

def main():
    henstatusQuery = HenStatusCGI()

if __name__ == "__main__":
    main()
