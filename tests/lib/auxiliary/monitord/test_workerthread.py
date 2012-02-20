from auxiliary.monitord.workerthread import *
from auxiliary.monitord.workertask import *
from auxiliary.monitord.monitordb import *
import unittest, threading, time

""" Taken from workerthread.py """
TASK_DECAY_TIME = 300
MAX_WORKER_TASKS = 50

class WorkerThreadTest(unittest.TestCase):
    
    __workernumber = None
    __monitordb = None
    __workerthread = None
    
    def setUp(self):
        self.__monitordb = MonitorDB()
        self.__workernumber = 1
        self.__workerthread = WorkerThread(self.__workernumber, \
                                           self.__monitordb)
		
    def tearDown(self):
        self.__workerthread.stop()
        self.__workerthread = None
        self.__workernumber = None
        self.__monitordb = None

    def testStartAndStop(self):
        self.__workerthread.start()
        self.assertEqual(2, threading.activeCount())
        self.__workerthread.stop()
        time.sleep(2)
        self.assertEqual(1, threading.activeCount())
        
    def testRunTaskQueueMaintenance(self):       
        """ 
        Schedule a task for 596 seconds ago. It should not be cleared.
        Wait 6 seconds, run maintenance, and it should clear.
        """
        timenow = int(time.time())
        self.__workerthread.addTask(WorkerTask("", 0, \
                               timenow - (TASK_DECAY_TIME - 4)))
        self.assertEqual(1, self.__workerthread.getTaskQueueSize())
        self.__workerthread.runTaskQueueMaintenance()
        self.assertEqual(1, self.__workerthread.getTaskQueueSize())
        time.sleep(6)
        self.__workerthread.runTaskQueueMaintenance()
        self.assertEqual(0, self.__workerthread.getTaskQueueSize())
        
        timenow = int(time.time())
        for i in range(0, 50):
            self.__workerthread.addTask(WorkerTask("", 0, \
                               timenow - (TASK_DECAY_TIME + 1)))
        self.assertEqual(50, self.__workerthread.getTaskQueueSize())
        self.__workerthread.runTaskQueueMaintenance()
        self.assertEqual(0, self.__workerthread.getTaskQueueSize())
    
    def testAddTask(self):
        self.assertEqual(0, self.__workerthread.getTaskQueueSize())
        self.__workerthread.addTask(WorkerTask("", 0, 0))
        self.assertEqual(1, self.__workerthread.getTaskQueueSize())
        for i in range(0, MAX_WORKER_TASKS + 20):
            self.__workerthread.addTask(WorkerTask("", 0, 0))
        self.assertEqual(MAX_WORKER_TASKS, \
                         self.__workerthread.getTaskQueueSize())
        
    def testHasWork(self):
        self.assertEqual(False, self.__workerthread.hasWork())
        self.__workerthread.addTask(WorkerTask("", 0, 0))
        self.assertEqual(True, self.__workerthread.hasWork())
        
    def testCheckHostStatus(self):
        class TempTestNode:
            __nodeid = None
            def __init__(self, nodeid):
                self.__nodeid = nodeid
            def getNodeID(self):
                return self.__nodeid
        
        self.__workerthread.checkHostStatus(TempTestNode("localhost"))
        result = self.__monitordb.getHostStatus("localhost")
        self.assertEqual(0, result)
        self.__workerthread.checkHostStatus(TempTestNode("nonexistanthost"))
        result = self.__monitordb.getHostStatus("nonexistanthost")
        self.assertEqual(1, result)
        
if __name__ == '__main__':
    unittest.main()
