#!/usr/bin/env python
# $Id: PyTail.py 195 2006-08-11 13:41:19Z munlee $

import os
import sys
import time
import re
import threading
import xmlrpclib
import SimpleXMLRPCServer
import string

PHYSICALFILES = "/usr/local/hen/etc/physical/*.xml"
ORPHANFILE = "orphans.txt"
NEWFILE = "newfile.txt"
theLock = threading.Lock()
# global mac address entries
MacAddrEntries = []

class PyTail:
    stopevent = threading.Event()

    def __init__(self):
        pass

    def _usage(self):
        """Prints the usage message."""
        print "Usage:  %s /var/log/dhcpd" % os.path.basename(sys.argv[0])

    def _xmlMarshal(self, line):
        """@fn _xmlMarshal(line)
           @brief marshalls data into xml structure
           @param line a list structure of lines in the file"""
        p = re.compile("no free leases")
        aList = []      # empty list

        # store matching strings into a list
        for l in line:
            m = p.search(l)
            if m:                   # string matches
                aList.append(l)     # append matched string

        print aList
        # deal with list contents
        aList2 = []
        mac = ""
        interface = ""
        ip = ""
        for li in aList:
            aList2 = re.split('\s', li)
            for i in range(len(aList2)):
                if aList2[i] == "from":
                    mac = aList2[i + 1]         # mac address
                    continue
                if aList2[i] == "via":
                    interface = aList2[i + 1]   # interface name
                    interface = interface[:-1]  # slice off last char
                    continue
                if aList2[i] == "network":
                    ip = aList2[i + 1]          # ip address
                    ip = ip[:-1]                # slice off last char
                    continue


        # make sure these are not empty strings
        if mac != "" or interface != "" or ip != "":
            # if entry already exists do nothing and return
            for entry in MacAddrEntries:
                if mac == entry:
                    return

            # add entry to global list of existing entries
            MacAddrEntries.append(mac)

            print aList2


            nodeString = "<node if=\"" + interface + "\" ip=\"" + ip + "\" mac=\"" + mac + "\"/>\n" 

            theLock.acquire()
            print "Lock acquired in _xmlMarshal()"
            orphansFile = open(ORPHANFILE, "a")
            orphansFile.write(nodeString)
            orphansFile.close()
            print "Lock released in _xmlMarshal()"
            theLock.release()


    def getMarshalledXml(self):
        """@fn getMarshalledXml()
           @brief returns a list of nodes"""
        try:
            theLock.acquire()
            print "getMarshalledXml Lock acquired"
            orphansFile = open(ORPHANFILE, 'r')
            tmp = orphansFile.read()
            orphansFile.close()
            print tmp
            print "getMarshalledXml Lock released"
            theLock.release()
            return tmp
        except Exception, e:
            print "Exception getMarshalledXml(): ", e

#    def removeXmlEntry(self, macaddress):
#        p = re.compile(macaddress)
#        theLock.acquire()
#        print "removeXmlEntry Lock acquired"
#
#        # open file read/write (r+ not rw)
#        orphansFile = open(ORPHANFILE, "r+")
#        beforeLines = open(NEWFILE, "a")
#
#        lines = orphansFile.readlines()
#        currentLine = 0
#        for line in lines:
#            m = p.search(line)
#            if m:                   # string matches
#                try:
#                    beforeLines.write("".join(lines[currentLine + 1:]))
#                    break
#                except Exception, e:
#                    print "Exception removeXmlEntry(): ", e
#            beforeLines.write(line)
#            currentLine += 1
#
#        orphansFile.close()
#        beforeLines.close()
#        os.system("mv -f " + NEWFILE + " " + ORPHANFILE)
#        print "removeXmlEntry Lock released"
#        theLock.release()

class ServerProxy(SimpleXMLRPCServer.SimpleXMLRPCServer):
    """The SimpleXMLRPCServer class has a class variable named
    allow_reuse_address which when True tells the instance to set
    the configuration option called SO_REUSEADDR which tells the
    operating system to allow code to connect to a socket even if
    it's waiting for other potential packets."""
    allow_reuse_address = True


class xmlRpcServerThread(threading.Thread):
    """This class represents the xmlrpc server thread."""
    def __init__(self, name = 'xmlRpcServerThread'):
        threading.Thread.__init__(self, name = name)
        self.setDaemon(1)

    def run(self):
        print self.getName(), " started...\n"
        try:
            """logRequests = False disables the log messages on stdout."""
            server = ServerProxy(("localhost", 50003), logRequests = False)
            server.register_instance(PyTail())
            server.register_introspection_functions()

            try:
                server.serve_forever()  # go into the main listener loop
            finally:
                server.server_close()   # close the connection
        except Exception, e:
            print "Exception xmlRpcServerThread: ", e


