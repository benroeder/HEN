##################################################################################################################
# confignetboot.py: contains the class used to manipulate the symbolic links used to netboot nodes
#
# CLASSES
# --------------------------------------------------------------------
# ConfigNetboot              The class used to create the directory, symbolic links and other elements  needed to
#                            netboot a node on the testbed.
#
##################################################################################################################
import sys, os, string, time, __builtin__, logging, commands, string

class ConfigNetboot:
    """\brief Class used to manipulate the directory, symbolic links and other elements needed to netboot
              nodes on the testbed.
    """
    
    def __init__(self, autodetectNetbootInfo=None, groupName=None, nfsRoot=None, serialSpeed=None, pxeLinuxDirectory=None, pxeLinuxFile=None, startupFile=None, ifaceConfigScript=None, console=None, exportPath=None, pythonBinaryPath=None):
        """\brief initializes class
        \param autodetectNetbootInfo (\c NetbootInfo) A NetbootInfo object with the information for the autodetect symbolic links
        \param groupName (\c string) The UNIX group name to set the symbolic links to after creation
        \param nfsRoot (\c string) The IP address of the NFS server
        \param serialSpeed (\c string) The speed of the serial console
        \param pxeLinuxDirectory (\c string) The name of the pxe linux directory
        \param pxeLinuxFile (\c string) The name of the pxe linux file
        \param startupFile (\c string) The name of the startup file (startup.sh for instance)
        \param ifaceConfigScript (\c string) The name of the script that configures interfaces (configif.py for instance)
        \param console (\c string) The console to use for serial console output (ttyS0 for instance)
        \param exportPath (\c string) The path to the netboot info export directory (/export/machines for instace)
        \param pythonBinaryPath (\c string) The path to the Python executable
        """
        self.__autodetectNetbootInfo = autodetectNetbootInfo
        self.__groupName = groupName
        self.__nfsRoot = nfsRoot
        self.__serialSpeed = serialSpeed
        self.__pxeLinuxDirectory = pxeLinuxDirectory
        self.__pxeLinuxFile = pxeLinuxFile
        self.__startupFile = startupFile
        self.__ifaceConfigScript = ifaceConfigScript
        self.__console = console
        self.__exportPath = exportPath        
        self.__pythonBinaryPath = pythonBinaryPath
        self.__netbootInfo = None

    def setAutodetectNetbootInfo(self, a):
        """\brief Sets the netboot info
        \param a (\c NetbootInfo) The NetbootInfo object to retrieve information from
        """
        self.__autodetectNetbootInfo = a

    def getAutodetectNetbootInfo(self):
        """\brief Gets the netboot info
        \return (\c NetbootInfo) The NetbootInfo object containint the netboot information
        """
        return self.__autodetectNetbootInfo

    def setGroupName(self, g):
        """\brief Sets the UNIX group name
        \param g (\c string) The UNIX group name to use
        """
        self.__groupName = g

    def getGroupName(self):
        """\brief Gets the UNIX group name
        \return (\c string) The UNIX group name
        """
        return self.__groupName

    def setNFSRoot(self, n):
        """\brief Sets the nfs root (the nfs server's ip address)
        \param n (\c string) The nfs root
        """
        self.__nfsRoot = n

    def getNFSRoot(self):
        """\brief Gets the nfs root (the nfs server's ip address)
        \return (\c string) The nfs root
        """
        return self.__nfsRoot

    def setSerialSpeed(self, s):
        """\brief Sets the serial console's speed
        \param s (\c string) The serial console's speed
        """
        self.__serialSpeed = s

    def getSerialSpeed(self):
        """\brief Gets the serial console's speed
        \return (\c string) The serial console's speed
        """
        return self.__serialSpeed

    def setPXELinuxDirectory(self, p):
        """\brief Sets the pxe linux directory name
        \param p (\c string) The pxe linux directory name
        """
        self.__pxeLinuxDirectory = p

    def getPXELinuxDirectory(self):
        """\brief Gets the pxe linux directory name
        \return (\c string) The pxe linux directory name
        """
        return self.__pxeLinuxDirectory

    def setPXELinuxFile(self, p):
        """\brief Sets the pxe linux file name
        \param p (\c string) The pxe linux file name
        """
        self.__pxeLinuxFile = p

    def getPXELinuxFile(self):
        """\brief Gets the pxe linux file name
        \return (\c string) The pxe linux file name
        """
        return self.__pxeLinuxFile

    def setStartupFile(self, s):
        """\brief Sets the startup file
        \param e (\c string) The startup file
        """
        self.__startupFile = s

    def getStartupFile(self):
        """\brief Gets the startup file
        \return (\c string) The startup file
        """
        return self.__startupFile

    def setIfaceConfigScript(self, i):
        """\brief Sets the interface configuration script
        \param e (\c string) The interface configuration script
        """
        self.__ifaceConfigScript = i

    def getIfaceConfigScript(self):
        """\brief Gets the interface configuration script
        \return (\c string) The interface configuration script
        """
        return self.__ifaceConfigScript

    def setConsole(self, c):
        """\brief Sets the console
        \param e (\c string) The console
        """
        self.__console = c

    def getConsole(self):
        """\brief Gets the console
        \return (\c string) The console
        """
        return self.__console
    
    def setExportPath(self, e):
        """\brief Sets the export path
        \param e (\c string) The export path
        """
        self.__exportPath = e

    def getExportPath(self):
        """\brief Gets the export path
        \return (\c string) The export path
        """
        return self.__exportPath

    def setPythonBinaryPath(self, p):
        """\brief Sets the python binary path
        \param e (\c string) The python binary path
        """
        self.__pythonBinaryPath = p

    def getPythonBinaryPath(self):
        """\brief Gets the python binary path
        \return (\c string) The python binary path
        """
        return self.__pythonBinaryPath

    def createNetbootDir(self, nodeID):
        """\brief Creates a node's netboot directory, including its pxe linux file
        \param nodeID (\c string) The id of the node to create the directory for
        \return (\c int) 0 if successful, -1 otherwise        
        """
        nodePath = self.getExportPath() + nodeID

        os.system("rm -rf " + nodePath)
        os.system("mkdir " + nodePath)
        os.system("chgrp " + self.getGroupName() + " " + nodePath)
        os.system("chmod 775 " + nodePath)
        
        try:
            pxeConfigFile = open(nodePath + "/" + self.getPXELinuxDirectory() + "/" + self.getPXELinuxFile(), 'w')
            pxeConfigFile.write("default linux\nlabel linux\n  kernel kernel\n  append ip=dhcp root=/dev/nfs nfsroot=" + \
                                self.getNFSRoot() + ":" + nodePath + "/filesystem console=" + \
                                self.getConsole() + "\nserial 0 " + self.getSerialSpeed())
            pxeConfigFile.close()
        except:
            return -1
        
        return 0
        
    def createNetbootInfo(self, nodeID, netbootInfo):
        """\brief Creates netboot symbolic links based on information from a Netboot object
        \param nodeID (\c string) The ID of the node to create the symbolic links for
        \param netbootInfo (\c NetbootInfo) The NetbootInfo to obtain information from
        \return (\c int) 0 if successful, -1 otherwise
        """
        filesystem = netbootInfo.getFileSystem()
        kernel = netbootInfo.getKernel()
        loader = netbootInfo.getLoader()
        nodePath = self.getExportPath() + nodeID

        try:
            os.system("rm -rf " + nodePath)
            os.system("mkdir " + nodePath)
            os.system("chgrp " + self.getGroupName() + " " + nodePath)
            os.system("chmod 775 " + nodePath)
            os.system("ln -s " + filesystem + " " + nodePath + "/filesystem")
            os.system("ln -s " + kernel + " " + nodePath + "/kernel")
            os.system("ln -s " + loader + " " + nodePath + "/loader")
            os.system("mkdir " + nodePath + "/" + self.getPXELinuxDirectory())
            
            pxeConfigFile = open(nodePath + "/" + self.getPXELinuxDirectory() + "/" + self.getPXELinuxFile(), 'w')
            pxeConfigFile.write("default linux\nlabel linux\n  kernel kernel\n  append ip=dhcp root=/dev/nfs nfsroot=" + \
                                self.getNFSRoot() + ":" + nodePath + "/filesystem console=" + \
                                self.getConsole() + "\nserial 0 " + self.getSerialSpeed())
            pxeConfigFile.close()
        except:
            return 500
        
        return 200

    def createAutodetectNetbootInfo(self, nodeID):
        """\brief Creates auto-detect  netboot symbolic links based on information from a Netboot object.
                  The function uses the Netboot info object returned by getAutodetectNetbootInfo()
        \param nodeID (\c string) The ID of the node to create the auto-detect symbolic links for
        \return (\c int) 0 if successful, -1 otherwise
        """
        return self.createNetbootInfo(nodeID, self.getAutodetectNetbootInfo())    

    def removeNetbootInfo(self, nodeID, removeDirectory = 0):
        """\brief Removes the netboot symbolic links for the given computer node
        \param nodeID (\c string) The node's id
        \param removeDirectory (\c int) Whether to remove the directory containing the symbolic links (1 if yes)
        \return (\c int) 0 if sucessful, -1 otherwise
        """
        nodePath = self.getExportPath() + nodeID
        try:
            if (removeDirectory == 1):
                os.system("rm -rf " + nodePath)
            elif (removeDirectory == 0):
                os.system("rm " + nodePath + "/kernel")
                os.system("rm " + nodePath + "/filesystem")
                os.system("rm " + nodePath + "/loader")            
            else:
                return -1
        except:
            return -1

        return 0

    def createStartupCommands(self, nodeID, commands):
        """\brief Adds commands to the startup file (a file in a node's netboot directory that
                  gets automatically run at boot time). The commands should not have line breaks
                  in them.
        \param nodeID (\c string) The ID of the node to write the start up file for
        \param commands (list of strings) A list of strings representing the commands to add
        \return (\c int) 0 if sucessful, -1 if unsuccessful or if the list was None or empty
        """
        if (commands == None or len(commands) == 0):
            return -1
        
        try:
            filename = str(self.getExportPath()) + str(nodeID) + "/" + str(self.getStartupFile())
            startupFile = open(filename, "a")

            commandsList = ""
            for command in commands:
                commandsList += command + "\n"

            startupFile.write(commandsList)
            startupFile.close()
            os.system("chgrp " + self.getGroupName() + " " + filename)

        except Exception, e:
            print Exception, e
            print "confignetboot.py::createStartupCommands: Error while writing to: " + filename
            return -1
        
        return 0            
            
    def createStartupInterfaceConfig(self, nodeID, interfaces):
        """\brief Adds entries to the startup file of a node (a file in a node's netboot directory that
                  gets automatically run at boot time) so that the given interfaces are automatically
                  set up with the given ip addresses
        \param nodeID (\c string) The node to add lines to the startup script for
        \param interfaces (\c list) A list of Interface objects containing the configuration information
        \return (\c int) 0 if sucessful, -1 otherwise
        """
        try:
            filename = self.getExportPath() + nodeID + "/" + self.getStartupFile()
            startupFile = open(filename, 'a')
            for interface in interfaces:
                mac = interface.getMAC()
                ip = interface.getIP()
                subnet = interface.getSubnet()

                if (mac != None and mac != "" and ip != None and ip != "" and subnet != None and subnet != ""):
                    startupFile.write(self.getPythonBinaryPath() + " " + self.getIfaceConfigScript() + " " + \
                                      mac + " " + ip + " " + subnet + "\n")

            startupFile.close()
            os.system("chgrp " + self.getGroupName() + " " + filename)
        except Exception, e:
            print Exception, e
            print "confignetboot.py::createStartupInterfaceConfig: Error while writing to: " + filename
            return -1
        
        return 0
    
    def deleteStartupFile(self, nodeID):
        """\brief Deletes a given node's startup file
        \param nodeID (\c string) The id of the node
        \return (\c int) 0 if successful, other if not
        """
        return commands.getstatusoutput("rm " + self.getExportPath() + nodeID + "/" + self.getStartupFile())[0]
