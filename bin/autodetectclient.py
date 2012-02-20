import socket, commands, time, os, re, sys, os
sys.path.append("/usr/local/hen/lib")
os.environ["PATH"] += ":/usr/local/bin:/usr/bin"
from henmanager import HenManager
from auxiliary.daemonports import DaemonPorts
from auxiliary.daemonlocations import DaemonLocations
import auxiliary.protocol

AUTONEGOTIATION_WAIT_TIME = 20
POLL_INTERFACE_INTERVAL = 1

class HardwareDetectionRunner:

    __prot = None
    __host = None
    __port = None
    __hm = None
    __interfaceNames = None
    __data = None

    def __init__(self, host, port):
        self.__prot = auxiliary.protocol.Protocol(None)
        self.__host = host
        self.__port = port
        self.__data = ""
        self.__hm = HenManager()

    def run(self):
        """\brief Runs all the necessary detection methods."""
        print "Running hardware detection:"
        print "\tRetrieving experimental interface names..."
        self.getExperimentalInterfacesNames()
        print "\tPolling interfaces..."
        self.pollInterfaces()
        # Sometimes mii-tool will report no link if this sleep time is not here
        print "Waiting " + str(AUTONEGOTIATION_WAIT_TIME) + \
                " seconds for autonegotiation to finish",
        self.waitForAutonegotiation()
        print "Retrieving number of processors..."
        self.getNumberProcessors()
        print "Retrieving number of cores..."
        self.getNumberCores()
        print "Retrieving no-carrier-sense MACs..."
        self.getNoCarrierMACs()
        print "Retrieving output from lshw..."
        self.getLSHWOutput()
        print "Polling interfaces once to seed fdb"
        self.pollInterfaces()
        print "Sending results to AutodetectDaemon... "
        self.sendData()
        print "Polling interfaces continually..."
        while 1:
            self.pollInterfaces()    
            time.sleep(POLL_INTERFACE_INTERVAL)

    def waitForAutonegotiation(self):
        """\brief Prints a dot per second whilst waiting for the number of
            seconds defined by AUTONEGOTIATION_WAIT_TIME
        """
        ticks = AUTONEGOTIATION_WAIT_TIME
        while ticks > 0:
            print '.',
            ticks -= 1
            time.sleep(1)

    def pollInterfaces(self):
        for interfaceName in self.__interfaceNames:
            cmd = "/sbin/ifconfig " + interfaceName + " up"
            os.system(cmd)
            cmd = "etherwake -i " + interfaceName + " 00:11:22:33:44:55"
            os.system(cmd)

    def getExperimentalInterfacesNames(self):
        # First create a list containing the mac addresses of all the interfaces
        macAddresses = []
        macAddressMatcher = re.compile('(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}')
        lines = commands.getstatusoutput("ifconfig -a")[1].splitlines()
        for line in lines:
            matchObject = macAddressMatcher.search(line)
            if (matchObject):
                macAddresses.append(\
                        line[matchObject.start():matchObject.end()].upper())

        # Find which of these is the management interface so we can filter it out
        nodes = self.__hm.getNodes("computer", "all")
        for node in nodes.values():
            managementMACAddress = \
                node.getInterfaces("management")[0].getMAC().upper()
            if (managementMACAddress in macAddresses):
                break

        self.__interfaceNames = []
        for macAddress in macAddresses:
            if (macAddress != managementMACAddress):
                # We need to convert the mac addresses to interface names
               self.__interfaceNames.append(commands.getstatusoutput(\
                                       "ifconfig -a | grep " + macAddress + \
                                       " | awk '{print $1}'")[1])

    def getNumberProcessors(self):
        data = commands.getstatusoutput(\
                "cat /proc/cpuinfo | grep 'physical id'")[1]
        data = data.split("\n")
        uniqueIDs = []
        for line in data:
            processorID = line[line.find(":") + 1:]
            if (processorID not in uniqueIDs):
                uniqueIDs.append(processorID)
        self.__data += "<numbercpus>%s</numbercpus>" % str(len(uniqueIDs))

    def getNumberCores(self):
        data = commands.getstatusoutput(\
                "cat /proc/cpuinfo | grep 'cpu cores'")[1]
        cores = 1
        try:
            data = data.split("\n")[0]
            cores =  int(data[data.find(":") + 1:])
        except:
            pass
        self.__data += "<numbercorespercpu>%s</numbercorespercpu>" % str(cores)

    def getNoCarrierMACs(self):
        self.__data += "<nocarriermacs>"
        data = commands.getstatusoutput("mii-tool")[1]
        data = data.split("\n")
        counter = 0
        for line in data:
            if (line.find("no link") != -1):
                ifaceName = line[:line.find(":")]
                data = commands.getstatusoutput(\
                            "ifconfig " + ifaceName)[1].split("\n")[0]
                macAddress = data[data.find("HWaddr") + 7:].strip()
                self.__data += str(macAddress).upper()
                counter += 1
                if (counter != len(noCarrierMACs)):
                    self.__data += ","
        self.__data += "</nocarriermacs>"

    def getLSHWOutput(self):
        self.__data += commands.getstatusoutput("/usr/sbin/lshw -xml")[1]

    def sendData(self):
        """\brief Connects to the autodetectdaemon and sends the data created
            by the detection code.
        """
        self.__prot.open(self.__host, self.__port)
        self.__prot.sendRequest("receive_detectiondata", \
                                self.__data, \
                                self.responseHandler)
        self.__prot.readAndProcess()

    def responseHandler(self,code,seq,size,payload):
        """\brief Handles the response from the autodetectdaemon. We can add
            code here for re-sending the data, if need be.
        """
        if code == 200:
            print "Data successfully received by AutodetectDaemon"
            self.__prot.close()
        else:
            print "ERROR: Received code[%s] from daemon. Payload = %s" % \
                (str(code), str(payload))

def main():
    HOST = DaemonLocations.autodetectDaemon[0]
    #HOST = "192.168.0.1"
    PORT = DaemonLocations.autodetectDaemon[1]
    hd = HardwareDetectionRunner(HOST, PORT)
    hd.run()

if __name__ == "__main__":
    main()
