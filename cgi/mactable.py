#!/usr/local/bin/python
##################################################################################################################
# mactable.py: Class and runnable script that generates html containing switch database information
#
##################################################################################################################
import sys, os
sys.path.append("/usr/local/hen/lib")
os.environ["PATH"] += ":/usr/local/bin:/usr/bin"
from henmanager import HenManager
import threading

class Worker(threading.Thread):

    def setSwitch(self,switch,mtr):
        self.switch = switch
        self.mtr = mtr
        
    def run(self):
        try:
            macs = self.switch.getInstance().getFullMACTable()
        except:
            macs = []
        self.mtr.printVLANTable(self.switch.getInstance(),macs)
        

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
        self.__lock = threading.Lock()
        self.__final_lock = threading.Lock()
        self.__numOfSwitches = 0
        
    def printVLANTables(self):
        """\brief Prints html to the console with all of the learned addresses from all the switches in the testbed
	"""
        print "Content-type: text/html\n\n<html><title></title><head>"
        nodes = self.__manager.getNodes("switch")

        self.__numOfSwitches = len(nodes.values())
        self.__final_lock.acquire()
        
	for node in nodes.values():
	   if (node.getStatus() == "all"):
               self.__portsBlackList = []
               w = Worker()
               w.setSwitch(node,self)
               w.start()
	   
	self.__final_lock.acquire()
	print "</body></html>"
        self.__final_lock.release()

    def __release_final_lock(self):
        if (self.__numOfSwitches == 0):
            self.__final_lock.release()
    
    def __addUnique(self, theList, newItem):
        """\brief Adds a new item to the given list. The function ensures that if a port has learned more than one
	          mac address, it is removed from the list
	\param theList (\c list) The current list of learned addresses
	\param newItem (\c MACTableEntry) The item to add
	\return (\c list) The updated list
	"""
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
	
    def printVLANTable(self, switch, macs):
        """\brief Retrieves and prints a single switch database
	\param switch (\c subclass of Switch) The Switch objects used to retrieve information with
	"""
	uniqueMacs = []
	#macs = switch.getFullMACTable()

        nodes_dict = self.__manager.getNodes("all","all")

        self.__lock.acquire()
	for m in range(0, len(macs)):
	    macs[m].setSwitch(switch.getSwitchName())
	    uniqueMacs = self.__addUnique(uniqueMacs, macs[m])
            found = False
            for nodetype in nodes_dict:
                for node in nodes_dict[nodetype].values():
                    try:
                        interface_dict = node.getInterfaces()
                        for interface_type in interface_dict:
                            if interface_dict[interface_type] != None :
                                for interface in interface_dict[interface_type]:
                                    if (str(interface.getMAC().upper().strip()) == str(macs[m].getMAC().upper().strip())):
                                        macs[m].setDevice(node.getNodeID())
                                    
                    except AttributeError, a:
                        a = 2
                    except KeyError, a:
                        a = 1
                    except TypeError, a:
                        print a
                        print interface_dict 
	for x in range(0, len(uniqueMacs)):
            print str(uniqueMacs[x].getMAC()) + " " +  str(uniqueMacs[x].getSwitch()) + " " + \
		  str(uniqueMacs[x].getPort()) + " " + str(uniqueMacs[x].getLearned()) + " " + str(uniqueMacs[x].getDevice())+ "<br>"
        self.__numOfSwitches = self.__numOfSwitches - 1
        self.__release_final_lock()
        self.__lock.release()

###########################################################################################
#   Main execution
###########################################################################################
manager = HenManager()
manager.initLogging()
macRetriever = MACTableRetriever(manager)
macRetriever.printVLANTables()




