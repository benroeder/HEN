##################################################################################################################
# dns.py: this file contains the class used to generate the dns config files for the testbed
#
# CLASSES
# --------------------------------------------------------------------
# DHCPConfigWriter           The class used to generate the dns config files for the testbed
#
##################################################################################################################
from auxiliary.hen import DNSConfigInfo, reverseIPAddress
#from henmanager import HenManager
import time, os

class DNSConfigWriter:
    """\brief This class is used to generate the dns config files (forward and reverse
              lookup) used by the testbed. The file is generated from the information
              in the xml files (the testbed's database)
    """

    def __init__(self, dnsConfigInfo=None, outputPath=None, groupName=None, parser=None):
        """\brief Initializes the class
        \param dnsConfigInfo (\c DNSConfigInfo) The DNSConfigInfo object to obtain the information from
        \param outputPath (\c string) The path to write the DNS config out to
        \param parser (\c HenParser) An initialized parser object used to read testbed info with         
        """        
        self.__dnsConfigInfo = dnsConfigInfo
        self.__outputPath = outputPath
        self.__groupName = groupName
        self.__outputFile = None
        self.__serialTime = None
        self.__parser = parser

    def setDNSConfigInfo(self, c):
        """\brief Sets the DNSConfigInfo object
        \param c (\c DNSConfigInfo) The DNSConfigInfo object
        """
        self.__dnsConfigInfo = c
        
    def getDNSConfigInfo(self):
        """\brief Gets the DNSConfigInfo
        \return (\c DNSConfigInfo) The DNSConfigInfo object
        """
        return self.__dnsConfigInfo
    
    def setOutputFileName(self, p):
        """\brief Sets the path to write the config to 
        \param f (\c string) The path
        """        
        self.__outputPath = p

    def getOutputPath(self):
        """\brief Gets the path
        \return (\c string) The path
        """
        return self.__outputPath

    def writeDNSConfig(self):
        """\brief Writes the DNS config files. The files created are: forward and reverse lookup
                  files for the experimental subnet and forward and reverse lookup files for the
                  infrastructure subnet
        """
        #manager = HenManager()
        #nodes = manager.getNodes("all","all")
        self.__parser.parseAll()
        nodes = self.__parser.getNodes("all", "all")

        # Used to set the serial number in the DNS files to the current time
        currentTime = time.gmtime()
        currentYear = currentTime[0]
        currentMonth = currentTime[1]
        currentDay = currentTime[2]
        currentHour = currentTime[3]
        currentMinute = currentTime[4]
        self.__serialTime = str(currentYear) + str(currentMonth) + str(currentDay) + "1"


        experimentalForwardLookupPath = self.__outputPath + "/" + \
                                        self.__dnsConfigInfo.getExperimentalDomainName().strip('"') + \
                                        ".zone"
        experimentalReverseLookupPath = self.__outputPath + "/" + \
                                        self.__dnsConfigInfo.getExperimentalBaseNetworkAddress() + \
                                        ".zone"
        infrastructureForwardLookupPath = self.__outputPath + "/" + \
                                        self.__dnsConfigInfo.getInfrastructureDomainName().strip('"') + \
                                        ".zone"
        infrastructureReverseLookupPath = self.__outputPath + "/" + \
                                        self.__dnsConfigInfo.getInfrastructureBaseNetworkAddress() + \
                                        ".zone"
        virtualForwardLookupPath = self.__outputPath + "/" + \
                                        self.__dnsConfigInfo.getVirtualDomainName().strip('"') + \
                                        ".zone"
        virtualReverseLookupPath = self.__outputPath + "/" + \
                                        self.__dnsConfigInfo.getVirtualBaseNetworkAddress() + \
                                        ".zone"
        # Open files
        expForwardFile = open(experimentalForwardLookupPath, "w")
        expReverseFile = open(experimentalReverseLookupPath, "w")
        infraForwardFile = open(infrastructureForwardLookupPath, "w")
        infraReverseFile = open(infrastructureReverseLookupPath, "w")
        virtualForwardFile = open(virtualForwardLookupPath, "w")
        virtualReverseFile = open(virtualReverseLookupPath, "w")

        # Print start blocks
        self.__writeForwardLookupStartingBlock(expForwardFile, "experimental")
        self.__writeForwardLookupStartingBlock(infraForwardFile, "infrastructure")
        self.__writeForwardLookupStartingBlock(virtualForwardFile, "virtual")
        self.__writeReverseLookupStartingBlock(expReverseFile, "experimental")
        self.__writeReverseLookupStartingBlock(infraReverseFile, "infrastructure")
        self.__writeReverseLookupStartingBlock(virtualReverseFile, "virtual")

        # Print A entries
        for nodeType in nodes.keys():
            for node in nodes[nodeType].values():
                expInterfaces = node.getInterfaces("management")
                intraInterfaces = node.getInterfaces("infrastructure")
                virtualInterfaces = node.getInterfaces("virtual")

                if (expInterfaces):
                    for interface in expInterfaces:
                        self.__writeForwardLookupNodeEntry(expForwardFile, "experimental", node.getNodeID(), interface.getIP())
                        self.__writeReverseLookupNodeEntry(expReverseFile, "experimental", node.getNodeID(), interface.getIP())
                if (intraInterfaces):
                    for interface in intraInterfaces:
                        self.__writeForwardLookupNodeEntry(infraForwardFile, "infrastructure", node.getNodeID(), interface.getIP())
                        self.__writeReverseLookupNodeEntry(infraReverseFile, "infrastructure", node.getNodeID(), interface.getIP())
                if (virtualInterfaces):
                    for interface in virtualInterfaces:
                        self.__writeForwardLookupNodeEntry(virtualForwardFile, "virtual", node.getNodeID(), interface.getIP())
                        self.__writeReverseLookupNodeEntry(virtualReverseFile, "virtual", node.getNodeID(), interface.getIP())

        # Print CNAME entries
        for nodeType in nodes.keys():
            for node in nodes[nodeType].values():
                dnsInfrastructureAlias = node.getSingleAttribute("dnsinfrastructurealias")
                dnsManagementAlias = node.getSingleAttribute("dnsmanagementalias")
                dnsVirtualAlias = node.getSingleAttribute("dnsvirtualalias")
                managementInterfaces = node.getInterfaces("management")
                infrastructureInterfaces = node.getInterfaces("infrastructure")
                virtualInterfaces = node.getInterfaces("virtual")

                # Handle management aliases
                if (dnsManagementAlias != None and managementInterfaces != None and len(managementInterfaces) != 0):
                    self.__writeDNSAlias(expForwardFile, "experimental", node.getNodeID(), dnsManagementAlias)
                # Handle infrastructure aliases
                if (dnsInfrastructureAlias != None and infrastructureInterfaces != None and len(infrastructureInterfaces) != 0):
                    self.__writeDNSAlias(infraForwardFile, "infrastructure", node.getNodeID(), dnsInfrastructureAlias)
                # Handle virtual aliases
                if (dnsVirtualAlias != None and virtualInterfaces != None and len(virtualInterfaces) != 0):
                    self.__writeDNSAlias(virtualForwardFile, "virtual", node.getNodeID(), dnsVirtualAlias)

                        
        # Close files
        try:
            expForwardFile.close()
            expReverseFile.close()
            infraForwardFile.close()
            infraReverseFile.close()
            virtualForwardFile.close()
            virtualReverseFile.close()
        except:
            print "Error while closing files"
            
        os.system("chgrp " + self.__groupName + " " + experimentalForwardLookupPath)
        os.system("chmod 775 " + experimentalForwardLookupPath)
        os.system("chgrp " + self.__groupName + " " + experimentalReverseLookupPath)
        os.system("chmod 775 " + experimentalReverseLookupPath)
        os.system("chgrp " + self.__groupName + " " + infrastructureForwardLookupPath)
        os.system("chmod 775 " + infrastructureForwardLookupPath)
        os.system("chgrp " + self.__groupName + " " + infrastructureReverseLookupPath)
        os.system("chmod 775 " + infrastructureReverseLookupPath)
        os.system("chgrp " + self.__groupName + " " + virtualForwardLookupPath)
        os.system("chmod 775 " + virtualForwardLookupPath)
        os.system("chgrp " + self.__groupName + " " + virtualReverseLookupPath)
        os.system("chmod 775 " + virtualReverseLookupPath)
        
    def __writeForwardLookupStartingBlock(self, outputFile, subnetType):
        """\brief Writes the starting block for the forward lookup DNS files
        \param outputFile (\c File) The File object to write the starting block to
        \param subnetType (\c string) The subnet type (experimental or infrastructure)
        """
        string = "$TTL " + str(self.__dnsConfigInfo.getTTL()) + "\n" + \
                 "@\t\t\tIN\tSOA\t"

        if (subnetType == "experimental"):
            string += str(self.__dnsConfigInfo.getExperimentalDomainName().strip('"'))
        elif (subnetType == "virtual"):
            string += str(self.__dnsConfigInfo.getVirtualDomainName().strip('"'))
        else:
            string += str(self.__dnsConfigInfo.getInfrastructureDomainName().strip('"'))


        string += ".\t" + str(self.__dnsConfigInfo.getContact()) + ".\t(\n" + \
                  "\t\t\t\t\t\t\t\t\t" + self.__serialTime + "\t; serial\n" + \
                  "\t\t\t\t\t\t\t\t\t" + self.__dnsConfigInfo.getRefreshTime() + "\t; refresh\n" + \
                  "\t\t\t\t\t\t\t\t\t" + self.__dnsConfigInfo.getRetryTime() + "\t; retry\n" + \
                  "\t\t\t\t\t\t\t\t\t" + self.__dnsConfigInfo.getExpiryTime() + "\t; expiry\n" + \
                  "\t\t\t\t\t\t\t\t\t" + self.__dnsConfigInfo.getMinimumTime() + ")\t; minimum\n\n" + \
                  "\t\t\tIN\tNS\t"

        if (subnetType == "experimental"):
            string += str(self.__dnsConfigInfo.getExperimentalServerAddress()) + ".\n\n"
        elif (subnetType == "virtual"):
            string += str(self.__dnsConfigInfo.getVirtualServerAddress()) + ".\n\n"
        else:
            string += str(self.__dnsConfigInfo.getInfrastructureServerAddress()) + ".\n\n"
        
        try:
            outputFile.write(string + "\n")
        except:
            print "Error while writing in __writeForwardLookupStartingBlock"

    def __writeReverseLookupStartingBlock(self, outputFile, subnetType):
        """\brief Writes the starting block for the reverse lookup DNS files
        \param outputFile (\c File) The File object to write the starting block to
        \param subnetType (\c string) The subnet type (experimental or infrastructure)        
        """
        string = "$TTL " + str(self.__dnsConfigInfo.getTTL()) + "\n" + \
                 "@\t\t\tIN\tSOA\t"

        if (subnetType == "experimental"):
            string += str(reverseIPAddress(self.__dnsConfigInfo.getExperimentalBaseNetworkAddress())) + ".in-addr.arpa"
        elif (subnetType == "virtual"):
            string += str(reverseIPAddress(self.__dnsConfigInfo.getVirtualBaseNetworkAddress())) + ".in-addr.arpa"
        else:
            string += str(reverseIPAddress(self.__dnsConfigInfo.getInfrastructureBaseNetworkAddress())) + ".in-addr.arpa"


        string += ".\t" + str(self.__dnsConfigInfo.getContact()) + ".\t(\n" + \
                  "\t\t\t\t\t\t\t\t\t" + self.__serialTime + "\t; serial\n" + \
                  "\t\t\t\t\t\t\t\t\t" + self.__dnsConfigInfo.getRefreshTime() + "\t; refresh\n" + \
                  "\t\t\t\t\t\t\t\t\t" + self.__dnsConfigInfo.getRetryTime() + "\t; retry\n" + \
                  "\t\t\t\t\t\t\t\t\t" + self.__dnsConfigInfo.getExpiryTime() + "\t; expiry\n" + \
                  "\t\t\t\t\t\t\t\t\t" + self.__dnsConfigInfo.getMinimumTime() + ")\t; minimum\n\n" + \
                  "\t\t\tIN\tNS\t"

        if (subnetType == "experimental"):
            string += str(self.__dnsConfigInfo.getExperimentalServerAddress()) + ".\n\n"
        elif (subnetType == "virtual"):
            string += str(self.__dnsConfigInfo.getVirtualServerAddress()) + ".\n\n"
        else:
            string += str(self.__dnsConfigInfo.getInfrastructureServerAddress()) + ".\n\n"

        try:
            outputFile.write(string + "\n")
        except:
            print "Error while writing in __writeReverseLookupStartingBlock"
            
    def __writeForwardLookupNodeEntry(self, outputFile, subnetType, nodeID, nodeIP):
        """\brief Writes a node entry in a forward lookup file
        \param outputFile (\c File) The File object to write the node entry to
        \param subnetType (\c string) The subnet type (experimental or infrastructure)
        \param nodeID (\c string) The node's id
        \param nodeIP (\c string) The node's IP address
        """
        if ((nodeIP == None) or (nodeIP == "None")):
            return

        string = str(nodeID) + "."

        if (subnetType == "experimental"):
            string += str(self.__dnsConfigInfo.getExperimentalDomainName().strip('"')) + ".\t\tIN\tA\t" + str(nodeIP)
        elif (subnetType == "virtual"):
            string += str(self.__dnsConfigInfo.getVirtualDomainName().strip('"')) + ".\t\tIN\tA\t" + str(nodeIP)
        else:
            string += str(self.__dnsConfigInfo.getInfrastructureDomainName().strip('"')) + ".\t\tIN\tA\t" + str(nodeIP)

        try:
            outputFile.write(string + "\n")
        except:
            print "Error while writing in __writeForwardLookupNode"

    def __writeReverseLookupNodeEntry(self, outputFile, subnetType, nodeID, nodeIP):
        """\brief Writes a node entry in a reverse lookup file
        \param outputFile (\c File) The File object to write the node entry to
        \param subnetType (\c string) The subnet type (experimental or infrastructure)
        \param nodeID (\c string) The node's id
        \param nodeIP (\c string) The node's IP address        
        """
        if ((nodeIP == None) or (nodeIP == "None")):
            return
                    
        
        string = str(reverseIPAddress(nodeIP)) + ".in-addr.arpa.\t\tIN\tPTR\t" + str(nodeID) + "."

        if (subnetType == "experimental"):
            string += str(self.__dnsConfigInfo.getExperimentalDomainName().strip('"')) + "."
        elif (subnetType == "virtual"):
            string += str(self.__dnsConfigInfo.getVirtualDomainName().strip('"')) + "."
        else:
            string += str(self.__dnsConfigInfo.getInfrastructureDomainName().strip('"')) + "."

        try:
            outputFile.write(string + "\n")
        except:
            print "Error while writing in __writeReverseLookupNode"

    def __writeDNSAlias(self, outputFile, subnetType, nodeID, dnsAlias):
        """
        """
        string = str(dnsAlias) + "."
        if (subnetType == "experimental"):
            string += str(self.__dnsConfigInfo.getExperimentalDomainName().strip('"')) + ".\t\tIN\tCNAME\t" + \
                      str(nodeID) + "." + str(self.__dnsConfigInfo.getExperimentalDomainName().strip('"')) + "."
        elif (subnetType == "virtual"):
            string += str(self.__dnsConfigInfo.getVirtualDomainName().strip('"')) + ".\t\tIN\tCNAME\t" + \
                      str(nodeID) + "." + str(self.__dnsConfigInfo.getVirtualDomainName().strip('"')) + "."
        else:
            string += str(self.__dnsConfigInfo.getInfrastructureDomainName().strip('"')) + ".\t\tIN\tCNAME\t" + \
                      str(nodeID) + "." + str(self.__dnsConfigInfo.getInfrastructureDomainName().strip('"')) + "."

        try:
            outputFile.write(string + "\n")
        except:
            print "Error while writing in ____writeDNSAlias"
