#!/usr/bin/env /usr/local/bin/python
import sys, time, xml.dom.minidom, random, commands, os
sys.path.insert(0, "/usr/local/hen/lib")
os.environ['PATH'] = "/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin"
import cgi
import auxiliary.protocol
from auxiliary.daemonstatus import DaemonStatus
from auxiliary.daemonlocations import DaemonLocations

import cgitb; cgitb.enable()

HOST = DaemonLocations.monitorDaemon[0]
PORT = DaemonLocations.monitorDaemon[1]

class SensorPlotCGI:

    __prot = None
    __form = None
    __nodeid = None
    __sensorid = None
    __timerange = None

    __error = None

    def __init__(self):
        self.__error = ""
        self.__prot = auxiliary.protocol.Protocol(None)
        self.__form = cgi.FieldStorage()
        self.__getAndCheckFormFields()
        if DaemonStatus().monitorDaemonIsOnline(3):
            self.__runQuery()
        else:
            print "Content-type: text/html\n\n"
            print "MonitorDaemonIsOffline"

    def handler(self,code,seq,sz,payload):
        print "Content-type: text/html\n\n"
        if code != 200:
            print 'makesensorgraph.py: handler received bad code. ' + \
                'Payload is: ' + str(payload)
            return
        #print "<img src=\"%s\" />" % str(payload)
        print str(payload)

    def __runQuery(self):
        self.__checkForErrors()
        self.__prot.open(HOST, PORT)
        method = "get_nodesensorgraph"
        payload = "%s %s %s" % \
            (str(self.__nodeid), str(self.__sensorid), str(self.__timerange))
        self.__prot.sendRequest(method,payload,self.handler)
        self.__prot.readAndProcess()

    def __checkForErrors(self):
        if self.__error:
           print "Content-type: text/html\n"
           print 'makesensorgraph.py: errors: %s' % self.__error
           sys.exit(-1)

    def __getAndCheckFormFields(self):
        """\brief Retrieves form fields.
        """
        if self.__form.has_key('nodeid'):
            self.__nodeid = self.__form['nodeid'].value
        else:
            self.__error += "nodeid not passed as field value\n"
        if self.__form.has_key('sensorid'):
            self.__sensorid = self.__form['sensorid'].value
        else:
            self.__error += "sensorid not passed as field value\n"
        if self.__form.has_key('timerange'):
            self.__timerange = int(self.__form['timerange'].value)
        else:
            self.__error += "timerange not passed as field value\n"

def main():
    sensorPlotQuery = SensorPlotCGI()

if __name__ == "__main__":
    main()
