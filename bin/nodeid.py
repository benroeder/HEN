#!/usr/bin/env python
##################################################################################################################
# nodename.py: Prints the name of the node that the script is run from. To do so it matches the mac addresses of
# all running interfaces against the mac addresses in the testbed's database. Prints None if no match is found
#
##################################################################################################################
import commands, re
from henmanager import HenManager

# First create a list containing the mac addresses of all the running interfaces
macAddresses = []
macAddressMatcher = re.compile('(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}')
lines = commands.getstatusoutput("ifconfig")[1].splitlines()
for line in lines:
    matchObject = macAddressMatcher.search(line)
    if (matchObject):
        macAddresses.append(line[matchObject.start():matchObject.end()].upper())

# Now match the created list against all of the management mac addresses in the testbed's database
# for computer nodes
manager = HenManager()
manager.initLogging()
nodes = manager.getNodes("computer","all")
nodeName = None
for node in nodes.values():
    for interface in node.getInterfaces("management"):
        for macAddress in macAddresses:
            if (macAddress == interface.getMAC().upper()):
                nodeName = node.getNodeID()
if nodeName == None:
    nodes = manager.getNodes("virtualcomputer","all")
    for node in nodes.values():
        for interface in node.getInterfaces("management"):
            for macAddress in macAddresses:
                if (macAddress == interface.getMAC().upper()):
                    nodeName = node.getNodeID()
print nodeName
