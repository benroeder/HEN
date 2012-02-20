#! /usr/bin/env python
from test import *

class ServiceProcessorPowerTest(ServiceProcessorTest):
    def __init__(self):
        ServiceProcessorTest()
        self.numTests = 2
        
    def test0(self):
        res = self.target.poweroff(2)
        print "Power off : "+str(res)
        return 0

    def test1(self):
        res = self.target.poweron(2)
        print "Power on : "+str(res)
        return 0                  

s = ServiceProcessorPowerTest()
s.run(sys.argv)
