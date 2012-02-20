##################################################################################################################
# serviceprocessor.py: contains the service processor super class
#
# CLASSES
# --------------------------------------------------------------------
# ServiceProcessor            The super class for any service processor in the testbed. Subclasses representing specific
#                             models of a service processor will be found in a file called [manufacturer].py. For
#                             instance, the class for a terminal server of brand Sun and whose model is fire v20z will
#                             be named SunFirev20zServiceProcessor and will reside in sun.py
#
##################################################################################################################

#.1.3.6.1.4.1.9237.2.1.1.4.1, SP-SST-MIB.mib
import os, commands
from hardware.device import Device

class ServiceProcessor(Device):
    """\brief Superclass for any service processor in the testbed
    """

    functions = []

    def __init__(self, serviceProcessorNode):
       """\brief Initializes the class
       \param serialNode (\c ServiceProcessorNode) A ServiceProcessorNode object containing information to instantiate the class with
       """
       self.__ipmiCommand = None
       self.__serviceProcessorNode = serviceProcessorNode
       self.__serviceProcessorNodeID = serviceProcessorNode.getNodeID()
       self.__ipmiPassword = self.__serviceProcessorNode.getSingleAttribute("ipmipassword")
       foundUser = False
       users = self.__serviceProcessorNode.getUsers()
       for user in users:
           if (user.getDescription() == "ipmi"):
               self.__ipmiCommand = "ipmitool -I lan -H " + self.__serviceProcessorNodeID + " -U " + \
                                    user.getUsername() + " -P " + user.getPassword()
               foundUser = True
               break
       if not foundUser:
           if (self.__ipmiPassword):
               self.__ipmiCommand = "ipmitool -I lan -H " + self.__serviceProcessorNodeID + " -P " + self.__ipmiPassword
           else:
               self.__ipmiCommand = "ipmitool -I lan -H " + self.__serviceProcessorNodeID

    def getNodeID(self):
        return  self.__serviceProcessorNodeID

    def getIPMICommand(self):
        """\brief Returns the ipmi command
        \return (\c string) The ipmi command
        """
        return self.__ipmiCommand
