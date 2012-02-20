#!/usr/bin/env python
##################################################################################################################
# inventoryd.py: carries out add/edit/delete element operations from cgi clients
#
##################################################################################################################
import sys
sys.path.append("/usr/local/hen/lib")
import SimpleXMLRPCServer
from henmanager import HenManager

class ElementManager:

    def __init__(self):
        self.__manager = HenManager()

    ##########################################################################################        
    # Create functions
    ##########################################################################################
    def computerNodeCreate(self, netbootable, infrastructure, rackName, macAddress, powerID, powerPort, serialID, serialPort, serviceProcessorID, attributes, building, floor, room, rackRow, rackStartUnit, rackEndUnit, rackPosition, status, vendor, model):
        return self.__manager.computerNodeCreate(netbootable, infrastructure, rackName, macAddress, powerID, powerPort, serialID, serialPort, serviceProcessorID, attributes, building, floor, room, rackRow, rackStartUnit, rackEndUnit, rackPosition, status, vendor, model)

    def serverNodeCreate(self, rackName, serialID, serialPort, managementMAC, infrastructureMAC, externalMAC, externalIP, externalSubnet, attributes, building, floor, room, rackRow, rackStartUnit, rackEndUnit, rackPosition, powerID, powerPort, serviceProcessorID, status, vendor, model):
        return self.__manager.serverNodeCreate(rackName, serialID, serialPort, managementMAC, infrastructureMAC, externalMAC, externalIP, externalSubnet, attributes, building, floor, room, rackRow, rackStartUnit, rackEndUnit, rackPosition, powerID, powerPort, serviceProcessorID, status, vendor, model)

    def serialNodeCreate(self, vendor, model, macAddress, powerID, powerPort, username, password, rackName, attributes, building, floor, room, rackRow, rackStartUnit, rackEndUnit, rackPosition, status):
        return self.__manager.serialNodeCreate(vendor, model, macAddress, powerID, powerPort, username, password, rackName, attributes, building, floor, room, rackRow, rackStartUnit, rackEndUnit, rackPosition, status)

    def switchNodeCreate(self, infrastructure, vendor, model, macAddress, powerID, powerPort, serialID, serialPort, rackName, attributes, building, floor, room, rackRow, rackStartUnit, rackEndUnit, rackPosition, status):
        return self.__manager.switchNodeCreate(infrastructure, vendor, model, macAddress, powerID, powerPort, serialID, serialPort, rackName, attributes, building, floor, room, rackRow, rackStartUnit, rackEndUnit, rackPosition, status)
        
    def powerswitchNodeCreate(self, vendor, model, macAddress, serialID, serialPort, rackName, username, password, attributes, building, floor, room, rackRow, rackStartUnit, rackEndUnit, rackPosition, status):
        return self.__manager.powerswitchNodeCreate(vendor, model, macAddress, serialID, serialPort, rackName, username, password, attributes, building, floor, room, rackRow, rackStartUnit, rackEndUnit, rackPosition, status)

    def routerNodeCreate(self, vendor, model, macAddress, powerID, powerPort, serialID, serialPort, rackName, attributes, building, floor, room, rackRow, rackStartUnit, rackEndUnit, rackPosition, status):
        return self.__manager.routerNodeCreate(vendor, model, macAddress, powerID, powerPort, serialID, serialPort, rackName, attributes, building, floor, room, rackRow, rackStartUnit, rackEndUnit, rackPosition, status)
            
    def serviceprocessorNodeCreate(self, macAddress, powerID, powerPort, username, password, attributes, status, vendor, model):
        return self.__manager.serviceprocessorNodeCreate(macAddress, powerID, powerPort, username, password, attributes, status, vendor, model)

    def infrastructureRackCreate(self, vendor, model, description, building, floor, room, rackRow, rowPosition, height, width, depth, rearRightSlots, rearLeftSlots, numberUnits, status, attributes):
        return self.__manager.infrastructureRackCreate(vendor, model, description, building, floor, room, rackRow, rowPosition, height, width, depth, rearRightSlots, rearLeftSlots, numberUnits, status, attributes)

    def fileNodeCreate(self, fileNodeType, owner, path, architecture, osType, version, mustClone, description, attributes, username, password, status):
        return self.__manager.fileNodeCreate(fileNodeType, owner, path, architecture, osType, version, mustClone, description, attributes, username, password, status)

    ##########################################################################################
    # Edit functions
    ##########################################################################################
    def elementEdit(self, elementID, parameters, attributes):
        return self.__manager. elementEdit(elementID, parameters, attributes)

    ##########################################################################################    
    # Delete functions
    ##########################################################################################
    def elementDelete(self, elementID):
        return self.__manager.elementDelete(elementID)

class ElementServerProxy(SimpleXMLRPCServer.SimpleXMLRPCServer):
    allow_reuse_address = True

def main():
    try:
        server = ElementServerProxy(("localhost", 50006), logRequests = False)
        server.register_instance(ElementManager())
        server.register_introspection_functions()

        try:
            server.serve_forever()  
        finally:
            server.server_close() 
    except Exception, e:
        print "Exception: ", e

if __name__ == "__main__":
    main()
