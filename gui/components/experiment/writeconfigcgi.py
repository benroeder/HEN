#!/usr/local/bin/python
# $Id$

import cgi
from socket import *

def main():

    form = cgi.FieldStorage(keep_blank_values=1)

    data = ""
    keys = form.keys()
    for key in keys:
        data += key
        data += form[key].value

    # due to possible name resolution issues, use '127.0.0.1'
    # instead of localhost
    #serverHost = 'localhost'
    #serverHost = 'arkell.cs.ucl.ac.uk'
    #serverHost = '192.168.0.1'
    serverPort = 55000
    serverHost = '127.0.0.1'
    #serverPort = 4789

    s = socket(AF_INET, SOCK_STREAM)

    s.connect((serverHost, serverPort)) # connect to server on the port
    #s.send(data)               # send the data
    s.sendall(data)               # send the data

if __name__ == "__main__":
    main()
