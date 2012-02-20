#!/usr/local/bin/python
import sys
sys.path.insert(0, "/usr/local/hen/lib")

from henmanager import HenManager

manager = HenManager()
manager.initLogging()
nodes = manager.getNodes("all","all")

subnets = {}
subnets["192.168.0."] = []
subnets["192.168.1."] = []
subnets["192.168.2."] = []
interfaces = []

# Get all interfaces from nodes
for nt in nodes:
    for node in nodes[nt]:
        ints = nodes[nt][node].getInterfaces()
        if ints != None:
            for it in ints:
                if ints[it] == None:
                    break
                for i in ints[it]:
                    interfaces.append(i)

# Fill subnets with all possible addresses
for i in ["192.168.0.","192.168.1.","192.168.2."]:
    for j in range(1,255):
        subnets[i].append(i+str(j))

# Remove entries
for i in interfaces:
    if i.getIP() == None:
        pass
    elif i.getIP().startswith("192.168.0."):
        try:
            subnets["192.168.0."].remove(i.getIP())
        except:
            print "Already removed",i.getIP()
    elif i.getIP().startswith("192.168.1."):
        try:
            subnets["192.168.1."].remove(i.getIP())
        except:
            print "Already removed",i.getIP()
    elif i.getIP().startswith("192.168.2."):
        try:
            subnets["192.168.2."].remove(i.getIP())
        except:
            print "Already removed",i.getIP()
    else:
        if i.getIP() == None or i.getIP() == "None":
            pass
        else:
            if i.getIP().startswith("128.16"):
                pass
            else:
                print "Can't find address",i.getIP()

if len(sys.argv) == 1:
    print sys.argv[0]+" management|infrastructure"
    sys.exit(1)

if sys.argv[1] == "management":
    print "\nFree management interface ips "
    for i in subnets["192.168.0."]:
        print "\t"+str(i)
elif sys.argv[1] == "infrastructure":
    print "\nFree infrastructure interface ips "
    for i in subnets["192.168.1."]:
        print "\t"+str(i)


#print "Free virtual interface ips "
#for i in subnets["192.168.2."]:
#    print i,
