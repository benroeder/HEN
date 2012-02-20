#!/usr/local/bin/python
##################################################################################################################
# history.py: back-end for the experiment tab, handles any queries related to a user's saved experiments
#
##################################################################################################################
import sys, os, time, cgi
temp = sys.path
sys.path.append("/usr/local/hen/lib/")

from henmanager import HenManager
from auxiliary.hen import findFirstNumberInString, isDateAfter

###########################################################################################
#   Main execution
###########################################################################################            

def printExperiments(experimentsList):
    for experiment in experimentsList:
        experimentNodes = experiment.getExperimentNodes()
        startDate = experiment.getStartDate()
        endDate = experiment.getEndDate()
        experimentID = experiment.getExperimentID()
        owner = experiment.getUser().getUsername()

        print '\t<experiment id="' + str(experimentID) + \
              '" startdate="' + str(startDate) + \
              '" enddate="' + str(endDate) + \
              '" owner="' + str(owner) + \
              '">'
        
        for experimentNodeTypes in experimentNodes.values():
            for experimentNode in experimentNodeTypes.values():
                node = experimentNode.getNode()
                powerSwitch = node.getPowerNodeID()
                hasPowerSwitch = "yes"
                if (node.getPowerNodeID() == "None"):
                    hasPowerSwitch = "no"
                print '\t\t<node id="' + str(node.getNodeID()) + '" haspowerswitch="' + hasPowerSwitch + '" />'

        print '\t</experiment>'

def sortExperiments(experimentsList):
    if ( (len(experimentsList) == 0) or (len(experimentsList) == 1) ):
        return experimentsList
    
    sortedExperiments = []
    for experiment in experimentsList:
        startDate = experiment.getStartDate()

        if (len(sortedExperiments) == 0):
            sortedExperiments.append(experiment)
        else:
            counter = 0
            sortedDate = sortedExperiments[counter].getStartDate()
            while ( (not isDateAfter(startDate, sortedDate)) and (startDate != sortedDate) ):
                counter += 1
            sortedExperiments.insert(counter, experiment)

    return sortedExperiments

# Make sure that the necessary cgi parameters are given and retrieve them
form = cgi.FieldStorage()

if ((not form) or (not form.has_key("username"))):
    sys.exit()

print "Content-Type: text/xml"
print ""
print ""
print '<experiments>'
manager = HenManager()
experiments = manager.getExperiments()
experimentsList = []

# If no experiment id is given or it is set to 'all', return all the experiments for the user,
# including those that are shared
if ( (not form.has_key("experimentid")) or (form.has_key("experimentid") and (form["experimentid"].value == "all")) ):

    # Retrieve the user's experiment groups from the LDAP server (hard-coded for now)
    userExperimentGroups = ["dostunneling"]
            
    username = form["username"].value
    if (experiments):
        for experiment in experiments.values():
            user = experiment.getUser().getUsername()
            experimentGroups = experiment.getExperimentGroups()
            if (user == username):
                experimentsList.append(experiment)
            elif (experimentGroups):
                for userExperimentGroup in userExperimentGroups:
                    if (userExperimentGroup in experimentGroups):
                        experimentsList.append(experiment)

    # Sort experiments by date and print them
    experimentsList = sortExperiments(experimentsList)
    printExperiments(experimentsList)

# Retrieve a specific experiment for the given user
else:
    experimentID = form["experimentid"].value
    if (experiments):
        for experiment in experiments.values():
            if (experiment.getExperimentID() == experimentID):
                experimentsList.append(experiment)
                break
    printExperiments(experimentsList)
    
print '</experiments>'
