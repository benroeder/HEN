#! /usr/bin/env python

from henManager import HenManager
from auxiliary.hen import Node, SwitchNode

manager = HenManager()
manager.initLogging()
nodes = manager.getNodes("switch")

for n in nodes.values():
    s = n.getInstance()
    if s != None:
        print s.getSwitchUptime()
    else:
        print "Failure to get instance of object"
        

