#!/usr/local/bin/python
##################################################################################################################
# inventory.py: back-end for the Inventory tab on the GUI
#
##################################################################################################################
import sys, os, time, cgi, xmlrpclib
temp = sys.path
sys.path.append("/usr/local/hen/lib/")
from henmanager import HenManager
from auxiliary.hen import findFirstNumberInString
###########################################################################################
#   Main execution
###########################################################################################            
manager = HenManager()
print "Content-Type: text/xml"
print ""
print ""

def convertParameterNames(parameters):
    newParameters = {}
    namesMapping = {}
    namesMapping["rackname"] = "rackName"
    namesMapping["powerswitch"] = "powerNodeID"
    namesMapping["powerswitchport"] = "powerNodePort"
    namesMapping["serial"] = "serialNodeID"
    namesMapping["serialport"] = "serialNodePort"
    namesMapping["serviceprocessor"] = "SPNodeID"
    namesMapping["rackrow"] = "rackRow"
    namesMapping["rackstartunit"] = "rackStartUnit"
    namesMapping["rackendunit"] = "rackEndUnit"    
    namesMapping["nodeposition"] = "nodePosition"
    namesMapping["rearrightslots"] = "rearRightSlots"
    namesMapping["rearleftslots"] = "rearLeftSlots"    
    namesMapping["numberunits"] = "numberUnits"
    namesMapping["externalmacaddress"] = "externalMACAddress"
    namesMapping["externalip"] = "externalIP"
    namesMapping["externalsubnet"] = "externalSubnet"
    namesMapping["ostype"] = "osType"
    namesMapping["mustclone"] = "mustClone"
    namesMapping["rowposition"] = "rowPosition"
    namesMapping["numberports"] = "numberPorts"
    
    for oldName in parameters.keys():
        if (namesMapping.has_key(oldName)):
            newParameters[namesMapping[oldName]] = parameters[oldName]
        else:
            newParameters[oldName] = parameters[oldName]
        
    return newParameters
    
def findElementType(elementID):
    nodes = manager.getNodes("all", "all")
    for nodeType in nodes.values():
        for node in nodeType.values():
            if (node.getNodeID() == elementID):
                return node.getNodeType()

    infrastructures = manager.getInfrastructures("all", "all")        
    for infrastructureType in infrastructures.values():
        for infrastructure in infrastructureType.values():
            if (infrastructure.getID() == elementID):
                return infrastructure.getType()

    fileNodes = manager.getFileNodes("all", "all")
    for fileNodeType in fileNodes.values():
        for fileNode in fileNodeType.values():
            if (fileNode.getID() == elementID):
                return fileNode.getType()

    return None

def sortElementIDs(elements, elementType):
    # Filter any elements that don't have their type as part of their ids
    filteredElements = []
    for element in elements:
        if (element.find(elementType) != -1):
            filteredElements.append(element)

    indexFirstNumber = findFirstNumberInString(filteredElements[0])

    numberList = []
    for element in filteredElements:
        numberList.append(int(element[indexFirstNumber:]))

    numberList.sort()
    elements = []
    for number in numberList:
        elements.append(elementType + str(number))

    return elements

def retrieveCGIParameters(parameterNames):
    
    values = {}
    for parameterName in parameterNames:
        if (form.has_key(parameterName)):
            values[parameterName] = form[parameterName].value

    return values

# Make sure that the necessary cgi parameters are given and retrieve them
form = cgi.FieldStorage()

if (not form.has_key("retrieve")):
    sys.exit()

retrieve = form["retrieve"].value

