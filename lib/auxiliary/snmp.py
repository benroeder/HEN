# Notes, the last results from each call are maintained in the object.
# This is not thread safe.
from pysnmp.proto.rfc1902 import ObjectName
from pysnmp.entity import engine, config
from pysnmp.carrier.asynsock.dgram import udp
from pysnmp.entity.rfc3413 import cmdgen
import threading
import logging

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

class SNMP:
    SNMPv1 = 0;
    SNMPv2C = 1;
    SNMPv3 = 3;
                
    def __init__(self,community,ip,version=1):
        self.__community = community
        self.__ip = ip
        self.__version = version
        self.__errorIndication = None
        self.__errorStatus = None
        self.__errorIndex = None
        self.__varBinds = None
        #self.__lock = threading.Lock()
        
        self.__snmp_engine = engine.SnmpEngine()
        config.addV1System(self.__snmp_engine, 'test-agent', self.__community)
        config.addTargetParams(self.__snmp_engine, 'myParams', 'test-agent', 'noAuthNoPriv', self.__version)
        config.addTargetAddr(
            self.__snmp_engine, 'myRouter', config.snmpUDPDomain,
            (self.__ip, 161), 'myParams'
            )
        config.addSocketTransport(
            self.__snmp_engine,
            udp.domainName,
            udp.UdpSocketTransport().openClientMode()
            )

    def printOptions(self):
        rtn_str = ""
	try:
        	if self.__version == SNMP.SNMPv1:
            		rtn_str = "-v1"
        	elif self.__version == SNMP.SNMPv2C:
            		rtn_str = "-v2c"
       	 	elif self.__version == SNMP.SNMPv3:
            		rtn_str = "-v3"
        	else:
            		rtn_str = "-v?"
        	rtn_str += " -c "+str(self.__community)+" "+str(self.__ip)+" "
        except Exception,e:
		rtn_str = str(e)
	return rtn_str
    
    def get(self,oid):
        #log.info("snmpget "+self.printOptions()+str(oid.prettyPrint()))
        def cbFun(sendRequestHandle, errorIndication, errorStatus, errorIndex,
                  varBinds, cbCtx):
            cbCtx['errorIndication'] = errorIndication
            cbCtx['errorStatus'] = errorStatus
            cbCtx['errorIndex'] = errorIndex
            cbCtx['varBinds'] = varBinds
        cb = {}
        #self.__lock.acquire()
        cmdgen.GetCommandGenerator().sendReq(self.__snmp_engine, 'myRouter', ((oid, None),), cbFun, cb)
        self.__snmp_engine.transportDispatcher.runDispatcher()
        #self.__lock.release()
        self.__errorIndication = cb['errorIndication']
        self.__errorStatus = cb['errorStatus']
        self.__errorIndex = cb['errorIndex']
        self.__varBinds = cb['varBinds']
        #self.__snmp_engine.transportDispatcher().closeDispatcher()



        if self.getErrorStatus():
            log.critical("Error in snmp get "+str(self.showError()))
        
        return self.__varBinds

    def set(self,oid,value):
        #log.info("snmpset "+self.printOptions()+str(oid.prettyPrint())+" "+self.getSnmpValueType(value))
        def cbFun(sendRequestHandle, errorIndication, errorStatus, errorIndex,
                  varBinds, cbCtx):
            cbCtx['errorIndication'] = errorIndication
            cbCtx['errorStatus'] = errorStatus
            cbCtx['errorIndex'] = errorIndex
            cbCtx['varBinds'] = varBinds
        cb = {}
        #self.__lock.acquire()
        cmdgen.SetCommandGenerator().sendReq(self.__snmp_engine, 'myRouter',
                                            ((oid,value),), cbFun, cb)
        self.__snmp_engine.transportDispatcher.runDispatcher()
        #self.__lock.release()
        self.__errorIndication = cb['errorIndication']
        self.__errorStatus = cb['errorStatus']
        self.__errorIndex = cb['errorIndex']
        self.__varBinds = cb['varBinds']
        
        #self.__snmp_engine.transportDispatcher().closeDispatcher()
        if self.getErrorStatus():
            log.critical("Error in snmp set "+str(self.showError()))
        return self.__varBinds

    def getSnmpValueType(self,value):
        if str(value.__class__) == "pysnmp.proto.rfc1902.Integer32":
            return "i "+str(value)
        elif str(value.__class__) == "pysnmp.proto.rfc1902.OctetString":
            temp_str = (value.prettyPrint())
            if temp_str.find("\\x") != -1:
                return "x "+temp_str.replace("\\x","")
            else:
                return "s "+temp_str
        elif str(value.__class__) == "pysnmp.proto.rfc1902.Unsigned32":
            return "u "+str(value)
        else:
            return str(value.__class__)

    def printSetList(self,value):
        rtn_str = ""
        for i in value:
            rtn_str += " " + i[0].prettyPrint() + " " + self.getSnmpValueType(i[1])
            
            #+ i[1].prettyPrint()
        return rtn_str
    def complex_set(self,value):
        log.info("snmpset "+self.printOptions()+" "+str(self.printSetList(value)))
        def cbFun(sendRequestHandle, errorIndication, errorStatus, errorIndex,
                  varBinds, cbCtx):
            cbCtx['errorIndication'] = errorIndication
            cbCtx['errorStatus'] = errorStatus
            cbCtx['errorIndex'] = errorIndex
            cbCtx['varBinds'] = varBinds
        cb = {}
        #self.__lock.acquire()
        #cmdgen.SetCommandGenerator().sendReq(self.__snmp_engine, 'myRouter', ((value, None),), cbFun, cb)
        try:
            cmdgen.SetCommandGenerator().sendReq(self.__snmp_engine, 'myRouter', value, cbFun, cb)
            self.__snmp_engine.transportDispatcher.runDispatcher()
            #self.__lock.release()
            self.__errorIndication = cb['errorIndication']
            self.__errorStatus = cb['errorStatus']
            self.__errorIndex = cb['errorIndex']
            self.__varBinds = cb['varBinds']
        except Exception, e:
            log.debug(e)
            self.__errorIndication = "crash"
            self.__errorStatus = 1
        
        #self.__snmp_engine.transportDispatcher().closeDispatcher()
        if self.getErrorStatus():
            log.critical("Error in snmp complex set "+str(self.showError()))
        return self.__varBinds

    def walk(self,oid):
        #log.info("snmpwalk "+self.printOptions()+str(oid.prettyPrint()))
        if (self.__version == SNMP.SNMPv1):
            return self.walk_v1(oid)
        else:
            # this is twice as fast the v1 method
            return self.walk_v2(oid)

    def walk_v1(self,oid):
        def cbFun(sendRequestHandle, errorIndication, errorStatus, errorIndex,
                  varBinds, cbCtx):
            cbCtx['errorIndication'] = errorIndication
            cbCtx['errorStatus'] = errorStatus
            cbCtx['errorIndex'] = errorIndex


            for varBindRow in varBinds:

                inTableFlag = 0
                for oi, val in varBindRow:
                    if val is None or not oid.isPrefixOf(oi):
                        continue
                    inTableFlag = 1
                if not inTableFlag:
                    return # stop on end-of-table
                cbCtx['varBinds'].append(varBindRow)
            return 1 # continue walking
                                                                                            
        cb = {}
        cb['varBinds'] = []
        #self.__lock.acquire()
        cmdgen.NextCommandGenerator().sendReq(self.__snmp_engine, 'myRouter', ((oid,None),), cbFun, cb)
        self.__snmp_engine.transportDispatcher.runDispatcher()
        #self.__lock.release()
        self.__errorIndication = cb['errorIndication']
        self.__errorStatus = cb['errorStatus']
        self.__errorIndex = cb['errorIndex']
        self.__varBinds = cb['varBinds']
        if self.getErrorStatus():
            log.critical("Error in snmp walk (v1) "+str(self.showError()))
        return self.__varBinds

    def walk_v2(self,oid):
        def cbFun(sendRequestHandle, errorIndication, errorStatus, errorIndex,
                  varBinds, cbCtx):
            cbCtx['errorIndication'] = errorIndication
            cbCtx['errorStatus'] = errorStatus
            cbCtx['errorIndex'] = errorIndex
            #cbCtx['varBinds'] = varBinds
            for varBindRow in varBinds:

                inTableFlag = 0
                for oi, val in varBindRow:
                    if val is None or not oid.isPrefixOf(oi):
                        continue
                    inTableFlag = 1
                
                if not inTableFlag:
                    return # stop on end-of-table
                cbCtx['varBinds'].append(varBindRow)
            return 1 # continue walking     
        cb = {}
        cb['varBinds'] = []
        #self.__lock.acquire()
        cmdgen.BulkCommandGenerator().sendReq(self.__snmp_engine, 'myRouter', 0,25, ((oid, None),), cbFun, cb)
        self.__snmp_engine.transportDispatcher.runDispatcher()
        #self.__lock.release()
        self.__errorIndication = cb['errorIndication']
        self.__errorStatus = cb['errorStatus']
        self.__errorIndex = cb['errorIndex']
        self.__varBinds = cb['varBinds']
        if self.getErrorStatus():
            log.critical("Error in snmp walk (v2) "+str(self.showError()))
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


