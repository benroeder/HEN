#########################################################################################
#
# Recursively counts the number of lines in .py and .js files starint from the current directory
#
#########################################################################################
import os

def wc(filename):
    try:
        theFile = open(filename, "r")
    except IOError:
        print "cannot open " + str(filename) + " for reading"
        return -1

    counter = 0
    for line in theFile:
        counter += 1
        
    return counter


count = 0
for (dirPath, dirNames, filenames) in os.walk("."):
    string = str(dirPath) + "\n"
    string += "---------------------\n"    

    hasValidFiles = False
    directoryCount = 0
    for filename in filenames:
        fileExtension = filename[len(filename) - 2:]
        if ((fileExtension == "py" or fileExtension == "js") and (filename.find("#") == -1)):
            hasValidFiles = True
            filenameCount = wc(dirPath + "/" + filename)
            if (filenameCount != -1):
                count += filenameCount
                directoryCount += filenameCount
            string += filename + ": " + str(filenameCount) + "\n"


    if (hasValidFiles):
        print string,
        print "---------------------"
        print "TOTAL: " + str(directoryCount) + "\n"

print "****************************"
print "* "
print "* TOTAL COUNT: " + str(count)
print "* "
print "****************************"