# Retrieve a brief description of all elements in the testbed
if (retrieve == "all"):
    print '<inventory>'

    # Get all nodes 
    nodes = manager.getNodes("all", "all")

    for nodeType in nodes.keys():
        specificNodeTypes = nodes[nodeType]
        print '\t<elementtype supertype="node" type="' + nodeType + '">\n'

        # Sort the nodes by their id names, this is done by sorting the keys of the dictionary
        nodeIDs = specificNodeTypes.keys()
        nodeIDs = sortElementIDs(nodeIDs, nodeType)        
        for nodeID in nodeIDs:
            node = specificNodeTypes[nodeID]

            if (nodeType == "computer"):
                print '\t\t<element status="' + node.getStatus() +'">'
                print '\t\t\t<attribute name="element id" value="' + str(node.getNodeID()) + '" />'
                print '\t\t\t<attribute name="# interfaces" value="' + str(len(node.getInterfaces("experimental"))) + '" />'
                print '\t\t\t<attribute name="power(power port)" value="' + \
                      str(node.getPowerNodeID()) + '(' + \
                      str(node.getPowerNodePort()) + ')" />'
                print '\t\t\t<attribute name="serial(serial port)" value="' + \
                      str(node.getSerialNodeID()) + '(' + \
                      str(node.getSerialNodePort()) + ')" />'
                print '\t\t\t<attribute name="serviceprocessor" value="' + str(node.getSPNodeID()) + '" />'
                print '\t\t\t<attribute name="memory" value="' + str(node.getSingleAttribute("memory")) + '" />'
                print '\t\t\t<attribute name="cpu" value="' + str(node.getSingleAttribute("cputype")) + '" />'
                print '\t\t\t<attribute name="cpu speed" value="' + str(node.getSingleAttribute("cpuspeed")) + '" />'
                print '\t\t\t<attribute name="# cpus" value="' + str(node.getSingleAttribute("numbercpus")) + '" />'
                print '\t\t\t<attribute name="serial #" value="' + str(node.getSingleAttribute("serialnumber")) + '" />'
                print '\t\t</element>'                
            elif (nodeType == "server"):
                print '\t\t<element status="' + node.getStatus() +'">'
                print '\t\t\t<attribute name="element id" value="' + str(node.getNodeID()) + '" />'
                print '\t\t\t<attribute name="# interfaces" value="' + str(len(node.getInterfaces("experimental"))) + '" />'
                print '\t\t\t<attribute name="serial(serial port)" value="' + \
                      str(node.getSerialNodeID()) + '(' + \
                      str(node.getSerialNodePort()) + ')" />'
                print '\t\t\t<attribute name="serviceprocessor" value="' + str(node.getSPNodeID()) + '" />'
                print '\t\t\t<attribute name="memory" value="' + str(node.getSingleAttribute("memory")) + '" />'
                print '\t\t\t<attribute name="cpu" value="' + str(node.getSingleAttribute("cputype")) + '" />'
                print '\t\t\t<attribute name="cpu speed" value="' + str(node.getSingleAttribute("cpuspeed")) + '" />'
                print '\t\t\t<attribute name="# cpus" value="' + str(node.getSingleAttribute("numbercpus")) + '" />'
                print '\t\t\t<attribute name="serial #" value="' + str(node.getSingleAttribute("serialnumber")) + '" />'
                print '\t\t</element>'                    
            elif (nodeType == "switch"):
                print '\t\t<element status="' + node.getStatus() +'">'
                print '\t\t\t<attribute name="element id" value="' + str(node.getNodeID()) + '" />'
                print '\t\t\t<attribute name="# ports" value="' + str(node.getSingleAttribute("numberports")) + '" />'
                print '\t\t\t<attribute name="power(power port)" value="' + \
                      str(node.getPowerNodeID()) + '(' + \
                      str(node.getPowerNodePort()) + ')" />'
                print '\t\t\t<attribute name="serial(serial port)" value="' + \
                      str(node.getSerialNodeID()) + '(' + \
                      str(node.getSerialNodePort()) + ')" />'
                print '\t\t\t<attribute name="vendor" value="' + str(node.getVendor()) + '" />'
                print '\t\t\t<attribute name="model" value="' + str(node.getModel()) + '" />'
                print '\t\t\t<attribute name="infrastructure" value="' + str(node.getInfrastructure()) + '" />'
                print '\t\t\t<attribute name="serial #" value="' + str(node.getSingleAttribute("serialnumber")) + '" />'
                print '\t\t</element>'                
            elif (nodeType == "serviceprocessor"):
                print '\t\t<element status="' + node.getStatus() +'">'                
                print '\t\t\t<attribute name="element id" value="' + str(node.getNodeID()) + '" />'
                print '\t\t\t<attribute name="power(power port)" value="' + \
                      str(node.getPowerNodeID()) + '(' + \
                      str(node.getPowerNodePort()) + ')" />'
                print '\t\t\t<attribute name="vendor" value="' + str(node.getVendor()) + '" />'
                print '\t\t\t<attribute name="model" value="' + str(node.getModel()) + '" />'
                print '\t\t\t<attribute name="serial #" value="' + str(node.getSingleAttribute("serialnumber")) + '" />'
                print '\t\t</element>'
            elif (nodeType == "serial"):
                print '\t\t<element status="' + node.getStatus() +'">'                
                print '\t\t\t<attribute name="element id" value="' + str(node.getNodeID()) + '" />'
                print '\t\t\t<attribute name="# ports" value="' + str(node.getSingleAttribute("numberports")) + '" />'
                print '\t\t\t<attribute name="power(power port)" value="' + \
                      str(node.getPowerNodeID()) + '(' + \
                      str(node.getPowerNodePort()) + ')" />'
                print '\t\t\t<attribute name="vendor" value="' + str(node.getVendor()) + '" />'
                print '\t\t\t<attribute name="model" value="' + str(node.getModel()) + '" />'
                print '\t\t\t<attribute name="serial #" value="' + str(node.getSingleAttribute("serialnumber")) + '" />'
                print '\t\t</element>'                
            elif (nodeType == "powerswitch"):
                print '\t\t<element status="' + node.getStatus() +'">'
                print '\t\t\t<attribute name="element id" value="' + str(node.getNodeID()) + '" />'
                print '\t\t\t<attribute name="# ports" value="' + str(node.getSingleAttribute("numberports")) + '" />'
                print '\t\t\t<attribute name="serial(serial port)" value="' + \
                      str(node.getSerialNodeID()) + '(' + \
                      str(node.getSerialNodePort()) + ')" />'
                print '\t\t\t<attribute name="vendor" value="' + str(node.getVendor()) + '" />'
                print '\t\t\t<attribute name="model" value="' + str(node.getModel()) + '" />'
                print '\t\t\t<attribute name="serial #" value="' + str(node.getSingleAttribute("serialnumber")) + '" />'
                print '\t\t</element>'

        print '\t</elementtype>'

    # Get all infrastructures
    infrastructures = manager.getInfrastructures("all", "all")
    for infrastructureType in infrastructures.keys():
        specificInfrastructureTypes = infrastructures[infrastructureType]
        print '\t<elementtype supertype="infrastructure" type="' + infrastructureType + '">\n'
        
        # Sort the infrastructures by their id names, this is done by sorting the keys of the dictionary
        infrastructureIDs = specificInfrastructureTypes.keys()
        infrastructureIDs = sortElementIDs(infrastructureIDs, infrastructureType)        
        for infrastructureID in infrastructureIDs:
            infrastructure = specificInfrastructureTypes[infrastructureID]            

            if (infrastructureType == "rack"):
                print '\t\t<element status="' + infrastructure.getStatus() +'">'                
                print '\t\t\t<attribute name="element id" value="' + str(infrastructure.getID()) + '" />'
                print '\t\t\t<attribute name="vendor" value="' + str(infrastructure.getVendor()) + '" />'
                print '\t\t\t<attribute name="model" value="' + str(infrastructure.getModel()) + '" />'
                print '\t\t\t<attribute name="description" value="' + str(infrastructure.getDescription()) + '" />'
                print '\t\t\t<attribute name="serial #" value="' + str(infrastructure.getSingleAttribute("serialnumber")) + '" />'
                print '\t\t</element>'

        print '\t</elementtype>'

    # Get all file nodes 
    fileNodes = manager.getFileNodes("all", "all")

    for fileNodeType in fileNodes.keys():
        specificFileNodeTypes = fileNodes[fileNodeType]
        print '\t<elementtype supertype="filenode" type="' + fileNodeType + '">\n'

        # Sort the fileNodes by their id names, this is done by sorting the keys of the dictionary
        fileNodeIDs = specificFileNodeTypes.keys()
        fileNodeIDs = sortElementIDs(fileNodeIDs, fileNodeType)        
        for fileNodeID in fileNodeIDs:
            fileNode = specificFileNodeTypes[fileNodeID]

            if (fileNodeType == "kernel" or fileNodeType == "loader" or fileNodeType == "filesystem"):
                print '\t\t<element status="' + fileNode.getStatus() +'">'                
                print '\t\t\t<attribute name="element id" value="' + str(fileNode.getID()) + '" />'
                print '\t\t\t<attribute name="path" value="' + str(fileNode.getPath()) + '" />'
                print '\t\t\t<attribute name="architecture" value="' + str(fileNode.getArchitecture()) + '" />'
                print '\t\t\t<attribute name="OS Type" value="' + str(fileNode.getOsType()) + '" />'
                print '\t\t\t<attribute name="version" value="' + str(fileNode.getVersion()) + '" />'
                print '\t\t\t<attribute name="must clone" value="' + str(fileNode.getMustClone()) + '" />'                
                print '\t\t</element>'                

        print '\t</elementtype>'
        
    print '\t</inventory>'

# Retrieve all of an element's information, use HTML
elif (retrieve == "element"):
    if (not form.has_key("elementid")):
        sys.exit()

    elementID = form["elementid"].value

    print "<inventory>"
    
    nodes = manager.getNodes("all", "all")
    for specificNodeTypes in nodes.values():
        for specificNode in specificNodeTypes.values():
            if (specificNode.getNodeID() == elementID):
                string = "<item>"
                counter = 0
                for letter in str(specificNode):
                    if (letter == "\n" and str(specificNode)[counter + 1] != "\n"):
                        string += "</item><item>"
                    elif (letter == "-"):
                        pass
                    else:
                        string += letter
                    ++counter
                string += "</item>"
                print string
                print "</inventory>"
                sys.exit()
                
    # the id given is not that of a node, search through the infrastructure ids
    infrastructures = manager.getInfrastructures("all", "all")
    for specificInfrastructureTypes in infrastructures.values():
        for specificInfrastructure in specificInfrastructureTypes.values():
            if (specificInfrastructure.getID() == elementID):
                string = "<item>"
                counter = 0
                for letter in str(specificInfrastructure):
                    if (letter == "\n" and str(specificInfrastructure)[counter + 1] != "\n"):
                        string += "</item><item>"
                    elif (letter == "-"):
                        pass
                    else:
                        string += letter
                    ++counter
                string += "</item>"
                print string
                print "</inventory>"
                sys.exit()

    # the id given is not that of a node nor infrastructure, search through the file node ids
    fileNodes = manager.getFileNodes("all", "all")
    for specificFileNodeTypes in fileNodes.values():
        for specificFileNode in specificFileNodeTypes.values():
            if (specificFileNode.getID() == elementID):
                string = "<item>"
                counter = 0
                for letter in str(specificFileNode):
                    if (letter == "\n" and str(specificFileNode)[counter + 1] != "\n"):
                        string += "</item><item>"
                    elif (letter == "-"):
                        pass
                    else:
                        string += letter
                    ++counter
                string += "</item>"
                print string
                print "</inventory>"
                sys.exit()                

    
