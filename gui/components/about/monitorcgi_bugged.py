#!/usr/bin/env /usr/local/bin/python
import sys
sys.path.insert(0, "/usr/local/hen/lib")
import threading, time
from auxiliary.daemonstatus import DaemonStatus

THREAD_TIMEOUT = 10
STATUS_TIMEOUT = 5

class DaemonStatusChecker(threading.Thread):
    
    __checkMethod = None
    __stopEvent = None
    __doneEvent = None
    __daemonStatus = None
    __timeout = None
    
    def __init__(self, checkMethod, doneEvent, timeout=3):
        threading.Thread.__init__(self)
        self.__checkMethod = checkMethod
        self.__stopEvent = threading.Event()
        self.__doneEvent = doneEvent
        self.__timeout = timeout
    
    def run(self):
        self.__daemonStatus = self.__checkMethod(self.__timeout)
        self.__doneEvent.set()
        self.__stopEvent.wait(THREAD_TIMEOUT)
        
    def isOnline(self):
        self.__stopEvent.set()
        return self.__daemonStatus

class MonitorCGI:
    
    __stoppedDaemons = None
    __runningDaemons = None
    __checkerThreads = None
    __doneList = None
    
    def __init__(self):
        self.__stoppedDaemons = []
        self.__runningDaemons = []
        self.__checkerThreads = {}
        self.__doneList = []
        self.__createStatusThreads()
        self.__waitForResults()
        self.__collectResults()
        self.__printResults()

    def __collectResults(self):
        for daemon in self.__checkerThreads.keys():
            if self.__checkerThreads[daemon].isOnline():
                self.__runningDaemons.append(daemon)
            else:
                self.__stoppedDaemons.append(daemon)

    def __waitForResults(self):
        while 1:
            done = True
            for doneEvent in self.__doneList:
                if not doneEvent.isSet():
                    done = False
            if done:
                break

    def __createStatusThreads(self):
        for (daemon, method) in DaemonStatus().getAllDaemonStatusMethods():
            doneEvent = threading.Event()
            self.__checkerThreads[daemon] = \
                DaemonStatusChecker(method, doneEvent, STATUS_TIMEOUT)
            self.__checkerThreads[daemon].start()
            self.__doneList.append(doneEvent)
            

    def __printResults(self):
        """\brief Prints the results to stdout, in xml format."""

        print "Content-type: text/xml"
        print "Cache-Control: no-store, no-cache, must-revalidate\n\n"
        print "<processmanagement>"
        print "\t<running>"
        for daemon in self.__runningDaemons:
            print "\t\t<process name=\"%s\" />" % str(daemon)
        print "\t</running>"
        print "\t<stopped>"
        for daemon in self.__stoppedDaemons:
            print "\t\t<process name=\"%s\" />" % str(daemon)
        print "\t</stopped>"
        print "</processmanagement>"
        

def main():
    monitorCGI = MonitorCGI()

if __name__ == "__main__":
    main()
