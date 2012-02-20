#!/usr/local/bin/python
# $Id: loadexperimentxml.py 189 2006-08-11 10:01:17Z munlee $

import os
import cgi
import sys

import cgitb; cgitb.enable()

path = "/usr/local/hen/etc/experiment/"

print "Content-Type: text/xml\n"

form = cgi.FieldStorage()
if form.has_key("filename"):
    pass
else:
    print "exiting early"
    sys.exit()

filename = form["filename"].value

def main():
    # open file as readonly
    f = open(path + filename, "r")
    print f.read()

    f.close()

if __name__ == "__main__":
    main()
