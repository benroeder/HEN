#################################################################################################################
# powerswitch.py: contains the powerswitch superclass
#
# CLASSES
# --------------------------------------------------------------------
# PowerSwitch                 The super class for any power switch in the testbed. Subclasses representing specific
#                             models of a power switch will be found in a file called manufacturer.py. For instance
#                             the class for a power switch of brand BlackBox and whose model is master will be named
#                             BlackboxMaster and will reside in blackbox.py
#
##################################################################################################################
from auxiliary.snmp import SNMP

from pysnmp.proto import rfc1902
from pysnmp.smi import builder
from hardware.device import Device

class Powerswitch(Device):
    """\brief Superclass for any power switch in the testbed
    """
    
    functions = [] 
    
    def __init__(self, powerswitchNode):
        """\brief Initializes the class
        \param powerswitchNode (\c PowerswitchNode) A PowerswitchNode object containing information to instantiate the class with
        """
        self.__powerswitchNode = powerswitchNode
        self.__community = powerswitchNode.getSNMPwriteCommunity()
	self.__powerswitchNodeID = powerswitchNode.getNodeID()
	self.__ipAddress = powerswitchNode.getInterfaces("infrastructure")[0].getIP()
        self.__username = None
        self.__password = None
        if (powerswitchNode.getUsers() != None):
            self.__username = powerswitchNode.getUsers()[0].getUsername()
            self.__password = powerswitchNode.getUsers()[0].getPassword()
	
        self.snmp = SNMP(self.__community,self.__ipAddress,SNMP.SNMPv1)
        
    def setPowerswitchNode(self, n):
        """\brief Sets the PowerswitchNode object
	\param n (\c PowerswitchNode) The PowerswitchNode object to set this class to
	"""
        self.__powerswitchNode = n

    def getPowerswitchNode(self):
        """\brief Gets the PowerswitchNode object
	\return (\c PowerswitchNode) The PowerswitchNode object
	""" 
        return self.__powerswitchNode

    def setCommunity(self, c):
        """\brief Sets the community and updates the snmp commands accordingly
        \param c (\c string) The community
        """
        self.__community = c
        del self.snmp
        self.snmp = SNMP(self.__community,self.__ipAddress,SNMP.SNMPv1)

    def getCommunity(self):
        """\brief Gets the community
        \return (\c string) The community
        """
        return self.__community

    def setPowerswitchNodeID(self, i):
        """\brief Sets the power switch's id
	\param i (\c string) The power switch's id
	"""
	self.__powerswitchNodeID = i
	
    def getPowerswitchNodeID(self):
        """\brief Gets the power switch's id
	\return (\c PowerswitchNode) The power switch's id
	""" 
        return self.__powerswitchNodeID

    def setNodeID(self, i):
        """\brief Sets the power switch's id
	\param i (\c string) The power switch's id
	"""
	self.__powerswitchNodeID = i
	
    def getNodeID(self):
        """\brief Gets the power switch's id
	\return (\c PowerswitchNode) The power switch's id
	""" 
        return self.__powerswitchNodeID
	
    def setIPAddress(self, i):
        """\brief Sets the power switch's IP address
	\param i (\c string) The power switch's IP address
	"""
        self.__ipAddress = i
         
    def getIPAddress(self):
        """\brief Gets the power switch's IP address
	\return (\c string) The power switch's IP address
	""" 
        return self.__ipAddress

    def setUsername(self, u):
        """\brief Sets the power switch's user name
	\param u (\c string) The power switch's user name
	"""
        self.__username = u
	    
    def getUsername(self):
        """\brief Gets the user name
	\return (\c string) The user name
	""" 
        return self.__username

    def setPassword(self, p):
        """\brief Sets the power switch's password
	\param p (\c string) The power switch's password
	"""
        self.__password = p
	    
    def getPassword(self):
        """\brief Gets the password
	\return (\c string) The password
	""" 
        return self.__password

    def getSensorReadings(self):
        return {}
