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
class AviosysIppower9258Powerswitch(Powerswitch):
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
        
	
        #self.__theURL = "http://"+str(self.getUsername())+":"+str(self.getPassword())+"@"+str(self.getIPAddress())+"/Set.cmd?CMD="
	self.__theURL = "http://"+str(self.getIPAddress())

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

        #data = {"P"+str(self.slaveID) + str(portNumber):action}
        

	if (self.getUsername() == "" and self.getPassword() == ""):
	    print "Invalid username and password, both are set to an empty string"
	    sys.exit()

	passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
	passman.add_password(None, self.__theURL, str(self.getUsername()), str(self.getPassword()))
	authhandler = urllib2.HTTPBasicAuthHandler(passman)
	opener = urllib2.build_opener(authhandler)
	urllib2.install_opener(opener)
        #print self.__theURL+"/Set.cmd?CMD=SetPower+P"+str(int(59)+int(portNumber))+"="+str(action)
        if action == '0' or action == '1':
            pagehandle = urllib2.urlopen(self.__theURL+"/Set.cmd?CMD=SetPower+P"+str(int(59)+int(portNumber))+"="+str(action))
	    res = self.__parse_reply(pagehandle.readlines()[0])
	    for i in res:
		if i[0] == int(portNumber) and i[1] == action:
		    return (0, "success")
	    return (-1, "could not turn port on")
	    
        elif action == 'status':
	    pagehandle = urllib2.urlopen(self.__theURL+"/Set.cmd?CMD=GetPower+P"+str(int(59)+int(portNumber))+"="+str(action))
	    res = self.__parse_reply(pagehandle.readlines()[0])
	    for i in res:
		if i[0] == int(portNumber) and i[1] == '1':
		    return (0, "on")
		if i[0] == int(portNumber) and i[1] == '0':
		    return (0, "off")
	    return (-1, "unknown power status")
        else:
            return -1

    def __parse_reply(self,s):
	s = s.replace('<html>','')
	s = s.replace('</html>\r\n','')
	s = s.replace('P','')
	s = s.split(',')
	res = []
	for i in s:
	    res.append((int(i.split('=')[0])-59,i.split('=')[1]))
	return res
    def poweroff(self, port):
        """\brief Attemps to power a port off
        \param port (\c string) The port to power off
        """
        return self.__sendCommand(port,'0')

    def poweron(self, port):
        """\brief Attemps to power a port on
        \param port (\c string) The port to power on
        """
        return self.__sendCommand(port,'1')

    def restart(self, port):
        """\brief Attemps to restart a port
        \param port (\c string) The port to restart
        """
        res_off = self.poweroff(port)
        res_on = self.poweron(port)
	if res_off[0] == 0 and res_on[0] == 0:
	    return (0, "success")
	elif res_off[0] == 1 and res_on[0] == 0:
	    return (-1, "failure turning port off")
	elif res_off[0] == 0 and res_on[0] == 1:
	    return (-1, "failure turning port on")
	elif res_off[0] == 1 and res_on[0] == 1:
	    return (-1, "failure turning port off and on")

    def startup(self,port):
        return (-1,"not supported")

    def status(self, portNumber):
        """\brief Retrieves the power status of a port
        \param port (\c string) The port to retrieve the status from
        \return (\c string) A string containing, on|off|reboot|unknown power status
        """
        return self.__sendCommand(portNumber,'status')

    def current(self):
        """\brief Retrieves the current draw of the device
        \return (\c string) A float of the number amps the device is currently drawing
        """
        return -1