# Retrieve all elements of one type along with information about them
elif (retrieve == "typedescription"):

    if (not form.has_key("type")):
        sys.exit()
        
    elementType = form["type"].value

    nodes = manager.getNodes(elementType, "all")
    infrastructures = manager.getInfrastructures(elementType, "all")
    fileNodes = manager.getFileNodes(elementType, "all")
    
    print '<inventory>'

    if (elementType == "computer"):
        
        # Sort the nodes by their id names, this is done by sorting the keys of the dictionary
        nodeIDs = nodes.keys()
        nodeIDs = sortElementIDs(nodeIDs, elementType)        
        for nodeID in nodeIDs:
            node = nodes[nodeID]
            print '\t\t<element status="' + node.getStatus() +'">'
            print '\t\t<attribute name="element id" value="' + str(nodeID) + '" />'
            experimentalInterfaces = node.getInterfaces("experimental")
            numberExperimentalInterfaces = 0
            if (experimentalInterfaces):
                numberExperimentalInterfaces = len(experimentalInterfaces)
                
            print '\t\t<attribute name="# exp interfaces" value="' + str(numberExperimentalInterfaces) + '" />'
            print '\t\t<attribute name="power(power port)" value="' + \
                  str(node.getPowerNodeID()) + '(' + \
                  str(node.getPowerNodePort()) + ')" />'
            print '\t\t<attribute name="serial(serial port)" value="' + \
                  str(node.getSerialNodeID()) + '(' + \
                  str(node.getSerialNodePort()) + ')" />'
            print '\t\t<attribute name="service processor" value="' + str(node.getSPNodeID()) + '" />'
            print '\t\t<attribute name="memory (in GB)" value="' + str(node.getSingleAttribute("memory")) + '" />'
            print '\t\t<attribute name="cpu" value="' + str(node.getSingleAttribute("cputype")) + '" />'
            print '\t\t<attribute name="cpu speed (in GHz)" value="' + str(node.getSingleAttribute("cpuspeed")) + '" />'
            print '\t\t<attribute name="# cpus" value="' + str(node.getSingleAttribute("numbercpus")) + '" />'
            print '\t\t<attribute name="# cores per cpu" value="' + str(node.getSingleAttribute("numbercorespercpu")) + '" />'
            print '\t\t<attribute name="serial #" value="' + str(node.getSingleAttribute("serialnumber")) + '" />'
            print '\t</element>'

    elif (elementType == "server"):
        # Sort the nodes by their id names, this is done by sorting the keys of the dictionary
        # Note that the function ignores any non-HEN servers

        nodeIDs = nodes.keys()
        nodeIDs = sortElementIDs(nodeIDs, elementType)        
        
        for nodeID in nodeIDs:        

            node = nodes[nodeID]
            print '\t\t<element status="' + node.getStatus() +'">'            
            print '\t\t<attribute name="element id" value="' + str(nodeID) + '" />'
            print '\t\t<attribute name="# interfaces" value="' + str(len(node.getInterfaces("experimental"))) + '" />'
            print '\t\t<attribute name="serial(serial port)" value="' + \
                  str(node.getSerialNodeID()) + '(' + \
                  str(node.getSerialNodePort()) + ')" />'
            print '\t\t<attribute name="serviceprocessor" value="' + str(node.getSPNodeID()) + '" />'
            print '\t\t<attribute name="memory" value="' + str(node.getSingleAttribute("memory")) + '" />'
            print '\t\t<attribute name="cpu" value="' + str(node.getSingleAttribute("cputype")) + '" />'
            print '\t\t<attribute name="cpu speed" value="' + str(node.getSingleAttribute("cpuspeed")) + '" />'
            print '\t\t<attribute name="# cpus" value="' + str(node.getSingleAttribute("numbercpus")) + '" />'
            print '\t\t<attribute name="serial #" value="' + str(node.getSingleAttribute("serialnumber")) + '" />'
            print '\t</element>'            
            
    elif (elementType == "switch"):
        # Sort the nodes by their id names, this is done by sorting the keys of the dictionary
        nodeIDs = nodes.keys()
        nodeIDs = sortElementIDs(nodeIDs, elementType)        
        for nodeID in nodeIDs:        
            node = nodes[nodeID]        
            print '\t\t<element status="' + node.getStatus() +'">'            
            print '\t\t<attribute name="element id" value="' + str(nodeID) + '" />'
            print '\t\t<attribute name="# ports" value="' + str(node.getSingleAttribute("numberports")) + '" />'
            print '\t\t<attribute name="power(power port)" value="' + \
                  str(node.getPowerNodeID()) + '(' + \
                  str(node.getPowerNodePort()) + ')" />'
            print '\t\t<attribute name="serial(serial port)" value="' + \
                  str(node.getSerialNodeID()) + '(' + \
                  str(node.getSerialNodePort()) + ')" />'
            print '\t\t<attribute name="vendor" value="' + str(node.getVendor()) + '" />'
            print '\t\t<attribute name="model" value="' + str(node.getModel()) + '" />'
            print '\t\t<attribute name="infrastructure" value="' + str(node.getInfrastructure()) + '" />'
            print '\t\t<attribute name="serial #" value="' + str(node.getSingleAttribute("serialnumber")) + '" />'            
            print '\t</element>'

    elif (elementType == "serviceprocessor"):
        # Sort the nodes by their id names, this is done by sorting the keys of the dictionary
        nodeIDs = nodes.keys()
        nodeIDs = sortElementIDs(nodeIDs, elementType)        
        for nodeID in nodeIDs:        
            node = nodes[nodeID]        
            print '\t\t<element status="' + node.getStatus() +'">'            
            print '\t\t<attribute name="element id" value="' + str(nodeID) + '" />'
            print '\t\t<attribute name="power(power port)" value="' + \
                  str(node.getPowerNodeID()) + '(' + \
                  str(node.getPowerNodePort()) + ')" />'
            print '\t\t<attribute name="vendor" value="' + str(node.getVendor()) + '" />'
            print '\t\t<attribute name="model" value="' + str(node.getModel()) + '" />'
            print '\t\t<attribute name="serial #" value="' + str(node.getSingleAttribute("serialnumber")) + '" />'            
            print '\t</element>'            

    elif (elementType == "serial"):
        # Sort the nodes by their id names, this is done by sorting the keys of the dictionary
        nodeIDs = nodes.keys()
        nodeIDs = sortElementIDs(nodeIDs, elementType)        
        for nodeID in nodeIDs:        
            node = nodes[nodeID]        
            print '\t\t<element status="' + node.getStatus() +'">'            
            print '\t\t<attribute name="element id" value="' + str(nodeID) + '" />'
            print '\t\t<attribute name="# ports" value="' + str(node.getSingleAttribute("numberports")) + '" />'
            print '\t\t<attribute name="power(power port)" value="' + \
                  str(node.getPowerNodeID()) + '(' + \
                  str(node.getPowerNodePort()) + ')" />'
            print '\t\t<attribute name="vendor" value="' + str(node.getVendor()) + '" />'
            print '\t\t<attribute name="model" value="' + str(node.getModel()) + '" />'
            print '\t\t<attribute name="serial #" value="' + str(node.getSingleAttribute("serialnumber")) + '" />'            
            print '\t</element>'

    elif (elementType == "powerswitch"):
        # Sort the nodes by their id names, this is done by sorting the keys of the dictionary
        nodeIDs = nodes.keys()
        nodeIDs = sortElementIDs(nodeIDs, elementType)        
        for nodeID in nodeIDs:        
            node = nodes[nodeID]        
            print '\t\t<element status="' + node.getStatus() +'">'            
            print '\t\t<attribute name="element id" value="' + str(nodeID) + '" />'
            print '\t\t<attribute name="# ports" value="' + str(node.getSingleAttribute("numberports")) + '" />'
            print '\t\t<attribute name="serial(serial port)" value="' + \
                  str(node.getSerialNodeID()) + '(' + \
                  str(node.getSerialNodePort()) + ')" />'
            print '\t\t<attribute name="vendor" value="' + str(node.getVendor()) + '" />'
            print '\t\t<attribute name="model" value="' + str(node.getModel()) + '" />'
            print '\t\t<attribute name="serial #" value="' + str(node.getSingleAttribute("serialnumber")) + '" />'            
            print '\t</element>'
            
    elif (elementType == "rack"):
        # Sort the infrastructures by their id names, this is done by sorting the keys of the dictionary
        infrastructureIDs = infrastructures.keys()
        infrastructureIDs = sortElementIDs(infrastructureIDs, elementType)        
        for infrastructureID in infrastructureIDs:
            infrastructure = infrastructures[infrastructureID]

            print '\t\t<element status="' + infrastructure.getStatus() +'">'            
            print '\t\t<attribute name="element id" value="' + str(infrastructureID) + '" />'
            print '\t\t<attribute name="vendor" value="' + str(infrastructure.getVendor()) + '" />'
            print '\t\t<attribute name="model" value="' + str(infrastructure.getModel()) + '" />'
            print '\t\t<attribute name="description" value="' + str(infrastructure.getDescription()) + '" />'
            print '\t\t<attribute name="serial #" value="' + str(infrastructure.getSingleAttribute("serialnumber")) + '" />'            
            print '\t</element>'

    elif (elementType == "kernel" or elementType == "loader" or elementType == "filesystem"):
        # Sort the fileNodes by their id names, this is done by sorting the keys of the dictionary
        fileNodeIDs = fileNodes.keys()
        fileNodeIDs = sortElementIDs(fileNodeIDs, elementType)        
        for fileNodeID in fileNodeIDs:
            fileNode = fileNodes[fileNodeID]        

            print '\t\t<element status="' + fileNode.getStatus() +'">'                
            print '\t\t\t<attribute name="element id" value="' + str(fileNode.getID()) + '" />'
            print '\t\t\t<attribute name="path" value="' + str(fileNode.getPath()) + '" />'
            print '\t\t\t<attribute name="architecture" value="' + str(fileNode.getArchitecture()) + '" />'
            print '\t\t\t<attribute name="OS Type" value="' + str(fileNode.getOsType()) + '" />'
            print '\t\t\t<attribute name="version" value="' + str(fileNode.getVersion()) + '" />'
            print '\t\t\t<attribute name="must clone" value="' + str(fileNode.getMustClone()) + '" />'                
            print '\t\t</element>'                
                
    print '</inventory>'
    

