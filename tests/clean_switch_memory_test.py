#!/usr/local/bin/python

#from henmanager import HenManager
import time
import resource
import gc
import sys
import types

#manager = HenManager()
#manager.initLogging()

#switches = manager.getNodes("switch","all")

#switch = None
#switch_node = None
#for sw in switches.values():
#    if sw.getNodeID() == "switch5":
#        #switch_node = sw
#        switch = sw.getInstance()


def get_refcounts():
    d = {}
    sys.modules
    # collect all classes
    for m in sys.modules.values():
        for sym in dir(m):
            o = getattr (m, sym)
            if type(o) is types.ClassType:
                d[o] = sys.getrefcount (o)
    # sort by refcount
    pairs = map (lambda x: (x[1],x[0]), d.items())
    pairs.sort()
    pairs.reverse()
    return pairs

def print_ref_diffs(lastrefs, newrefs):
    for newn, newc in newrefs:
        found = False
        for lastn, lastc in lastrefs:
            if lastc.__name__ == newc.__name__:
                if newn - lastn > 0:
                    print 'diff: %10d %s' % (newn - lastn, newc.__name__)
                found = True
                continue
        if not found:
            print 'class %s not found in previous refcount' % newc.__name__

def test1():
    from auxiliary.hen import SwitchNode
    from auxiliary.hen import Interface
    from hardware.switches.extreme import ExtremeSummitSwitch

    interface={}
    interface["infrastructure"] = []
    interface["management"] = []
    interface["management"].append(Interface("00:e0:2b:17:c7:00","192.168.1.9"))
    interface["infrastructure"].append(Interface("00:e0:2b:17:c7:00","192.168.1.9"))
    
    switch_node = SwitchNode("switch5","switch",interface);
    switch_node.setSNMPwriteCommunity("private");
    switch = ExtremeSummitSwitch(switch_node)

    lastmemusage = 0
    lastrefs = None
    errors = 0
    gc.enable()
    while (errors < 3):
        #sn = switch.getSensorReadings()
        sn = switch.getSerialNumber()
        print sn
        gc.collect()
        newmemusage = resource.getrusage(resource.RUSAGE_SELF)[2]
        memdiff = (newmemusage - lastmemusage)
        newrefs = get_refcounts()
        if memdiff > 0:
            print "Leaked %d Kb... printing refcount diff" % memdiff
            if lastrefs == None:
                print "No previous refcount, skipping"
            else:
#                print_ref_diffs(lastrefs, newrefs)
                errors = errors + 1
        
        lastrefs = newrefs
        lastmemusage = newmemusage
        #print resource.getrusage(resource.RUSAGE_SELF)[3]
        time.sleep(1)

def test2():
    from pysnmp.v4.proto.rfc1902 import ObjectName
    from pysnmp.entity import engine, config
    from pysnmp.carrier.asynsock.dgram import udp
    from pysnmp.entity.rfc3413 import cmdgen
    
    sysName = ObjectName("1.3.6.1.2.1.1.5.0")
    ip = "192.168.1.9"
    snmp_engine = engine.SnmpEngine()
    config.addV1System(snmp_engine, 'test-agent', "public")
    config.addTargetParams(snmp_engine, 'myParams', 'test-agent', 'noAuthNoPriv', 0)
    config.addTargetAddr(
        snmp_engine, 'myRouter', config.snmpUDPDomain,
        (ip, 161), 'myParams'
        )
    config.addSocketTransport(
        snmp_engine,
        udp.domainName,
        udp.UdpSocketTransport().openClientMode()
        )

    cb = {}
    
    def cbFun(sendRequestHandle, errorIndication, errorStatus, errorIndex,
              varBinds, cbCtx):
        cbCtx['errorIndication'] = errorIndication
        cbCtx['errorStatus'] = errorStatus
        cbCtx['errorIndex'] = errorIndex
        cbCtx['varBinds'] = varBinds
        

    cmdgen.GetCommandGenerator().sendReq(snmp_engine, 'myRouter', ((sysName, None),), cbFun, cb)
        
        
    lastmemusage = 0
    lastrefs = None
    errors = 0
    while (errors < 2):
        snmp_engine.transportDispatcher.runDispatcher()
        print cb['varBinds'][0][1]
        snmp_engine.transportDispatcher.closeDispatcher()
        #asynCommandGenerator.flushConfig()
        newmemusage = resource.getrusage(resource.RUSAGE_SELF)[2]
        memdiff = (newmemusage - lastmemusage)
        newrefs = get_refcounts()
        if memdiff > 0:
            print "Leaked %d Kb... printing refcount diff" % memdiff
            if lastrefs == None:
                print "No previous refcount, skipping"
            else:
                print_ref_diffs(lastrefs, newrefs)
                errors = errors + 1
        gc.collect()
        lastrefs = newrefs
        lastmemusage = newmemusage
        #print resource.getrusage(resource.RUSAGE_SELF)[3]
        time.sleep(1)

gc.enable()

# test1 uses hen libs
test1()

# test2 just uses pysnmp
#test2()


