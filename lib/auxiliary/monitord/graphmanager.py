import random, xml.dom.minidom, time, os, commands, datetime

# Directory for storing temporary data
TMP_DIR = '/tmp/monitord/graphmanager'
# Full path to gnuplot binary
GNU_PLOT_CMD = '/usr/local/bin/gnuplot '
# Full path to mv binary
MV_CMD = '/bin/mv '

# httpd user/group permissions for hosted files/directories
WEB_UID = 80
WEB_GID = 80

PLT_TEMPLATE = """
set output "%s/plot%s.gif"
set term gif transparent xffffff x000000 xc0c0c0 xd00000 xe0e0e0 x000000 x5050a0
set size 1.2,0.4
set format x "%s"
set title "%s" 0,-0.75
set xdata time
set timefmt "%s"
set xlabel "%s"
set ylabel "%s"
set key below
set grid lt 2
set nobars
set pointsize 0.1
set nokey
set yrange [%s:%s]
plot "%s/plotdata%s.dat" using 1:2 with linespoints
"""
# plot "%s/plotdata%s.dat" using 1:2 with lines

class GraphManager:
    """
        The GraphManager handles generation and hosting of graphs created with
        gnuplot. Should be thread-safe - uses random session ids to
        differentiate processes, rather than locking a counter.
    """

    __baseurl = None
    __webdir = None

    def __init__(self, baseurl, webdir):
        """
            \param baseurl - base url for returned urls.
                        example: '/status/graphs'
                        (Note: cannot pass hostname, as it breaks tunnelling..)
            \param webdir - directory corresponding to the hosted urls.
                        example: '/home/arkell/u0/www/data/status/graphs'
        """
        self.__baseurl = baseurl
        self.__webdir = webdir
        self.__createDirectories()
        random.seed()

    def cleanOldFiles(self):
        """\brief Cleans out (removes) any files in temp and web directories
            that are older than 5 minutes.
            \throws Exception - if an error occurred.
        """
        timenow = int(time.time())
        try:
            for file in os.listdir(TMP_DIR):
                statinfo = os.stat("%s/%s" % (TMP_DIR, file))
                if (timenow - statinfo.st_mtime) > 300:
                    os.remove("%s/%s" % (TMP_DIR, file))
        except Exception, e:
            raise Exception, "cleanOldFiles(): %s" % str(e)

    def createGraph(self, data, nodeid, sensorid, sensortype, sincetime):
        """\brief Creates a graph from given data, and returns url to it.
            \param data - list of (time,val) data points to plot
            \param nodeid - nodeid of node to which sensor is attached
            \param sensorid - sensorid
            \param sensortype - type of sensor, as defined in driver
            \param sincetime - time from which graph should be plotted
            \return imageurl - url to generated graph
            \throws Exception - if an error occurred during graph generation.
                                The Exception will hold a reason for the error.
        """
        sessionid = str(random.randint(1, 1000000))
        ylabel = self.__getYLabel(sensortype)
        (xlabel,timeformat) = self.__getXLabel(sincetime)
        (ymin,ymax) = self.__createDatFile(sessionid, data)
        self.__createPlotFile(sessionid, timeformat, xlabel, ylabel, nodeid, \
              sensorid, sensortype, sincetime, ymin, ymax)
        self.__runGnuPlot(sessionid)
        self.__hostPlotFile(sessionid)
        #self.__cleanUpTempFiles(sessionid)
        return "%s/plot%s.gif" % (self.__baseurl, sessionid)

    def __cleanUpTempFiles(self, sessionid):
        """\brief Removes temp files used in graph creation.
            \param sessionid - current sessionid to use for naming the files
        """
        try:
            os.remove("%s/plot%s.plt" % (TMP_DIR, sessionid))
            os.remove("%s/plotdata%s.dat" % (TMP_DIR, sessionid))
        except Exception, e:
            raise Exception, "__cleanUpTempFiles(): %s" % str(e)

    def __hostPlotFile(self, sessionid):
        """\brief Moves the generated graph to the hosting directory.
            \param sessionid - current sessionid to use for naming the file
        """
        (status,output) = commands.getstatusoutput("%s %s/plot%s.gif %s/" % \
                           (MV_CMD, TMP_DIR, sessionid, self.__webdir))
        if status != 0:
            raise Exception, "__hostPlotFile(): %s" % str(output)

    def __runGnuPlot(self, sessionid):
        """\brief Runs gnuplot on the .plt file, to generate a gif graph.
            \param sessionid - current sessionid to use for naming the file
        """
        (status,output) = commands.getstatusoutput("%s %s/plot%s.plt" % \
                           (GNU_PLOT_CMD, TMP_DIR, sessionid))
        if status != 0:
            raise Exception, "__runGnuPlot(): %s" % str(output)
