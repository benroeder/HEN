#! /usr/bin/env python
from test import *

class SwitchTestConfig(SwitchTest):
    def __init__(self):
        SwitchTest()
        self.numTests = 5

    def test0(self):
        print self.target.getSwitchName()
        return 0

    def test1(self):
        print self.target.getSwitchName(True)
        return 0

    def test2(self):
        print self.target.setSwitchName(self.target.getSwitchName(),True)
        return 0

    def test3(self):
        print "number of ports "+str(self.target.getNumberofPorts())
    
    def test4(self):
        print "serial number "+str(self.target.getSerialNumber())
s = SwitchTestConfig()
s.run(sys.argv)
