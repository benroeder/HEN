#!/usr/bin/env python
# $Id$

import os
import sys
sys.path.append("/usr/local/hen/lib")
import SimpleXMLRPCServer


class ExperimentManager:
    """User needs to start this daemon with:
    (1) export PYTHONPATH=~/hen_scripts/hen_scripts/trunk/lib/
    (2) sudo ./ExperimentManager.py """

    def __init__(self):
        print "Starting daemon %s..." % os.path.basename(sys.argv[0])
        pass

    def _usage(self):
        """Prints the usage message."""
        print "Usage:  %s" % os.path.basename(sys.argv[0])

    def delete(self, experimentid):
        """Delete experiment."""
        cmd = "sudo hm experiment delete " + experimentid
        os.system(cmd)


class ServerProxy(SimpleXMLRPCServer.SimpleXMLRPCServer):
    """The SimpleXMLRPCServer class has a class variable named
    allow_reuse_address which when True tells the instance to set
    the configuration option called SO_REUSEADDR which tells the
    operating system to allow code to connect to a socket even if
    it's waiting for other potential packets."""
    allow_reuse_address = True


def main():

    try:
        # logRequests = False disables the log messages on stdout.
        server = ServerProxy(("127.0.0.1", 50001), logRequests = False)
        server.register_instance(ExperimentManager())
        server.register_introspection_functions()

        try:
            server.serve_forever()  # go into the main listener loop
        finally:
            server.server_close()   # close the connection
    except Exception, e:
        print "Exception: ", e

if __name__ == "__main__":
    main()
