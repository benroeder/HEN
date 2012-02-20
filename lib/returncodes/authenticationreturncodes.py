from returncodes import ReturnCodes

class AuthenticationReturnCodes(ReturnCodes):

    def __init__(self):
        ReturnCodes.__init__(self)
        self.__returnCodes[421] = "invalid username or password"