# Retrieve only the ids of all elements of one type    
elif (retrieve == "type"):
    
    if (not form.has_key("type")):
        sys.exit()
        
    elementType = form["type"].value

    nodes = manager.getNodes(elementType, "all")
    infrastructures = manager.getInfrastructures(elementType, "all")
    fileNodes = manager.getFileNodes(elementType, "all")
    
    print '<inventory>'
    if (nodes):
        for nodeID in nodes.keys():
            print '<element id="' + str(nodeID) + '" />'
    elif (infrastructures):
        if (infrastructures):
            for infrastructureID in infrastructures.keys():
                print '<element id="' + str(infrastructureID) + '" />'
    elif (fileNodes):
        if (fileNodes):
            for fileNodeID in fileNodes.keys():
                print '<element id="' + str(fileNodeID) + '" />'                
    
    print '</inventory>'
    
# Retrieve all of the types of elements on the testbed 
elif (retrieve == "types"):
    
    nodes = manager.getNodes("all", "all")
    infrastructures = manager.getInfrastructures("all", "all")
    fileNodes = manager.getFileNodes("all", "all")

    print '<inventory>'
    for nodeType in nodes.keys():
        print '<nodetype value="' + str(nodeType) + '" />' 
        
    for infrastructureType in infrastructures.keys():
        print '<infrastructuretype value="' + str(infrastructureType) + '" />'

    for fileNodeType in fileNodes.keys():
        print '<filenodetype value="' + str(fileNodeType) + '" />'        
        
    print '</inventory>'

# Retrieve all of the types supported by the testbed
elif (retrieve == "alltypes"):
    print '<inventory>'    
    for elementType in manager.parser.getTestbedElementsTypes():
        print '<elementtype value="' + str(elementType) + '" />'
        
    print '</inventory>'

# Retrieve all of the node types supported by the testbed
elif (retrieve == "nodetypes"):
    print '<inventory>'    
    for elementType in manager.parser.getNodeElementTypes():
        print '<elementtype value="' + str(elementType) + '" />'
        
    print '</inventory>'
    
# Retrieve the ids of all elements in the testbed
elif (retrieve == "allelements"):
    nodes = manager.getNodes("all", "all")
    infrastructures = manager.getInfrastructures("all", "all")
    fileNodes = manager.getFileNodes("all", "all")

    print '<inventory>'
    for nodeType in nodes.values():
        for nodeID in nodeType.keys():
            theType = nodeType[nodeID].getNodeType()
            print '<element id="' + str(nodeID) + '" type="' + str(theType) + '" />' 

    for infrastructureType in infrastructures.values():
        for infrastructureID in infrastructureType.keys():
            theType = infrastructureType[infrastructureID].getType()
            print '<element id="' + str(infrastructureID) + '" type="' + str(theType) + '" />' 

    for fileNodeType in fileNodes.values():
        for fileNodeID in fileNodeType.keys():
            theType = fileNodeType[fileNodeID].getType()
            print '<element id="' + str(fileNodeID) + '" type="' + str(theType) + '" />' 
        
    print '</inventory>'    

