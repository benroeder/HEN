#!/usr/local/bin/python
##################################################################################################################
# logcgi.py: performs log operations
#
##################################################################################################################
import sys, os, time, cgi
temp = sys.path
sys.path.append("/usr/local/hen/lib/")

from henmanager import HenManager

###########################################################################################
#   Main execution
###########################################################################################

def reverseLogEntries(logEntries):
    reversedEntries = []

    for x in xrange(len(logEntries) - 1, -1, -1):
        print x
        reversedEntries.append(logEntries[x])
    
    return reversedEntries


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

if (action == "getlogsbyelement"):
    if (not form.has_key("elementid")):
        print '</experiments>'
        sys.exit()
        
    elementID = form["elementid"].value

    logEntries = manager.getLogEntriesByElement(elementID)
    logEntries = reverseLogEntries(logEntries)
    for logEntry in logEntries:
        author = logEntry.getAuthorLoginID()
        affectedElements = logEntry.getAffectedElementsIDs()
        date = logEntry.getDate()
        time = logEntry.getTime()
        description = logEntry.getDescription()

        print '\t<logentry date="' + str(date) + '" time="' + str(time) + '" author="' + str(author) + '" >'
        print '\t<description>' + str(description) + '</description>'
        
        for affectedElement in affectedElements:
            print '\t\t<element id="' + str(affectedElement) + '" />'
        
        print '\t</logentry>'
    
print '</experiments>'    
