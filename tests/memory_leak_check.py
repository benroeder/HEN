#!/usr/local/bin/python

from henmanager import HenManager
import time
import resource
import gc

manager = HenManager()
manager.initLogging()

switches = manager.getNodes("switch","all")

switch = None
#switch_node = None
for sw in switches.values():
    if sw.getNodeID() == "switch5":
        #switch_node = sw
        switch = sw.getInstance()
while True:
    
    sn = switch.getSensorReadings()
    print sn,
    print resource.getrusage(resource.RUSAGE_SELF)[2]
    try:
        pnodeid = switch.getPowerNodeID()
        if (pnodeid == "None" or pnodeid == "none"):
            pass
        (st,msg) = manager.powerSilent(switch.getNodeID(), "status", \
                                                    pnodeid)
        print "power status[%S], message[%s]" % (st,msg)
    except:
        pass
    gc.collect()
    #print resource.getrusage(resource.RUSAGE_SELF)[3]
    time.sleep(1)    
    
    