#! /usr/local/bin/python
"""
Felipe Huici f.huici@cs.ucl.ac.uk
Moves any ports on a switch that do not belong to any vlans to the specified vlan.
This script assumes that the given vlan actually exists; if it doesn't, nothing is
done for that particular switch
"""

import sys

from auxiliary.hen import SNMPResult, VLAN
from hardware.switches.switch import getSwitchType
from hardware.switches.extremesummit import ExtremeSummit
from hardware.switches.threecomsuperstack import ThreeComSuperstack

if len(sys.argv) < 3:
    print "Usage: python populatevlan switch1:community1 [switch2:community2,  ...] vlan"
    sys.exit(1)

vlanToPopulate = sys.argv[len(sys.argv) - 1]

for x in range(1, len(sys.argv) - 1):
    argument = sys.argv[x]

    # make sure that there is a colon separating swich name from the community
    indexOfColon = argument.find(":")
    if indexOfColon == -1:
        print "argument " + sys.argv[x] + " is invalid, no colon found, bypassing..."
    else:
        switchName = argument[0:indexOfColon]
        switchCommunity = argument[indexOfColon + 1:len(argument)]
        switchType = getSwitchType(switchName, switchCommunity)

        switch = None

        # 3com switch
        if (switchType == "threecomsuperstack"):
            switch = ThreeComSuperstack(switchName, switchCommunity)

        # Extreme switch
        elif (switchType == "extremesummit"):
            switch = ExtremeSummit(switchName, switchCommunity)

        # Unknown switch
        else:
            print "unrecognized switch type for switch " + switchName + ", bypassing..."
            exit(1)

        # Apply changes
        print switch.populateVLAN(vlanToPopulate)
