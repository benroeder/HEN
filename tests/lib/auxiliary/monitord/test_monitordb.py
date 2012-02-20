from auxiliary.monitord.monitordb import *
import unittest, commands, sys, time

TEST_DIR = '/tmp/monitord_test'
MK_DBDIR_CMD = 'mkdir ' + TEST_DIR
RM_DBDIR_CMD = 'rm -rf ' + TEST_DIR

"""
TODO:
    - Write tests for log rotation (and retreival of information from the files)
    - Write tests for sensor reading analysis (critical value warnings)
"""

class MonitorDBTest(unittest.TestCase):
    
    __nodeid = None
    __sensorid = None
    __sensorid2 = None
    __sensortype = None
    __time = None
    __time2 = None
    __value = None
    __value2 = None
    __critical_value = None
    __sensor_check_interval = None
    __monitordb = None
    
    def setUp(self):
        self.__nodeid = "computer5"
        self.__sensorid = "cpu1.temp"
        self.__sensorid2 = "cpu2.temp"
        self.__sensortype = "temperature"
        self.__time = int(time.time())
        self.__time2 = self.__time + 180
        self.__value = 35.2
        self.__value2 = 35.3
        self.__critical_value = 36.0
        self.__sensor_check_interval = 180 # 3 minutes
        self.__monitordb = MonitorDB()
        # make test directory
        (status, output) = commands.getstatusoutput(MK_DBDIR_CMD)
        if (status != 0):
            print "FAILURE: Couldn't create /tmp/monitord_test directory!"
            sys.exit(-1)
        self.__monitordb.setSensorCheckInterval(self.__sensor_check_interval)    
        self.__monitordb.setDBDirectory(TEST_DIR)      
            		
    def tearDown(self):
        self.__monitordb = None
        # remove test directory
        (status, output) = commands.getstatusoutput(RM_DBDIR_CMD)
        if (status != 0):
            print "FAILURE: Couldn't create /tmp/monitord_test directory!"
            sys.exit(-1)

    def testGetStorageStats(self):
        """ GetStorageStats Test """
        self.assertStatsEqual((0, 0, 0, 0, 0, 0, 0, 0))

    def testGetAndSetHostStatus(self):
        """ Get/Set HostStatus Test """
        self.assertEqual(-1, self.__monitordb.getHostStatus("computer5"))
        self.__monitordb.setHostStatus("computer5", 1)
        self.assertStatsEqual((0, 0, 0, 0, 1, 0, 0, 0))
        self.assertEqual(1, self.__monitordb.getHostStatus("computer5"))
        self.__monitordb.setHostStatus("computer5", 2)
        self.assertEqual(2, self.__monitordb.getHostStatus("computer5"))
        self.__monitordb.setHostStatus("computer5", 0)
        self.assertEqual(0, self.__monitordb.getHostStatus("computer5"))
        self.assertStatsEqual((0, 0, 0, 0, 1, 0, 0, 0))
        
    def testWriteMonitorValue(self):
        """ WriteMonitorValue Test """
        self.assertStatsEqual((0, 0, 0, 0, 0, 0, 0, 0))
        self.__monitordb.writeMonitorValue(self.__nodeid, self.__sensorid, \
                                           self.__sensortype, self.__time, \
                                           self.__value, self.__critical_value)
        self.assertStatsEqual((1, 1, 1, 1, 0, 1, 1, 1))
        
    def testGetAllCurrentSensorReadings(self):
        """ GetAllCurrentSensorReadings Test """
        self.__monitordb.writeMonitorValue(self.__nodeid, self.__sensorid, \
                                           self.__sensortype, self.__time, \
                                           self.__value, self.__critical_value)
        results = self.__monitordb.getAllCurrentSensorReadings()
        self.assertEqual(1, len(results.keys()))
        self.assertEqual(1, len(results.values()))
        sensor_readings = results[self.__nodeid]
        self.assertEqual(1, len(sensor_readings.keys()))
        self.assertEqual(1, len(sensor_readings.values()))
        self.assertStatsEqual((1, 1, 1, 1, 0, 1, 1, 1))
        
        self.__monitordb.writeMonitorValue(self.__nodeid, self.__sensorid2, \
                                           self.__sensortype, self.__time2, \
                                           self.__value2, self.__critical_value)
        results = self.__monitordb.getAllCurrentSensorReadings()
        self.assertEqual(1, len(results.keys()))
        self.assertEqual(1, len(results.values()))
        sensor_readings = results[self.__nodeid]
        self.assertEqual(2, len(sensor_readings.keys()))
        self.assertEqual(2, len(sensor_readings.values()))
        self.assertStatsEqual((1, 2, 1, 1, 0, 1, 1, 2)) 

    def testCheckTrendFanWarning1(self):
        """ CheckTrend Test: Fan Warning Status Test #1
                
               Decrease fan speed at a slow rate (1000rpm/minute). This
               should not trigger a warning until:
                   1000 * sensor_check_interval (in minutes)
               i.e. if sensors are checked every 3 minutes, a warning should
               trigger at 3000rpm, as by the time the next reading is taken,
               it could have reached critical.
        """
        critval = 500
        value = 10000
        time = self.__time
        self.__monitordb.setSensorCheckInterval(180)
        while value > 0:
            self.__monitordb.writeMonitorValue("fakecomputer1", "fakefan1", \
                                               "fanspeed", time, \
                                               value, critval)
            status = self.getSensorStatus("fakecomputer1", "fakefan1")
            if status in [-1, 1, 2]:
                break
            value -= 1000
            time += 60
        self.assertEqual(status, 1)
        self.assertEqual(value, 3000)

    def testCheckTrendFanWarning2(self):
        """ CheckTrend Test: Fan Warning Status Test #2
        
               Increase fan speed at a steady rate (1000rpm/minute). This
               should not trigger an alarm.
        """
        critval = 500
        value = 1000
        time = self.__time
        self.__monitordb.setSensorCheckInterval(180)
        while value < 10000:
            self.__monitordb.writeMonitorValue("fakecomputer1", "fakefan1", \
                                               "fanspeed", time, \
                                               value, critval)
            status = self.getSensorStatus("fakecomputer1", "fakefan1")
            if status in [-1, 1, 2]:
                break
            value += 1000
            time += 60
        self.assertEqual(status, 0)
        self.assertEqual(value, 10000)

    def testCheckTrendTempWarning1(self):
        """ CheckTrend Test: Temperature Warning Status Test #1

            Increase temperature at a rate of 5 degc/minute.  This should
            trigger a warning at approach to critical.
        """
        critval = 45
        value = 5
        time = self.__time
        self.__monitordb.setSensorCheckInterval(180)
        while value < 45:
            self.__monitordb.writeMonitorValue("fakecomputer1", "faketemp1", \
                                               "temperature", time, \
                                               value, critval)
            status = self.getSensorStatus("fakecomputer1", "faketemp1")
            if status in [-1, 1, 2]:
                break
            value += 5
            time += 60
        self.assertEqual(status, 1)
        self.assertEqual(value, 30)

    def testCheckTrendTempWarning2(self):
        """ CheckTrend Test: Temperature Warning Status Test #2

            Increase temperature at a rate of 0.5 degc/minute.  This should
            trigger a warning at approach to critical.
        """
        critval = 45
        value = 40.0
        time = self.__time
        self.__monitordb.setSensorCheckInterval(180)
        while value < 45:
            self.__monitordb.writeMonitorValue("fakecomputer1", "faketemp1", \
                                               "temperature", time, \
                                               value, critval)
            status = self.getSensorStatus("fakecomputer1", "faketemp1")
            if status in [-1, 1, 2]:
                break
            value += 0.5
            time += 60
        self.assertEqual(status, 1)
        self.assertEqual(value, 43.5)

    def testCheckTrendTempWarning1(self):
        """ CheckTrend Test: Current Warning Status Test #1

            Increase current at a rate of 0.2 Amps/minute.  This should
            trigger a warning at approach to critical.
        """
        critval = 3.6
        value = 2.6
        time = self.__time
        self.__monitordb.setSensorCheckInterval(180)
        while value < 3.6:
            self.__monitordb.writeMonitorValue("fakecomputer1", "fakecur1", \
                                               "current", time, \
                                               value, critval)
            status = self.getSensorStatus("fakecomputer1", "fakecur1")
            if status in [-1, 1, 2]:
                break
            value += 0.2
            time += 60
        self.assertEqual(status, 1)
        self.assertEqual(int(value), 3)

    def testCheckTrendTempWarning2(self):
        """ CheckTrend Test: Current Warning Status Test #2

            Fluctuate current at a rate of 0.1 Amps/minute.  This should not
            trigger a warning.
        """
        critval = 3.6
        value = 2.9
        time = self.__time
        self.__monitordb.setSensorCheckInterval(180)
        iterations = 0
        alternator = 1
        while value < 3.6:
            self.__monitordb.writeMonitorValue("fakecomputer1", "fakecur1", \
                                               "current", time, \
                                               value, critval)
            status = self.getSensorStatus("fakecomputer1", "fakecur1")
            if status in [-1, 1, 2]:
                break
            value += alternator * 0.1
            alternator = -1 * alternator
            time += 60
            iterations += 1
            if iterations > 10:
                break
        self.assertEqual(status, 0)

    def getSensorStatus(self, nodeid, sensorid):
        """\return status --    0 = STATUS OK
                                1 = WARNING (APPROACHING CRITICAL VALUE)
                                2 = CRITICAL VALUE REACHED
                               -1 = NOT FOUND
        """
        results = self.__monitordb.getAllCurrentSensorReadings()
        if not results.has_key(nodeid):
            return -1
        readings = results[nodeid]
        if not readings.has_key(sensorid):
            return -1
        (type,time,val,maxval,status) = readings[sensorid]
        return status

    def assertStatsEqual(self, (a1, a2, a3, a4, a5, a6, a7, a8)):
        stats = self.__monitordb.getStorageStats()
        self.assertEqual(a1, stats["__sensor_history length"])
        self.assertEqual(a2, stats["Total history entries"])
        self.assertEqual(a3, stats["__sensor_max length"])
        self.assertEqual(a4, stats["__write_buf length"])
        self.assertEqual(a5, stats["__host_status length"])
        self.assertEqual(a6, stats["__node_locks length"])
        self.assertEqual(a7, stats["__node_fds length"])
        self.assertEqual(a8, stats["__writes_since_flush"])
        
if __name__ == '__main__':
    unittest.main()
