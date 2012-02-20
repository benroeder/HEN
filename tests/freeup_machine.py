import sys, os, commands

class SymlinkRemover:
    def __init__(self, targets):
        self.__idKeyword = "computer"
        self.__idDelimiters = ["-", ","]
        self.__targets = self.__expandIDs(targets)

    def removeLinks(self):
        for target in self.__targets:
            self.__removeLinks(target)
            print "freed up", target

    def __removeLinks(self, target):
        cmd = "rm /export/machines/" + target + "/kernel"
        commands.getstatusoutput(cmd)
        cmd = "rm /export/machines/" + target + "/filesystem"
        commands.getstatusoutput(cmd)
        cmd = "rm /export/machines/" + target + "/loader"
        commands.getstatusoutput(cmd)
        cmd = "rm /export/machines/" + target + "/IN_USE_BY*"
        commands.getstatusoutput(cmd)
    
    def __findDelimiterIndex(self, string, begin=0):
        for x in range(begin, len(string)):
            if (string[x] in self.__idDelimiters):
                return x

        return len(string)
                                
    def __expandIDs(self, string):
        items = []
        keywordLen = len(self.__idKeyword)

        # First expand any dashes ("-")                                                                                                                                                              
        dashIndex = string.find("-")
        while (dashIndex != -1):
            beginID = int(string[string[:dashIndex].rfind(self.__idKeyword) + keywordLen:dashIndex])
            endID = int(string[dashIndex + keywordLen + 1:self.__findDelimiterIndex(string, dashIndex + 1)])

            string = string[:string[:dashIndex].rfind(self.__idKeyword)] + string[self.__findDelimiterIndex(string, dashIndex + 1):]
            dashIndex = string.find("-")

            for x in range(beginID, endID + 1):
                itemID = self.__idKeyword + str(x)
                if (itemID not in items):
                    items.append(self.__idKeyword + str(x))

        # Remove any leading/trailing commas and any repeated commas                                                                                                                                 
        string = string.strip(",")
        while (string.find(",,") != -1):
            string = string.replace(",,", ",")

        # Expand any commas (",")                                                                                                                                                                    
        commaIndex = string.find(",")
        while (commaIndex != -1):
            itemID = self.__idKeyword + string[string[:commaIndex].rfind(self.__idKeyword) + keywordLen:commaIndex]
            if (itemID not in items):
                items.append(itemID)
            string = string[commaIndex + 1:]
            commaIndex = string.find(",")



        # Add single item                                                                                                                                                                            
        if (string not in items and string != ""):
            items.append(string)

        return items

if (len(sys.argv) < 2):
    print "usage: python freeup_machine.py [list of computers, use dashes for ranges or commas]"
    os._exit(1)

remover = SymlinkRemover(sys.argv[1])
remover.removeLinks()
