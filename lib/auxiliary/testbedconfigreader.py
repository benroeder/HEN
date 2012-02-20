##################################################################################################################
# testbedconfigreader.py: this class reads the testbed's main config file
#
# CLASSES
# --------------------------------------------------------------------
# TestbedConfigReader            The class used to read the testbed's main config file
#
##################################################################################################################
from auxiliary.henparser import HenParser
from operatingsystem.confignetboot import ConfigNetboot
from auxiliary.hen import NetbootInfo
import auxiliary.hen
import ConfigParser, logging

class TestbedConfigReader:
    """\brief Class used to read the testbed's main config file
    """

    def __init__(self, configFilePath='/usr/local/hen/etc/configs/testbed.conf'):
        """\brief Initializes the class and the logger
        \param configFilePath (\c string) The path to the config file for the testbed. Default: /usr/local/hen/etc/configs/config
        """
	self.__configFile = ConfigParser.ConfigParser()
	self.__configFile.read(configFilePath)

	self.__henRoot = self.__configFile.get('DEFAULT', 'ROOT') 
	self.__pythonBin = self.__configFile.get('MAIN','PYTHON_BIN')	  
	self.__henRoot = self.__configFile.get('MAIN','ROOT')
	self.__henBinPath = self.__configFile.get('MAIN','BIN_PATH')
	self.__henEtcPath = self.__configFile.get('MAIN','ETC_PATH')
	self.__henVarPath = self.__configFile.get('MAIN','VAR_PATH')
        self.__henExperimentalBaseAddress = self.__configFile.get('MAIN', 'EXPERIMENTAL_BASE_ADDRESS')
        self.__henInfrastructureBaseAddress = self.__configFile.get('MAIN', 'INFRASTRUCTURE_BASE_ADDRESS')
	self.__henExportPath = self.__configFile.get('MAIN','EXPORT_PATH')     
	self.__henLogPath = self.__configFile.get('MAIN','LOG_PATH')
	self.__henPhysicalTopology = self.__configFile.get('MAIN','PHYSICAL_TOPOLOGY')
        self.__henExperimentTopology = self.__configFile.get('MAIN','EXPERIMENTAL_TOPOLOGY')
	self.__userLogFile = "%s%s-%s-%s"%(self.__henLogPath, "/log", auxiliary.hen.getUserName(), auxiliary.hen.getTime())
	self.__henManager = self.__configFile.get('MAIN','MANAGER')
        self.__physicalPath = self.__configFile.get('MAIN', 'PHYSICAL_PATH')
        self.__testbedGroup = self.__configFile.get('NETBOOT', 'GROUP')
        self.__experimentPath = self.__configFile.get('MAIN', 'EXPERIMENTAL_PATH')
        self.__configFilesPath = self.__configFile.get('MAIN', 'CONF_PATH')

        self.__hmDaemonConfig = self.__configFile.get('CONFIG_FILES', 'HM_DAEMON_CONFIG_FILENAME')
        self.__powerDaemonConfig = self.__configFile.get('CONFIG_FILES', 'POWER_DAEMON_CONFIG_FILENAME')
        self.__switchDaemonConfig = self.__configFile.get('CONFIG_FILES', 'SWITCH_DAEMON_CONFIG_FILENAME')
        self.__consoleDaemonConfig = self.__configFile.get('CONFIG_FILES', 'CONSOLE_DAEMON_CONFIG_FILENAME')
        self.__moteDaemonConfig = self.__configFile.get('CONFIG_FILES', 'MOTE_DAEMON_CONFIG_FILENAME')
        self.__monitorDaemonConfig = self.__configFile.get('CONFIG_FILES', 'MONITOR_DAEMON_CONFIG_FILENAME')

        self.__dhcpServerControlScript = self.__configFile.get('DHCP', 'SERVER_CONTROL_SCRIPT')
        self.__namedConfPath = self.__configFile.get('DNS', 'NAMED_CONF_PATH')
        
	self.__running = None
        self.__log = None

        self.__configNetboot = ConfigNetboot(NetbootInfo(self.__configFile.get('NETBOOT', 'AUTODETECT_LOADER'), \
                                             self.__configFile.get('NETBOOT', 'AUTODETECT_FILESYSTEM'), \
                                             self.__configFile.get('NETBOOT', 'AUTODETECT_KERNEL')), \
                                             self.__testbedGroup, \
                                             self.__configFile.get('NETBOOT', 'NFS_ROOT'), \
                                             self.__configFile.get('NETBOOT', 'SERIAL_SPEED'), \
                                             self.__configFile.get('NETBOOT', 'PXE_LINUX_DIRECTORY'), \
                                             self.__configFile.get('NETBOOT', 'PXE_LINUX_FILE'), \
                                             self.__configFile.get('NETBOOT', 'STARTUP_FILE'), \
                                             self.__configFile.get('NETBOOT', 'INTERFACE_CONFIG_SCRIPT'), \
                                             self.__configFile.get('NETBOOT', 'CONSOLE'), \
                                             self.__henExportPath, \
                                             self.__pythonBin)

	self.initLogging()
	self.__parser = HenParser(self.__henPhysicalTopology, self.__henExperimentTopology, \
                                self.__log, self.__physicalPath, self.__experimentPath, self.__configFile.get('MAIN', 'CURRENT_EXPERIMENTS'), self.__testbedGroup)

    def initLogging(self, loggerName='hen'):
        """\brief Initializes the logger
        \param loggerName (\c string) The name of the logger. Default value: hen
        """ 
        self.__log = logging.getLogger(loggerName)
	user = auxiliary.hen.getUserName()
	if (user != "web"):
	    self.__log.setLevel(logging.DEBUG)
	    sth = logging.StreamHandler()
	    sth.setLevel(logging.INFO)
	    self.__log.addHandler(sth)

    def getParser(self):
        """\brief Returns the parser
        \return (\c HenParser) The parser
        """
        return self.__parser

    def getConfigFilesPath(self):
        """\brief Returns the path to the testbed's config files
        \return (\c string) The path to the testbed's config files
        """
        return self.__configFilesPath

    def getHMDaemonConfig(self):
        """\brief Gets the name of the hm daemon's config file
        \return (\c string) The name of the hm daemon's config file
        """
        return self.__hmDaemonConfig

    def getPowerDaemonConfig(self):
        """\brief Gets the name of the power daemon's config file
        \return (\c string) The name of the power daemon's config file
        """        
        return self.__powerDaemonConfig

    def getSwitchDaemonConfig(self):
        """\brief Gets the name of the switch daemon's config file
        \return (\c string) The name of the switch daemon's config file
        """        
        return self.__switchDaemonConfig

    def getConsoleDaemonConfig(self):
        """\brief Gets the name of the console daemon's config file
        \return (\c string) The name of the console daemon's config file
        """        
        return self.__consoleDaemonConfig

    def getMoteDaemonConfig(self):
        """\brief Gets the name of the mote daemon's config file
        \return (\c string) The name of the mote daemon's config file
        """        
        return self.__moteDaemonConfig

    def getMonitorDaemonConfig(self):
        """\brief Gets the name of the monitor daemon's config file
        \return (\c string) The name of the monitor daemon's config file
        """        
        return self.__monitorDaemonConfig    

    def getDHCPServerControlScript(self):
        """\brief Gets the path and name to the dhcp server's control script
        \return (\c string) The path and name to the dhcp server's control script
        """
        return self.__dhcpServerControlScript
    
    def getNamedConfPath(self):
        """\brief Gets the path to the named config file
        \return (\c string) The path to the named config file
        """
        return self.__namedConfPath

    def getConfigNetboot(self):
        """\brief Returns the object used to configure netboot information with
        \return (\c ConfigNetboot) The object used to configure netboot information with
        """
        return self.__configNetboot
