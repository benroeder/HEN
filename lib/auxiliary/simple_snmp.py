# Notes, the last results from each call are maintained in the object.
# This is not thread safe.
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.v4.entity.rfc3413.oneliner.cmdgen import CommandGenerator, CommunityData, UdpTransportTarget

class SNMP:
    def __init__(self,community,ip,version=1):
        self.__community = community
        self.__ip = ip
        self.__version = version
        self.__errorIndication = None
        self.__errorStatus = None
        self.__errorIndex = None
        self.__varBinds = None
        
    def get(self,oid):
        self.__errorIndication, self.__errorStatus, self.__errorIndex, self.__varBinds = cmdgen.CommandGenerator().getCmd(
            cmdgen.CommunityData('my-agent', 'public', 0),
            cmdgen.UdpTransportTarget((self.__ip, 161)),
            (oid)
            )
        return self.__varBinds

    def set(self,oid,value):
        self.__errorIndication, self.__errorStatus, self.__errorIndex, self.__varBinds = cmdgen.CommandGenerator().setCmd(
            cmdgen.CommunityData('my-agent', self.__community, 1),
            cmdgen.UdpTransportTarget((self.__ip, 161)),
            (oid, value)
            )
        
        return self.__varBinds

    def complex_set(self,value):
        self.__errorIndication, self.__errorStatus, self.__errorIndex, self.__varBinds = cmdgen.CommandGenerator().setCmd(
            cmdgen.CommunityData('my-agent', self.__community, 1),
            cmdgen.UdpTransportTarget((self.__ip, 161)),
            (value)
            )

        return self.__varBinds
                        
    def walk(self,oid):
         self.__errorIndication, self.__errorStatus, self.__errorIndex, self.__varBinds = cmdgen.CommandGenerator().bulkCmd(
             cmdgen.CommunityData('my-agent', self.__community, 1),
             cmdgen.UdpTransportTarget((self.__ip, 161)),
             0, 25, # nonRepeaters, maxRepetitions
             (oid)
             )
         return self.__varBinds

    def getErrorStatus(self):
        return self.__errorStatus

    def getErrorIndication(self):
        return self.__errorIndication

    def getErrorIndex(self):
        return self.__errorIndex

    def showError(self):
        return "Error with " + str(self.__varBinds[int(self.getErrorIndex())-1])

    def getVarBinds(self):
        return self.__varBinds

    def getCommunity(self):
        return self.__community

    def setCommunity(self,s):
        self.__community = s

    def getIpAddress(self):
        return self.__ip

    def setIpAddress(self,i):
        self.__ip = i


