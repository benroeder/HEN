#!/usr/bin/env python
import __builtin__, sys, os, select, struct, array
from socket import socket, AF_INET, SOCK_STREAM, gaierror as SocketError
from xmlrpclib import ServerProxy as RemoteXMLRPCServer, Error as XMLRPCError, ProtocolError
sys.path.append("/usr/local/hen/lib")

#LOG_REQUEST_PORT_PREFIX = 8000

class Mote:
    
    def __init__(self, moteNode):
        # Assigned values
        self.__nodeid = moteNode.getNodeID()
        self.__controllerid = moteNode.getControllerID()
        self.__groupid = moteNode.getGroupID()
        
        # Inspected values
        self.__vendor = moteNode.getVendor()
        self.__model = moteNode.getModel()
        
        # Introspected values
        self.__mac = moteNode.getMACAddresses()[0]
#        self.__controllerid = moteNode.getControllerID()
#        
#        self.__sock = socket(AF_INET, SOCK_STREAM)
#        self.__xmlRpcPort = 9001
#        self.__listening = 0
#        
#        url = "http://%s:%d" % (self.__controllerid, self.__xmlRpcPort)
#        self.__controller = RemoteXMLRPCServer(url)
#    
#    def __open(self):
#        """\brief
#        """
#        self.__sock.connect((self.__controllerid, LOG_REQUEST_PORT_PREFIX + int(self.__nodeid[4:])))
#    
#    def __close(self):
#        """\brief
#        """
#        self.__listening = 0
#        self.__sock.close()
#    
#    def __read(self):
#        """\brief
#        \param
#        \param
#        """
#        ready,_,_ = select.select([self.__sock],[],[self.__sock])
#       if not ready:
#           raise RuntimeError("some error occured")
#        return self.__sock.recv(1024)
#        
#    def __write(self, data):
#        length = len(data)
#        count = 0
#        self.__sock.send(str(length))
#        while count < length:
#            count = self.__sock.send(data)
#    
#    def listen(self, ammsgtype):
#        """\brief
#        \param
#        \param
#        """
#        try:
#            self.__listening += 1
#            #self.__write(str(ammsgtype))
#            while self.__listening:
#                try:
#                    data = self.__read()
#                except EOFError:
#                    continue
#                print data
#        except KeyboardInterrupt:
#            return
#    
#    def connect(self):
#        """\brief
#        """
#        self.__open()
#        
#    def disconnect(self):
#        """\brief
#        """
#        self.__close()
#    
#    def readMsg(self):
#        """\brief
#        """
#        data = self.__read()
#        return data
#    
#    def sendMsg(self, type, data):
#        try:
#            server.moteSend(self.__nodeid, type,  data)
#        except XMLRPCError, v:
#            self.__log.error("Error invoking %s.moteSend:\t%s" % (controller, v))
#        except gaierror, v:
#            self.__log.error("Error invoking %s.moteSend:\t%s" % (controller, v))
#    
    def getMoteVendor(self):
        return self.__vendor
    
    # Introspection Methods
    def getMACAddress(self):
        return self.__mac
    
#    def getRadioPreset(self):
#        """\brief Virtual function placeholder
#        \return (\c None)
#        """        
#        return None
#    
#    def setRadioPreset(self, channel):
#        """\brief Virtual function placeholder
#        \return (\c None)
#        """        
#        return None
#    
#    def getRadioFrequency(self):
#        """\brief Virtual function placeholder
#        \return (\c None)
#        """        
#        return None
#    
#    def setRadioFrequency(self, frequency):
#        """\brief Virtual function placeholder
#        \return (\c None)
#        """        
#        return None
#    
#    def getRadioPower(self):
#        """\brief Virtual function placeholder
#        \return (\c None)
#        """        
#        return None
#    
#    def setRadioPower(self, level):
#        try:
#            self.__controller.moteSend(self.__nodeid, 20, "3H", 3, 1 << 15, level)
#        #except XMLRPCError, v:
#        #    print "Error invoking %s:%s.setRadioPower:\t%s" % (self.__controllerid, self.__nodeid, v)
#        except SocketError, v:
#            print "Error invoking %s:%s.setRadioPower:\t%s" % (self.__controllerid, self.__nodeid, v)
#    
#    def getImageName(self):
#        """\brief Virtual function placeholder
#        \return (\c None)
#        """        
#        return None
#
#    def reset(self):
#        self.runCommand(0, [0])
#        
#    def runCommand(self, cmdid, args):
#        try:
#            self.__controller.moteSend(self.__nodeid, 20, "3H", cmdid, 1 << 15, args[0])
#        #except XMLRPCError, v:
#        #    print "Error invoking %s:%s.runCommand:\t%s" % (self.__controllerid, self.__nodeid, v)
#        except SocketError, v:
#            print "Error invoking %s:%s.runCommand:\t%s" % (self.__controllerid, self.__nodeid, v)

