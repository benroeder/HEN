##################################################################################################################
# dhcp.py: this file contains the class used to generate the dhcp config file for the testbed
#
# CLASSES
# --------------------------------------------------------------------
# DHCPConfigWriter           The class used to generate the dhcp config file for the testbed
#
##################################################################################################################
from henmanager import HenManager
from auxiliary.hen import DHCPConfigInfo
import os

class DHCPConfigWriter:
    """\brief This class is used to generate the dhcp config file used by the testbed.
              The file is generated from the information in the xml files (the testbed's
              database)
    """

    def __init__(self, dhcpConfigInfo=None, outputFilename=None, exportPath=None, groupName=None, parser=None):
        """\brief Initializes the class
        \param dhcpConfigInfo (\c DHCPConfigInfo) The DHCPConfigInfo object to obtain the information from
        \param outputFilename (\c string) The path and filename to write the dhcp config to
        \param exportPath (\c string) The path to the directories with the symbolic links (/export/machines/ for instance)
        \param groupName (\c string) The name for the group of developers on the testbed
        \param parser (\c HenParser) An initialized parser object used to read testbed info with
        """
        self.__dhcpConfigInfo = dhcpConfigInfo
        self.__outputFilename = outputFilename
        self.__groupName = groupName
        self.__outputFile = None
        self.__exportPath = exportPath
        self.__parser = parser
        
    def getOutputFile(self):
        """\brief Gets the File object
        \return (\c File) The File object
        """
        return self.__outputFile

    def setOutputFileName(self, f):
        """\brief Sets the filename to write the config to (including its path)
        \param f (\c string) The filename
        """        
        self.__outputFilename = f

    def getOutputFilename(self):
        """\brief Gets the file name (its path included)
        \return (\c string) The file name
        """
        return self.__outputFilename

    def setExportPath(self, e):
        """\brief Sets the export path. The export path is the path to the directories
                  with the symbolic links (/export/machines/ for instance).
        \param e (\c string) The export path
        """
        self.__exportPath = e

    def getExportPath(self):
        """\brief Gets the export path
        \return (\c string) The export path
        """
        return self.__exportPath

    def setDHCPConfigInfo(self, c):
        """\brief Sets the DHCPConfigInfo object
        \param c (\c DHCPConfigInfo) The DHCPConfigInfo object
        """
        self.__dhcpConfigInfo = c
        
    def getDHCPConfigInfo(self):
        """\brief Gets the DHCPConfigInfo
        \return (\c DHCPConfigInfo) The DHCPConfigInfo object
        """
        return self.__dhcpConfigInfo

    def writeDHCPConfig(self):
        """\brief Writes the dhcp config file
        """
        dnsServer = self.getDHCPConfigInfo().getDomainNameServers()
        self.__outputFile = open(self.__outputFilename, "w")
        manager = HenManager()
        nodes = manager.getNodes("all","all")