# Retrieve all editable information for the given element
elif (retrieve == "elementedit"):
    if (not form.has_key("elementid")):
        sys.exit()

    elementID = form["elementid"].value

    nodes = manager.getNodes("all", "all")
    infrastructures = manager.getInfrastructures("all", "all")
    fileNodes = manager.getFileNodes("all", "all")
    theElement = None
    
    print '<inventory>'

    for nodeTypeDictionary in nodes.values():
        for node in nodeTypeDictionary.values():
            if (node.getNodeID() == elementID):
                theElement = node
                nodeType = node.getNodeType()

                print '<element id="' + str(node.getNodeID()) + '" type="' + str(nodeType) + '" >'
                
                physicalLocation = node.getPhysicalLocation()
                if (nodeType == "computer"):
                    
                    macAddress = str(node.getInterfaces("management")[0].getMAC())
                    print '\t<property name="macaddress" value="' + macAddress + '" />'
                    print '\t<property name="status" value="' + str(node.getStatus()) + '" />'
                    print '\t<property name="vendor" value="' + str(node.getVendor()) + '" />'
                    print '\t<property name="model" value="' + str(node.getModel()) + '" />'
                    print '\t<property name="serviceprocessor" value="' + str(node.getSPNodeID()) + '" />'
                    print '\t<property name="netbootable" value="' + str(node.getNetbootable()) + '" />'
                    print '\t<property name="infrastructure" value="' + str(node.getInfrastructure()) + '" />'
                    print '\t<property name="powerswitch" value="' + str(node.getPowerNodeID()) + '" />'
                    print '\t<property name="powerswitchport" value="' + str(node.getPowerNodePort()) + '" />'
                    print '\t<property name="serial" value="' + str(node.getSerialNodeID()) + '" />'
                    print '\t<property name="serialport" value="' + str(node.getSerialNodePort()) + '" />'

                elif (nodeType == "server"):
                    managementMACAddress = str(node.getInterfaces("management")[0].getMAC())
                    infrastructureMACAddress = str(node.getInterfaces("infrastructure")[0].getMAC())
                    externalMACAddress = str(node.getInterfaces("external")[0].getMAC())
                    externalIPAddress = str(node.getInterfaces("external")[0].getIP())
                    externalSubnetAddress = str(node.getInterfaces("external")[0].getSubnet())                    

                    print '\t<property name="vendor" value="' + str(node.getVendor()) + '" />'
                    print '\t<property name="model" value="' + str(node.getModel()) + '" />'                    
                    print '\t<property name="managementmacaddress" value="' + managementMACAddress + '" />'
                    print '\t<property name="infrastructuremacaddress" value="' + infrastructureMACAddress + '" />'
                    print '\t<property name="externalmacaddress" value="' + externalMACAddress + '" />'
                    print '\t<property name="externalip" value="' + externalIPAddress + '" />'
                    print '\t<property name="externalsubnet" value="' + externalSubnetAddress + '" />'                    
                    print '\t<property name="status" value="' + str(node.getStatus()) + '" />'
                    print '\t<property name="serviceprocessor" value="' + str(node.getSPNodeID()) + '" />'
                    print '\t<property name="netbootable" value="' + str(node.getNetbootable()) + '" />'
                    print '\t<property name="infrastructure" value="' + str(node.getInfrastructure()) + '" />'
                    print '\t<property name="powerswitch" value="' + str(node.getPowerNodeID()) + '" />'
                    print '\t<property name="powerswitchport" value="' + str(node.getPowerNodePort()) + '" />'
                    print '\t<property name="serial" value="' + str(node.getSerialNodeID()) + '" />'
                    print '\t<property name="serialport" value="' + str(node.getSerialNodePort()) + '" />'
                     
                elif ( (nodeType == "switch") or (nodeType == "router") ):
                    if (node.getInterfaces("infrastructure")):                        
                        macAddress = str(node.getInterfaces("infrastructure")[0].getMAC())
                        print '\t<property name="macaddress" value="' + macAddress + '" />'
                    elif (node.getInterfaces("management")):
                        macAddress = str(node.getInterfaces("management")[0].getMAC())
                        print '\t<property name="macaddress" value="' + macAddress + '" />'                        
                    print '\t<property name="status" value="' + str(node.getStatus()) + '" />'                    
                    print '\t<property name="vendor" value="' + str(node.getVendor()) + '" />'
                    print '\t<property name="model" value="' + str(node.getModel()) + '" />'
                    print '\t<property name="infrastructure" value="' + str(node.getInfrastructure()) + '" />'
                    print '\t<property name="powerswitch" value="' + str(node.getPowerNodeID()) + '" />'
                    print '\t<property name="powerswitchport" value="' + str(node.getPowerNodePort()) + '" />'
                    print '\t<property name="serial" value="' + str(node.getSerialNodeID()) + '" />'
                    print '\t<property name="serialport" value="' + str(node.getSerialNodePort()) + '" />'
                    # Special case, this is  saved as an attribute but displayed as input on the GUI
                    attributes = theElement.getAttributes()
                    if (attributes and attributes.has_key("numberports")):
                        attributes["numberports"]
                        print '\t<property name="numberports" value="' + str(attributes["numberports"]) + '" />'

                elif (nodeType == "powerswitch"):
                    macAddress = str(node.getInterfaces("infrastructure")[0].getMAC())
                    username = node.getUsers()[0].getUsername()
                    password = node.getUsers()[0].getPassword()
                    print '\t<property name="status" value="' + str(node.getStatus()) + '" />'                    
                    print '\t<property name="macaddress" value="' + macAddress + '" />'
                    print '\t<property name="vendor" value="' + str(node.getVendor()) + '" />'
                    print '\t<property name="model" value="' + str(node.getModel()) + '" />'
                    print '\t<property name="serial" value="' + str(node.getSerialNodeID()) + '" />'
                    print '\t<property name="serialport" value="' + str(node.getSerialNodePort()) + '" />'
                    print '\t<property name="username" value="' + str(username) + '" />'
                    print '\t<property name="password" value="' + str(password) + '" />'                    
                    # Special case, this is  saved as an attribute but displayed as input on the GUI
                    attributes = theElement.getAttributes()
                    if (attributes):
                        attributes["numberports"]
                        print '\t<property name="numberports" value="' + str(attributes["numberports"]) + '" />'

                elif (nodeType == "serial"):
                    macAddress = str(node.getInterfaces("infrastructure")[0].getMAC())
                    username = node.getUsers()[0].getUsername()
                    password = node.getUsers()[0].getPassword()
                    print '\t<property name="status" value="' + str(node.getStatus()) + '" />'                    
                    print '\t<property name="macaddress" value="' + macAddress + '" />'
                    print '\t<property name="vendor" value="' + str(node.getVendor()) + '" />'
                    print '\t<property name="model" value="' + str(node.getModel()) + '" />'
                    print '\t<property name="powerswitch" value="' + str(node.getPowerNodeID()) + '" />'
                    print '\t<property name="powerswitchport" value="' + str(node.getPowerNodePort()) + '" />'
                    print '\t<property name="username" value="' + str(username) + '" />'
                    print '\t<property name="password" value="' + str(password) + '" />'                    
                    # Special case, this is  saved as an attribute but displayed as input on the GUI
                    attributes = theElement.getAttributes()
                    if (attributes):
                        attributes["numberports"]
                        print '\t<property name="numberports" value="' + str(attributes["numberports"]) + '" />'
                    
                elif (nodeType == "serviceprocessor"):
                    macAddress = str(node.getInterfaces("infrastructure")[0].getMAC())
                    username = node.getUsers()[0].getUsername()
                    password = node.getUsers()[0].getPassword()
                    print '\t<property name="status" value="' + str(node.getStatus()) + '" />'                    
                    print '\t<property name="macaddress" value="' + macAddress + '" />'
                    print '\t<property name="vendor" value="' + str(node.getVendor()) + '" />'
                    print '\t<property name="model" value="' + str(node.getModel()) + '" />'
                    print '\t<property name="powerswitch" value="' + str(node.getPowerNodeID()) + '" />'
                    print '\t<property name="powerswitchport" value="' + str(node.getPowerNodePort()) + '" />'
                    print '\t<property name="username" value="' + str(username) + '" />'
                    print '\t<property name="password" value="' + str(password) + '" />'

                if (nodeType != "serviceprocessor"):
                    if (physicalLocation):
                        print '\t<property name="building" value="' + str(physicalLocation.getBuilding()) + '" />'
                        print '\t<property name="floor" value="' + str(physicalLocation.getFloor()) + '" />'
                        print '\t<property name="room" value="' + str(physicalLocation.getRoom()) + '" />'
                        print '\t<property name="rackrow" value="' + str(physicalLocation.getRackRow()) + '" />'
                        print '\t<property name="rackname" value="' + str(physicalLocation.getRackName()) + '" />'
                        print '\t<property name="rackstartunit" value="' + str(physicalLocation.getRackStartUnit()) + '" />'
                        print '\t<property name="rackendunit" value="' + str(physicalLocation.getRackEndUnit()) + '" />'
                        print '\t<property name="nodeposition" value="' + str(physicalLocation.getNodePosition()) + '" />'
                    else:
                        print '\t<property name="building" value="None" />'
                        print '\t<property name="floor" value="None" />'
                        print '\t<property name="room" value="None" />'
                        print '\t<property name="rackrow" value="None" />'
                        print '\t<property name="rackname" value="None" />'
                        print '\t<property name="rackstartunit" value="None" />'
                        print '\t<property name="rackendunit" value="None" />'
                        print '\t<property name="nodeposition" value="None" />'

                # Print any attributes
                attributes = theElement.getAttributes()
                if (attributes):
                    for attributeName in attributes.keys():
                        if (attributeName != "numberports"):
                            print '\t<attribute name="' + str(attributeName) + \
                                  '" value="' + str(attributes[attributeName]) + '" />'
                    
                print '</element>'
                break

    # Requested element is not a node, search infrastructures
    if (not theElement):
        for infrastructureTypeDictionary in infrastructures.values():
            for infrastructure in infrastructureTypeDictionary.values():
                if (infrastructure.getID() == elementID):
                    theElement = infrastructure
                    infrastructureType = infrastructure.getType()

                    print '<element id="' + str(infrastructure.getID()) + '" type="' + str(infrastructureType) + '" >'

                    physicalSize = infrastructure.getPhysicalSize();
                    if (infrastructureType == "rack"):
                        print '\t<property name="status" value="' + str(node.getStatus()) + '" />'                        
                        print '\t<property name="vendor" value="' + str(infrastructure.getVendor()) + '" />'
                        print '\t<property name="model" value="' + str(infrastructure.getModel()) + '" />'
                        print '\t<property name="description" value="' + str(infrastructure.getDescription()) + '" />'
                        print '\t<property name="building" value="' + str(infrastructure.getBuilding()) + '" />'
                        print '\t<property name="floor" value="' + str(infrastructure.getFloor()) + '" />'
                        print '\t<property name="room" value="' + str(infrastructure.getRoom()) + '" />'
                        print '\t<property name="rackrow" value="' + str(infrastructure.getRackRow()) + '" />'
                        print '\t<property name="height" value="' + str(physicalSize.getHeight()) + '" />'
                        print '\t<property name="width" value="' + str(physicalSize.getWidth()) + '" />'
                        print '\t<property name="depth" value="' + str(physicalSize.getDepth()) + '" />'
                        print '\t<property name="numberunits" value="' + str(physicalSize.getNumberUnits()) + '" />'

                        # Special case, these are saved as attributes but displayed as inputs on the GUI
                        attributes = theElement.getAttributes()
                        if (attributes):
                            for attributeName in attributes.keys():
                                if ( (attributeName == "rearrightslots") or (attributeName == "rearleftslots") or
                                     (attributeName == "rackrow") or (attributeName == "rowposition") ):
                                    print '\t<property name="' + str(attributeName) + \
                                          '" value="' + str(attributes[attributeName]) + '" />'

                    # Print any attributes
                    attributes = theElement.getAttributes()
                    if (attributes):
                        for attributeName in attributes.keys():
                            if ( (attributeName != "rearrightslots") and (attributeName != "rearleftslots") and
                                 (attributeName != "rackrow") and (attributeName != "rowposition") ):
                                print '\t<attribute name="' + str(attributeName) + \
                                      '" value="' + str(attributes[attributeName]) + '" />'
                    
                    print '</element>'
                    break 

    # Requested element is not a node nor an infrastructure, search file nodes
    if (not theElement):
        for fileNodeTypeDictionary in fileNodes.values():
            for fileNode in fileNodeTypeDictionary.values():
                if (fileNode.getID() == elementID):
                    theElement = fileNode
                    fileNodeType = fileNode.getType()

                    print '<element id="' + str(fileNode.getID()) + '" type="' + str(fileNodeType) + '" >'
                    
                    print '\t<property name="status" value="' + str(node.getStatus()) + '" />'
                    print '\t<property name="path" value="' + str(fileNode.getPath()) + '" />'
                    print '\t<property name="owner" value="' + str(fileNode.getOwner()) + '" />'                    
                    print '\t<property name="architecture" value="' + str(fileNode.getArchitecture()) + '" />'
                    print '\t<property name="ostype" value="' + str(fileNode.getOsType()) + '" />'
                    print '\t<property name="version" value="' + str(fileNode.getVersion()) + '" />'
                    print '\t<property name="mustclone" value="' + str(fileNode.getMustClone()) + '" />'
                    print '\t<property name="description" value="' + str(fileNode.getDescription()) + '" />'

                    if (fileNodeType == "kernel"):
                        pass
                    elif (fileNodeType == "loader"):
                        pass
                    elif (fileNodeType == "filesystem"):
                        if (fileNode.getUserManagement() and fileNode.getUserManagement()[0]):
                            username = fileNode.getUserManagement()[0].getUsername()
                            password = fileNode.getUserManagement()[0].getPassword()
                            print '\t<property name="username" value="' + str(username) + '" />'
                            print '\t<property name="password" value="' + str(password) + '" />'

                    # Print any attributes
                    attributes = theElement.getAttributes()
                    if (attributes):
                        for attributeName in attributes.keys():
                            print '\t<attribute name="' + str(attributeName) + \
                                  '" value="' + str(attributes[attributeName]) + '" />'
                    
                    print '</element>'
                    break                     
                    
    print '</inventory>'

