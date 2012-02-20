#! /usr/bin/env python
##################################################################################################################
# configif.py: A simple script that uses ifconfig to determine an interface's name (ie eth0) from
#              the given mac address. It then configures that interface to the ip address and mask given. The
#              scriptly currently works on Linux and Freebsd. This script is used to configure experiment intefaces
#              on nodes at boot-time
#
##################################################################################################################
import sys, commands, os, string

if (len(sys.argv) < 4):
    print "usage: python configif [mac address] [ip address] [subnet mask]"
    os._exit(1)

macAddress = sys.argv[1]
ipAddress = sys.argv[2]
subnetMask = sys.argv[3]
localOS = commands.getstatusoutput("uname")[1]
theInterface = None

if (localOS == "Linux"):
    ifaceNames = commands.getstatusoutput("ifconfig -a | grep HWaddr")[1].splitlines()
    for i in ifaceNames:
        upperCase = string.upper(i)
        if (upperCase.find(string.upper(macAddress)) != -1):
            indexOfSpace = i.find(" ")
            theInterface = i[:indexOfSpace]            
elif (localOS == "FreeBSD"):
    ifaceNameLine = None
    lines = commands.getstatusoutput("ifconfig -a")[1].splitlines()
    for i in lines:
        upperCase = string.upper(i)
        if (i.find("flags") != -1):
            ifaceNameLine = i
        if (upperCase.find(string.upper(macAddress)) != -1):
            indexOfColon = ifaceNameLine.find(":")
            theInterface = ifaceNameLine[:indexOfColon]
            break
    
if (theInterface == None):
    print "could not find interface with mac address " + macAddress
    os._exit(1)

returnCode = commands.getstatusoutput("ifconfig " + theInterface + " " + ipAddress + " netmask " + subnetMask + " up")[0]

if (returnCode != 0):
    print "error while configuring " + theInterface + " with ifconfig"
