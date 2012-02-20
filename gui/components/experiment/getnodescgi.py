#!/usr/local/bin/python
# $Id$

import cgi
import sys
from xml.dom import minidom, Node
sys.path.append("/usr/local/hen/lib/")
from henmanager import HenManager
from auxiliary.hen import Node, SwitchNode, VLAN, Port
import string


def main():
    manager = HenManager()
    manager.initLogging()


#    doc = minidom.Document()
#    nodesTag = doc.createElement("nodes")
#    doc.appendChild(nodesTag)
#
#    nodes = manager.getNodes("all")
#    for nodeTypeDictionary in nodes.values():
#        for node in nodeTypeDictionary.values():
#
#            nodeTag = doc.createElement("node")
#            nodesTag.appendChild(nodeTag)
#            targetNode = node.getNodeID()
#            nodeTag.setAttribute("id", targetNode)
#
#    print doc.toprettyxml(indent = '    ')

    print "Cache-Control: no-store, no-cache, must-revalidate"
    print "Content-type: text/xml\n\n"

    print "<nodes>"
    nodes = manager.getNodes("all")
    for nodeTypeDictionary in nodes.values():
        for node in nodeTypeDictionary.values():
            print "\t<node id=\"" + node.getNodeID() + "\"/>"

    print "</nodes>"
if __name__ == "__main__":
    main()
