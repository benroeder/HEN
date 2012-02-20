class TaskID:
    checkSensorTask = 0
    hostStatusTask = 1

class WorkerTask:
    nodeinstance = None
    node = None
    taskid = None
    timeScheduled = None

    def __init__(self, node, nodeinstance, taskid, timeScheduled):
        self.nodeinstance = nodeinstance
        self.node = node
        self.taskid = taskid
        self.timeScheduled = timeScheduled

    def __del__(self):
        del self.nodeinstance
        del self.node
        del self.taskid
        del self.timeScheduled