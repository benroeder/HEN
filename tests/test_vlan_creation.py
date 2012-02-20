#! /usr/bin/env python
from test import *

class SwitchTestVlanCreation(SwitchTest):
    def __init__(self):
        SwitchTest()
        self.numTests = 2
        
    def test0(self):
        res = self.target.deleteVLAN("testcase")
        print "deleting vlan return value "+str(res)
        return res

    def test1(self):
        print "One port in new vlan"
        switches = {}
        switches[self.target_name] = []
        if (self.target_name == "switch14"):
            switches[self.target_name].append(Port("GigabitEthernet 0/41",False,41))
        elif (self.target_name == "switch6"):
            switches[self.target_name].append(Port("FastEthernet0/11",False,19))
        else:
            switches[self.target_name].append(Port(11,False,11))
        v = VLAN("testcase",switches,11)
        res = self.target.createVLAN(v)
        print "result "+str(res)
        res = self.target.getFullVLANInfo("testcase")
        for i in  res:
            print i
                        
        return 0

    def test2(self):
        res = self.target.getFullVLANInfo()
        for i in  res:
            print i
        self.target.deleteVLAN("testcase")
        return 0

    def test3(self):
        print "Two port in new vlan"
        switches = {}
        switches[self.target_name] = []
        if  (self.target_name == "switch14"):
            switches[self.target_name].append(Port("GigabitEthernet 0/41",True,41))
            switches[self.target_name].append(Port("GigabitEthernet 1/41",False,41))
        elif (self.target_name == "switch6"):
            switches[self.target_name].append(Port("FastEthernet0/11",False,19))
            switches[self.target_name].append(Port("FastEthernet0/12",True,20))
        else:
            switches[self.target_name].append(Port(11,True,11))
            switches[self.target_name].append(Port(12,False,12))
        v = VLAN("testcase",switches,11)
        res = self.target.createVLAN(v)
        print "result "+str(res)
        return 0

    def test4(self):
        res = self.target.getFullVLANInfo()
        for i in  res:
            print i
        return 0

    def test5(self):
        self.target.deleteVLAN("testcase")
        return 0
        
s = SwitchTestVlanCreation()
s.run(sys.argv)
