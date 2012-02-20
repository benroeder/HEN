#! /usr/bin/env python
from test import *

class SwitchTestVlanPortErrorAddition(SwitchTest):
    def __init__(self):
        SwitchTest()
        self.numTests = 7

    def test0(self):
        print self.target.getSwitchName()
        return 0

    def test1(self):
        res = self.target.getSwitchName(True)
        return 0

    def test2(self):
        res = self.target.deleteVLAN("testcasevlan")
        res = self.target.deleteVLAN("testcasevlan2")
        return 0

    def test3(self):
        print "Added port 10 to vlan testcasevlan"
        switches = {}
        switches[self.target_name] = []
        switches[self.target_name].append(Port(10,False,10))
        v = VLAN("testcasevlan",switches,4001)
        res = self.target.createVLAN(v)
        print "result "+str(res)
        return 0

    def test4(self):
        print "Added port 10 to vlan testcasevlan2"
        switches = {}
        switches[self.target_name] = []
        switches[self.target_name].append(Port(10,False,10))
        v = VLAN("testcasevlan2",switches,4002)
        res = self.target.createVLAN(v)
        print "result "+str(res)
        return 0
                        
    def test5(self):
        res = self.target.getFullVLANInfo("testcasevlan")
        for r in res:
            print r
        res = self.target.getFullVLANInfo("testcasevlan2")
        for r in res:
            print r
        res = self.target.getFullVLANInfo()
        for r in res:
            print r
        
        return 0

    def test6(self):
        res = 0
        res = self.target.deleteVLAN("testcasevlan")
        res = self.target.deleteVLAN("testcasevlan2")
        return res
        
s = SwitchTestVlanPortErrorAddition()
s.run(sys.argv)
