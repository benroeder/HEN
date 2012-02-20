#! /usr/bin/env python
from henmanager import HenManager
from auxiliary.hen import Node, SwitchNode, VLAN, Port

manager = HenManager()
manager.initLogging()
nodes = manager.getNodes("switch")

theSwitch = None
for node in nodes.values():
    if (node.getNodeID() == "switch9"):
        theSwitch = node.getInstance()

vlan = VLAN("test", None, "100")
ports = []
port1 = Port("GigabitEthernet2/1/1", False)
port2 = Port("GigabitEthernet2/1/2", True)
ports.append(port1)
ports.append(port2)
vlan.addPorts(ports, "switch7")

#table = theSwitch.getFullMACTable()
#for entry in table:
#    print entry
print theSwitch.createVLAN(vlan)
#print theSwitch.deleteVLAN(vlan.getName())
#print theSwitch.getAvailableTaggedInterfaceInternalID()
#print theSwitch.getNextVLANID()
#print theSwitch.deleteVLAN("cd")
#print theSwitch.addPorts("cd", ports)
#print theSwitch.deletePorts("B", ports)
#print theSwitch.populateVLAN("test")
#print theSwitch.addPorts("test", ports)
#theSwitch.getInterfaceDescriptionTable()
#theSwitch.getInterfaceTypeTable()
#print theSwitch.getInterfaceType("122")
#theSwitch.deletePorts("test", ports)
#table = theSwitch.getFullVLANInfo()
#for vlan in table:
#   print vlan
#print theSwitch.getNextVLANID()
#table = theSwitch.getFullVLANInfo()
#for vlan in table:
#   print vlan
#or key in table.keys():
#  print key, table[key]
