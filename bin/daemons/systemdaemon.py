#!/usr/local/bin/python
import sys, pickle, ConfigParser
sys.path.append("/usr/local/hen/lib")

from daemonizer import Daemonizer
from daemon import Daemon
import logging, threading, socket
from auxiliary.daemonlocations import DaemonLocations
from auxiliary.henparser import HenParser
from operatingsystem.dns import DNSConfigWriter
from operatingsystem.dhcp import DHCPConfigWriter
from auxiliary.hen import DNSConfigInfo, DHCPConfigSubnetInfo, DHCPConfigInfo

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

class SystemControl(Daemon):
    """\brief Implements basic system daemon functionality.
    """
    def __init__(self, configFilePath='/usr/local/hen/etc/configs/config'):
        Daemon.__init__(self)

        self.__version = "System Daemon v0.2 (dumb)"

        # Initialize testbed config file
        self.__configFilePath = configFilePath
        self.__configFile = ConfigParser.ConfigParser()
        self.__configFile.read(configFilePath)

        # Initialize parser
        self.__henPhysicalTopology = self.__configFile.get('MAIN','PHYSICAL_TOPOLOGY')
        self.__henLogPath = self.__configFile.get('MAIN', 'LOG_PATH')        
        self.__parser = HenParser(self.__henPhysicalTopology, \
                                  None, \
                                  None, \
                                  self.__henLogPath, \
                                  None,
                                  None,
                                  None, \
                                  None)

        # Initialize DNS writer
        self.__testbedGroup = self.__configFile.get('NETBOOT', 'GROUP')
        configInfo = DNSConfigInfo(self.__configFile.get('DNS', 'TTL'), \
                                   self.__configFile.get('DNS', 'CONTACT'), \
                                   self.__configFile.get('DNS', 'REFRESH_TIME'), \
                                   self.__configFile.get('DNS', 'RETRY_TIME'), \
                                   self.__configFile.get('DNS', 'EXPIRY_TIME'), \
                                   self.__configFile.get('DNS', 'MINIMUM_TIME'), \
                                   self.__configFile.get('MAIN', 'EXPERIMENTAL_BASE_ADDRESS'), \
                                   self.__configFile.get('DNS', 'EXPERIMENTAL_DOMAIN_NAME'), \
                                   self.__configFile.get('DNS', 'EXPERIMENTAL_SERVER_ADDRESS'), \
                                   self.__configFile.get('MAIN', 'INFRASTRUCTURE_BASE_ADDRESS'), \
                                   self.__configFile.get('DNS', 'INFRASTRUCTURE_DOMAIN_NAME'), \
                                   self.__configFile.get('DNS', 'INFRASTRUCTURE_SERVER_ADDRESS'), \
                                   self.__configFile.get('MAIN', 'VIRTUAL_BASE_ADDRESS'), \
                                   self.__configFile.get('DNS', 'VIRTUAL_DOMAIN_NAME'), \
                                   self.__configFile.get('DNS', 'VIRTUAL_SERVER_ADDRESS'))
        self.__dnsWriter = DNSConfigWriter(configInfo, \
                                           self.__configFile.get('DNS', 'CONFIG_FILES_PATH'), \
                                           self.__testbedGroup,
                                           self.__parser)

        # Initialize DHCP writer
        expSubnet = DHCPConfigSubnetInfo(self.__configFile.get('DHCP', 'EXPERIMENTAL_NET'), \
                                         self.__configFile.get('DHCP', 'EXPERIMENTAL_NET_NETMASK'), \
                                         self.__configFile.get('DHCP', 'EXPERIMENTAL_USE_HOST_DECL_NAMES'), \
                                         self.__configFile.get('DHCP', 'EXPERIMENTAL_NET_NETMASK'), \
                                         self.__configFile.get('DHCP', 'EXPERIMENTAL_NET_BROADCAST_ADDRESS'), \
                                         self.__configFile.get('DHCP', 'EXPERIMENTAL_DOMAIN_NAME'), \
                                         self.__configFile.get('DHCP', 'EXPERIMENTAL_ROUTERS'), \
                                         self.__configFile.get('DHCP', 'EXPERIMENTAL_NEXT_SERVER'), \
                                         "experimental")
        infraSubnet = DHCPConfigSubnetInfo(self.__configFile.get('DHCP', 'INFRASTRUCTURE_NET'), \
                                           self.__configFile.get('DHCP', 'INFRASTRUCTURE_NET_NETMASK'), \
                                           self.__configFile.get('DHCP', 'INFRASTRUCTURE_USE_HOST_DECL_NAMES'), \
                                           self.__configFile.get('DHCP', 'INFRASTRUCTURE_NET_NETMASK'), \
                                           self.__configFile.get('DHCP', 'INFRASTRUCTURE_NET_BROADCAST_ADDRESS'), \
                                           self.__configFile.get('DHCP', 'INFRASTRUCTURE_DOMAIN_NAME'), \
                                           self.__configFile.get('DHCP', 'INFRASTRUCTURE_ROUTERS'), \
                                           self.__configFile.get('DHCP', 'INFRASTRUCTURE_NEXT_SERVER'), \
                                           "infrastructure")
        virtualSubnet = DHCPConfigSubnetInfo(self.__configFile.get('DHCP', 'VIRTUAL_NET'), \
                                             self.__configFile.get('DHCP', 'VIRTUAL_NET_NETMASK'), \
                                             self.__configFile.get('DHCP', 'VIRTUAL_USE_HOST_DECL_NAMES'), \
                                             self.__configFile.get('DHCP', 'VIRTUAL_NET_NETMASK'), \
                                             self.__configFile.get('DHCP', 'VIRTUAL_NET_BROADCAST_ADDRESS'), \
                                             self.__configFile.get('DHCP', 'VIRTUAL_DOMAIN_NAME'), \
                                             self.__configFile.get('DHCP', 'VIRTUAL_ROUTERS'), \
                                             self.__configFile.get('DHCP', 'VIRTUAL_NEXT_SERVER'), \
                                             "virtual")
        subnetList = []
        subnetList.append(expSubnet)
        subnetList.append(infraSubnet)
        subnetList.append(virtualSubnet)
        configInfo = DHCPConfigInfo(self.__configFile.get('DHCP', 'DOMAIN_NAME'), \
                                    self.__configFile.get('DHCP', 'DOMAIN_NAME_SERVERS'), \
                                    self.__configFile.get('DHCP', 'DEFAULT_LEASE_TIME'), \
                                    self.__configFile.get('DHCP', 'MAXIMUM_LEASE_TIME'), \
                                    self.__configFile.get('DHCP', 'AUTHORITATIVE'), \
                                    self.__configFile.get('DHCP', 'DDNS_UPDATE_STYLE'), \
                                    self.__configFile.get('DHCP', 'LOG_FACILITY'), \
                                    subnetList)
        self.__henExportPath = self.__configFile.get('MAIN','EXPORT_PATH')
        self.__dhcpWriter = DHCPConfigWriter(configInfo, self.__configFile.get('DHCP', 'CONFIG_FILE_PATH'), \
                                             self.__henExportPath,  self.__testbedGroup, self.__parser)

        # Export methods
        self.__registerMethods()

    def __registerMethods(self):
        self.registerMethodHandler("dhcp", self.dhcp)
        self.registerMethodHandler("dns", self.dns)        

    def dhcp(self,prot,seq,ln,payload):
        """\brief Performs action on the dhcp server. It retrieves the path and name of the server's
                  control script from the config file. Possible actions are start, stop, restart and
                  create, which creates the dhcpd configuration file from the hen database (the xml
                  files)
        \param action (\c string) Either start, stop, restart or create
        \return (\c int) 0 if successful, -1 otherwise
        """
        (username, groups, parameters) = pickle.loads(payload)

        if "henmanager" not in groups:
            prot.sendReply(400, seq, "only managers can perform this operation")
            return
        
        action = parameters[0]
        if (action == "create"):
            self.__dhcpWriter.writeDHCPConfig()            
            message = "wrote " + self.__configFile.get('DHCP', 'CONFIG_FILE_PATH')
            prot.sendReply(200, seq, message)
            return
        
        serverControlScript = self.__configFile.get('DHCP', 'SERVER_CONTROL_SCRIPT')
        print str(serverControlScript) + " " + action
        returnCode = commands.getstatusoutput(str(serverControlScript) + " " + action)[0]
        if (returnCode != 0):
            
            message = "error while performing " + action + " on dhcpd, error code: " + str(returnCode) + "\n" + \
                      "(is the daemon running with su privileges?)"
            prot.sendReply(400, seq, message)
            return
        else:
            message = "successfully performed the following action on dhcpd: " + action
            prot.sendReply(200, seq, message)
            return 

    def dns(self,prot,seq,ln,payload):
        """\brief Performs action on the dns server. Possible actions are start, stop, restart and
                  create, which creates the named configuration files from the hen database (the xml
                  files). The function gets the path to the named.conf file from the hen config file
        \param action (\c string) Either start, stop, restart or create
        \return (\c int) 0 if successful, -1 otherwise
        """
        (username, groups, parameters) = pickle.loads(payload)

        if "henmanager" not in groups:
            prot.sendReply(400, seq, "only managers can perform this operation")
            return
        
        action = parameters[0]        
        message = ""
        if (action == "restart"):
            pid = (commands.getstatusoutput("ps axf | grep named | awk '{print $1}'")[1].splitlines())[0]
            cmd = "kill -s SIGHUP " + pid
            returnCode = commands.getstatusoutput(cmd)[0]
            if (returnCode != 0):
                message = "error while restarting dns server, error code: " + str(returnCode) + "\n" + \
                          "(is the daemon running with su privileges?)"
                prot.sendReply(400, seq, message)
                return
            print "restarted dns server"
        elif (action == "start"):
            returnCode = commands.getstatusoutput("named -c " + self.__configFile.get('DNS', 'NAMED_CONF_PATH'))[0]
            if (returnCode != 0):
                message = "error while restarting dns server, error code: " + str(returnCode) + "\n" + \
                          "(is the daemon running with su privileges?)"
                prot.sendReply(400, seq, message)                
                return
            print "started dns server"
        elif (action == "stop"):
            pid = (commands.getstatusoutput("ps axf | grep named | awk '{print $1}'")[1].splitlines())[0]
            cmd = "kill " + pid
            returnCode = commands.getstatusoutput(cmd)[0]
            if (returnCode != 0):
                message = "error while restarting dns server, error code: " + str(returnCode) + "\n" + \
                          "(is the daemon running with su privileges?)"
                prot.sendReply(400, seq, message)                
                return 
            print "stopped dns server"
        elif (action == "create"):
            self.__dnsWriter.writeDNSConfig()
            message = "wrote dns config files to " + self.__configFile.get('DNS', 'CONFIG_FILES_PATH')

        prot.sendReply(200, seq, message)
                                                
    def stopDaemon(self,prot,seq,ln,payload):
        """\brief Stops the daemon and all threads
        This method will first stop any more incoming queries, then wait for
        any update tasks to complete, before stopping itself.
        """
        log.info("stopDaemon called.")
        prot.sendReply(200, seq, "Accepted stop request.")
        log.debug("Sending stopDaemon() response")
        self.acceptConnections(False)
        log.info("Stopping SystemDaemon (self)")
        self.stop()

                     
class SystemDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    __bind_addr = DaemonLocations.systemDaemon[0]
    __port = DaemonLocations.systemDaemon[1]
    __sockd = None
    __systemcontrol = None

    def __init__(self, doFork):
        Daemonizer.__init__(self, doFork)

    def run(self):
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        self.__sockd.settimeout(2) # 2 second timeouts
        log.debug("Creating SystemDaemon")
        self.__systemcontrol = SystemControl()
        log.info("Starting SystemDaemon")
        self.__systemcontrol.start()
        while self.__systemcontrol.isAlive():
            if self.__systemcontrol.acceptingConnections():
                # allow timeout of accept() to avoid blocking a shutdown
                try:
                    (s,a) = self.__sockd.accept()
                    log.debug("New connection established from " + str(a))
                    self.__systemcontrol.addSocket(s)
                except:
                    pass
            else:
                log.warning("SystemDaemon still alive, but not accepting connections")
                time.sleep(2)
        log.debug("Closing socket.")
        self.__sockd.shutdown(socket.SHUT_RDWR)
        self.__sockd.close()
        while threading.activeCount() > 1:
            cThreads = threading.enumerate()
            log.warning("Waiting on " + str(threading.activeCount()) + \
                        " active threads...")
            time.sleep(2)
        log.info("SystemDaemon Finished.")
        # Now everything is dead, we can exit.
        sys.exit(0)

def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    WORKDIR = '/var/hen/systemdaemon'
    PIDDIR = '/var/run/hen'
    LOGDIR = '/var/log/hen/systemdaemon'
    LOGFILE = 'systemdaemon.log'
    PIDFILE = 'systemdaemon.pid'
    GID = 17477 # schooley
    UID = 17477 # schooley
    systemd = SystemDaemon(False)
    systemd.setWorkingDir(WORKDIR)
    systemd.setPIDDir(PIDDIR)
    systemd.setLogDir(LOGDIR)
    systemd.setLogFile(LOGFILE)
    systemd.setPidFile(PIDFILE)
    systemd.setUid(UID)
    systemd.setGid(GID)
    systemd.start()

if __name__ == "__main__":
    main()
