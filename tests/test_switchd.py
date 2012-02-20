#!/usr/local/bin/python

from henmanager import HenManager
from auxiliary.switchdb import SwitchDB

def main():
    
    manager = HenManager()
    manager.initLogging()
    #switchdb automatically loads most information into memory.
    switchdb = SwitchDB(manager)
    #nodes = manager.getNodes("switch","all")
    #links = manager.getLinks("all","all")

    #for linktype in links.values():
    #    for link in linktype.values():
    #        print link
    
    #for node in nodes.values():
    #    if node.getNodeID() == "switch10":
    #        print "just using switch10"
    #        fdb = node.getInstance().getFullMACTable()
    #        switchdb.addFDB(node.getNodeID(),fdb)
        
    
    
if __name__ == "__main__":
    main()
