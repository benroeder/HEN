#! /usr/bin/env python
##################################################################################################################
# ifacesup.py:  A simple scripts that runs ifconfig up on all interfaces on a system. Used to bring all the interfaces
#               up during auto-detection so that lshw will be able to report the speed (max bandwidth) of an interface.
#               This works only in Linux.
#
##################################################################################################################
import commands, sys, os

ifaces = commands.getstatusoutput("ifconfig -a | grep eth | awk '{print $1}'")[1].splitlines()
for iface in ifaces:
    commands.getstatusoutput("ifconfig " + iface + " up")
