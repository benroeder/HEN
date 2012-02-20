################################################################################
# sun.py: contains the service processor subclasses for computer nodes
#
# CLASSES
# --------------------------------------------------------------------
# SunFirev20zServiceProcessor  The class used to support Sun Fire v20z service 
# processors
################################################################################
import os, commands
from serviceprocessor import ServiceProcessor

################################################################################
#   SNMP SUN OIDs
################################################################################
# ipmitool -I lan -H serviceprocessor5 -P manager


################################################################################
#   CLASSES
################################################################################
class SunFirev20zServiceProcessor(ServiceProcessor):
    """\brief Subclass used to control sun fire v20z service processors.
    """

    functions = ["serviceprocessor","power"]
    
    SENSOR_DESCRIPTIONS = {'temperature':{ \
                                          'ambienttemp':40.200, \
                                          'cpu0.dietemp':73.200, \
                                          'cpu0.memtemp':55.200, \
                                          'cpu1.dietemp':73.200, \
                                          'cpu1.memtemp':55.200, \
                                          'gbeth.temp':60.000, \
                                          'hddbp.temp':60.000, \
                                          'sp.temp':60.000
                                          }, \
                           'fanspeed':{ \
                                       'fan1.tach':1980.000, \
                                       'fan2.tach':1980.000, \
                                       'fan3.tach':1980.000, \
                                       'fan4.tach':1980.000, \
                                       'fan5.tach':1980.000, \
                                       'fan6.tach':1980.000 \
                                       }, \
                           'voltage':{ \
                                       'bulk.v12-0-s0':13.800, \
                                       'bulk.v3_3-s0':3.600, \
                                       'bulk.v3_3-s5':3.600, \
                                       'bulk.v5-s0':5.520, \
                                       'bulk.v5-s5':5.520, \
                                       'cpu0.vcore-s0':1.680, \
                                       'cpu0.vldt2':1.320, \
                                       'cpu1.vcore-s0':1.680 \
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
        """
        cmd = self.getIPMICommand() + " sdr"
        cmdResults = commands.getstatusoutput(cmd)
        sensorResults = self.getEmptySensorDictionary()

        if (cmdResults[0] != 0):
            return None
        else:
            for line in cmdResults[1].splitlines():
                lineFields = line.split("|")
                sensorName = lineFields[0].strip()
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

class SunX4100ServiceProcessor(ServiceProcessor):
    """\brief Subclass used to control sun fire X4100 service processors.
    """

    functions = ["serviceprocessor","power"]
    
    SENSOR_DESCRIPTIONS = {'temperature':{ \
                                          'mb.t_amb':45.000, \
                                          'fp.t_amb':43.000, \
                                          'pdb.t_amb':42.000, \
                                          'io.t_amb':42.000, \
                                          'p0.t_core':75.000 \
                                          }, \
                           'voltage':{ \
                                       'mb.v_bat':3.792, \
                                       'mb.v_+3v3stby':3.996 \
                                       }}

    def __init__(self, serviceProcessorNode):
        """\brief Initializes the class
        \param serviceProcessorNode (\c ServiceProcessorNode) 
        A ServiceProcessorNode object containing information to instantiate the 
        class with
        """
        ServiceProcessor.__init__(self, serviceProcessorNode)   

    def set_boot_pxe(self):
        cmd = self.getIPMICommand() + " chassis bootdev pxe"
        results = commands.getstatusoutput(cmd)
        if (results[0] != 0):
            return "error setting boot dev to pxe"                     

    def poweroff(self,port):
        # hack to work around old bios
        self.set_boot_pxe()
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
        # hack to work around old bios
        self.set_boot_pxe()
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
        # hack to work around old bios
        self.set_boot_pxe()
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
        """
        cmd = self.getIPMICommand() + " sdr"
        cmdResults = commands.getstatusoutput(cmd)
        sensorResults = self.getEmptySensorDictionary()

        if (cmdResults[0] != 0):
            return None
        else:
            for line in cmdResults[1].splitlines():
                lineFields = line.split("|")
                sensorName = lineFields[0].strip()
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
