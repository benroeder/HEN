#!/usr/local/bin/python
import logging
import auxiliary.protocol
import pickle
import hashlib
import time
from auxiliary.daemonlocations import DaemonLocations
import hardware.switches.switch
from hardware.switches import *
from auxiliary.hen import VLAN, Interface, DHCPConfigSubnetInfo, \
     DHCPConfigInfo, DNSConfigInfo, NetbootInfo, isVLANInList, \
     isHigherIPAddress, incrementIPAddress, ServerNode, ComputerNode, \
     SerialNode, SwitchNode, PowerSwitchNode, RouterNode, ServiceProcessorNode,\
     SensorNode, KVMNode, UserManagement, InfrastructureRack, PhysicalSize, \
     InfrastructureFloorBox, FloorBoxPowerPlug, FloorBoxRJ45Port, \
     PhysicalLocation, Port, LogEntry, generateMD5Signature, fileExists, \
     MoteNode
       
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

return_payload = None

def handler(code, seq, sz,payload):
    global return_payload
    log.debug("***********HANDLER***********")
    log.debug("Size["+str(sz)+"]")
    log.debug("PayloadSize["+str(len(payload))+"]")
    log.debug("Payload:\n"+str(pickle.loads(payload)))
    #log.debug(str(payload))
    return_payload = payload
    log.debug("*****************************")
    
def state_check(code, seq, sz,p):
    global payload
    m = md5.new()
    m.update(payload)

    log.debug("State reply:"+str(code)+" checksum check:"+str(m.digest()==p))

p = auxiliary.protocol.Protocol(None)

HOST = DaemonLocations.configDaemon[0]
PORT = DaemonLocations.configDaemon[1]

p.open(HOST,PORT)

method = "get_object_for_id"
payload = "switch1"
p.sendRequest(method,payload,handler)
p.readAndProcess()
