#!/usr/local/bin/python
##################################################################################################################
# physicallocationdaemon.py: 
#
##################################################################################################################
import sys, os, time
temp = sys.path
sys.path = []
#sys.path.append("/home/arkell/u0/adam/development/svn/hen_scripts/lib/")
for i in temp:
    sys.path.append(i)
#os.environ["PATH"] += ":/usr/local/bin:/usr/bin"
from henmanager import HenManager

###########################################################################################
#   Main execution
###########################################################################################            
print "Content-Type: text/xml"
print ""
print ""


print "<row>"
manager = HenManager()
racks = manager.getInfrastructures("rack")
nodes = manager.getNodes("all")

for key in racks.keys():
    r = racks[key]
    print "<rack id=\""+str(r.getID())+ \
          "\" rowposition=\""+str(r.getRowPosition())+ \
          "\" height=\""+str(r.getPhysicalSize().getHeight())+ \
          "\" width=\""+str(r.getPhysicalSize().getWidth())+ \
          "\" numberunits=\""+str(r.getPhysicalSize().getNumberUnits())+ "\" >"

    for nodeTypeDictionary in nodes.values():
        for node in nodeTypeDictionary.values():
            location = node.getPhysicalLocation()
            if (location != None):
                if (location.getRackName() == r.getID() ):
                    s = "<node id=\""+str(node.getNodeID())
                    s = s + "\" type=\""+str(node.getNodeType())
                    
                    if (location.getRackStartUnit() != None):
                        s = s + "\" rackstartunit=\""+str(location.getRackStartUnit())
                    if (location.getRackEndUnit() != None):
                        s = s + "\" rackendunit=\""+str(location.getRackEndUnit())
                    s = s + "\" position=\""+str(location.getNodePosition())
                    s = s + "\" />"
                    print s

    print "</rack>"    

print "</row>"
