##################################################################################################################
# serviceprocessor.py: contains the service processor super class
#
# CLASSES
# --------------------------------------------------------------------
# ServiceProcessor            The super class for any sensor in the testbed. Subclasses representing specific
#                             models of a sensor will be found in a file called [manufacturer].py. For
#                             instance, the class for a sensor of brand Sensatronics and whose model is e4 will
#                             be named SensatronicsE4Sensor and will reside in sensatronics.py
#
##################################################################################################################
import os, commands
from auxiliary.snmp import SNMP

from pysnmp.proto import rfc1902
from pysnmp.smi import builder

class Sensor:
    """\brief Superclass for any sensor in the testbed
    """

    functions = []    

    def __init__(self, sensorNode):
       """\brief Initializes the class
       \param serialNode (\c SensorNode) A SensorNode object containing information to instantiate the class with
       """
       self.__sensorNode = sensorNode
       self.__ipAddress = sensorNode.getInterfaces("infrastructure")[0].getIP()
       self.snmp = SNMP("private",self.__ipAddress,SNMP.SNMPv1)

    def getSensorNode(self):
        return self.__sensorNode

