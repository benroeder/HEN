#!/usr/bin/env python
import os, sys, commands
from henmanager import HenManager

manager = HenManager()
nodes = manager.getNodes("computer")
user=""

usage = "usage: reservations.py [computerid] [computerid]\n"
usage += "usage: reservations.py all\n"
usage += "usage: reservations.py model [dell2950|dell1950|dell1850|sunx4100|sunv20z|delloptiplex]\n"
usage += "usage: reservations.py user [username]"

if (len(sys.argv) < 2):
    print usage
    os._exit(0)

if (sys.argv[1] == "model"):
    
    if (len(sys.argv) != 3):
        print usage
        os._exit(0)
    elif (sys.argv[2] == "dell2950"):
        beginID="computer81"
        endID="computer100"
    elif (sys.argv[2] == "dell1950"):
        beginID="computer56"
        endID="computer80"
    elif (sys.argv[2] == "dell1850"):
        beginID="computer21"
        endID="computer25"
    elif (sys.argv[2] == "delloptiplex"):
        beginID="computer1"
        endID="computer4"
    elif (sys.argv[2] == "sunv20z"):
        beginID="computer15"
        endID="computer20"
    elif (sys.argv[2] == "sunx4100"):
        beginID="computer26"
        endID="computer55"
    else:
        print usage
        os._exit(0)
elif (sys.argv[1] == "all"):
	beginID="computer1"
	endID="computer100"
elif (sys.argv[1] == "user"):
        beginID="computer1"
	endID="computer100"
        user=sys.argv[2]
else:
    beginID = sys.argv[1]
    if (len(sys.argv) == 2):
        endID = sys.argv[1]
    else:
        endID = sys.argv[2]
try:
	beginNumber = int(beginID[8:])
	endNumber = int(endID[8:])
except:
	print "syntax error "+str(sys.argv)
	print usage
	os._exit(0)
print "getting status of machines, please wait..."
results = commands.getstatusoutput("hm power status range " + beginID + " " + endID)[1].splitlines()
powerStatuses = {}
for x in range(beginNumber, endNumber + 1):
    powerStatuses["computer"+str(x)] = "unknown"
for result in results:
    if result[result.find(": ") + 2:].upper() == "ON" or result[result.find(": ") + 2:].upper() == "OFF" :
        powerStatuses[result[:result.find(":")]] = result[result.find(": ") + 2:]
    
freeMachines = []
usersMachines = []
for x in range(beginNumber, endNumber + 1):
    kernel = commands.getstatusoutput("ls -lha /export/machines/computer" + str(x) + " | grep 'kernel ->'")[1]
    kernel = kernel[kernel.find("->") + 3:]
    filesystem = commands.getstatusoutput("ls -lha /export/machines/computer" + str(x) + " | grep 'filesystem ->'")[1]
    filesystem = filesystem[filesystem.find("->") + 3:]
    inUse = commands.getstatusoutput("ls -lha /export/machines/computer" +
                                     str(x) + " | grep -i use | awk '{ print $9 }'")[1]

    if (user == "" or (inUse.upper().find(user.upper()) != -1)):    
        print "\nCOMPUTER" + str(x) + ": " + powerStatuses["computer" + str(x)]
        print "-------------------"
        usersMachines.append("computer" +str(x))
        if (inUse != ""):
            print inUse
        if (kernel != ""):
            print "kernel: " + kernel
        if (filesystem != ""):
            print "filesystem: " + filesystem
    
        if (inUse == "" and kernel == "" and filesystem == "" and powerStatuses["computer" + str(x)] == "off"):
            freeMachines.append("computer" + str(x))

if (user == ""):
    print "\n\nFREE MACHINES"
    print "===================="
    for freeMachine in freeMachines:
        try:
            s = str(freeMachine)+ "(" + str(nodes[freeMachine].getVendor()) +" " +str( nodes[freeMachine].getModel())+ ")"
            print s
        except KeyError:
            pass
    print "===================="    
    print "TOTAL: ", len(freeMachines)
else:
    print "\n\nUser",user,"'s Machines"
    print "===================="
    for userMachine in usersMachines:
        print str(userMachine),
    print "\n"
    print "===================="    
    print "TOTAL: ", len(usersMachines)