#        if (not self.__parser):
#            print "error: parser is null"
#            return
#        self.__parser.parseAll()
#        nodes = self.__parser.getNodes("all", "all")

        # write initial block
	self.__writeStartingBlock()

        # process each subnet
        subnetInfoList = self.getDHCPConfigInfo().getSubnetInfoList()
        
        for subnetInfo in subnetInfoList:
            
            self.__writeSubnetBlock(subnetInfo)
            if (subnetInfo.getSubnetType() == "experimental"):
                for nodeType in nodes.keys():
                    for node in nodes[nodeType].values():
                        interfacesList = node.getInterfaces("management")
                        if (interfacesList != None):
                            for interface in interfacesList:
                                self.__writeNode(node.getNodeID(), interface, node.getNetbootable(), dnsServer, node.getNodeType(), subnetInfo.getDomainName())
            elif (subnetInfo.getSubnetType() == "infrastructure"):
                for nodeType in nodes.keys():
                    for node in nodes[nodeType].values():
                        interfacesList = node.getInterfaces("infrastructure")
                        if (interfacesList != None):
                            for interface in interfacesList:
                                self.__writeNode(node.getNodeID(), interface, node.getNetbootable(), dnsServer, node.getNodeType(), subnetInfo.getDomainName())
            elif (subnetInfo.getSubnetType() == "virtual"):
                for nodeType in nodes.keys():
                    for node in nodes[nodeType].values():
                        interfacesList = node.getInterfaces("virtual")
                        
                        if (interfacesList != None):
                            for interface in interfacesList:
                                self.__writeNode(node.getNodeID(), interface, node.getNetbootable(), dnsServer, node.getNodeType(), subnetInfo.getDomainName())

            self.__writeEndingBlock()

        self. __closeFile()
        return 0

    def __writeStartingBlock(self):
        """\brief Writes the starting section of the dhcp config file. If an output
                  file is set, the function writes to it, otherwise the output gets sent to
                  the screen
        """
        string = "option domain-name " + str(self.getDHCPConfigInfo().getDomainName()) + ";\n" + \
                 "option domain-name-servers " + str(self.getDHCPConfigInfo().getDomainNameServers()) + ";\n" + \
                 "default-lease-time " + str(self.getDHCPConfigInfo().getDefaultLeaseTime()) + ";\n" + \
                 "max-lease-time " + str(self.getDHCPConfigInfo().getMaximumLeaseTime()) + ";\n" + \
                 str(self.getDHCPConfigInfo().getAuthoritative()) + ";\n" + \
                 "ddns-update-style " + str(self.getDHCPConfigInfo().getDDNSUpdateStyle()) + ";\n" + \
                 "log-facility " + str(self.getDHCPConfigInfo().getLogFacility()) + ";\n"
        
        if (self.__outputFile == None):
            print string
        else:
            try:
                self.__outputFile.write(string + "\n")
            except:
                print "1 error while writing DHCP configuration to " + self.__getOutputFilename()
            
    def __writeSubnetBlock(self, subnetInfo):
        """\brief Writes the starting section of a subnet block of the dhcp config file. If an output
                  file is set, the function writes to it, otherwise the output gets sent to
                  the screen
        \param subnetInfo (\c DHCPConfigSubnetInfo) The DHCPConfigSubnetInfo object containing the information
        """
        string = "\nsubnet " + str(subnetInfo.getSubnet()) + " netmask " + str(subnetInfo.getNetmask()) + " { \n" + \
                 "use-host-decl-names " + str(subnetInfo.getUseHostDeclNames()) + ";\n" + \
                 "option subnet-mask " + str(subnetInfo.getSubnetMask()) + ";\n" + \
                 "option broadcast-address " + str(subnetInfo.getBroadcastAddress()) + ";\n" + \
                 "option domain-name " + str(subnetInfo.getDomainName()) + ";\n" + \
                 "option routers " + str(subnetInfo.getRouters()) + ";\n" + \
                 "next-server " + str(subnetInfo.getNextServer()) + ";\n"
        
        if (self.__outputFile == None):
            print string
        else:
            try:
                self.__outputFile.write(string + "\n")
            except:
                print "2 error while writing DHCP configuration to " + self.__getOutputFilename()

    def __writeNode(self, nodeID, interface, netBootable, server, nodeType, nodeDomainName):
        """\brief Writes a dhcp entry for a node's interface. If the last parameter is set to yes,
                  the function writes an entry for a netbootable node.
        \param nodeID (\c string) The id of the node whose entry is to be written
        \param interface (\c Interface) The Interface object to retrieve information from
        \param netBootable (\c string) Either yes or no
        \param nodeType (\c string) The node type
        \param nodeDomainName (\c string) The domain name
        """
        if ((interface.getIP() == None) or (interface.getIP() == "None")):
            return
        nodeDomainName = nodeDomainName.strip('"')
#        string = None
#        if (interface.getIfaceType() == "management" and nodeType == "server"):
#            string = "host " + str(nodeID) + "." + str(nodeDomainName) + " {\n"
#        else:
#            string = "host " + str(nodeID) + " {\n"
                     
        string = "host " + str(nodeID) + "." + str(nodeDomainName) + " {\n" + \
                 "\t hardware ethernet " + str(interface.getMAC()) + ";\n" + \
                 "\t fixed-address " + str(interface.getIP()) + ";\n"

        if (netBootable == "yes"):
            string += "\t option root-path \"" + str("192.168.0.250") + ":" + str(self.__exportPath) + str(nodeID) + \
                      "/filesystem,nfsvers=3 \"" + ";\n" + \
                      "\t filename \"/machines/" + str(nodeID) + "/loader" + "\";\n" + \
                      "}"
        else:
            string += "}"
            
        if (self.__outputFile == None):
            print string
        else:
            try:
                self.__outputFile.write(string + "\n")
            except:
                print "3 error while writing DHCP configuration to " + self.__getOutputFilename()

    def __writeEndingBlock(self):
        """\brief Writes an ending block
        """
        string = "\n\n}"
        if (self.__outputFile == None):
            print string
        else:
            try:
                self.__outputFile.write(string + "\n")
            except:
                print "4 error while writing DHCP configuration to " + self.__getOutputFilename()

    def __closeFile(self):
        """\brief Attemps to close the file, throws an exception if it fails to do so
        """
        try:
            self.__outputFile.close()

        except:
            print "5 error while closing file or setting its permissions"
            
        os.system("chgrp " + self.__groupName + " " + self.__outputFilename)
        os.system("chmod 775 " + self.__outputFilename)
