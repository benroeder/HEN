#! /usr/local/bin/python

import sys
import hardware.switches.switch
from hardware.switches.threecomsuperstack import ThreeComSuperstack
from hardware.switches.extremesummit import ExtremeSummit
from auxiliary.hen import VLAN


if len(sys.argv) < 5:
    print "usage: portstatus.py [switchaddress] [community] [set|get] [portnumber] [up|down]"
    sys.exit(0)

switchAddress = sys.argv[1]
community = sys.argv[2]
operation =  sys.argv[3]
port = sys.argv[4]
if (operation != "get"):
    updown = sys.argv[5]

switchType = switch.getSwitchType(switchAddress, community)
if (switchType == "threecomsuperstack"):
    switch =  ThreeComSuperstack(switchAddress, community)
    if (operation == "get"):
        status = switch.getPortStatus(int(port))
        if (status == "1"):
            print "up"
        elif (status == "2"):
            print "down"
        else:
            print "testing"
    else:
        if (updown == "up"):
            switch.enablePort(int(port))
            print "enabled port " + port
        else:
            switch.disablePort(int(port))
            print "disabled port " + port
elif (switchType == "extremesummit"):
    switch = ExtremeSummit(switchAddress, community)
    if (operation == "get"):
        status = switch.getPortStatus(int(port))
        if (status == "1"):
            print "up"
        elif (status == "2"):
            print "down"
        else:
            print "testing"
    else:
        if (updown == "up"):
            switch.enablePort(int(port))
            print "enabled port " + port
        else:
            switch.disablePort(int(port))
            print "disabled port " + port
            
