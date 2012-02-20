#!/usr/bin/env python
"""
Prints out the hen name, mac address and ip address
"""
import string,sys
sys.path.append("/usr/local/hen/lib")
from henManager import HenManager


# Load the topology information
manager = HenManager()

manager.initLogging()
topology = manager.getPhysical()
for d in topology.keys():
	# Get the name of the device
	physicalDevice = topology[d]
	name=physicalDevice.id
	# Get the management interface
	for i in physicalDevice.mngInterface.values():
		# Convert the mac address to a upper case string
		mac=string.upper(i.mac)
		# Convert the ip address to a upper case string
		ip=string.upper(i.ip)
		# Print everything
		print name + " " +  mac + " " +  ip

	# Get the experimental interfaces
	for i in physicalDevice.interfaces.values():
		mac = string.upper(i.mac)
		if i.ip != None:
			ip = string.upper(i.ip)
		port = i.port
		switch = i.switch
		print name + " " + mac + " " + ip + " " + switch + " " + port