#        try:
#            os.chmod(BASE_DIR + plotFile, 664)
#        except Exception, e:
#            raise Exception, "__runGnuPlot(): %s" % str(e)

    def __createPlotFile(self, sessionid, timeformat, xlabel, ylabel, \
             nodeid, sensorid, sensortype, sincetime, ymin, ymax):
        """\brief Generates the .plt file for use with gnuplot, given the
            provided information.
            \param sessionid - current sessionid to use for naming the file
            \param timeformat - format string for time data
            \param xlabel - x axis label
            \param xlabel - y axis label
            \param nodeid - nodeid of node to which sensor is attached
            \param sensorid - sensorid
            \param sensortype - type of sensor, as defined in driver
            \param sincetime - time from which graph should be plotted
            \param ymin - Min y axis range
            \param ymax - Max y axis range
        """
        try:
            since = datetime.datetime.fromtimestamp(sincetime).\
                        strftime("%d-%b-%y-%H:%M")
            title = "Plot of [%s:%s] readings (%s over time), since %s" % \
                    (nodeid, sensorid, ylabel, since)
            plt_file = open('%s/plot%s.plt' % \
                            (TMP_DIR, sessionid), 'w')
            plt_file.write(PLT_TEMPLATE % (TMP_DIR, sessionid, timeformat, \
                  title, "%s", xlabel, ylabel, ymin, ymax, TMP_DIR, sessionid))
            plt_file.close()
        except Exception, e:
            raise Exception, "__createPlotFile(): %s\n" % str(e)
        pass

    def __getYLabel(self, sensortype):
        if sensortype == "temperature":
            return "Temperature (C)"
        elif sensortype == "fanspeed":
            return "Fanspeed (RPM)"
        elif sensortype == "current":
            return "Current (A)"
        elif sensortype == "voltage":
            return "Voltage (V)"
        elif sensortype == "alarm":
            return "SNMP Alarm (0 = off, 1 = on)"
        else:
            return "Unknown type [%s]" % sensortype

    def __getXLabel(self, sincetime):
        """\brief Given the data, the range of the time axis can be calculated,
            and a suitable time format/label found.
            \param sincetime - time from which graph should be plotted
            \return (xlabel, timeformat) - x axis label, and a suitable
                timeformat. example: ('Time, from 21-02-06 to 28-02-06', %d%H)
        """
        timenow = int(time.time())
        timeformat = "%d-%m-%Y"
        labelformat = "%d-%m-%Y"
        xrange = timenow - sincetime
        if xrange < 0:
            raise Exception, "__getXLabel(): sincetime in future"
        elif xrange < 4000:
            timeformat = "%H:%M"
            xlabelformat = "%H:%M"
        elif xrange < 86700:
            timeformat = "%H:%M"
            labelformat = "%A, %H:%M"
        elif xrange < 2592300:
            timeformat = "%d-%b"
            labelformat = "%d-%b, %H:%M"
        xlabel = "Time, from [%s] to [%s]" % \
            (datetime.datetime.fromtimestamp(sincetime).strftime(labelformat),
             datetime.datetime.fromtimestamp(timenow).strftime(labelformat))
        return (xlabel, timeformat)

    def __createDatFile(self, sessionid, data):
        """\brief Create a .dat file using the provided data
            \param sessionid - current sessionid to use for naming the file
            \param data - data to use
            \return (ymin,ymax) - min/max y range
        """
        ymin = None
        ymax = None
        try:
            dat_file = open('%s/plotdata%s.dat' % \
                            (TMP_DIR, sessionid), 'w')
            for (stime,sval) in data:
                if ymin == None or float(sval) < ymin:
                    ymin = float(sval)
                if ymax == None or float(sval) > ymax:
                    ymax = float(sval)
                dat_file.write("%s %s\n" % (stime, sval))
            dat_file.close()
        except Exception, e:
            raise Exception, "__createDatFile(): %s\n" % str(e)
        if ymax and ymin:
            diff = ymax - ymin
            if diff == 0:
                ymin -= 1.0
                ymax += 1.0
            else:
                ymin -= diff/2.0
                ymax += diff/2.0
            return (ymin,ymax)
        else:
            raise Exception, "__createDatFile(): ymax/ymin have NoneType"

    def __createDirectories(self):
        """\brief Checks that tmp and hosting directories exist, and if not,
            attempts to create them.
        """
        try:
            if not os.path.exists(TMP_DIR):
                os.makedirs(TMP_DIR)
        except Exception, e:
            raise Exception, "__createDirectories(%s): %s" % (TMP_DIR, str(e))
        try:
            if not os.path.exists(self.__webdir):
                os.makedirs(self.__webdir)
            #os.chown(self.__webdir, WEB_UID, WEB_GID)
        except Exception, e:
            raise Exception, "__createDirectories(%s): %s" % \
                    (self.__webdir, str(e))

