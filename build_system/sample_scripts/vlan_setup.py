#!/usr/bin/env python
import sys
sys.path.append("/home/hen/u0/adam/development/svn/hen_scripts/lib")

import logging
import auxiliary.protocol
import pickle
import hashlib
import time
from auxiliary.daemonlocations import DaemonLocations


logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

return_payload = None

def handler(code, seq, sz,payload):
    global return_payload
    print str(payload)
    
def state_check(code, seq, sz,p):
    global payload
    m = md5.new()
    m.update(payload)

    log.debug("State reply:"+str(code)+" checksum check:"+str(m.digest()==p))

p = auxiliary.protocol.Protocol(None)

HOST = DaemonLocations.switchDaemon[0]
PORT = DaemonLocations.switchDaemon[1]

p.open(HOST,PORT)

vlans = {}

# uncomment the below lines (one per vlan), and change :
# myvlanX to your vlanname , less than 12 character
# computerXX to your reserved computer
# interfaceXX to the interface you are going to use con computerXX.
#vlans['myvlan1'] = [("computerXX","interfaceA"),("computerYY","interfaceB"),("computerZZ","interfaceC")]
#vlans['myvlan2'] = [("computerXX","interfaceD"),("computerYY","interfaceE"),("computerZZ","interfaceF")]


for vlan in vlans:
    print vlan
    for interface in vlans[vlan]:
        print interface[0],interface[1]
        method = "add_port_to_vlan_by_name"
        payload = pickle.dumps((str(interface[0]),str(interface[1]),str(vlan)))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
        method = "get_vlan_id_for_port"
        payload = pickle.dumps((str(interface[0]),str(interface[1])))
        p.sendRequest(method,payload,handler)
        p.readAndProcess()
sys.exit(0)

