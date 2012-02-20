#! /usr/bin/python

import commands, time, threading

class NetworkInterface:

    def __init__(self, ipAddress=None, hostname=None, ifaceName=None):
        self.__ipAddress = ipAddress
        self.__hostname = hostname
        self.__ifaceName = ifaceName

    def getIPAddress(self):
        return self.__ipAddress

    def setIPAddress(self, ipAddress):
        self.__ipAddress = ipAddress

    def getHostname(self):
        return self.__hostname

    def setHostname(self, hostname):
        self.__hostname = hostname

    def getIfaceName(self):
        return self.__ifaceName

    def setIfaceName(self, ifaceName):
        self.__ifaceName = ifaceName

    def __str__(self):
        return str(self.getIPAddress()) + " " + str(self.getHostname()) + " " + str(self.getIfaceName())

    
class ThreadedNetperfClient(threading.Thread):

    def __init__(self, command, threadNumber=None):
        self.__threadNumber = threadNumber
        self.__command = command
        
        threading.Thread.__init__(self)

    def getThreadNumber(self):
        return self.__threadNumber

    def setThreadNumber(self, threadNumber):
        self.__threadNumber = threadNumber
        
    def getCommand(self):
        return self.__command

    def setCommand(self, command):
        self.__command = command
        
    def run(self):
        #print "\n\n" + str(self.getThreadNumber()) + ":" + self.getCommand()
        return commands.getstatusoutput(self.getCommand())


