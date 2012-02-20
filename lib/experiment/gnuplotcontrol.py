#! /usr/bin/python

import commands, os

class DataSet:

    def __init__(self, dataColumn=None, stdDeviationColumn=None, dataTitle=None):
        self.__dataColumn = dataColumn
        self.__stdDeviationColumn = stdDeviationColumn
        self.__dataTitle = dataTitle

    def getDataColumn(self):
        return self.__dataColumn

    def setDataColumn(self, dataColumn):
        self.__dataColumn = dataColumn

    def getStdDeviationColumn(self):
        return self.__stdDeviationColumn

    def setStdDeviationColumn(self, stdDeviationColumn):
        self.__stdDeviationColumn = stdDeviationColumn

    def getDataTitle(self):
        return self.__dataTitle

    def setDataTitle(self, dataTitle):
        self.__dataTitle = dataTitle        

    def __str__(self):
        return "datacolumn:" + str(self.getDataColumn()) + \
               " stddeviationcolumn:" + str(self.getStdDeviationColumn()) + \
               " datatitle:" + str(self.getDataTitle())

    
class GNUPlotControl:
    """\brief Class to programatically generate gnuplot scripts and run them
    """

    def __init__(self, terminalType=None, size=None, inputFile=None, outputFile=None, xLabel=None, yLabel=None, yRange=None, keyPosition=None, grid=None, gnuplotScriptFilename=None, graphDataSets=None, basePath=None):
        """\brief Initializes class
        \param terminalType (\c string) The terminal type (png for example)
        \param size (\c float) Used to set the graph's size (0.7 for example)
        \param inputFile (\c string) The full path to the file containing the data to graph
        \param outputFile (\c string) The full path to the graph file to generate
        \param xLabel (\c string) The x-axis label
        \param yLabel (\c string) The y-axis label
        \param yRange (\c tuple of ints) The y axis range (the x axis range is computed from the data)
        \param keyPosition (\c string) The position of the graphs key (below, for example)
        \param grid (\c boolean) True if a grid is desired, False otherwise
        \param gnuplotScriptFilename(\c string) The full path of the gnuplot script to generate
        \param graphDataSets(\c array of DataSet objects) The data sets to graph
        \param basePath (\c string) The base path to the input and output directories
        """
        self.__terminalType = terminalType
        self.__size = size
        self.__inputFile = inputFile
        self.__outputFile = outputFile
        self.__xLabel = xLabel
        self.__yLabel = yLabel
        self.__yRange = yRange
        self.__keyPosition = keyPosition
        self.__grid = grid
        self.__gnuplotScriptFilename = gnuplotScriptFilename
        self.__graphDataSets = graphDataSets
        self.__xRange = None
        self.__basePath = basePath

    def getTerminalType(self):
        return self.__terminalType

    def setTerminalType(self, terminalType):
        self.__terminalType = terminalType
        
    def getSize(self):
        return self.__size

    def setSize(self, size):
        self.__size = size

    def getInputFile(self):
        return self.__inputFile

    def setInputFile(self, inputFile):
        self.__inputFile = inputFile
        
    def getOutputFile(self):
        return self.__outputFile

    def setOutputFile(self, outputFile):
        self.__outputFile = outputFile
        
    def getXLabel(self):
        return self.__xLabel

    def setXLabel(self, xLabel):
        self.__xLabel = xLabel
        
    def getYLabel(self):
        return self.__yLabel

    def setYLabel(self, yLabel):
        self.__yLabel = yLabel
        
    def getYRange(self):
        return self.__yRange

    def setYRange(self, yRange):
        self.__yRange = yRange

    def getXRange(self):
        return self.__xRange

    def setXRange(self, xRange):
        self.__xRange = xRange        
    
    def getKeyPosition(self):
        return self.__keyPosition
    
    def setKeyPosition(self, keyPosition):
        self.__keyPosition = keyPosition
        
    def getGrid(self):
        return self.__grid

    def setGrid(self, grid):
        self.__grid = grid    

    def getDataSets(self):
        return self.__graphDataSets

    def setDataSets(self, graphDataSets):
        self.__graphDataSets = graphDataSets

    def getGnuplotScriptFilename(self):
        return self.__gnuplotScriptFilename

    def setGnuplotScriptFilename(self, gnuplotScriptFilename):
        self.__gnuplotScriptFilename = gnuplotScriptFilename

    def getBasePath(self):
        return self.__basePath

    def setBasePath(self, basePath):
        self.__basePath = basePath
        
    def calculateXRange(self):
        lines = None
        xMin = None
        xMax = None

        # Open the data file
        try:
            lines = open(self.getInputFile(), "r")
        except:
            print "error while opening " + self.getInputFile() + " in calculateXRange()"
            return None

        # The x values are in the first column of each line. Only process blanks that are not
        # blank and that are not comments
        counter = 0
        for line in lines:
            line = line.strip()

            if ( (line != "") and (line != "\n") and (line.find("#") == -1) ):
                firstColumnValue = int(line.split("\t")[0])
                if (counter == 0):
                    xMin = firstColumnValue
                    xMax = firstColumnValue
                else:
                    if (firstColumnValue < xMin):
                        xMin = firstColumnValue
                    if (firstColumnValue > xMax):
                        xMax = firstColumnValue
                counter += 1

        return (xMin - 10, xMax + 50)
    
    def writeGnuplotScript(self):
        xRange =  self.getXRange()
        graphDataSets = self.getDataSets()
        
        script = "set term " + self.getTerminalType() + "\n" + \
                 "set size " + str(self.getSize()) + "," + str(self.getSize()) + "\n" + \
                 "set output \"" + self.getBasePath() + self.getOutputFile() + "\"" + "\n" + \
                 "set xlabel \"" + self.getXLabel() + "\"" + "\n" + \
                 "set ylabel \"" + self.getYLabel() + "\"" + "\n" + \
                 "set xrange [" + str(xRange[0]) + ":" + str(xRange[1]) + "]" + "\n" + \
                 "set yrange [" + str(self.getYRange()[0]) + ":" + str(self.getYRange()[1]) + "]" + "\n" + \
                 "set key " + self.getKeyPosition() + "\n"
        if (self.getGrid()):
            script += "set grid\n"

        script += "plot " 
        for dataSet in graphDataSets:
            dataColumn = dataSet.getDataColumn()
            dataStdDeviation = dataSet.getStdDeviationColumn()
            dataTitle = dataSet.getDataTitle()
            
            script += "\"" + self.getBasePath() + self.getInputFile() + "\" using 1:" + str(dataSet.getDataColumn())

            if (dataStdDeviation != None):
                script += ":" + str(dataStdDeviation) + " title \"" + dataTitle + "\" with yerrorlines, \\\n"
            else:
                script += " title \"" + dataTitle + "\" with line, \\\n"

        # remove trailing ', \\n', replace with a new line
        script = script[:len(script) - 4]
        script += "\n"

        try:
            theFile = open(self.getGnuplotScriptFilename(), "w")
            theFile.write(script)
            theFile.close()
        except:
            print "error while writing to " + str(self.getGnuplotScriptFilename())

    def removeGnuplotScript(self):
        os.remove(self.getGnuplotScriptFilename())
        
    def runGnuplot(self):
        cmd = "/usr/bin/gnuplot " + self.getGnuplotScriptFilename()
        return commands.getstatusoutput(cmd)[0]
