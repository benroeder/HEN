import time
import threading

class Timer(threading.Thread):
    __runTime  = 0
    __callback = None
    __stop = False
    
    def __init__(self, seconds, callback, startImmediate=False):
        threading.Thread.__init__(self)
        self.__runTime = seconds
        self.__callback = callback
        self.__start_immediately = startImmediate

    def run(self):
        if not self.__start_immediately:
            time.sleep(self.__runTime)
        while not self.__stop:
            if self.__callback:
                self.__callback()
            time.sleep(self.__runTime)            

    def stop(self):
        self.__callback = None
        self.__stop = True
        
class GracefulTimer(threading.Thread):
    __runTime  = 0
    __callback = None
    __stop = None
    
    def __init__(self, seconds, callback, startImmediate=False):
        threading.Thread.__init__(self)
        self.__runTime = seconds
        self.__callback = callback
        self.__stop = threading.Event()
        self.__start_immediately = startImmediate

    def run(self):
        if not self.__start_immediately:
            self.__stop.wait(self.__runTime)
        while not self.__stop.isSet():
            if self.__callback:
                self.__callback()
            self.__stop.wait(self.__runTime)

    def stop(self):
        self.__callback = None
        self.__stop.set()
