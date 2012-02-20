class ReturnCodes:
    def __init__(self):
        # Note: 400-420 and 500-520 are reserved for this superclass
        self.__returnCodes = {}
        self.__returnCodes[200] = "success"
        self.__returnCodes[400] = "not logged in or session expired"
        self.__returnCodes[401] = "operation not permitted for user"
        
    def getDescription(self, code):
        return self.__returnCodes[code]
