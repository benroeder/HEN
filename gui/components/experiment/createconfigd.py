#!/usr/local/bin/python

from socket import *
import sys
sys.path.append("/usr/local/hen/lib")
from henmanager import HenManager
import os
import re
import string

def main():
    # due to possible name resolution issues, use '127.0.0.1'
    # instead of localhost
    #myHost = gethostname()
    #myHost = "192.168.0.1"
    myPort = 55000
    myHost = "127.0.0.1"
    #myPort = 4789

    s = socket(AF_INET, SOCK_STREAM)    # create a TCP socket
    s.bind((myHost, myPort))            # bind it to the server port
    s.listen(5)                         # allow 5 simultaneous
                                        # pending connections

    manager = HenManager()
    dir = '/tmp/'
    filename = 'dumpfile'
    filepath = dir + filename

    while 1:
        # wait for next client to connect
        (connection, address) = s.accept() # connection is a new socket
        total_data = []
        while 1:
            data = connection.recv(32768)
            print data
            if not data: break
            total_data.append(data)

        f = open(filepath,'w')
        f.write(''.join(total_data))
        f.close()
        connection.close()              # close socket

        # open file again as readonly
        f = open(filepath, "r")
        lines = f.read()

        # find the experimentid attribute
        fname = re.findall('experimentid=\"[a-zA-Z0-9]+\"', lines)
        fn = fname[0]
        # get start index of attribute value
        start = string.find(fn,"\"")
        fid = fn[start+1:-1]

        # rename file to its id
        newfilepath = dir + fid
        os.rename(filepath, newfilepath)
        f.close()

        #manager.experimentCreate(filepath)
        cmd = "export PYTHONPATH=$HOME/hen_scripts/hen_scripts/trunk/lib"
        os.system(cmd)
        cmd = "cd /tmp; sudo hm experiment create " + fid + " " + fid
        os.system(cmd)

if __name__ == "__main__":
    main()
