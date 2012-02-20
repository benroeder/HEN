#! /usr/bin/env python
from test import *

class SwitchTestVlanDeletion(SwitchTest):
    def __init__(self):
        SwitchTest()
        self.numTests = 1

    def test0(self):
        self.target.deleteVLAN("testcasevlan")
        return 0

s = SwitchTestVlanDeletion()
s.run(sys.argv)