# Retrieve all the allowed status values for the given element type
elif (retrieve == "statuses"):
    if (not form.has_key("elementtype")):
        sys.exit()

    elementType = form["elementtype"].value

    print '<inventory>'

    elementTypeFound = False
    if (elementType in manager.parser.getNodeElementTypes()):
        elementTypeFound = True
        for status in manager.parser.getNodeStatuses():
            print '<status id="' + str(status) + '" />'

    if (not elementTypeFound):
        if (elementType in manager.parser.getInfrastructureElementTypes()):
            elementTypeFound = True
            for status in manager.parser.getInfrastructureStatuses():
                print '<status id="' + str(status) + '" />'

    if (not elementTypeFound):
        if (elementType in manager.parser.getFileNodeElementTypes()):
            elementTypeFound = True
            for status in manager.parser.getTestbedFileStatuses():
                print '<status id="' + str(status) + '" />'                
                
    print '</inventory>'

elif (retrieve == "orphans"):
    print '<inventory>'

    try:
        #server = xmlrpclib.ServerProxy(uri="http://127.0.0.1:50003")
        #node = server.getMarshalledXml()
        if (node == ""):
            pass    # no orphan nodes
        else:
            print node
    except Exception, e:
        pass

    print '</inventory>'

# Retrieve information about which vendor/models are supported for a particular element type
elif (retrieve == "supportedhardware"):
    if (not form.has_key("elementtype")):
        sys.exit()

    elementType = form["elementtype"].value

    print '<inventory>'

    supportedHardware = manager.getSupportedHardware(elementType);

    for vendor in supportedHardware.keys():
        print '\t<vendor id="' + str(vendor) + '" >'        
        for model in supportedHardware[vendor]:
            print '\t\t<model id="' + str(model) + '" />'
        print '\t</vendor>'
        
    print '</inventory>'
    