class tailDaemon(threading.Thread):
    """This is the daemon thread that does something similar
    to a Unix 'tail -f' on a file. It constantly compares and
    updates the file size in bytes."""
    def __init__(self,  pytail, filename, name = 'tailDaemon'):
        self.pytail = pytail
        self.filename = filename

        threading.Thread.__init__(self, name = name)
        self.setDaemon(1)

    def run(self):
        """wait() timeouts after 1 sec, but in that period listens
        for the event flag to be set from the main() thread. At set
        event flag will signal an exit from this thread."""
        print self.getName(), " started...\n"
        offset = 0              # seek byte offset
        while 1:
            if PyTail.stopevent.isSet():
                return

            try:
                size = os.path.getsize(self.filename)
                if size > offset:
                    f = open(self.filename, 'r')
                    f.seek(offset)
                    manylines = f.readlines()
                    #print manylines
                    self.pytail._xmlMarshal(manylines)
                    f.close()
                    offset = size
            except Exception, e:
                print "tailDaemon run() exception: ", e

            PyTail.stopevent.wait(1.0)  # wait until flagged

class EntryCleanUpDaemon(threading.Thread):
    """This daemon periodically compares the mac address entries in orphans.txt
    with the XML files in /usr/local/hen/etc/physical/. If a match is found,
    the entry in orphans.txt is removed."""
    def __init__(self, name = 'EntryCleanUpDaemon'):
        threading.Thread.__init__(self, name = name)
        self.setDaemon(1)

    def _getMACAddressValue(self, line):
        splitted = string.split(line, " ")
        value = splitted[len(splitted)-1][5:-3]
        return value

    def _isMACAddressExist(self, pattern):
        xmlFiles = PHYSICALFILES
        fileList = os.popen("ls " + xmlFiles)

        for entry in fileList:
            entry = entry[:-1]  # remove the newline character
            f = open(entry, "r")
            lines = f.readlines()
            for line in lines:
                m = pattern.search(line)
                if m:
                    return True
            f.close()
        return False


    def run(self):
        while 1:
            if PyTail.stopevent.isSet():
                return

            theLock.acquire()
            print "removeXmlEntry Lock acquired"

            # open file read/write (r+ not rw)
            orphansFile = open(ORPHANFILE, "r+")
            beforeLines = open(NEWFILE, "a")

            lines = orphansFile.readlines()
            currentLine = 0
            for line in lines:
                macaddr = self._getMACAddressValue(line)
                p = re.compile(macaddr)
                if self._isMACAddressExist(p):
                    try:
                        beforeLines.write("".join(lines[currentLine + 1:]))
                        break
                    except Exception, e:
                        print "Exception removeXmlEntry(): ", e
                beforeLines.write(line)
                currentLine += 1

            orphansFile.close()
            beforeLines.close()
            os.system("mv -f " + NEWFILE + " " + ORPHANFILE)
            print "removeXmlEntry Lock released"
            theLock.release()

            PyTail.stopevent.wait(1.0)  # wait until flagged

def main():
    """This main() thread allows an external event to interrupt
    the tailDaemon by setting the internal event flag to true.
    In response to a check on this flag, the running thread
    should be able to exit gracefully."""

    pytail = PyTail()

    args = sys.argv[1:]
    if len(args) == 1:
        if "-h" in args or "--help" in args:
            pytail._usage()
            sys.exit(2)

    if len(args) == 0:
        pytail._usage()
        sys.exit(2)

    filename = sys.argv[1]

    # need to delete existing data file
    os.system("rm -f " + ORPHANFILE)
    print "Deleted " + ORPHANFILE + "\n"

    # start xmlrpc server thread
    xmlrpcThread = xmlRpcServerThread()
    xmlrpcThread.start()
    time.sleep(0.5)     # allow time for thread to start

    # start the tail daemon thread
    tailThread = tailDaemon(pytail, filename)
    tailThread.start()
    time.sleep(0.5)     # allow time for thread to start

    # start the orphan files cleanup daemon
    entryCleanUpDaemon = EntryCleanUpDaemon()
    entryCleanUpDaemon.start()
    time.sleep(0.5)     # allow time for thread to start

    try:
        while 1:
            time.sleep(1.0)
    except KeyboardInterrupt:
        PyTail.stopevent.set()  # sets the internal event flag true

    # main blocks until threads terminate
    tailThread.join()
    entryCleanUpDaemon.join()

if __name__ == "__main__":
    main()
