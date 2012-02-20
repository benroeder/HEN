#! /usr/bin/env python
from test import *

class SwitchTestListPorts(SwitchTest):
    def __init__(self):
        SwitchTest()
        self.numTests = 1

    def test0(self):

        res = self.target.refreshVlanInfo()
        
        res = self.target.addMacsToPorts()
        res = self.target.getPorts()
        #res = self.target.getVlans()        
        for i in res:
            print str(res[i]),
        return 0
        
s = SwitchTestListPorts()
s.run(sys.argv)
