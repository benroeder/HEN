#!/usr/local/bin/python
##################################################################################################################
# configcgi.py: performs operations on the testbed's main config file
#
##################################################################################################################
import sys, os, time, cgi, xmlrpclib
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
print '<config>'

manager = HenManager()
action = form["action"].value

if (action == "getconfig"):
    print '\t<configfile>'
    for line in manager.getConfigFileLines():
        print '\t\t<line>' + str(line) + "</line>"
    print '\t</configfile>'
    
elif (action == "editconfig"):

    if (not form.has_key("configfile")):
        sys.exit()
        
    configFile = form["configfile"].value

    server = xmlrpclib.ServerProxy(uri="http://localhost:50005/")
    resultValue = server.writeConfigFileLines(configFile)
    
    print '\t<response value="' + str(resultValue) + '" />'
    
print '</config>'
