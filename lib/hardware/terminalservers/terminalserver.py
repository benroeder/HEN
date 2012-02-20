##################################################################################################################
# terminalserver.py: contains the terminal server (serial node) super class
#
# CLASSES
# --------------------------------------------------------------------
# PowerSwitch                 The super class for any terminal server in the testbed. Subclasses representing specific
#                             models of a terminal server will be found in a file called manufacturer.py. For instance,
#                             the class for a terminal server of brand Opengear and whose model is cm4148 will be named
#                             OpengearCm4148Terminalserver and will reside in opengear.py
#
##################################################################################################################
from hardware.device import Device

class Terminalserver(Device):
    """\brief Superclass for any terminal server in the testbed
    """
    functions = [] 
    def __init__(self, serialNode):
        """\brief Initializes the class
        \param serialNode (\c SerialNode) A SerialNode object containing information to instantiate the class with
        """        
        self.__serialNode = serialNode
	self.__serialNodeID = serialNode.getNodeID()
	self.__ipAddress = serialNode.getInterfaces("infrastructure")[0].getIP()

 #       users = serialNode.getUsers() #.getUsername()

        # Assume there is a basic username of "serial"
        self.__username = "serial"
        self.__password = None
        for user in serialNode.getUsers():
            if (user.getUsername() == "serial"):
                self.__password = user.getPassword()
#	self.__password = serialNode.getUser().getPassword()
        self.__sshCommand = None

    def setSSHCommand(self, s):
        """\brief Sets the ssh command. The ssh command consists of ssh -i followed by the private key to use for
                  authentication
        \param s (\c string) The ssh command
        """
        self.__sshCommand = s

    def getSSHCommand(self):
        """\brief Gets the ssh command
        \return (\c string) The ssh command
        """
        return self.__sshCommand

    def setSerialNode(self, n):
        """\brief Sets the SerialNode object
	\param n (\c SerialNode) The SerialNode object to set this class to
	"""
        self.__serialNode = n

    def getSerialNode(self):
        """\brief Gets the SerialNode object
	\return (\c SerialNode) The SerialNode object
	""" 
        return self.__serialNode

    def setSerialNodeID(self, i):
        """\brief Sets the terminal server's id
	\param i (\c string) The terminal server's id
	"""
	self.__serialNodeID = i
	
    def getSerialNodeID(self):
        """\brief Gets the terminal server's id
	\return (\c SerialNode) The terminal server's id
	""" 
        return self.__serialNodeID
	
    def setIPAddress(self, i):
        """\brief Sets the terminal server's IP address
	\param i (\c string) The terminal server's IP address
	"""
        self.__ipAddress = i
	    
    def getIPAddress(self):
        """\brief Gets the terminal server's IP address
	\return (\c string) The terminal server's IP address
	""" 
        return self.__ipAddress

    def setUsername(self, u):
        """\brief Sets the terminal server's user name
	\param u (\c string) The terminal server's user name
	"""
	self.__username = u
	    
    def getUsername(self):
        """\brief Gets the user name
	\return (\c string) The user name
	""" 
	return self.__username

    def setPassword(self, p):
        """\brief Sets the terminal server's password
	\param p (\c string) The terminal server's password
	"""
	self.__password = p

    def getPassword(self):
        """\brief Gets the password
	\return (\c string) The password
	""" 
	return self.__password
