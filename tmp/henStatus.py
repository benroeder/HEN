#! /usr/bin/env python

import fileinput
from xml.dom import minidom

class HenStatus:
    "Class to manipulate henstatus.xml"

    # Parses the given file using minidom
    def __init__(self, filename):
        self.filename = filename
        self.xmlDoc = minidom.parse(filename)

    # Returns an int representing the number of the highest hen node currently in use
    def getCurrentHenNumber(self):
        lastNode = self.xmlDoc.getElementsByTagName("lastNode")
        for d in lastNode:
            return int(d.attributes["value"].value)
        
    # Returns a string representing the name of the highest hen node currently in use
    def getCurrentHenName(self):
        return "hen" + str(self.getCurrentHenNumber())

    # Returns an int representing the number of the next hen node to add
    def getNextHenNumber(self):
        return self.getCurrentHenNumber() + 1

    # Returns a string representing the name of the next hen node to add
    def getNextHenName(self):
        return "hen" + str(self.getNextHenNumber())

    # Modifies the xml file's lastNode tag so that its "value" attribute is incremented
    def incrementHenNumber(self):
        f = fileinput.input(self.filename, inplace = 1)
        for line in f:
            if line.find("lastNode") == -1:
                print line,
            else:
                print '\t<lastNode value="' + str(self.getNextHenNumber())  + '"/>'
        self.xmlDoc = minidom.parse(self.filename)
        
