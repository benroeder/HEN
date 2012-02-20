#! /usr/bin/env python
from henmanager import HenManager
from auxiliary.hen import Node, SwitchNode, VLAN, Port

manager = HenManager()
manager.initLogging()
nodes = manager.getNodes("switch")

theSwitch = None
for node in nodes.values():
#    print node
    if (node.getNodeID() == "switch1"):
        print node.getNodeID()
        theSwitch = node.getInstance()

vlans = theSwitch.getFullVLANInfo()
for vlan in vlans:
    print vlan


#res = theSwitch.getVLANToInterfacesTable()

#for p in res:
#    print str(p) + " res " + str(res[p])


