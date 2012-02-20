import threading, logging, time, commands
from henmanager import HenManager

# length of time a worker thread will sleep before checking for work
CHECK_FDB_SLEEP_TIME = 2

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

class ReadSwitchFdbTask(threading.Thread):
    __nodeInstance = None
    __switchMacTable = None
    __stop = None

    def __init__(self, nodeInstance, doneEvent):
        threading.Thread.__init__(self)
        self.__nodeInstance = nodeInstance
        self.__workdone = doneEvent
        self.__stop = threading.Event()

    def __del__(self):
        del self.__nodeInstance
        if self.__switchMacTable:
            del self.__switchMacTable

    def run(self):
        try:
            self.__switchMacTable = \
                                self.__nodeInstance.getFullMACTable(True)
            #log.debug(str(self.__switchMacTable))
        except Exception, e:
            log.debug(str(e))
        self.__workdone.set()
        while not self.__stop.isSet():
            self.__stop.wait(CHECK_FDB_SLEEP_TIME)

    def getMacTable(self):
        self.__stop.set()
        return self.__switchMacTable
