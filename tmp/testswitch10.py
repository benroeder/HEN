#! /usr/bin/env python
from henmanager import HenManager
from auxiliary.hen import Node, SwitchNode, VLAN, Port

manager = HenManager()
manager.initLogging()
nodes = manager.getNodes("switch")

theSwitch = None
for node in nodes.values():
#    print node
    if (node.getNodeID() == "switch10"):
        print node.getNodeID()
        theSwitch = node.getInstance()
#print theSwitch

# get name
print "Get Switch name : " + theSwitch.getSwitchName()
# get name - via snmp
#print "Get Switch name (via snmp) : " + theSwitch.getSwitchName(True)
# get description
print "Get Switch description : " + theSwitch.getSwitchDescription()
# get uptime
print "Get Switch uptime : " + theSwitch.getSwitchUptime()
# get contact
#print "Get Switch contact : " + theSwitch.getSwitchContact()
# get port status (need to cast to a string since return is an int)
print "Get Switch port 1 status " + str(theSwitch.getPortStatus(1))









#print "Set Switch name : "
#theSwitch.setSwitchName("switch10",True)
#print "Get Switch name : " + theSwitch.getSwitchName()
# get ip
#print "Get Switch Description : " + theSwitch.getSwitchDescription()
# get uptime
#print "Get Switch Uptime : " + theSwitch.getSwitchUptime()
# get number of ports
#print "Get Number of ports : " + theSwitch.getNumberPorts()
# get ConnectedPortsTable
#print "Get Connected Ports Table : "
#d = theSwitch.getConnectedPortsTable()
#for k in d.keys():
#    print k + " " + d[k] + " ",
#print ""
# get vlan names
#print "Get VLAN Names - doesn't get default vlan"

#switches = {}

#switches["switch10"] = [Port(10,True,10)]

#v = VLAN("a",switches,4001)
#theSwitch.deleteVLAN(v.getName())

#theSwitch.deletePorts("a", [Port(10,True,10)])

#theSwitch.createVLAN(v)






#v2 = theSwitch.getFullVLANInfo()
#for vv in v2:
#    print vv


# get full mac table
t = theSwitch.getFullMACTable()
for m in t:
    print str(m),
print ""

# get vlan to interface table
#t = theSwitch.getVLANToInterfacesTable()
#print t
#for m in t:
#    print str(m),
#print ""

#get vlan table
#t = theSwitch.getVLANTable()



#print t["Default VLAN"]

#t["Default VLAN"].deletePorts([Port(10,False,10)],"switch10")

#t["a"].addPorts([Port(10,False,10)],"switch10")

#for v in t:
#    print t[v]

#print v.isPortInVLAN(pp)

#theSwitch.setVLANTable(t)

#print "after"
#print str(v)

#s = theSwitch.getVLANTable()

#for i in s:
#    print s[i]
