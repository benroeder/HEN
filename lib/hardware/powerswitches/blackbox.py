##################################################################################################################
# blackbox.py: contains the power switch subclasses for Blackbox power switches
#
# CLASSES
# --------------------------------------------------------------------
# BlackboxMasterPowerswitch  The class used to support Blackbox Master power switches.
# BlackboxSlavePowerswitch   The class used to support Blackbox Slave power switches.
#
##################################################################################################################
import urllib2, urllib
from powerswitch import Powerswitch

###########################################################################################
#   CLASSES
###########################################################################################
class BlackboxMasterPowerswitch(Powerswitch):
    """\brief Subclass used to control Blackbox Master power switches. All interaction is done through http,
              the power switch uses the following codes:
	      0 power off
	      1 power on
	      r restart
    """
    functions = ["powerswitch"]

    def __init__(self, powerswitchNode):
        """\brief Initializes the class
        \param powerswitchNode (\c PowerswitchNode) A PowerswitchNode object containing information to instantiate the class with
        """
        Powerswitch.__init__(self, powerswitchNode)

	self.__theURL = "http://" + str(self.getIPAddress()) + "/"
	self.__postURL = "http://" + str(self.getIPAddress()) + "/rack.html"
        # Slave id of 1 is the master device.
        self.slaveID = 1


    def __setURL(self, u):
        """\brief Sets the power switch's url
	\param u (\c string) The power switch's url
	"""
        self.__theURL = u

    def __getURL(self):
        """\brief Gets the power switch's url
	\return (\c string) The power switch's url
	"""
        return self.__theURL

    def __setPostURL(self, u):
        """\brief Sets the power switch's post url
	\param u (\c string) The power switch's post url
	"""
	self.__postURL = u

    def __getPostURL(self):
        """\brief Gets the power switch's post url
	\return (\c string) The power switch's post url
	"""
	return self.__postURL

    def __sendCommand(self, portNumber, action):
        """\brief Sends a command to the power switch
	\param portNumber (\c string) The port to perform the action on
	\param action (\c string) The action to perform
	"""

        data = {"P"+str(self.slaveID) + str(portNumber):action}

	if (self.getUsername() == "" and self.getPassword() == ""):
	    print "Invalid username and password, both are set to an empty string"
	    sys.exit()

        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
	passman.add_password(None, self.__theURL, self.getUsername(), self.getPassword())
	authhandler = urllib2.HTTPBasicAuthHandler(passman)
	opener = urllib2.build_opener(authhandler)
	result = opener.open(self.__postURL, data=urllib.urlencode(data))

    def poweroff(self, port):
        """\brief Attemps to power a port off
        \param port (\c string) The port to power off
        """
        self.__sendCommand(port,'0')

    def poweron(self, port):
        """\brief Attemps to power a port on
        \param port (\c string) The port to power on
        """
        self.__sendCommand(port,'1')

    def restart(self, port):
        """\brief Attemps to restart a port
        \param port (\c string) The port to restart
        """
        self.__sendCommand(port,'r')

    def startup(self,port):
        return (-1,"not supported")

    def status(self, portNumber):
        """\brief Retrieves the power status of a port
        \param port (\c string) The port to retrieve the status from
        \return (\c string) A string containing, on|off|reboot|unknown power status
        """
        portNumber = str(int(portNumber) - 1)
        if (self.getUsername() == "" and self.getPassword() == ""):
    	    print "Invalid username and password, both are set to an empty string"
    	    sys.exit()

        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    	passman.add_password(None, self.__theURL, self.getUsername(), self.getPassword())
    	authhandler = urllib2.HTTPBasicAuthHandler(passman)
    	opener = urllib2.build_opener(authhandler)
    	urllib2.install_opener(opener)
        data = None
        try:
            # XXX: TODO: Handle more gracefully, notify user (?)
            data = opener.open(self.__postURL)
        except:
            return -1
        counter = 0
        for x in data:
            # We're only interested in the second line coming back from the server
            if (counter == 1):
                # First remove everything before "display(" from the string
		indexOfDisplayFunction = x.find("display(")
		x = x[indexOfDisplayFunction + 8:]

		# The third double quotes from the end marks the end of the last parameter, find this
		searchUntil = len(x)
		for j in range (0, 3):
		    indexOfLastParam = x.rfind('"', 0, searchUntil)
                    searchUntil = indexOfLastParam - 1

                x = x[:indexOfLastParam + 4]

                # At this point x is composed of parameters of the form: "name     ",1    ,
		# since this is the case, the number of parameters is the number of double quotes divided by 2
		numberParameters = x.count('"') / 2

                # Go through each parameter, retrieving the device name and its status. Match the device name with
                # the given device name and print out its status (0 or 1)
                for j in range (0, numberParameters):
                    deviceName = x[1:x.find('"', 1)]
                    deviceName = deviceName.rstrip()
                    indexOfComma = x.find(',')
                    deviceStatus = x[indexOfComma + 1:x.find(',', indexOfComma + 1)]
                    deviceStatus = deviceStatus.rstrip()

                    if (str(j) == portNumber):
                        if (deviceStatus == "1"):
                            return (0,"on")
                        elif (deviceStatus == "0"):
                            return (0,"off")
                        elif (deviceStatus == "r"):
                            return (0,"reboot")
                        else:
                            return (-1,"unknown power status" + str(deviceStatus))
                    x = x[x.find('"', indexOfComma):]
            counter += 1
        return (-1,"Cannot connect to power switch")

    def current(self):
        """\brief Retrieves the current draw of the device
        \return (\c string) A float of the number amps the device is currently drawing
        """
        return -1

class BlackboxSlavePowerswitch(BlackboxMasterPowerswitch):
    """\brief Subclass used to control Blackbox Master power switches. All interaction is done through http,
              the power switch uses the following codes:
	      0 power off
	      1 power on
	      r restart
    """
    functions = []

    def __init__(self, powerswitchNode):
        """\brief Initializes the class
        \param powerswitchNode (\c PowerswitchNode) A PowerswitchNode object containing information to instantiate the class with
        """
        BlackboxMasterPowerswitch.__init__(self, powerswitchNode)

	self.__theURL = "http://" + str(self.getIPAddress()) + "/"
	self.__postURL = "http://" + str(self.getIPAddress()) + "/rack.html"
        self.slaveID = powerswitchNode.getAttributes()["slaveid"]


