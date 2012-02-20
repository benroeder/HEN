from returncodes import ReturnCodes

class ComputerReturnCodes(ReturnCodes):

    def __init__(self):
        ReturnCodes.__init__(self)
        self.__returnCodes[422] = "error executing command"
