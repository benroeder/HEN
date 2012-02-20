class TaskID:
    checkSensorTask = 0
    hostStatusTask = 1
    switchReadFdbTask = 2
    linkStatusTask = 3
    networkMapGenerationTask = 4
    
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

    def __str__(self):
        s = "WorkerTask "
        if self.taskid == TaskID.checkSensorTask:
            s += "checkSensorTask "
        elif self.taskid == TaskID.hostStatusTask:
            s += "hostStatusTask "
        elif self.taskid == TaskID.switchReadFdbTask:
            s += "switchReadFdbTask "
        elif self.taskid == TaskID.linkStatusTask:
            s += "linkStatusTask "
        elif self.taskid == TaskID.networkMapGenerationTask:
            s += "networkMapGenerationTask "
        try:
            s += str(self.node.getNodeID())
        except:
            s += str(self.node)
        return s
