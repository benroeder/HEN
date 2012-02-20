#! /usr/bin/env python
from test import *
import time

class PowerswitchTestConfig(PowerswitchTest):
    def __init__(self):
        PowerswitchTest()
        self.numTests = 3

    def test0(self):
        print "serial number ",self.target.getSerialNumber()
        return 0

    def test1(self):
        print "current (A)",self.target.getCurrent()
        return 0

    def test2(self):
        print "status",self.target.status(11)
        return 0

    def test3(self):
        print "restart ",self.target.restart(11)
        time.sleep(5)
        return 0

    def test4(self):
        print "status",self.target.status(11)
        return 0

    def test5(self):
        print "poweron",self.target.poweron(11)
        time.sleep(5)
        return 0

    def test6(self):
        print "status",self.target.status(11)
        return 0

    def test7(self):
        print "poweroff ",self.target.poweroff(11)
        time.sleep(5)
        return 0

    def test8(self):
        print "status",self.target.status(11)
        return 0


s = PowerswitchTestConfig()
s.run(sys.argv)
