#!/usr/bin/env python
import sys
sys.path.append("/home/arkell/u0/adam/development/svn/hen_scripts/lib")

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

# Uncomment the lines below, one per vlan , and change the names to those you set in vlan_setup.
#vlans['myvlan1'] = []
#vlans['myvlan2'] = []

for vlan in vlans:
    print vlan
    method = "delete_vlan_by_name"
    payload = pickle.dumps((str(vlan),"switch14"))
    p.sendRequest(method,payload,handler)
    p.readAndProcess()
    
sys.exit(0)

