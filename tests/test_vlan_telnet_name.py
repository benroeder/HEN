#! /usr/bin/env python
from test import *

class SwitchTestVlanTelnetName(SwitchTest):
    def __init__(self):
        SwitchTest()
        self.numTests = 1

    def test0(self):
        import getpass
        import sys
        import telnetlib

        HOST = "switch14"
        user = "admin"
        password = "admin"
        vlan_id = "4"
        vlan_name = "testcase4"
        TIMEOUT = 2
        tn = telnetlib.Telnet(HOST)
        tn.set_debuglevel(1)
        tn.read_until("Login: ")
        tn.write(user + "\n")
        if password:
            tn.read_until("Password: ",TIMEOUT)
            tn.write(password + "\n")
            
        tn.write("configure\n")
        tn.read_until("Force10(conf)#",TIMEOUT)
        tn.write("interface vlan 4\n")
        tn.read_until("Force10(conf-if-vl-"+str(vlan_id)+")#",TIMEOUT)
        tn.write("name "+str(vlan_name)+"\n")
        tn.read_until("Force10(conf-if-vl-"+str(vlan_id)+")#",TIMEOUT)
        tn.write("exit\n")
        tn.read_until("Force10(conf)#",TIMEOUT)
        tn.write("exit\n")
        tn.read_until("Force10#",TIMEOUT)
        tn.write("exit\n")
        
        print tn.read_all()
                    
        
s = SwitchTestVlanTelnetName()
s.run(sys.argv)
