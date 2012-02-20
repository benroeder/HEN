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
from hardware.switches.force10 import *
from henmanager import HenManager


portsBlackList = []

def addUnique(list, newItem):
	list.append(newItem)
	return list
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
		

print "Content-type: text/html\n\n"
print "<html><title></title><head>"

manager = HenManager()
manager.initLogging()
nodes = manager.getNodes("switch")

for n in nodes.values():
	portsBlackList = []
#	if ( (n.getNodeID() == "switch6") or (n.getNodeID() == "switch3") ):
	if ( (n.getNodeID() == "switch8") ):
		s = n.getInstance()
		if s != None:
			#print s
			printVlanTable(s)
		else:
			print "Failure to get instance of object"
print "</body></html>"

