#!/usr/local/bin/python
##################################################################################################################
# powercgi.py: performs power operations
#
##################################################################################################################
import sys, os, time, cgi
temp = sys.path
sys.path.append("/usr/local/hen/lib/")

from henmanager import HenManager

###########################################################################################
#   Main execution
###########################################################################################            

# Make sure that the necessary cgi parameters are given and retrieve them
form = cgi.FieldStorage()

if ((not form) or (not form.has_key("action"))):
    sys.exit()

print "Content-Type: text/xml"
print ""
print ""
print '<power>'

manager = HenManager()
action = form["action"].value

# Perform power operation
if (action == "status" or action == "poweron" or action == "poweroff" or action == "restart"):
    if (not form.has_key("numbernodes")):
        print '</power>'
        sys.exit()

    numberNodes = form["numbernodes"].value

    if (action != "status"):
        for i in range(0, int(numberNodes)):
            nodeID = form["node" + str(i)].value
            manager.powerSilent(nodeID, action)

    for i in range(0, int(numberNodes)):
        nodeID = form["node" + str(i)].value
        (returnCode, status) = manager.powerSilent(nodeID, "status")
        if (returnCode != 0):
            status = "no powerswitch"
        print '\t<node id="' + str(nodeID) + '" status="' + str(status) + '" />'

# Get the ids of all nodes that have a power switch
elif (action == "getnodeids"):
    nodes = manager.getNodes("all")
    experiments = manager.getExperiments()
    
    for nodeTypeDictionary in nodes.values():
        for node in nodeTypeDictionary.values():
            if (node.getPowerNodeID()):

                owner = "none"
                # Get the node's owner
                if (experiments):
                    for experiment in experiments.values():
                        experimentNodes = experiment.getExperimentNodes()
                        if (experimentNodes):
                            for nodeTypeDictionary in experimentNodes.values():
                                for theNode in nodeTypeDictionary.values():
                                    if (node.getNodeID() == theNode.getNodeID()):
                                        owner = experiment.getUser().getUsername()
                # Print the results                        
                print '\t<node id="' + str(node.getNodeID()) + '" owner="' + str(owner) + '" />'                

                
print '</power>'
