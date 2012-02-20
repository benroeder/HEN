#!/usr/local/bin/python
##################################################################################################################
# power.py: performs power operations
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

if ((not form) or (not form.has_key("numbernodes")) or (not form.has_key("action"))):
    sys.exit()

print "Content-Type: text/xml"
print ""
print ""
print '<experiments>'

manager = HenManager()
action = form["action"].value
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
    
print '</experiments>'
