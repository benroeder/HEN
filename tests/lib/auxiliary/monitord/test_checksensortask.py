from auxiliary.monitord.checksensortask import *
from auxiliary.hen import ServiceProcessorNode, UserManagement
from hardware.serviceprocessors.sun import SunX4100ServiceProcessor
import unittest, threading

class CheckSensorTaskTest(unittest.TestCase):
    
    __user = None
    __sp_node = None
    __node_instance = None
    __done_event = None

    __check_sensor_task = None
    
    def setUp(self):
        self.__user = UserManagement("root", "changeme", "", "ipmi")
        self.__sp_node = ServiceProcessorNode("serviceprocessor16", \
            "serviceprocessor", interfaces=None, netBootable=None, \
            infrastructure=None, vendor="sun", model="X4100", \
            attributes = None, physicalLocation=None)
        self.__sp_node.setUsers([self.__user])
        self.__node_instance = SunX4100ServiceProcessor(self.__sp_node)
        self.__done_event = threading.Event()
        
        self.__check_sensor_task = CheckSensorTask(self.__node_instance, \
                                                   self.__done_event)
		
    def tearDown(self):
        self.__check_sensor_task = None
        self.__done_event = None
        self.__node_instance = None

    def testGetSensorReadings(self):
        TIMEOUT = 30
        self.__check_sensor_task.start()
        self.__done_event.wait(TIMEOUT)
        results = self.__check_sensor_task.getSensorReadings()
        self.assertNotEqual(False, results)
        self.assertEqual(5, len(results.keys()))
        self.assertEqual(0, len(results["fanspeed"]))
        self.assertEqual(0, len(results["current"]))
        self.assertEqual(0, len(results["alarm"]))
        self.assertEqual(5, len(results["temperature"]))
        self.assertEqual(2, len(results["voltage"]))

if __name__ == '__main__':
    unittest.main()
