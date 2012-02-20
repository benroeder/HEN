#!/usr/local/bin/python
##################################################################################################################
# physicallocationdaemon.py: 
#
##################################################################################################################
import sys, os, time
temp = sys.path
sys.path = []
sys.path.append("/usr/local/hen/lib/")
for i in temp:
    sys.path.append(i)

from henmanager import HenManager

###########################################################################################
#   Main execution
###########################################################################################            
print "Content-Type: text/xml"
print ""
print ""

print "<row>"
manager = HenManager("/usr/local/hen/etc/configs/config" )
racks = manager.getInfrastructures("rack")
nodes = manager.getNodes("all", "all")

rackNodes = {}

for key in racks.keys():
    rackNodes[key] = []

for nodeTypeDictionary in nodes.values():
    for node in nodeTypeDictionary.values():
        location = node.getPhysicalLocation()
        if (location != None):
            if rackNodes.has_key(location.getRackName()):
                s = '<node id="' + str(node.getNodeID())
                s += '" type="physicallocation-' + str(node.getNodeType())
                if (location.getRackStartUnit() != None):
                    s += '" rackstartunit="' + str(location.getRackStartUnit())
                if (location.getRackEndUnit() != None):
                    s += '" rackendunit="' + str(location.getRackEndUnit())
                s += '" position="' + str(location.getNodePosition())
                s += '" />'
                rackNodes[location.getRackName()].append(s)

for key in rackNodes.keys():
    r = manager.getInfrastructures("rack")[key]
    s = '<rack id="' + str(r.getID()) + \
        '" rowposition="' + str(r.getRowPosition()) + \
        '" height="' + str(r.getPhysicalSize().getNumberUnits())
    if (r.getPhysicalSize().getWidth() == "75"):
        s += '" width="wide" >'
    elif (r.getPhysicalSize().getWidth() == "60"):
        s += '" width="narrow" >'
    else:
        s += '" width="wide" >'
    print s

    for nodeString in rackNodes[key]:
        print nodeString
        pass

    print "</rack>"

print "</row>"
