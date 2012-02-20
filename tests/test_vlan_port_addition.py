#! /usr/bin/env python
from test import *

class SwitchTestVlanPortAddition(SwitchTest):
    def __init__(self):
        SwitchTest()
        self.numTests = 8

    def test0(self):
        print self.target.getSwitchName()
        return 0

    def test1(self):
        res = self.target.getSwitchName(True)
        return 0

    def test2(self):
        print "deleteing test vlan"
        res = self.target.deleteVLAN("testcasevlan")
        return res

    def test3(self):
        print "One port in new vlan"
        switches = {}
        switches[self.target_name] = []
        switches[self.target_name].append(Port(10,True,10))
        v = VLAN("testcasevlan",switches,24)
        res = self.target.createVLAN(v)
        print "result "+str(res)
        return 0

    def test4(self):
        res = self.target.getFullVLANInfo("testcasevlan")
        print "result "+str(res)
        return res

    def test5(self):
        print "Add port to vlan"
        res = self.target.addPorts("testcasevlan",[Port(11,False,11)])
        print "result "+str(res)
        return 0

    def test6(self):
        res = self.target.getFullVLANInfo("testcasevlan")
        print "result "+str(res)
        return res

    def test7(self):
        #res = self.target.deleteVLAN("testcasevlan")
        res = 0
        return res
        
s = SwitchTestVlanPortAddition()
s.run(sys.argv)
