#! /usr/bin/env python

import sys, string, os

class ConsoleMenu:
    "A simple class that prints a menu to the console consisting of all files in a given directory. It returns the user's selection"
    def __init__(self, directory, menuLabel):
        self.directory = directory
        self.menuLabel = menuLabel

    def setDirectory(self, directory):
        self.directory = directory

    def setMenuLabel(self, menuLabel):
        self.menuLabel = menuLabel
        
    def getDirectory(self):
        return self.directory

    def getMenuLabel(self):
        return self.menuLabel
    
    def getUserInput(self):
        files = os.listdir(self.directory);
        optionNumber = 1
        tmp = self.menuLabel + "s"
        print "\n\n" + string.upper(tmp) + ":\n----------------------------------------------"
        for thefile in files:
            print str(optionNumber) + ") " + thefile
            optionNumber = optionNumber + 1
        print "0) Exit"

        print "\nWhich " + string.lower(self.menuLabel) + " would you like to use? ",
        selection = 0
        while 1:
                selection = sys.stdin.readline()
                selection = selection.rstrip()
                if not selection:
                    print "nothing selected, please try again: "
                elif selection == "0":
                    print "exiting..."
                    return None
                else:
                    try:
                        if string.atoi(selection) < optionNumber:
                            selection = string.atoi(selection)
                            break
                        else:
                            print "please enter a value in the range 0 to " + str(optionNumber - 1)
                            print "Which " + string.lower(self.menuLabel) + " would you like to use? ",
                    except ValueError:
                            print "please enter a value in the range 0 to " + str(optionNumber - 1)

        count = 1
        selectedOption = 0
        for thefile in files:
            if count == selection:
                selectedOption = thefile
                break
            count = count + 1
  

        return selectedOption
                                                                                                                        
