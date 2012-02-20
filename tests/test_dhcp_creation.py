#! /usr/bin/env python
from test import *

class DhcpCreateTest(FileTest):
    def __init__(self):
        FileTest()
        self.numTests = 1

    def test0(self):
        manager = HenManager("/home/arkell/u0/adam/development/hen_base_testing/etc/configs/config")
        manager.initLogging()
        manager.dhcpServer("create")

s = DhcpCreateTest()
s.run(sys.argv)
