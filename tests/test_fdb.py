#! /usr/bin/env python
from test import *

class SwitchTestFDB(SwitchTest):
    def __init__(self):
        SwitchTest()
        self.numTests = 1

    def test0(self):
        res = self.target.getFullMACTable(True)
        #print res
        for i in res:
            print i
        return 0
        
s = SwitchTestFDB()
s.run(sys.argv)
