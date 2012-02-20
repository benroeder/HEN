#! /usr/bin/env python
from test import *

class SwitchTestVlanPortDeletion(SwitchTest):
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
        res = self.target.deleteVLAN("testcasevlan")
        return 0

    def test3(self):
        print "Two port in new vlan"
        switches = {}
        switches[self.target_name] = []
        switches[self.target_name].append(Port(10,False,10))
        switches[self.target_name].append(Port(11,True,11))
        v = VLAN("testcasevlan",switches,4001)
        res = self.target.createVLAN(v)
        print "result "+str(res)
        return 0

    def test4(self):
        res = self.target.getFullVLANInfo()
        for r in res:
            print "result "+str(r)
        return res

    def test5(self):
        print "Delete port to vlan"
        res = self.target.deletePorts("testcasevlan",[Port(10,False,10)])
        print "result "+str(res)
        return 0

    def test6(self):
        res = self.target.getFullVLANInfo()
        for r in res:
            print "result "+str(r)
        return res

    def test7(self):
        res = self.target.deleteVLAN("testcasevlan")
        return res
        return 0
        
s = SwitchTestVlanPortDeletion()
s.run(sys.argv)
