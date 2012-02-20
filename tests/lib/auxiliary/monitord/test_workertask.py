import unittest, time
from auxiliary.monitord.workertask import WorkerTask

class WorkerTaskTest(unittest.TestCase):
    
    __nodeid = None
    __taskid = None
    __time_scheduled = None
    __worker_task = None
    
    def setUp(self):
        self.__nodeid = "computer5"
        self.__taskid = 54
        self.__time_scheduled = int(time.time())
        self.__worker_task = WorkerTask(self.__nodeid, self.__taskid, \
                                        self.__time_scheduled)

    def tearDown(self):
        self.__nodeid = None
        self.__taskid = None
        self.__time_scheduled = None
        self.__worker_task = None

    def testNodeID(self):
        self.assertEqual(self.__nodeid, self.__worker_task.nodeid)

    def testTaskID(self):
        self.assertEqual(self.__taskid, self.__worker_task.taskid)

    def testTimeScheduled(self):
        self.assertEqual(self.__time_scheduled, self.__worker_task.timeScheduled)

if __name__ == '__main__':
    unittest.main()
