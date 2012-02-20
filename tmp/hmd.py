import logging
import auxiliary.protocol
import pickle
from henmanager import HenManager
import hashlib
from auxiliary.daemonports import DaemonPorts

"""\brief Stub for the hmd part that talks to the powerdaemon
"""        

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

hm = HenManager()

def handler(code, seq, sz,payload):
    log.debug("Got code:"+str(code)+" size:"+str(sz)+" payload:"+payload)

def state_check(code, seq, sz,p):
    global payload
    m = md5.new()
    m.update(payload)
    
    log.debug("State reply:"+str(code)+" checksum check:"+str(m.digest()==p))

p = auxiliary.protocol.Protocol(None)

#read connection info from user
#host = raw_input("host name (localhost):")
#if (host==""):
#    host = "localhost"
#try:
#    port = int(raw_input("port (1105):"))
#except:
##    port = 1105
host = DaemonPorts().powerDaemonHost
port = DaemonPorts().powerDaemonPort
print "connecting to "+host+"port "+str(port)
p.open(host,port)

#send state!
payload = "10,"+ pickle.dumps(hm.getNodes("all"))

#p.sendRequest("set_config",payload,state_check)
#p.readAndProcess()
p.doSynchronousCall("set_config",payload)

#read smth from the user
while True:
    	method = raw_input("method:")
    	payload = raw_input("payload:")
    	#p.sendRequest(method,payload,handler)
    	#p.readAndProcess()
	print p.doSynchronousCall(method,payload)
