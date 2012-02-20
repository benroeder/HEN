################################################################################
# sensatronics.py: contains the sensor subclasses for sensatronics sensors
#
# CLASSES
# --------------------------------------------------------------------
# SensatronicsE4Sensor  The class used to support Sensatronics E4 sensors
#
################################################################################
import os, commands, urllib
from auxiliary.snmp import SNMP
from auxiliary.oid import OID

from pysnmp.proto import rfc1902
from pysnmp.smi import builder

from sensor import Sensor
from hardware.device import Device

################################################################################
#   CLASSES
################################################################################
class SensatronicsE4Sensor(Sensor, Device):
    """\brief Subclass used to control Sensatronics E4 sensors
    """

    functions = ["sensor"]

    SENSOR_DESCRIPTIONS = {'temperature':{ \
                                          'Probe 1':35, \
                                          'Probe 2':35, \
                                          'Probe 3':35, \
                                          'Probe 4':35 \
                                          }}

    def __init__(self, sensorNode):
        """\brief Initializes the class
        \param sensorNode (\c SensorNode) A SensorNode object containing
        information to instantiate the class with
        """
        Sensor.__init__(self, sensorNode)
        self.__ipAddress = sensorNode.getInterfaces("infrastructure")[0].getIP()

    def getSensorDescriptions(self):
        """\brief Returns the dictionary of sensorname:critical-value pairs.
        """
        return self.SENSOR_DESCRIPTIONS

    def getSensorReadings(self):
        """\brief Returns a dictionary of the form:
                        {sensorclass:{sensorname:reading}}.

        The reading will either be a numeric value (no units of measurements are
        given in the value) or -1 for sensors that could not be read.

        Rather than use SNMP, this method simplifies life by using the standard
        sensatronics text file, obtainable via http.
        """

        sensorResults = self.getEmptySensorDictionary()
        for index in range(0,4):
            probe = int(index) + 1
            sensorName = "Probe "+str(probe)
            sensorClass = self.getSensorClassFromName(self.SENSOR_DESCRIPTIONS,\
                                                      sensorName)
            try:
                sensorReading = \
                        self.snmp.get(OID.sensatronicsProbe+(probe,2,0,))[0][1]
                (sensorResults[sensorClass])[sensorName] = \
                                                float(str(sensorReading))
            except:
                (sensorResults[sensorClass])[sensorName] = -1.0
        return sensorResults
