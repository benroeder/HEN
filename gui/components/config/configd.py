#!/usr/bin/env python
##################################################################################################################
# configd.py: carries out write operations on the testbed's main config file
#
##################################################################################################################
import sys
sys.path.append("/usr/local/hen/lib")
import SimpleXMLRPCServer
from henmanager import HenManager

class ConfigManager:

    def __init__(self):
        self.__manager = HenManager()

    def writeConfigFileLines(self, lines):
        return self.__manager.writeConfigFileLines(lines)

class ConfigServerProxy(SimpleXMLRPCServer.SimpleXMLRPCServer):
    allow_reuse_address = True

def main():
    try:
        server = ConfigServerProxy(("127.0.0.1", 50005), logRequests = False)
        server.register_instance(ConfigManager())
        server.register_introspection_functions()

        try:
            server.serve_forever()  
        finally:
            server.server_close() 
    except Exception, e:
        print "Exception: ", e

if __name__ == "__main__":
    main()
