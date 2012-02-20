#!/usr/local/bin/python
##################################################################################################################
# physicallocationdaemon.py: 
#
##################################################################################################################
import sys, os, time, cgi
temp = sys.path

sys.path.append("/usr/local/hen/lib/")
from henmanager import HenManager

###########################################################################################
#   Main execution
###########################################################################################            
print "Content-Type: text/html"
print ""
print ""

manager = HenManager()
nodes = manager.getNodes("all")

form = cgi.FieldStorage()
if form.has_key("id"):
    pass
else:
    sys.exit()

nodeid = form["id"].value

for nodeTypeDictionary in nodes.values():
    for node in nodeTypeDictionary.values():
        if (nodeid == node.getNodeID()):
            print "<p>"
            print "power status of "
            manager.power(nodeid,"status")
            print "</p>"
            sys.exit()
                

            
                