# Retrieve information used to populate select boxes with (power switch id/port, serial id/port, etc)
elif (retrieve == "populateselectboxes"):
    print '<inventory>'

    nodes = manager.getNodes("all")

    # Find any unassigned service processors
    serviceProcessorIDs = manager.getNodes("serviceprocessor").keys()
    assignedServiceProcessorIDs = []
    for computerNode in manager.getNodes("computer").values():
        if (computerNode.getSPNodeID() and computerNode.getSPNodeID() != "none"):
            assignedServiceProcessorIDs.append(computerNode.getSPNodeID())

    for serviceProcessorID in serviceProcessorIDs:
        if (serviceProcessorID not in assignedServiceProcessorIDs):
            print '\t<serviceprocessor id="' + str(serviceProcessorID) + '" />'

    # Find any unassigned ports on power switches
    for powerswitchID in manager.getNodes("powerswitch").keys():
        assignedPowerPorts = []
        for nodeTypes in nodes.values():
            for node in nodeTypes.values():
                # service processors share the same power port with the computers they're on, ignore this case
                if ( (node.getPowerNodeID() == powerswitchID) and (node.getNodeType() != "serviceprocessor") ):
                    assignedPowerPorts.append(node.getPowerNodePort())

        print powerswitchID
        numberPorts = int(manager.getNodes("powerswitch")[powerswitchID].getSingleAttribute("numberports"))
        unassignedPowerPorts = []
        for port in range(1, numberPorts + 1):
            if (str(port) not in assignedPowerPorts):
                unassignedPowerPorts.append(port)

        if (len(unassignedPowerPorts) > 0):
            print '\t<powerswitch id="' + str(powerswitchID) + '" >'

            for unassignedPort in unassignedPowerPorts:
                print '\t\t<port number="' + str(unassignedPort) + '" />'
            print '\t</powerswitch>'
    
    # Find any unassigned ports on serial servers
    for serialID in manager.getNodes("serial").keys():
        assignedSerialPorts = []
        for nodeTypes in nodes.values():
            for node in nodeTypes.values():
                if (node.getSerialNodeID() == serialID):
                    assignedSerialPorts.append(node.getSerialNodePort())

        print manager.getNodes("serial")[serialID].getSingleAttribute("numberports"), serialID
        numberPorts = int(manager.getNodes("serial")[serialID].getSingleAttribute("numberports"))
        unassignedSerialPorts = []
        for port in range(1, numberPorts + 1):
            if (str(port) not in assignedSerialPorts):
                unassignedSerialPorts.append(port)

        if (len(unassignedSerialPorts) > 0):
            print '\t<serial id="' + str(serialID) + '" >'

            for unassignedPort in unassignedSerialPorts:
                print '\t\t<port number="' + str(unassignedPort) + '" />'
            print '\t</serial>'

    # Retrieve unused units in the racks
    for rackID in manager.getInfrastructures("rack").keys():
        assignedRackUnits = []
        for nodeTypes in nodes.values():
            for node in nodeTypes.values():
                physicalLocation = node.getPhysicalLocation()
                if (physicalLocation and physicalLocation.getRackName() == rackID):
                    startUnit = physicalLocation.getRackStartUnit()
                    endUnit = physicalLocation.getRackEndUnit()

                    if (startUnit):
                        for x in range(int(startUnit), int(endUnit) + 1):
                            assignedRackUnits.append(str(x))

        numberUnits = int(manager.getInfrastructures("rack")[rackID].getPhysicalSize().getNumberUnits())
        unassignedRackUnits = []
        for unit in range(1, numberUnits + 1):
            if (str(unit) not in assignedRackUnits):
                unassignedRackUnits.append(unit)

        if (len(unassignedRackUnits) > 0):
            print '\t<rack id="' + str(rackID) + '" >'

            for unassignedUnit in unassignedRackUnits:
                print '\t\t<unit number="' + str(unassignedUnit) + '" />'
            print '\t</rack>'

    print '</inventory>'


