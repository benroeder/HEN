#! /usr/bin/env python
from test import *

class SwitchTestListVlans(SwitchTest):
    def __init__(self):
        SwitchTest()
        self.numTests = 1

    def test0(self):
        res = self.target.getFullVLANInfo("testcasevlan2")
        
        for i in res:
            print i,
        return 0
        
s = SwitchTestListVlans()
s.run(sys.argv)
