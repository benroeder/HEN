#!/usr/local/bin/python
import auxiliary.protocol
import pickle


def handler(code, seq, sz,payload):
    print payload
    
prot = auxiliary.protocol.Protocol(None)

HOST = "server1.infrastructure-hen-net"
PORT = 56005

prot.open(HOST,PORT)

method = "dhcp"
payload = "restart"
prot.sendRequest(method,payload,handler)
prot.readAndProcess()
