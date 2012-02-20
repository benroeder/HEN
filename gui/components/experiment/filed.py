#!/usr/bin/env python
##################################################################################################################
# filed.py: carries out file node operations from cgi clients
#
##################################################################################################################
import sys
sys.path.append("/usr/local/hen/lib")
import SimpleXMLRPCServer
from henmanager import HenManager

class FileNodeManager:

    def __init__(self):
        self.__manager = HenManager()

    def fileNodeCreate(self, fileNodeType, owner, path, architecture, osType, version, mustClone, description, attributes, username, password):

        return self.__manager.fileNodeCreate(fileNodeType, owner, path, architecture, osType, version, mustClone, description, attributes, username, password)
    
    def elementEdit(self, elementID, parameters, attributes):
        return self.__manager. elementEdit(elementID, parameters, attributes)

    def elementDelete(self, elementID):
        # Send a non-manager delete command
        return self.__manager.elementDelete(elementID, False)
                            
class FileNodeServerProxy(SimpleXMLRPCServer.SimpleXMLRPCServer):
    allow_reuse_address = True

def main():
    try:
        server = FileNodeServerProxy(("127.0.0.1", 50004), logRequests = False)
        server.register_instance(FileNodeManager())
        server.register_introspection_functions()

        try:
            server.serve_forever()  
        finally:
            server.server_close() 
    except Exception, e:
        print "Exception: ", e

if __name__ == "__main__":
    main()
