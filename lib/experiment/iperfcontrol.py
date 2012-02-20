#! /usr/bin/python

import commands, os, sys, time, math

class IperfBandwidthResult:
    """\brief A simple class that contains two values: a sender's rate (bandwidth) and a receiver's rate
    """
    def __init__(self, senderRate=None, receiverRate=None):
        self.__senderRate = senderRate
        self.__receiverRate = receiverRate

    def getSenderRate(self):
        return self.__senderRate

    def setSenderRate(self, senderRate):
        self.__senderRate = senderRate
        
    def getReceiverRate(self):
        return self.__receiverRate

    def setReceiverRate(self, receiverRate):
        self.__receiverRate = receiverRate
        
    def __str__(self):
        return str(self.getSenderRate()) + " " + str(self.getReceiverRate())


class IperfControl:
    """\brief Class to control a iperf experiment
    """
    def __init__(self, trafficType=None, experimentID=None, minPacketSize=None, maxPacketSize=None, incrementSize=None, senderAddress=None, receiverAddress=None, testRuntime=None, numberIterations=None, bandwidth=None):
        self.__trafficType = trafficType
        self.__experimentID = experimentID
        self.__minPacketSize = minPacketSize
        self.__maxPacketSize = maxPacketSize
        self.__incrementSize = incrementSize
        self.__senderAddress = senderAddress
        self.__receiverAddress = receiverAddress
        self.__testRuntime = testRuntime
        self.__numberIterations = numberIterations
        self.__outputFile = experimentID + "-iperf.log"
        self.__basePath = None
        self.__logDirectory = None
        self.__bandwidth = None
        if (not bandwidth):
            self.__bandwidth = "1000M"
        else:
            self.__bandwidth = bandwidth

    def getBasePath(self):
        return self.__basePath
    
    def setBasePath(self, basePath):
        self.__basePath = basePath

    def getLogDirectory(self):
        return self.__logDirectory
    
    def setLogDirectory(self, logDirectory):
        self.__logDirectory = logDirectory
        
    def getTrafficType(self):
        return self.__trafficType
    
    def setTrafficType(self, trafficType):
        self.__trafficType = trafficType

    def getExperimentID(self):
        return self.__experimentID

    def setExperimentID(self, experimentID):
        self.__experimentID = experimentID

    def getMinPacketSize(self):
        return self.__minPacketSize

    def setMinPacketSize(self, minPacketSize):
        self.__minPacketSize = minPacketSize
        
    def getMaxPacketSize(self):
        return self.__maxPacketSize    
    
    def setMaxPacketSize(self, maxPacketSize):
        self.__maxPacketSize = maxPacketSize        
        
    def getIncrementSize(self):
        return self.__incrementSize

    def setIncrementSize(self, incrementSize):
        self.__incrementSize = incrementSize
        
    def getSenderAddress(self):
        return self.__senderAddress

    def setSenderAddress(self, senderAddress):
        self.__senderAddress = senderAddress
        
    def getReceiverAddress(self):
        return self.__receiverAddress

    def setReceiverAddress(self, receiverAddress):
        self.__receiverAddress = receiverAddress

    def getRuntime(self):
        return self.__testRuntime

    def setRuntime(self, runtime):
        self.__testRuntime = runtime

    def getNumberIterations(self):
        return self.__numberIterations

    def setNumberIterations(self, numuberIterations):
        self.__numberIterations = numberIterations

    def getOutputFile(self):
        return self.__outputFile
    
    def setOutputFile(self, outputFile):
        self.__outputFile = outputFile

    def getBandwidth(self):
        return self.__bandwidth

    def setBandwidth(self, bandwidth):
        self.__bandwidth = bandwidth
        
    def calculateAverage(self, results, senderFlag):
        theSum = 0
        for result in results:
            if (senderFlag):
                theSum += float(result.getSenderRate())
            else:
                theSum += float(result.getReceiverRate())

        average = str(theSum / len(results))
        return float(average[:average.find(".") + 3])

    def calculateStandardDeviation(self, results, senderFlag):
        average = self.calculateAverage(results, senderFlag)

        theSum = 0
        for result in results:
            if (senderFlag):
                theSum += pow(float(result.getSenderRate()) - average, 2)
            else:
                theSum += pow(float(result.getReceiverRate()) - average, 2)

        return math.sqrt(theSum / len(results))

    def getDateID(self):
        return time.strftime("%d/%m/%G %H:%M:%S", time.localtime(time.time()))

    def findMbitRate(self, outputLine):
        counter = 0
        for field in outputLine:
            if (field == "MBytes"):
                return outputLine[counter + 1]
            counter += 1
            
    def runIperf(self, stdDeviationFlag=None):
        output = "# experimentid:" + str(self.getExperimentID()) + \
                 " date:" + str(self.getDateID()) + \
                 " traffictype:" + str(self.getTrafficType()) + \
                 " bandwidth:" + str(self.getBandwidth()) + \
                 " testruntime:" + str(self.getRuntime()) + \
                 "sec numberiterations:" + str(self.getNumberIterations()) + "\n" + \
                 "# minpacketsize:" + str(self.getMinPacketSize()) + \
                 " maxpacketsize:" + str(self.getMaxPacketSize()) + \
                 " incrementsize:" + str(self.getIncrementSize()) + "\n" + \
                 "# sender:" + str(self.getSenderAddress()) + \
                 " receiver:" + str(self.getReceiverAddress()) + "\n\n"

        print output + "\n\n"

        # the last parameter in the range function specifies the increment
        for currentPacketSize in range(self.getMinPacketSize(), self.getMaxPacketSize(), self.getIncrementSize()):
            # create the basic command
            cmd = "iperf -c " + self.getReceiverAddress() + " "
            if (self.getTrafficType() == "udp"):
                cmd += "--udp "
            cmd += "-b " + self.getBandwidth() + " -l " + str(currentPacketSize) + " -t " + str(self.getRuntime())
                   
            # now run each experiment numberIteration times for each packet size
            bandwidthResults = []
            for iteration in range(0, self.getNumberIterations()):
                print cmd
                results = commands.getstatusoutput(cmd)[1]
                print results
                results = results.splitlines();

                bandwidthResults.append(IperfBandwidthResult(self.findMbitRate(results[6].split()), \
                                                             self.findMbitRate(results[9].split())))

            # now calculate the average sender and receiver rates for this packet size
            output += str(currentPacketSize) + "\t" + \
                      str(self.calculateAverage(bandwidthResults, True)) + "\t" +  \
                      str(self.calculateAverage(bandwidthResults, False))

            # calculate standard deviation for sender and receiver if requested
            if (stdDeviationFlag):
                output += "\t" + str(self.calculateStandardDeviation(bandwidthResults, True)) + \
                          "\t" + str(self.calculateStandardDeviation(bandwidthResults, False))
                
            output += "\n"

            print "\n" + output

        # finally, write the results out to file
        filename = None
        if (self.getBasePath() != None):
            filename = self.getBasePath()
        if (self.getLogDirectory() != None):
            if (filename != None):
                filename += self.getLogDirectory() + "/"
            else:
                filename = self.getLogDirectory() + "/"
        filename += self.getOutputFile()
         
        theFile = open(filename, "w")
        theFile.write(output)
        theFile.close()

    def mkdir(self, dirName):
        cmd = "mkdir " + dirName
        return commands.getstatusoutput(cmd)[0]
