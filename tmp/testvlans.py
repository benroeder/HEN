#!/usr/local/bin/python

import sys, os
sys.path.append("/usr/local/hen/lib")
os.environ["PATH"] += ":/usr/local/bin:/usr/bin"

import hardware
from hardware.switches.switch import Switch
from hardware.switches.extreme import *
from hardware.switches.cisco import *
from hardware.switches.huawei import *
from hardware.switches.threecom import *
from henmanager import HenManager


portsBlackList = []

def addUnique(list, newItem):
#	list.append(newItem)
#	return list
	if newItem.getPort() in portsBlackList:
		return list
	else:
		for i in list:
			if newItem.getPort() == i.getPort():
				portsBlackList.append(i.getPort())
				list.remove(i)
				return list
		list.append(newItem)
	return list
	
def printVlanTable(switch):
	uniqueMacs = []
	macs = switch.getFullMACTable()

	for m in range(0, len(macs)):
		macs[m].setSwitch(switch.getSwitchName())
		uniqueMacs = addUnique(uniqueMacs, macs[m])
	for x in range(0, len(uniqueMacs)):
		print str(uniqueMacs[x].getMAC())+ " "+  str(uniqueMacs[x].getSwitch())+ " " + str(uniqueMacs[x].getPort())+ " " + str(uniqueMacs[x].getLearned()) + "<br>"

def printVlans(switch):
	vlans = switch.getFullVLANInfo()
	for i in vlans:
		print "vlan "+i.getName()+" id "+i.getID()+"<br>"
		for j in i.getPorts():
			print str(j)+" ",
		print "<br>"

def addPorts(switch,name,port):
	if switch.addPorts(name,port) == -1:
		print "Error"

def deletePorts(switch,name,port):
	if switch.deletePorts(name,port) == -1:
		print "Error"

def createVLAN(switch,name,id,ports=None):
	vlan = VLAN(name,id,ports,None)
	if switch.createVLAN(vlan) != 0:
		print "Error creating vlan"

def deleteVLAN(switch,name,id):
	vlan = VLAN(name,id,[],None)
	if switch.deleteVLAN(vlan) != 0:
		print "Error removing vlan"

print "Content-type: text/html\n\n"
print "<html><title></title><head>"

manager = HenManager()
manager.initLogging()
nodes = manager.getNodes("switch")

for n in nodes.values():
	portsBlackList = []
	s = n.getInstance()
	#s.setSwitchName(n.getNodeID())
	if s != None:
		#printVlans(s)
		deleteVLAN(s,"B",4)
		#createVLAN(s,"A",3,["GigabitEthernet2/1/1","GigabitEthernet2/1/2","GigabitEthernet2/1/3","GigabitEthernet2/1/4"])
		#createVLAN(s,"B",4,["GigabitEthernet2/1/5","GigabitEthernet2/1/6","GigabitEthernet2/1/7","GigabitEthernet2/1/8"])
		#addPorts(s,"vlana",["GigabitEthernet2/1/1","GigabitEthernet2/1/2","GigabitEthernet2/1/3"])
		#deletePorts(s,"vlana",["GigabitEthernet2/1/1","GigabitEthernet2/1/2","GigabitEthernet2/1/3"])
		#
		#addPorts(s,"henexp",[107,106,101])
		#deletePorts(s,"henexp",[108,109,110,111,112,115,116,117])
		printVlans(s)
	else:
		print "Failure to get instance of object"
print "</body></html>"