# Add an inventory element to the testbed
elif (retrieve == "addelement"):

    parameterNames = ["elementtype", "status", "serviceprocessor", "netbootable", "infrastructure", "powerswitch", \
                      "powerswitchport", "serial", "serialport", "building", "floor", "room", "rackrow", "rackname", \
                      "rackstartunit", "rackendunit", "nodeposition", "vendor", "model", "username", "password", \
                      "description", "height", "width", "depth", "rearrightslots", "rearleftslots", "numberunits", \
                      "managementmacaddress", "infrastructuremacaddress", "externalmacaddress", "externalip", \
                      "externalsubnet", "macaddress", "architecture", "ostype", "version", "mustclone", "owner", \
                      "rowposition", "path"]
    parameters = retrieveCGIParameters(parameterNames)

    # The attributes are anything after all the regular parameters that actually exist
    attributes = {}
    counter = 0
    for key in form.keys():
        if (counter > len(parameters)):
            attributes[key] = form[key].value
        counter += 1

    server = xmlrpclib.ServerProxy(uri="http://localhost:50006/")
    if (parameters["elementtype"] == "computer"):
        (result, newID) = server.computerNodeCreate(parameters["netbootable"], parameters["infrastructure"], \
                                                    parameters["rackname"], parameters["macaddress"], \
                                                    parameters["powerswitch"], parameters["powerswitchport"], \
                                                    parameters["serial"], parameters["serialport"], \
                                                    parameters["serviceprocessor"], attributes, \
                                                    parameters["building"], parameters["floor"], \
                                                    parameters["room"], parameters["rackrow"], \
                                                    parameters["rackstartunit"], parameters["rackendunit"], \
                                                    parameters["nodeposition"], parameters["status"], \
                                                    parameters["vendor"], parameters["model"])
        
    elif (parameters["elementtype"] == "server"):
        (result, newID) = server.serverNodeCreate(parameters["rackname"], parameters["serial"], \
                                                  parameters["serialport"], parameters["managementmacaddress"], \
                                                  parameters["infrastructuremacaddress"], parameters["externalmacaddress"], \
                                                  parameters["externalip"], parameters["externalsubnet"], \
                                                  attributes, parameters["building"], \
                                                  parameters["floor"], parameters["room"], \
                                                  parameters["rackrow"], parameters["rackstartunit"], \
                                                  parameters["rackendunit"], parameters["nodeposition"], \
                                                  parameters["powerswitch"], parameters["powerswitchport"], \
                                                  parameters["serviceprocessor"], parameters["status"], \
                                                  parameters["vendor"], parameters["model"])
        
    elif (parameters["elementtype"] == "serial"):
        (result, newID) = server.serialNodeCreate(parameters["vendor"], parameters["model"], \
                                                  parameters["macaddress"], parameters["powerswitch"], \
                                                  parameters["powerswitchport"], parameters["username"], \
                                                  parameters["password"], parameters["rackname"], \
                                                  attributes, parameters["building"], \
                                                  parameters["floor"], parameters["room"], \
                                                  parameters["rackrow"], parameters["rackstartunit"], \
                                                  parameters["rackendunit"], parameters["nodeposition"], \
                                                  parameters["status"]) 
        
    elif (parameters["elementtype"] == "switch"):
        (result, newID) = server.switchNodeCreate(parameters["infrastructure"], parameters["vendor"], \
                                                  parameters["model"], parameters["macaddress"], \
                                                  parameters["powerswitch"], parameters["powerswitchport"], \
                                                  parameters["serial"], parameters["serialport"], \
                                                  parameters["rackname"], attributes, \
                                                  parameters["building"], parameters["floor"], \
                                                  parameters["room"], parameters["rackrow"], \
                                                  parameters["rackstartunit"], parameters["rackendunit"], \
                                                  parameters["nodeposition"], parameters["status"])

    elif (parameters["elementtype"] == "router"):
        (result, newID) = server.routerNodeCreate(parameters["vendor"], parameters["model"], \
                                                  parameters["macaddress"], parameters["powerswitch"], \
                                                  parameters["powerswitchport"], parameters["serial"], \
                                                  parameters["serialport"], parameters["rackname"], \
                                                  attributes, parameters["building"], \
                                                  parameters["floor"], parameters["room"], \
                                                  parameters["rackrow"], parameters["rackstartunit"], \
                                                  parameters["rackendunit"], parameters["nodeposition"], \
                                                  parameters["status"]) 
                
    elif (parameters["elementtype"] == "powerswitch"):
        (result, newID) = server.powerswitchNodeCreate(parameters["vendor"], parameters["model"], \
                                                       parameters["macaddress"], parameters["serial"], \
                                                       parameters["serialport"], parameters["rackname"], \
                                                       parameters["username"], parameters["password"], \
                                                       attributes, parameters["building"], \
                                                       parameters["floor"], parameters["room"], \
                                                       parameters["rackrow"], parameters["rackstartunit"], \
                                                       parameters["rackendunit"], parameters["nodeposition"], \
                                                       parameters["status"])

    elif (parameters["elementtype"] == "serviceprocessor"):
        (result, newID) = server.serviceprocessorNodeCreate(parameters["macaddress"], parameters["powerswitch"], \
                                                            parameters["powerswitchport"], parameters["username"], \
                                                            parameters["password"], attributes, \
                                                            parameters["status"], parameters["vendor"], \
                                                            parameters["model"])
        
    elif (parameters["elementtype"] == "rack"):
        (result, newID) = server.infrastructureRackCreate(parameters["vendor"], parameters["model"], \
                                                          parameters["description"], parameters["building"], \
                                                          parameters["floor"], parameters["room"], \
                                                          parameters["rackrow"], parameters["rowposition"], \
                                                          parameters["height"], parameters["width"], \
                                                          parameters["depth"], parameters["rearrightslots"],
                                                          parameters["rearleftslots"], parameters["numberunits"], \
                                                          parameters["status"], attributes)
        
    elif (parameters["elementtype"] == "filesystem" or \
          parameters["elementtype"] == "kernel" or \
          parameters["elementtype"] == "loader"):
        password = " "
        username = " "
        if (parameters["elementtype"] == "filesystem"):
            password = parameters["password"]
            username = parameters["username"]
        (result, newID) = server.fileNodeCreate(parameters["elementtype"], parameters["owner"],
                                                parameters["path"], parameters["architecture"], \
                                                parameters["ostype"], parameters["version"], \
                                                parameters["mustclone"], parameters["description"],
                                                attributes, username, \
                                                password, parameters["status"])

    else:
        sys.exit()
    
    print '<inventory>'
    print '\t<result operation="create" elementid="' + str(newID) + '" value="' + str(result) + \
          '" elementtype="' + str(parameters["elementtype"]) + '" />'
    print '</inventory>'

# Edit an inventory element in the testbed
elif (retrieve == "editelement"):

    parameterNames = ["status", "serviceprocessor", "netbootable", "infrastructure", "powerswitch", \
                      "powerswitchport", "serial", "serialport", "building", "floor", "room", "rackrow", "rackname", \
                      "rackstartunit", "rackendunit", "nodeposition", "vendor", "model", "username", "password", \
                      "description", "height", "width", "depth", "rearrightslots", "rearleftslots", "numberunits", \
                      "managementmacaddress", "infrastructuremacaddress", "externalmacaddress", "externalip", \
                      "externalsubnet", "macaddress", "architecture", "ostype", "version", "mustclone", "owner", \
                      "path"]
    parameters = retrieveCGIParameters(parameterNames)
    parameters = convertParameterNames(parameters)

    # The attributes are anything after all the regular parameters that actually exist
    attributes = {}
    counter = 0
    for key in form.keys():
        if (counter > len(parameters) + 1):
            attributes[key] = form[key].value
        counter += 1

    if (not form.has_key("elementid")):
        sys.exit()
        
    elementID = form["elementid"].value
    elementType = findElementType(elementID)

    server = xmlrpclib.ServerProxy(uri="http://localhost:50006/")
    (result, message) = server.elementEdit(elementID, parameters, attributes)

    print '<inventory>'
    print '\t<result operation="edit" elementid="' + str(elementID) + '" value="' + str(result) + \
          '" elementtype="' + str(elementType) + '" />'          
    print '</inventory>'

# Delete an inventory element from the testbed
elif (retrieve == "deleteelement"):
    if (not form.has_key("elementid")):
        sys.exit()

    elementID = form["elementid"].value
    elementType = findElementType(elementID)

    server = xmlrpclib.ServerProxy(uri="http://localhost:50006/")
    (result, message) = server.elementDelete(elementID)

    print '<inventory>'
    print '\t<result operation="delete" elementid="' + str(elementID) + '" value="' + str(result) + \
          '" elementtype="' + str(elementType) + '" />'          
    print '</inventory>'

# Unknown value for retrieve
else:
    sys.exit();
