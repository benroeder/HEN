import logging
import auxiliary.protocol
import pickle
import hashlib
import time
import sys
from auxiliary.daemonlocations import DaemonLocations

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

def handler(code, seq, sz,payload):
    print payload
    
def state_check(code, seq, sz,p):
    global payload
    m = md5.new()
    m.update(payload)
    
    log.debug("State reply:"+str(code)+" checksum check:"+str(m.digest()==p))
    
p = auxiliary.protocol.Protocol(None)
    
HOST = DaemonLocations.switchDaemon[0]
PORT = DaemonLocations.switchDaemon[1]

p.open(HOST,PORT)

method = "find_mac"
payload = sys.argv[1]
p.sendRequest(method,payload,handler)
p.readAndProcess()
                                                                
