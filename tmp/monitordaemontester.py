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

p = auxiliary.protocol.Protocol(None)

HOST = DaemonLocations.monitorDaemon[0]
PORT = DaemonLocations.monitorDaemon[1]

p.open(HOST,PORT)

while True:
    method = raw_input("method: ")
    payload = raw_input("payload: ")
    p.sendRequest(method,payload,handler)
    p.readAndProcess()