class ExperimentControl:
    def __init__(self, hostname=None, pathToNetperfControl="/root/netperfcontrol/runnetperf.py", pathToIperfControl="/root/iperfcontrol/runiperf.py", pathToGnuplotControl="/root/gnuplotcontrol/rungnuplot.py", login="root", key="experiment_login"):
        self.__login = login
        self.__hostname = hostname
        self.__pathToNetperfControl = pathToNetperfControl
        self.__pathToIperfControl = pathToIperfControl
        self.__pathToGnuplotControl = pathToGnuplotControl
        self.__key = key
        
        if (hostname):
            self.__command = "ssh -i " + self.__key + " " + self.__login + "@" + hostname + " "

    def getLogin(self):
        return self.__login

    def setLogin(self, login):
        self.__login = login
        
    def getHostname(self):
        return self.__hostname

    def setHostname(self, hostname):
        if (hostname):
            self.__hostname = hostname
            self.__command = "ssh -i experiment_login " + self.getLogin() + "@" + hostname + " "

    def getPathToNetperfControl(self):
        return self.__pathToNetperfControl

    def setPathToNetperfControl(self, pathToNetperfControl):
        self.__pathToNetperfControl = pathToNetperfControl
        
    def getPathToIperfControl(self):
        return self.__pathToIperfControl

    def setPathToIperfControl(self, pathToIperfControl):
        self.__pathToIperfControl = pathToIperfControl

    def getPathToGnuplotControl(self):
        return self.__pathToGnuplotControl

    def setPathToGnuplotControl(self, pathToGnuplotControl):
        self.__pathToGnuplotControl = pathToGnuplotControl        

    def getKey(self):
        return self.__key

    def setKey(self, key):
        self.__key = key

    def startNetserver(self):
        cmd = self.__command + "screen -d -m netserver"
        return commands.getstatusoutput(cmd)[0]

    def startIperfserver(self,traffic_type):
        if (traffic_type.upper() == "UDP"):
            cmd = self.__command + "screen -d -m iperf -D -s -u -U"
        else :
            cmd = self.__command + "screen -d -m iperf -D -s"
        return commands.getstatusoutput(cmd)[0]

    def killProcessWithName(self,process):
        cmd = self.__command + "killall " + process 
        return commands.getstatusoutput(cmd)[0]

    def addNetRoute(self, network, netmask, gateway, interface):
        cmd = self.__command + "route add -net " + network + " netmask " + netmask + " gw " + gateway + " dev " + interface
        return commands.getstatusoutput(cmd)[0]

    def addNetRouteNoGateway(self, network, netmask, interface):
        cmd = self.__command + "route add -net " + network + " netmask " + netmask + " dev " + interface
        return commands.getstatusoutput(cmd)[0]
    
    def delNetRoute(self, network, netmask):
        cmd = self.__command + "route del -net " + network + " netmask " + netmask
        return commands.getstatusoutput(cmd)[0]

    def configIface(self, iface, address, netmask, tsoOff = True):
        cmd = self.__command + "ifconfig " + iface + " " + address + " netmask " + netmask + " up"
        commands.getstatusoutput(cmd)[0]

        # Turn off tcp segmentation offset
        if (tsoOff):
            cmd = self.__command + "ethtool -K " + iface + " tso off"
            commands.getstatusoutput(cmd)[0]

    def setIfaceState(self, iface, state):
        cmd = self.__command + "ifconfig " + iface + " " + state
        return commands.getstatusoutput(cmd)[0]

    def resetIface(self, iface):
        cmd = self.__command + "ifconfig " + iface + " down"
        commands.getstatusoutput(cmd)
        cmd = self.__command + "ifconfig " + iface + " up"
        return commands.getstatusoutput(cmd)
        
    def getDateID(self):
        return time.strftime("%G-%m-%d-%H-%M-%S", time.localtime(time.time()))

    def runNetperf(self, sourceAddress, destinationAddress, trafficType, experimentID, minPacketSize, maxPacketSize, incrementSize, testRuntime, ifaceName, numberIterations, setViaMTU, stdDeviation, basePath):
        cmd = self.__command + "python " + \
              str(self.getPathToNetperfControl()) + " " + \
              str(trafficType) + " " + \
              str(experimentID) + " " + \
              str(minPacketSize) + " " + \
              str(maxPacketSize) + " " + \
              str(incrementSize) + " " + \
              str(sourceAddress) + " " + \
              str(destinationAddress) + " " + \
              str(testRuntime) + " " + \
              str(ifaceName) + " " + \
              str(numberIterations) + " " + \
              str(setViaMTU) + " " + \
              str(stdDeviation) + " " + \
              str(basePath)

        print cmd
        return commands.getstatusoutput(cmd)

    def runThreadedNetperf(self, sourceList, destinationAddress, trafficType, experimentID, minPacketSize, maxPacketSize, incrementSize, testRuntime, numberIterations, setViaMTU, stdDeviation, basePath):

        counter = 1
        for source in sourceList:
            ifaceName = source.getIfaceName()
            ipAddress = source.getIPAddress()
            hostname = source.getHostname()

            self.setHostname(hostname)
            cmd = self.__command + "python " + \
                  str(self.getPathToNetperfControl()) + " " + \
                  str(trafficType) + " " + \
                  str(experimentID) + " " + \
                  str(minPacketSize) + " " + \
                  str(maxPacketSize) + " " + \
                  str(incrementSize) + " " + \
                  str(ipAddress) + " " + \
                  str(destinationAddress) + " " + \
                  str(testRuntime) + " " + \
                  str(ifaceName) + " " + \
                  str(numberIterations) + " " + \
                  str(setViaMTU) + " " + \
                  str(stdDeviation) + " " + \
                  str(basePath)

            s = ThreadedNetperfClient(cmd, counter)
            s.start()
            counter += 1

        return 0
    
    def runIperf(self, sourceAddress, destinationAddress, trafficType, experimentID, minPacketSize, maxPacketSize, incrementSize, testRuntime, numberIterations, bandwidth, stdDeviation, basePath):
        cmd = self.__command + "python " + \
              str(self.getPathToIperfControl()) + " " + \
              str(trafficType) + " " + \
              str(experimentID) + " " + \
              str(minPacketSize) + " " + \
              str(maxPacketSize) + " " + \
              str(incrementSize) + " " + \
              str(sourceAddress) + " " + \
              str(destinationAddress) + " " + \
              str(testRuntime) + " " + \
              str(numberIterations) + " " + \
              str(bandwidth) + " " + \
              str(stdDeviation) + " " + \
              str(basePath)

        print cmd
        return commands.getstatusoutput(cmd)

    def runGnuplot(self, basePath, terminalType="png", stdDeviation=True):
        cmd = self.__command + "python " + \
              str(self.getPathToGnuplotControl()) + \
              " log png temp.plt netperf.log netperf.png " + \
              terminalType + " " + \
              str(stdDeviation) + " " + \
              basePath

        print cmd
        return commands.getstatusoutput(cmd)[0]
              
    def clickInstall(self, pathToConfig):
        cmd = self.__command + "/usr/local/sbin/click-install " + pathToConfig
        return commands.getstatusoutput(cmd)[0]

    def clickUninstall(self):
        cmd = self.__command + "/usr/local/sbin/click-uninstall"
        return commands.getstatusoutput(cmd)[0]

    def clickCreateConfig(self, pathToFile):
        cmd = self.__command + "perl " + pathToFile + " \> "
        basePath = pathToFile[:pathToFile.rfind("/")]
        filename = pathToFile[pathToFile.rfind("/") + 1: pathToFile.find(".")]
        newPathToFile = basePath + "/" + filename + ".click"
        cmd += newPathToFile
        commands.getstatusoutput(cmd)
        return newPathToFile

    def clickAlign(self, pathToFile):
        cmd = self.__command + "/usr/local/bin/click-align " + pathToFile + " \> "
        basePath = pathToFile[:pathToFile.rfind("/")]
        filename = pathToFile[pathToFile.rfind("/") + 1: pathToFile.find(".")]
        newPathToFile = basePath + "/" + filename + "-aligned.click"
        cmd += newPathToFile
        commands.getstatusoutput(cmd)
        return newPathToFile
        
    def createTunnel(self, remoteIP, localIP, remoteTunnelIP, localTunnelIP, tunnelIface, physicalIface):
        cmd = self.__command + "ip tunnel add " + tunnelIface + " mode ipip remote " + remoteIP + " local " + localIP + " dev " + physicalIface + " ttl 64"
        commands.getstatusoutput(cmd)[0]        
        cmd = self.__command + "ip addr add " + localTunnelIP + "/24 dev " + tunnelIface
        commands.getstatusoutput(cmd)[0]        
        cmd = self.__command + "ip link set " + tunnelIface + " up"
        commands.getstatusoutput(cmd)[0]        

    def killTunnel(self, tunnelIface):
        cmd = self.__command + "ifconfig " + tunnelIface + " down"
        return commands.getstatusoutput(cmd)[0]

    def loadKernelModule(self, pathToModule):
        cmd = self.__command + "insmod " + pathToModule
        return commands.getstatusoutput(cmd)[0]

    def unloadKernelModule(self, moduleName):
        cmd = self.__command + "rmmod " + moduleName
        return commands.getstatusoutput(cmd)[0]        

    def activateLinuxNativeForwarding(self):
        cmd = self.__command + "echo '1' \> /proc/sys/net/ipv4/ip_forward"
        return commands.getstatusoutput(cmd)[0]

    def deactivateLinuxNativeForwarding(self):
        cmd = self.__command + "echo '0' \> /proc/sys/net/ipv4/ip_forward"
        return commands.getstatusoutput(cmd)[0]

    def mkdir(self, dirPath):
        cmd = self.__command + "mkdir -p " + dirPath
        return commands.getstatusoutput(cmd)[0]

    def copy(self, source, destination):
         cmd = "cp " + source + " " + destination
         return commands.getstatusoutput(cmd)[0]
                                            
    def move(self, source, destination):
         cmd = "mv " + source + " " + destination
         return commands.getstatusoutput(cmd)[0]
     
    def remove(self, target):
         cmd = "rm " + target
         return commands.getstatusoutput(cmd)[0]
    
    def scp(self, source, destination):
         cmd = "scp -i " + self.getKey() + " " + source + " " + self.getLogin() + "@" + self.getHostname() + ":" + destination
         return commands.getstatusoutput(cmd)[0]

    def mscp(self, sourceArray, destination):
        cmd = "scp -i " + self.getKey() + " "
        for source in sourceArray:
            cmd += source + " "

        cmd += self.getLogin() + "@" + self.getHostname() + ":" + destination
        return commands.getstatusoutput(cmd)[0]
