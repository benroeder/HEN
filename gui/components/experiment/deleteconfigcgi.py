#!/usr/local/bin/python
# $Id$

import cgi
import sys
sys.path.append("/usr/local/hen/lib/")
from henmanager import HenManager
from auxiliary.hen import Node, SwitchNode, VLAN, Port
import os
import xmlrpclib

def main():
    form = cgi.FieldStorage()
    manager = HenManager()
    manager.initLogging()


    if form.has_key("id"):
        experimentid = form["id"].value
        print experimentid
        #manager.experimentDelete(targetNode)

        #cmd = "export PYTHONPATH=$HOME/hen_scripts/hen_scripts/trunk/lib"
        #os.system(cmd)
        #cmd = "sudo hm experiment delete " + targetNode
        #os.system(cmd)


        server = xmlrpclib.ServerProxy(uri="http://localhost:50001/")
        server.delete(experimentid)

if __name__ == "__main__":
    main()
