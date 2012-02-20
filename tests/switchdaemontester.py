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

return_payload = None

def handler(code, seq, sz,payload):
    global return_payload
    log.debug("***********HANDLER***********")
    log.debug("Size["+str(sz)+"]")
    log.debug("PayloadSize["+str(len(payload))+"]")
    log.debug("Payload:\n"+str(payload))
#    log.debug(str(payload))
    return_payload = payload
    log.debug("*****************************")
    
def state_check(code, seq, sz,p):
    global payload
    m = md5.new()
    m.update(payload)

    log.debug("State reply:"+str(code)+" checksum check:"+str(m.digest()==p))

p = auxiliary.protocol.Protocol(None)

HOST = DaemonLocations.switchDaemon[0]
PORT = DaemonLocations.switchDaemon[1]

p.open(HOST,PORT)

#while True:
#    method = raw_input("method:")
#    payload = raw_input("payload:")
#    p.sendRequest(method,payload,handler)
#    p.readAndProcess()

method = "enable_test_mode"
#p.sendRequest(method,"",handler)
#p.readAndProcess()

#method = "add_port_to_vlan"
#payload = pickle.dumps(("computer1","interface0","testc"))
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

method = "clear_vlans"
payload = pickle.dumps(("switch14"))
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

method = "add_port_to_vlan_by_name"
payload = pickle.dumps(("computer1","interface0","testcasevlan"))
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

method = "add_port_to_vlan_by_name"
payload = pickle.dumps(("computer1","interface1","testcasevlan"))
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

method = "add_port_to_vlan_by_name"
payload = pickle.dumps(("computer1","interface1","testcasevla2"))
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

method = "add_port_to_vlan_by_name"
payload = pickle.dumps(("computer101","interface0","management"))
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

method = "get_next_free_vlan_id"
#payload = pickle.dumps(("switch14"))
payload = pickle.dumps((""))
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

method = "get_vlan_id_for_port"
payload = pickle.dumps(("computer1","interface0"))
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

method = "get_vlan_name_for_port"
payload = pickle.dumps(("computer1","interface1"))
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

method = "add_port_to_vlan_by_id"
payload = pickle.dumps(("computer1","interface0",return_payload))
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

method = "delete_port_from_vlan"
payload = pickle.dumps(("computer1","interface1","testcasevlan"))
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

method = "list_ports_on_vlan_on_switch"
payload = pickle.dumps(("switch14","wow"))
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

for i in range(1,16):
    method = "list_vlans_on_switch"
    payload = pickle.dumps(("switch"+str(i),"wow"))
#    p.sendRequest(method,payload,handler)
#    p.readAndProcess()

#method = "show_vlan_structure"
#payload = pickle.dumps("Vlan 212")
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

method = "show_vlan_structure"
payload = pickle.dumps("virtual")
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

#method = "add_port_to_vlan"
#payload = pickle.dumps(("computer1","interface0","Default VLAN"))
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

method = "list_empty_vlans_on_switch"
payload = pickle.dumps(("switch14"))
#p.sendRequest(method,payload,handler)
#p.readAndProcess()

method = "clear_empty_vlans_on_switch"
payload = pickle.dumps(("switch14"))
p.sendRequest(method,payload,handler)
p.readAndProcess()
