#! /usr/bin/env python
from test import *

class DnsCreateTest(FileTest):
    def __init__(self):
        FileTest()
        self.numTests = 1

    def test0(self):
        manager = HenManager("/home/arkell/u0/adam/development/hen_base_testing/etc/configs/config")
        manager.initLogging()
        manager.dnsServer("create")

s = DnsCreateTest()
s.run(sys.argv)
