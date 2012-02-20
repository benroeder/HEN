#!/usr/local/bin/python

from henmanager import HenManager
import time
import resource
import gc

manager = HenManager()
manager.initLogging()

switches = manager.getNodes("all","all")
alive_list =['switch14', 'switch5', 'serviceprocessor16', 'sensor1', 'serviceprocessor20','serviceprocessor22','serviceprocessor42','serviceprocessor43','serviceprocessor44', 'powerswitch3', 'switch1', 'switch2', 'switch3' , 'switch4' ,'switch8', 'computer71'  ]
switch = {}
#sn = {}
#switch_node = None
for a in switches.values():
    for sw in a.values():
        for h in alive_list:
            if sw.getNodeID() == h:
                
                try:
                    switch[sw.getNodeID()] = sw.getInstance()
                except:
                    
                    pass
num = 1
while True:
    print "run ",num
    for s in switch.keys():
        print s
        #sn[s] = switch[s].getSensorReadings()
        switch[s].getSensorReadings()
    #print sn,
    #print switch[s]
    print resource.getrusage(resource.RUSAGE_SELF)[2]
    gc.collect()
    #print resource.getrusage(resource.RUSAGE_SELF)[3]
    #time.sleep(1)    
    num = num + 1
