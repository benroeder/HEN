#! /usr/bin/env python
from henmanager import HenManager
from auxiliary.hen import Node, SensorNode

manager = HenManager()
manager.initLogging()
infrastructures = manager.getInfrastructures("all")

for infrastructureType in infrastructures.keys():
    for infrastructure in infrastructures[infrastructureType].values():
        #print infrastructure.getID()
        print str(infrastructure)
