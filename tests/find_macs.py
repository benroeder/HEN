#!/usr/local/bin/python
import logging
import auxiliary.protocol
import pickle
import hashlib
import time
from auxiliary.daemonlocations import DaemonLocations

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

def handler(code, seq, sz,payload):
    log.debug("***********HANDLER***********")
    log.debug("Size["+str(sz)+"]")
    log.debug("PayloadSize["+str(len(pickle.loads(payload)))+"]")
    #log.debug("Payload:\n"+str(pickle.loads(payload)))
    p = pickle.loads(payload)
    for q in p:
        print q,p[q]
    log.debug("*****************************")
    
def state_check(code, seq, sz,p):
    global payload
    m = md5.new()
    m.update(payload)

    log.debug("State reply:"+str(code)+" checksum check:"+str(m.digest()==p))

p = auxiliary.protocol.Protocol(None)

HOST = DaemonLocations.switchMonitorDaemon[0]
PORT = DaemonLocations.switchMonitorDaemon[1]

p.open(HOST,PORT)

#while True:
#    method = raw_input("method:")
#    payload = raw_input("payload:")
#    p.sendRequest(method,payload,handler)
#    p.readAndProcess()

pp = []
pp.append("00:01:02:87:84:46")
pp.append("03:c0:4f:7e:01:80")
pp.append("00:15:17:36:5E:48")
pp.append("00:15:17:36:5E:49")
pp.append("00:15:17:36:5E:4A")
pp.append("00:15:17:36:5E:4B")
pp.append("00:15:17:36:5E:D4")
pp.append("00:15:17:36:5E:D5")
pp.append("00:15:17:36:5E:D6")
pp.append("00:15:17:36:5E:D7")
pp.append("00:15:C5:EA:9B:00")
pp.append("00:15:C5:EA:9B:02")
pp.append("00:15:C5:EA:A5:ED")
method = "find_unique_macs"
payload = pickle.dumps(pp)
p.sendRequest(method,payload,handler)
p.readAndProcess()
    
