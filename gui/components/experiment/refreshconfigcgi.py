#!/usr/local/bin/python
# $Id$

import cgi
import sys
sys.path.append("/usr/local/hen/lib")

from henmanager import HenManager
from auxiliary.hen import Node, SwitchNode, VLAN, Port



def main():
    form = cgi.FieldStorage()
    manager = HenManager()
    manager.initLogging()


    print "Cache-Control: no-store, no-cache, must-revalidate"
    print "Content-type: text/xml\n"
    print "<experiments>"

    experiments = manager.getExperimentEntries()
    for experimentID in experiments.keys():
        #segments = experiment.split("/")
        #Bfilename = segments[len(segments) - 1]
        # slice off the '.xml' extension
        #fileid = filename[:-4]
        print "\t<experiment id=\"" + experimentID + "\"/>"

    print "</experiments>"

if __name__ == "__main__":
    main()
