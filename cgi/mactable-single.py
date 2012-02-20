#!/usr/local/bin/python
##################################################################################################################
# mactable.py: Class and runnable script that generates html containing switch database information
#
##################################################################################################################
import sys, os
sys.path.append("/usr/local/hen/lib")
os.environ["PATH"] += ":/usr/local/bin:/usr/bin"
from henmanager import HenManager

class MACTableRetriever:
    """\brief Class to generate html containing switch database information
    """
    
    def __init__(self, manager, portsBlackList=[]):
        """\brief Initializes class
	\param manager (\c HenManager) The HenManager objects used to retrieve information from the testbed's database with
	\param portsBlackList (\c list) Used to make sure that an entry is not printed for a port that has learned
	                                more than one mac address
	"""
	self.__manager = manager
        self.__portsBlackList = portsBlackList

    def printVLANTables(self):
        """\brief Prints html to the console with all of the learned addresses from all the switches in the testbed
	"""
        print "Content-type: text/html\n\n<html><title></title><head>"
        nodes = self.__manager.getNodes("switch","all")

	for node in nodes.values():
	   self.__portsBlackList = []
           switch = None
           
           switch = node.getInstance()
	   if (switch != None):
	       self.__printVLANTable(switch)
           else:
	       pass
	       #print "Failure to get instance of " + node.getNodeID()
	
	print "</body></html>"
    
    def __addUnique(self, theList, newItem):
        """\brief Adds a new item to the given list. The function ensures that if a port has learned more than one
	          mac address, it is removed from the list
	\param theList (\c list) The current list of learned addresses
	\param newItem (\c MACTableEntry) The item to add
	\return (\c list) The updated list
	"""
	#theList.append(newItem)
	#return theList

	if (newItem.getPort() in self.__portsBlackList):
	    return theList
	else:
	    for i in theList:
	        if newItem.getPort() == i.getPort():
		    self.__portsBlackList.append(i.getPort())
		    theList.remove(i)
		    return theList
	    theList.append(newItem)
	    
	return theList
	
    def __printVLANTable(self, switch):
        """\brief Retrieves and prints a single switch database
	\param switch (\c subclass of Switch) The Switch objects used to retrieve information with
	"""
	uniqueMacs = []
        try:
            macs = switch.getFullMACTable()
        except:
            macs = []
	for m in range(0, len(macs)):
	    macs[m].setSwitch(switch.getSwitchName())
	    uniqueMacs = self.__addUnique(uniqueMacs, macs[m])
	    
	for x in range(0, len(uniqueMacs)):
            print str(uniqueMacs[x].getMAC()) + " " +  str(uniqueMacs[x].getSwitch()) + " " + \
		  str(uniqueMacs[x].getPort()) + " " + str(uniqueMacs[x].getLearned()) + "<br>"

###########################################################################################
#   Main execution
###########################################################################################
manager = HenManager()
manager.initLogging()
macRetriever = MACTableRetriever(manager)
macRetriever.printVLANTables()
