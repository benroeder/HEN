#!/usr/local/bin/python

import sys, os
sys.path.append("/usr/local/hen/lib")
os.environ["PATH"] += ":/usr/local/bin:/usr/bin"

from hardware.switches.extremesummit import ExtremeSummit
from hardware.switches.ciscocatalyst import CiscoCatalyst
from hardware.switches.threecomsuperstack import ThreeComSuperstack

def printVLANSTable(vlans, switchName):
	print "<table align='center' width='50%' border='1'>\n"
	print "<tr><td colspan='3'><h3>" + switchName + "</h3></td></tr>\n"
	print "<tr><td><b>VLAN ID</b></td><td><b>VLAN NAME</b></td><td><b>VLAN PORTS</b></td></tr>\n"

	# no info for this vlan
	if (vlans == "-1"):
		print "<tr><td>Error, perhaps switch is not up</td></tr>\n"
		print "</table>\n"
		print "<br><br>\n"
		return
	
	# for each vlan	
	for x in range(0, len(vlans)):
		vlan = vlans[x]
		name = vlan.getName()
		ports = vlan.getPorts()
		id = vlan.getID()

		print "<tr>\n"
		print "<td>" + str(id) + "</td>\n"
		print "<td>" + name + "</td>\n"

		print "<td>",
	
		if (len(ports) == 0):
			print "&nbsp;"
		for x in range(0, len(ports)):
			value = ports[x]
			print str(value) + " ",
		
		print "</td></tr>\n"
	print "</table>\n"
	print "<br><br>\n"


print "Content-type: text/html\n\n"
print "<html><head><title>Hen - Switch Information</title></head><body>\n"


for x in range(1, 7):
	switchName = "switch" + str(x)
	community = "private"	

	switch = None
	#if (x == 4):
	#	switch = ThreeComSuperstack("switch4", community)
	if (x == 5):
		switch = ExtremeSummit(switchName, community)
	elif (x == 6):
		switch = CiscoCatalyst(switchName, community)
	else:
		switch = ThreeComSuperstack(switchName, community)

	vlans = switch.getFullVLANInfo()

	switchName = switchName + " - " + switch.getSwitchName()
	printVLANSTable(vlans, switchName)
