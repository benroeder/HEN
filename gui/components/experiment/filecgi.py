#!/usr/local/bin/python
##################################################################################################################
# filecgi.py: used for user file management
#
##################################################################################################################
import sys, os, time, cgi, xmlrpclib
temp = sys.path
sys.path.append("/usr/local/hen/lib/")

from henmanager import HenManager

###########################################################################################
#   Main execution
###########################################################################################            

def checkFormVariables(variableNamesList):
    for variableName in variableNamesList:
        if (not form.has_key(variableName)):
            return False
    return True

def retrieveCGIParameters(parameterNames):
    values = {}
    for parameterName in parameterNames:
        if (form.has_key(parameterName)):
            values[parameterName] = form[parameterName].value

    return values

def convertParameterNames(parameters):
    newParameters = {}
    namesMapping = {}
    namesMapping["ostype"] = "osType"
    namesMapping["mustclone"] = "mustClone"

    for oldName in parameters.keys():
        if (namesMapping.has_key(oldName)):
            newParameters[namesMapping[oldName]] = parameters[oldName]
        else:
            newParameters[oldName] = parameters[oldName]

    return newParameters
                                        
# Make sure that the necessary cgi parameters are given and retrieve them
form = cgi.FieldStorage()
if ( (not form) or (not form.has_key("action")) ):
    sys.exit()

print "Content-Type: text/xml"
print ""
print ""

manager = HenManager()
fileNodes = manager.getFileNodes("all")

action = form["action"].value

# Get all the files for the given user, including those that he/she owns through
# the <experimentgroup> tag
if (action == "getfilesbyuser"):
    print '<experiments>'

    if (not form.has_key("username")):
        print '</experiments>'        
        sys.exit()

    # Retrieve the user's experiment groups from the LDAP server (hard-coded for now)
    userExperimentGroups = ["dostunneling"]

    # Search for any kernel/loader/filesystem that the user can modify thanks to experiment groups
    experiments = manager.getExperiments()
    theFiles = {}
    for experiment in experiments.values():
        experimentGroups = experiment.getExperimentGroups()
        experimentNodes = experiment.getExperimentNodes()
        
        # If the experiment has experiment groups and the user belongs to them, get the experiment's
        # filesystems, kernels and loaders
        if (experimentGroups):
            for userExperimentGroup in userExperimentGroups:
                if (userExperimentGroup in experimentGroups):
                
                    for experimentNodeTypes in experimentNodes.values():
                        for experimentNode in experimentNodeTypes.values():
                            loader = None
                            try:
                                loader = experimentNode.getNetbootInfo().getLoader()
                            except:
                                pass
                            kernel = None
                            try:
                                kernel = experimentNode.getNetbootInfo().getKernel()
                            except:
                                pass
                            filesystem = None
                            try:
                                filesystem = experimentNode.getNetbootInfo().getFileSystem()
                            except:
                                pass
                            if ((loader) and (loader not in theFiles.keys())):
                                theFiles[loader] = "loader"
                            if ((kernel) and (kernel not in theFiles.keys())):
                                theFiles[kernel] = "kernel"
                            if ((filesystem) and (filesystem not in theFiles.keys())):
                                theFiles[filesystem] = "filesystem"
            
    # Print experiment group kernel/loader/filesystems
    for theFile in theFiles.keys():
        path = fileNodes[theFiles[theFile]][theFile].getPath()
        path = path[path.rfind("/") + 1:]
        print '\t<filenode id="' + str(theFile) + '" type="' + str(theFiles[theFile]) + '" path="' + path + '" />'
    
    username = form["username"].value
    for fileNodeTypeDictionary in fileNodes.values():
        for fileNode in fileNodeTypeDictionary.values():
            # Make sure that the filename actually exists on the filesystem
            if ( (fileNode.getOwner() == username) and (fileNode.fileExists()) ):
                if (fileNode.getID() not in theFiles.keys()):
                    path = fileNode.getPath()
                    path = path[path.rfind("/") + 1:]                    
                    print '\t<filenode id="' + str(fileNode.getID()) + '" type="' + str(fileNode.getType()) + \
                          '" path="' + path + '" />'

            # If so requested, include any 'standard' files (standard files have the mustclone attribute set to 'yes'
            if ( (form.has_key("getstandard")) and (form["getstandard"].value == "yes") and (fileNode.getMustClone() == "yes") ):
                path = fileNode.getPath()
                path = path[path.rfind("/") + 1:]                    
                print '\t<filenode id="' + str(fileNode.getID()) + '" type="' + str(fileNode.getType()) + \
                      '" standard="yes" path="' + path + '" />'

    print '</experiments>'

# Retrieve all the files in a user's kernel/loader/filesystem directory
elif (action == "getfilesindir"):
    if ((not form.has_key("username")) or (not form.has_key("filenodetype"))):
        sys.exit()

    username = form["username"].value
    fileNodeType = form["filenodetype"].value

    theFiles = manager.getUserFiles(username, fileNodeType)

    print '<experiment>'
    for theFile in theFiles:
        print '<filenode name="' + str(theFile) + '" />'
    print '</experiment>'        
       

