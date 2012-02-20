import threading, logging, time, commands
from henmanager import HenManager

# length of time a worker thread will sleep before checking for work
CHECK_SENSOR_SLEEP_TIME = 2
# TODO: TEMP WORKAROUND FOR PYSNMP LEAK
SNMP_SENSOR_COMMAND = '/usr/local/hen/bin/get_switch_sensor_readings.py '

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

class CheckSensorTask(threading.Thread):
    __nodeInstance = None
    __sensorReadings = None
    __sensorDescriptions = None
    __stop = None

    def __init__(self, nodeInstance, doneEvent):
        threading.Thread.__init__(self)
        self.__nodeInstance = nodeInstance
        self.__workdone = doneEvent
        self.__stop = threading.Event()

    def __del__(self):
        del self.__nodeInstance
        if self.__sensorReadings:
            del self.__sensorReadings
        if self.__sensorDescriptions:
            del self.__sensorDescriptions

    def run(self):
        try:
            self.__sensorDescriptions = \
                                self.__nodeInstance.getSensorDescriptions()
            self.__sensorReadings = self.__nodeInstance.getSensorReadings()
        except Exception, e:
            log.debug(str(e))
        self.__workdone.set()
        while not self.__stop.isSet():
            self.__stop.wait(CHECK_SENSOR_SLEEP_TIME)

    def getSensorReadings(self):
        self.__stop.set()
        return (self.__sensorDescriptions, self.__sensorReadings)
