#!/usr/local/bin/python
##################################################################################################################
# calendarcgi.py: performs calendar operations
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
print '<experiments>'

manager = HenManager()
action = form["action"].value
experiments = manager.getExperiments()

if (action == "getexperiments"):
    if (not form.has_key("username")):
        print '</experiments>'
        sys.exit()
        
    username = form["username"].value
    
    # Retrieve the user's experiment groups from the LDAP server (hard-coded for now)
    userExperimentGroups = ["dostunneling"]
                            
    for experiment in experiments.values():
        experimentID = experiment.getExperimentID()
        experimentGroups = experiment.getExperimentGroups()
        user = experiment.getUser().getUsername()
        email = experiment.getUser().getEmail()
        startDate = experiment.getStartDate()
        endDate = experiment.getEndDate()

        # Check whether the experiment is shared or not
        shared = "no"
        if ((user != username) and (experimentGroups)):
            for userExperimentGroup in userExperimentGroups:
                if (userExperimentGroup in userExperimentGroups):
                    shared = "yes"
                    break
        
        print '\t<experiment id="' + str(experimentID) + '" user="' + str(user) + '" email="' + str(email) + '" ' + \
              'startdate="' + str(startDate) + '" enddate="' + str(endDate) + '" shared="' + str(shared) + '" >'
        
        experimentNodes = experiment.getExperimentNodes()
        for experimentNodeTypes in experimentNodes.values():
            for experimentNode in experimentNodeTypes.values():
                node = experimentNode.getNode()
                print '\t\t<node id="' + str(node.getNodeID()) + '" />'
        print '\t</experiment>'

print '</experiments>'    
    