# Retrieve all information about a file
elif (action == "elementview"):
    if (not form.has_key("elementid")):
        sys.exit()

    elementID = form["elementid"].value
    fileNodes = manager.getFileNodes("all", "all")

    print '<experiment>'
    for fileNodeTypeDictionary in fileNodes.values():
        for fileNode in fileNodeTypeDictionary.values():
            if (fileNode.getID() == elementID):
                print str(fileNode)
    print '</experiment>'        

# Retrieve all editable information for the given element
elif (action == "elementedit"):     
    if (not form.has_key("elementid")):
        sys.exit()

    elementID = form["elementid"].value
    fileNodes = manager.getFileNodes("all", "all")
    theElement = None

    print '<experiments>'
    for fileNodeTypeDictionary in fileNodes.values():
        for fileNode in fileNodeTypeDictionary.values():
            if (fileNode.getID() == elementID):
                theElement = fileNode
                fileNodeType = fileNode.getType()

                print '<element id="' + str(fileNode.getID()) + '" type="' + str(fileNodeType) + '" >'

                print '\t<property name="path" value="' + str(fileNode.getPath()) + '" />'
                print '\t<property name="architecture" value="' + str(fileNode.getArchitecture()) + '" />'
                print '\t<property name="ostype" value="' + str(fileNode.getOsType()) + '" />'
                print '\t<property name="version" value="' + str(fileNode.getVersion()) + '" />'
                print '\t<property name="description" value="' + str(fileNode.getDescription()) + '" />'

                if (fileNodeType == "kernel"):
                    pass
                elif (fileNodeType == "loader"):
                    pass
                elif (fileNodeType == "filesystem"):
                    try:
                        username = fileNode.getUserManagement()[0].getUsername()
                        password = fileNode.getUserManagement()[0].getPassword()
                        print '\t<property name="username" value="' + str(username) + '" />'
                        print '\t<property name="password" value="' + str(password) + '" />'
                    except:
                        pass
                    
                # Print any attributes
                attributes = theElement.getAttributes()
                if (attributes):
                    for attributeName in attributes.keys():
                        print '\t<attribute name="' + str(attributeName) + \
                              '" value="' + str(attributes[attributeName]) + '" />'
                print '</element>'
                break
                

    print '</experiments>'

# Add a file node to the testbed
elif (action == "createfilenode"):
    variableNames = ["filenodetype", "owner", "path", "architecture", "ostype", "version", \
                     "mustclone", "description", "username", "password"]
    if (not checkFormVariables(variableNames)):
        sys.exit()

    # The attributes are anything after the first 10 items
    attributes = {}
    counter = 0
    for key in form.keys():
        if (counter > 10):
            attributes[key] = form[key].value
        counter += 1

    server = xmlrpclib.ServerProxy(uri="http://localhost:50004/")
    (result, newID) = server.fileNodeCreate(form["filenodetype"].value, form["owner"].value, form["path"].value, \
                                            form["architecture"].value, form["ostype"].value, form["version"].value, \
                                            form["mustclone"].value, form["description"].value, attributes, \
                                            form["username"].value, form["password"].value)

    print '<experiment>'
    print '\t<result operation="create" filenodeid="' + str(newID) + '" value="' + str(result) + '" />'
    print '</experiment>'

# Delete a file node from the testbed (in effect, set its status to 'deleted')
elif (action == "deletefilenode"):
    if (not form.has_key("filenodeid")):
        sys.exit()                    

    fileNodeID = form["filenodeid"].value

    server = xmlrpclib.ServerProxy(uri="http://localhost:50004/")
    (result, message) = server.elementDelete(fileNodeID)

    print '<experiment>'
    print '\t<result operation="delete" filenodeid="' + str(fileNodeID) + '" value="' + str(result) + '" />'
    print '</experiment>'
    
# Apply edit changes to a file node in the testbed
elif (action == "editfilenode"):
    parameterNames = ["filenodeid", "owner", "path", "architecture", "ostype", "version", \
                     "mustclone", "description", "username", "password"]    
    parameters = retrieveCGIParameters(parameterNames)
    parameters = convertParameterNames(parameters)

    # The attributes are anything after all the regular parameters that actually exist
    attributes = {}
    counter = 0

    for key in form.keys():
        if (counter > len(parameters) + 1):
            attributes[key] = form[key].value
        counter += 1

    if (not form.has_key("filenodeid")):
        sys.exit()

    elementID = form["filenodeid"].value

    server = xmlrpclib.ServerProxy(uri="http://localhost:50004/")
    (result, message) = server.elementEdit(elementID, parameters, attributes)

    print '<experiment>'
    print '\t<result operation="edit" filenodeid="' + str(form["filenodeid"].value) + '" value="' + str(result) + '" />'
    print '</experiment>'    

# Unknown value for action
else:
    sys.exit();
