#!/usr/bin/env python
from henmanager import HenManager

def getmac_from_interface(node,interface_str):
    interfaces = node.getInterfaces()
    for it in interfaces:
        for interface in interfaces[it]:
            if interface.getInterfaceID().upper() == interface_str.upper():
                return interface.getMAC().upper()
    return None

def interfaceid_to_mac(node_str,interface_str):
    manager = HenManager()
    manager.initLogging()
    nodes = manager.getNodes("all","all")
    for nt in nodes:
        for nn in nodes[nt]:
            if nodes[nt][nn].getNodeID().upper() == str(node_str).upper():
                mac = getmac_from_interface(nodes[nt][nn],interface_str)
                return mac
    return None

if __name__ == "__main__":
    import sys
    if not (len(sys.argv) == 3 or len(sys.argv) == 4):
        print str(sys.argv[0])+" <computer id> <interface id>"
        print str(sys.argv[0])+" <computer id> <interface id> -clean"
        sys.exit(1)
    else:
        try:
            mac = interfaceid_to_mac(sys.argv[1],sys.argv[2])
        except:
            print "ERROR"
            sys.exit(1)
        if mac == None:
            print "ERROR"
            sys.exit(1)
        if len(sys.argv) == 3:
            print mac
            sys.exit(0)
        if ((len(sys.argv) == 4) and (sys.argv[3]=="-clean")):
            print mac.replace(':','')
            sys.exit(0)

