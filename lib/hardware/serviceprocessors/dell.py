################################################################################
# dell.py: contains the service processor subclasses for computer nodes
#
# CLASSES
# --------------------------------------------------------------------
# DellSc1425ServiceProcessor  The class used to support Dell SC1425 service 
# processors
#
################################################################################
import os, commands
from serviceprocessor import ServiceProcessor

################################################################################
#   CLASSES
################################################################################
class DellSc1425ServiceProcessor(ServiceProcessor):
    """\brief Subclass used to control dell sc1425 service processors.
    """

    functions = ["serviceprocessor","power"]
    
    SENSOR_DESCRIPTIONS = {'temperature':{'Temp1':125.000, \
                                          'Temp2':125.000, \
                                          'Ambient Temp':47.000, \
                                          'Planar Temp':72.000, \
                                          'Riser Temp':67.000, \
                                          'Temp3':125.000, \
                                          'Temp4':125.000 \
                                          }, \
                           'fanspeed':{'FAN 1A RPM':2175.000, \
                                       'FAN 1B RPM':2175.000, \
                                       'FAN 2A RPM':2175.000, \
                                       'FAN 2B RPM':2175.000, \
                                       'FAN 3A RPM':2175.000, \
                                       'FAN 3B RPM':2175.000, \
                                       'FAN 4A RPM':2175.000, \
                                       'FAN 4B RPM':2175.000 \
                                       }}


    def __init__(self, serviceProcessorNode):
        """\brief Initializes the class
        \param serviceProcessorNode (\c ServiceProcessorNode) 
        A ServiceProcessorNode object containing information to instantiate the 
        class with
        """
        ServiceProcessor.__init__(self, serviceProcessorNode)   

    def poweroff(self,port):
        cmd = self.getIPMICommand() + " power off"
        results = commands.getstatusoutput(cmd)
        if (results[0] != 0):
            return (-1,"error")
        else:
            if results[1].upper().find("OFF") != -1:
                return (0,"off")
            elif results[1].upper().find("ON") != -1:
                return (0,"on")
            else:
                return (-1,"unknown")
            
    def poweron(self,port):
        cmd = self.getIPMICommand() + " power on"
        results = commands.getstatusoutput(cmd)
        if (results[0] != 0):
            return (-1,"error")
        else:
            if results[1].upper().find("OFF") != -1:
                return (0,"off")
            elif results[1].upper().find("ON") != -1:
                return (0,"on")
            else:
                return (-1,"unknown")
            
            
    def restart(self,port):
        cmd = self.getIPMICommand() + " power reset"
        results = commands.getstatusoutput(cmd)
        if (results[0] != 0):
            return (-1,"error")
        else:
            if results[1].upper().find("OFF") != -1:
                return (0,"off")
            elif results[1].upper().find("ON") != -1:
                return (0,"on")
            else:
                return (-1,"unknown")
            
    def status(self,port):
        cmd = self.getIPMICommand() + " power status"
        results = commands.getstatusoutput(cmd)
        if (results[0] != 0):
            return (-1,"error")
        else:
            if results[1].upper().find("OFF") != -1:
                return (0,"off")
            elif results[1].upper().find("ON") != -1:
                return (0,"on")
            else:
                return (-1,"unknown")

    def getSensorDescriptions(self):
        """\brief Returns the dictionary of sensorname:critical-value pairs.
        """
        return self.SENSOR_DESCRIPTIONS
    
    def getSensorReadings(self):
        """\brief Returns a dictionary of the form:
                        {sensorclass:{sensorname:reading}}.
                        
        The reading will either be a numeric value (no units of measurements are
        given in the value) or -1 for sensors that could not be read.
        
        NOTE: Dell have decided not to give some sensors unique names, so this
        method has a few dirty hacks to make it work. For instance, there are
        4 sensors named "Temp". For each found "Temp" sensor, a number from 1-4
        is appended in order of appearance (which is always the same in the sdr
        command), giving "Temp1", "Temp2", and so forth. Also note that the same
        will need doing if alarms require implementing.
        """
        cmd = self.getIPMICommand() + " sdr"
        cmdResults = commands.getstatusoutput(cmd)
        sensorResults = self.getEmptySensorDictionary()

        tempSensorNumber = 1

        if (cmdResults[0] != 0):
            return None
        else:
            for line in cmdResults[1].splitlines():
                lineFields = line.split("|")
                sensorName = lineFields[0].strip()
                if sensorName == "Temp":
                    sensorName = sensorName + str(tempSensorNumber)
                    tempSensorNumber = tempSensorNumber + 1
                    
                sensorClass = self.getSensorClassFromName( \
                               self.SENSOR_DESCRIPTIONS, sensorName)
                if not sensorClass:
                    continue
                reading = lineFields[1].strip()
                if reading[0].isdigit():
                    reading = reading[:reading.find(" ")]
                    (sensorResults[sensorClass])[sensorName] = reading
                else:
                    (sensorResults[sensorClass])[sensorName] = -1
        return sensorResults
