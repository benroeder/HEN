#! /usr/bin/env python
from test import *

class SwitchTestSensors(SwitchTest):
    def __init__(self):
        SwitchTest()
        self.numTests = 1

    def test0(self):
        results = self.target.getSensorReadings()
        if not results:
            print "Couldnt get results"
        else:
            for sensorType in results.keys():
                for sensorName in results[sensorType].keys():
                    print sensorType + ":" + str(sensorName)+":" + \
                            str((results[sensorType])[sensorName])
        
s = SwitchTestSensors()
s.run(sys.argv)
