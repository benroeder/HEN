#! /usr/bin/env python
from test import *

class SwitchTestPoE(SwitchTest):
    def __init__(self):
        SwitchTest()
        self.numTests = 9

    def test0(self):
        res = self.target.getPowerDetectionStatus(2)
        print "Power Detection Status : "+str(res)
        return 0

    def test1(self):
        res = self.target.getPowerConsumption()
        print "Power consumption : "+str(res)+" W"
        return 0

    def test2(self):
        res = self.target.getPowerPriority(2)
        print "Power Priority : "+str(res)
        return 0

    def test3(self):
        res = self.target.getPowerOverloadCounter(2)
        print "Power Overload Counter : "+str(res)
        return 0

    def test4(self):
        res = self.target.getPowerNominal()
        print "Power Nominal : "+str(res)
        return 0

    def test5(self):
        res = self.target.status(1)
        print "Power Status : "+str(res)
        return 0

    def test6(self):
        res = self.target.poweroff(2)
        print "Power Off : "+str(res)
        return 0

    def test7(self):
        res = self.target.poweron(2)
        print "Power On : "+str(res)
        return 0

    def test8(self):
        res = self.target.restart(2)
        print "Power Restart : "+str(res)
        return 0

    
    
s = SwitchTestPoE()
s.run(sys.argv)
