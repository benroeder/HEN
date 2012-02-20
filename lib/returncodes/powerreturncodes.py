from returncodes import ReturnCodes

class PowerReturnCodes(ReturnCodes):

    def __init__(self):
        ReturnCodes.__init__(self)
        self.__returnCodes[421] = "node does not exist in testbed"
        self.__returnCodes[521] = "node has no powerswitch"
        self.__returnCodes[522] = "sp returned error"

