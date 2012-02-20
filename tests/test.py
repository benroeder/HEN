from henmanager import HenManager
from auxiliary.hen import Node, SwitchNode, VLAN, Port
import sys

class TestResult:
    def __init__(self):
        self.result = False

    def getResult():
        return self.result

    def setResult(r):
        self.result = r

class Test:
    def __init__(self):
        self.target_name = ""
        self.target = None
        self.numTest = 0

    def run_tests(self):
        for i in range(0,self.numTests):
            run_test = getattr(self,"test"+str(i))
            result = run_test()

    def run(self):
        print "Please implement in subclass"

class ServiceProcessorTest(Test):

    def run(self,argv):
        if len(argv) != 2:
            print "Usage :"+argv[0]+" <sp name>"
            sys.exit(1)

        self.target_name = argv[1]
        
        manager = HenManager()
        manager.initLogging()
        nodes = manager.getNodes("serviceprocessor","all")

        self.target = None
        for node in nodes.values():
            if (node.getNodeID() == self.target_name):
                self.target = node.getInstance()
                
        if self.target == None:
            print "Unknown serviceprocessor "+argv[1]
            sys.exit(1)

        self.run_tests()
        
class SwitchTest(Test):

    def run(self,argv):
        if len(argv) != 2:
            print "Usage :"+argv[0]+" <switch name>"
            sys.exit(1)

        self.target_name = argv[1]
        
        manager = HenManager()
        manager.initLogging()
        nodes = manager.getNodes("switch","all")

        self.target = None
        for node in nodes.values():
            if (node.getNodeID() == self.target_name):
                self.target = node.getInstance()
                
        if self.target == None:
            print "Unknown switch "+argv[1]
            sys.exit(1)

        self.run_tests()

    def get_full_vlan_info(self,name=None):
        if (name!=None):
            res = self.target.getFullVLANInfo(name)
        else:
            res = self.target.getFullVLANInfo()
        for i in  res:
            print i
                            

class PowerswitchTest(Test):

    def run(self,argv):
        if len(argv) != 2:
            print "Usage :"+argv[0]+" <powerswitch name>"
            sys.exit(1)

        self.target_name = argv[1]
        
        manager = HenManager()
        manager.initLogging()
        nodes = manager.getNodes("powerswitch","all")

        self.target = None
        for node in nodes.values():
            if (node.getNodeID() == self.target_name):
                self.target = node.getInstance()
                
        if self.target == None:
            print "Unknown powerswitch "+argv[1]
            sys.exit(1)

        self.run_tests()

class FileTest(Test):

    def run(self,argv):
        if len(argv) != 1:
            print "Usage :"+argv[0]+""
            sys.exit(1)

        self.run_tests()
