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
    log.debug("PayloadSize["+str(len(payload))+"]")
    log.debug("Payload:\n"+str(payload))
    log.debug("*****************************")
    
def state_check(code, seq, sz,p):
    global payload
    m = md5.new()
    m.update(payload)

    log.debug("State reply:"+str(code)+" checksum check:"+str(m.digest()==p))

p = auxiliary.protocol.Protocol(None)

HOST = "0.0.0.0"
PORT = DaemonLocations.computerDaemon[1]

p.open(HOST,PORT)

#while True:
#    method = raw_input("method:")
#    payload = raw_input("payload:")
#    p.sendRequest(method,payload,handler)
#    p.readAndProcess()

#method = "execute_command"
#payload = "ls /"
method = "mkdir"
payload = "/var/mytest"
p.sendRequest(method,payload,handler)
p.readAndProcess()

