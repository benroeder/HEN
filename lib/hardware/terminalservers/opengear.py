##################################################################################################################
# opengear.py: contains the power switch subclasses for Opengear power switches
#
# CLASSES
# --------------------------------------------------------------------
# OpengearCm4148Terminalserver The class used to support Opengear Cm4148 power switches
#
##################################################################################################################
import os, sys, commands, socket
from terminalserver import Terminalserver
from subprocess import *
try:
    import paramiko
    from paramiko import SSHClient
except:
    pass

###########################################################################################
#   CLASSES
###########################################################################################
class OpengearCm4148Terminalserver(Terminalserver):
    """\brief Subclass used to control Opengear Cm4148 terminal servers. All interaction is done through telnet
    """

    functions = ["terminalserver"]    

    def __init__(self, serialNode):
        """\brief Initializes the class
        \param serialNode (\c SerialNode) A SerialNode object containing information to instantiate the class with
        """
        Terminalserver.__init__(self, serialNode)
        self.__sshCommand = None
        self.__socket = None
        self.__bufferThreshold = None
        self.__buffer = ""

    def connectTelnet(self, port):
        """\brief Connects to to the given port via telnet
        \param port (\c string) The port to connect to
        """
        cmd = "telnet " + str(self.getIPAddress()) + " " + str(2000 + int(port))
        print "To exit press ctrl-] (then type quit) , username=" + self.getUsername() + " , password=" + self.getPassword()
        os.system(cmd)

    def connect(self, port):
        """\brief Connects to to the given port via ssh
        \param port (\c string) The port to connect to
        """
        cmd = self.getSSHCommand() + " " + self.getUsername() + "@" + str(self.getIPAddress()) + " -p " + str(3000 + int(port))        
        os.system(cmd)

    def connectRaw(self, port, bufferThreshold=10):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.connect((self.getIPAddress(), 4000 + int(port)))
        self.__bufferThreshold = bufferThreshold

    def closeRaw(self):
        self.__socket.close()
        
    def sendRaw(self, data):
        self.__socket.send(data)

    def recvRaw(self):
        data = self.__socket.recv(1024)
        if (data == None):
            return False
        self.__buffer += data
        if (len(self.__buffer) >= self.__bufferThreshold):
            return True
        return False

    def getAndDeleteBuffer(self):
        temp = self.__buffer
        self.__buffer = ""
        return temp
                                                    
    def getSocket(self):
        return self.__socket

    def getBaudRate(self,port):  
        """\brief Retrieves a ports baud rate
        \param port (\c Int) The port for which to retrieve the baud rate
        """
  
        client = SSHClient()
        paramiko.util.logging.getLogger().setLevel(50)

        client.load_system_host_keys()
        client.connect(str(self.getIPAddress()),22,"root","default")
        stdin, stdout, stderr = client.exec_command("/bin/config --get=config.ports.port"+str(port)+".speed")
	        
        line = stdout.readline()
        if line.startswith("config.ports.port"):
            print "Baud Rate: " + line.partition(" ")[2]
            
        client.close()
            	
    def setBaudRate(self,port,rate):
        """\brief Sets a ports baud rate
        \param port (\c Int) The port for which to set the baud rate
        \param rate (\c String) The port for which to set the baud rate
        """

        client = SSHClient()
        paramiko.util.logging.getLogger().setLevel(40)

        client.load_system_host_keys()
        client.connect(str(self.getIPAddress()),22,"root","default")
        stdin, stdout, stderr = client.exec_command("/bin/config --set=config.ports.port"+str(port)+".speed="+str(rate))

        client.close()
