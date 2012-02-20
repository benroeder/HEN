#!/usr/local/bin/python
# $Id: vlancgi.py 160 2006-08-03 11:33:53Z munlee $

import cgi
import sys
from xml.dom import minidom, Node
sys.path.append("/usr/local/hen/lib/")
from henmanager import HenManager

print "Content-Type: text/xml\n"

manager = HenManager()
nodes = manager.getNodes("all")

form = cgi.FieldStorage()
if form.has_key("id"):
    pass
else:
    print "exiting early"
    sys.exit()

nodeid = form["id"].value


doc = minidom.Document()
nodeTag = doc.createElement("node")
doc.appendChild(nodeTag)

for nodeTypeDictionary in nodes.values():
    for node in nodeTypeDictionary.values():
        if (nodeid == node.getNodeID()):
            nodeTag.setAttribute("ident", node.getNodeID())
            nodeTag.setAttribute("motherboard", node.getMotherboard())
            nodeTag.setAttribute("cputype", node.getCPUType())
            nodeTag.setAttribute("cpuspeed", node.getCPUSpeed())
            nodeTag.setAttribute("multiproc", node.getNumberCPUs())
            nodeTag.setAttribute("memory", node.getSystemMemory())


            interfaces = node.getInterfaces("experimental")
            if (interfaces):
                for interface in interfaces:
                    interfaceTag = doc.createElement("interface")
                    nodeTag.appendChild(interfaceTag)
                    interfaceTag.setAttribute("mac", interface.getMAC())
                    interfaceTag.setAttribute("port", interface.getPort())
                    interfaceTag.setAttribute("model", interface.getModel())
                    interfaceTag.setAttribute("switch", interface.getSwitch())
                    interfaceTag.setAttribute("ip", interface.getIP())
                    interfaceTag.setAttribute("subnet", interface.getSubnet())

            print doc.toprettyxml(indent = '    ')

sys.exit()
