##################################################################################################################
# apc.py: contains the power switch subclass for APC power switches
#
# CLASSES
# --------------------------------------------------------------------
# ApcRackpduPowerswitch      The class used to support APC Rack PDU power switches.
#
##################################################################################################################
import os, commands
from powerswitch import Powerswitch
from auxiliary.snmp import SNMP
from auxiliary.oid import OID

###########################################################################################
#   CLASSES
###########################################################################################

from auxiliary.snmp import SNMP
from auxiliary.oid import OID
from pysnmp.proto import rfc1902


class ApcRackpduPowerswitch(Powerswitch):
    """\brief Subclass used to control APC Rack PDU power switches via SNMP version 1. The
              switch uses the following codes:
              1 on
              2 off
              3 reboot
              4 delayed on
              5 delayed off
              6 delayed reboot
    """

    SENSOR_DESCRIPTIONS = {'current':{'current':15.00}}

    functions = ["powerswitch"]
    
    def __init__(self, powerswitchNode):
        """\brief Initializes the class
        \param powerswitchNode (\c PowerswitchNode) A PowerswitchNode object containing information to instantiate the class with
        """
        Powerswitch.__init__(self, powerswitchNode)   

    def poweroff(self, port):
        """\brief Attemps to power a port off
        \param port (\c string) The port to power off
        \return (\c int) 0 if successful, -1 otherwise
        """
        self.snmp.set((OID.apcControl + (int(port),)),rfc1902.Integer32(2))
        if self.snmp.getErrorStatus() :
            return (-1, "could not turn port off")
        return (0, "success")
    
    def poweron(self, port):
        """\brief Attemps to power a port on
        \param port (\c string) The port to power on
        \return (\c int) 0 if successful, -1 otherwise
        """

        self.snmp.set((OID.apcControl + (int(port),)),rfc1902.Integer32(1))
        if self.snmp.getErrorStatus():
            return (-1, "could not turn port on")
        return (0, "success")        

    def restart(self, port):
        """\brief Attemps to restart a port
        \param port (\c string) The port to restart
        \return (\c int) 0 if successful, -1 otherwise
        """
        self.snmp.set(OID.apcControl + (int(port),),rfc1902.Integer32(3))
        if self.snmp.getErrorStatus():
            return (-1, "could not restart port")
        return (0, "success")                
	
    def status(self, port):
        """\brief Retrieves the power status of a port
        \param port (\c string) The port to retrieve the status from
        \return (\c string) A string containing, on|off|unknown power status
        """
        res = self.snmp.get(OID.apcStatus + (int(port),))[0][1]
        if (res == rfc1902.Integer32(1)):
            return (0, "on")
        elif (res == rfc1902.Integer32(2)):
            return (0, "off")
        else:
            return (-1, "unknown power status " + str(res))

    def startup(self,port):
        return (-1,"not supported")

    def getCurrent(self):
        """\brief Retrieves the current draw of the device
        \return (\c string) A float of the number amps the device is currently drawing
        """
        return float(float(self.snmp.get(OID.apcCurrent)[0][1])/10)

    def getSerialNumber(self):
        return self.snmp.get(OID.apcSerialNumber)[0][1]

    def getSensorDescriptions(self):
        """\brief Returns the dictionary of sensorname:critical-value pairs.
        """
        return self.SENSOR_DESCRIPTIONS
    
    def getSensorReadings(self):
        """\brief Returns a dictionary of the form:
                            {sensorclass:{sensorname:reading}}.
        The reading will either be a numeric value (no units of measurements are
        given in the value) or -1 for sensors that could not be read.
        """
        sensorResults = self.getEmptySensorDictionary()
    	current = self.getCurrent()
    	(sensorResults['current'])['current'] = float(current)
    	return sensorResults
