#! /usr/bin/env python
from henmanager import HenManager
import sys

def check_port(computer_str,interface_str):
	print computer_str,interface_str,
	switch_str = ""
        port_str = ""

        computer = None
        interface = None
        switch = None
        port = None

        switch_obj = None
        
        manager = HenManager()
        manager.initLogging()
        nodes = manager.getNodes("all")
        
        for node_type in nodes:
            for node in nodes[node_type]:
                if nodes[node_type][node].getNodeID() == computer_str:
                    computer = nodes[node_type][node]
                    break
                
        if computer != None:
            interfaces = computer.getInterfaces()
            for interface_type in interfaces:
                for iface in interfaces[interface_type]:
                    if iface.getInterfaceID() == interface_str:
                        switch_str = iface.getSwitch()
                        port_str = iface.getPort()

        for node_type in nodes:
            for node in nodes[node_type]:
                #print node,switch_str
                if nodes[node_type][node].getNodeID() == switch_str:
                    switch = nodes[node_type][node]
                    break

        if switch != None:
            switch_obj = switch.getInstance()
        
        if switch_obj != None:
	   port_internal_id = switch_obj.getPortInternalID(port_str)
           if (switch_obj.getPortStatus(port_str) == 1):
	      print "up",
	   else:
	      print "down"
	   #print switch_obj.getPortsSpeedByInternalID([port_internal_id])[0][1]
	   print switch_obj.getPortTdr(port_str)
	   
check_port(sys.argv[1],sys.argv[2])
                        
