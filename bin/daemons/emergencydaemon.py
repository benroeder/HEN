#!/usr/local/bin/python
import sys
sys.path.append("/usr/local/hen/lib")

from daemonizer import Daemonizer
from daemon import Daemon
from auxiliary.timer import GracefulTimer
from auxiliary.daemonlocations import DaemonLocations
from auxiliary.daemonstatus import DaemonStatus
from auxiliary.protocol import Protocol
import logging, socket, threading, datetime, xml.dom.minidom, \
    ConfigParser, textwrap, smtplib, commands

import os

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# seconds between checks
CHECKER_INTERVAL = 30
# MonitorD settings
MONITORD_HOST = DaemonLocations.monitorDaemon[0]
MONITORD_PORT = DaemonLocations.monitorDaemon[1]
POWERDOWN_COMMAND = '/usr/local/hen/bin/emergencypowerdown.py'
# Location of emergencyd.conf
HEN_PATH = '/usr/local/hen'
#HEN_PATH = '/home/arkell/u0/schooley/hen_scripts'
CONFIG_FILE = HEN_PATH + '/etc/configs/emergencydaemon.conf'
# Valid run levels
VALID_RUN_LEVELS = [0,1,2]
EMAIL_NODE_DETAILS = """\n========== %s ALERT ==========
        NodeID: %s
      SensorID: %s
    SensorType: %s
 CurrentStatus: %s
 TimeOfReading: %s
CurrentReading: %f
HighestReading: %f
===================================

EmergencyDaemon run_level: %d
       Action to be taken: %s

"""

class EmergencyChecker(Daemon):
    """
    \brief Implements the EmergencyD external interface
    This class contains the methods called when requests are recieved by the
    Daemon (inherited).
    """
    __version = "Emergency Daemon v0.1"
    __checker_timer = None
    __checker_lock = None
    __config = None
    __config_path = None
    
    __warning_email_addresses = None
    __critical_email_addresses = None
    __run_level = None
    
    def __init__(self, config=CONFIG_FILE):
        """\brief Registers remote methods and starts update thread (timer)
        """
        Daemon.__init__(self)
        self.__config_path = config
        self.__parseConfig(self.__config_path)
        self.__registerMethods()
        self.__checker_lock = threading.Lock()
    
    def testMethod(self,prot,seq,ln,payload):
        log.debug("testMethod() called.")
        sdata = (2, "cpu.w00t", "temperature", 1168342852, 32.5, 
                    32.6)
        self.__handleCriticalStatus("computer32", sdata)
        prot.sendReply(200, seq, "Test method called.")
    
    def manualRunChecker(self,prot,seq,ln,payload):
        log.debug("manualRunChecker() called.")
        prot.sendReply(200, seq, "Running runChecker.")
        self.runChecker()
        
    def manualStopUpdateTimer(self,prot,seq,ln,payload):
        log.debug("manualStopUpdateTimer() called.")
        if not self.updateTimerIsRunning():
            prot.sendReply(400, seq, "The update timer isn't running!") 
        else:
            self.stopUpdateTimer()
            prot.sendReply(200, seq, "Update Timer stopped.")
        
    def manualStartUpdateTimer(self,prot,seq,ln,payload):
        log.debug("manualStartUpdateTimer() called.")
        if self.updateTimerIsRunning():
            prot.sendReply(400, seq, "The update timer is already running!") 
        else:
            self.startUpdateTimer()
            prot.sendReply(200, seq, "Update Timer started.")
            
    def setRunLevel(self,prot,seq,ln,payload):
        log.debug("setRunLevel() called.")
        new_run_level = int(payload)
        if not self.__validRunLevel(new_run_level):
            log.debug("Invalid run_level (%d) given" % new_run_level)
            prot.sendReply(400, seq, "Invalid run_level given.")
            return
        if new_run_level < self.__run_level:
            payload = "Lowering run_level from %d to %d." % \
                      (self.__run_level, new_run_level)
        elif new_run_level > self.__run_level:
            payload = "Raising run_level from %d to %d." % \
                      (self.__run_level, new_run_level)
        else:
            payload = "No change in run_level."
        log.info(payload)
        prot.sendReply(200, seq, payload)
        self.__run_level = new_run_level
    
    def getRunLevel(self,prot,seq,ln,payload):
        log.debug("getRunLevel() called.")
        prot.sendReply(200, seq, str(self.__run_level))

    def reloadConfig(self,prot,seq,ln,payload):
        log.debug("reloadConfig() called.")
        self.__parseConfig(config)
        prot.sendReply(200, seq, "Reload of config file completed.")        

    def killDaemon(self,prot,seq,ln,payload):
        prot.sendReply(200, seq, "Killing Daemon!")
        os.abort()

    def getVersion(self,prot,seq,ln,payload):
        """\brief Returns version"""
        payload = self.__version
        prot.sendReply(200, seq, payload)
    
    def stopDaemon(self,prot,seq,ln,payload):
        """\brief Stops the daemon and all threads
        This method will first stop any more incoming queries, then wait for
        any update tasks to complete, before stopping itself.
        """
        log.debug("stopDaemon called.")
        prot.sendReply(200, seq, "Accepted stop request.")
        log.debug("Stopping Checker Timer")
        self.__checker_timer.stop()
        self.acceptConnections(False)
        log.debug("Stopping Emergency Daemon (self)")
        Daemon.stop(self)
    
    def startUpdateTimer(self):
        self.__checker_timer = GracefulTimer(CHECKER_INTERVAL, \
                                    self.runChecker, True)
        self.__checker_timer.start()
    
    def stopUpdateTimer(self):
        self.__checker_timer.stop()
        
    def updateTimerIsRunning(self):
        if self.__checker_timer:
            if self.__checker_timer.isAlive():
                return True
        return False
    
    def runChecker(self):
        log.debug("runChecker() called.")
        log.debug("Acquiring checker lock.")
        self.__checker_lock.acquire()
        p = Protocol(None)
        if DaemonStatus().monitorDaemonIsOnline(5):
            p.open(MONITORD_HOST, MONITORD_PORT)
            p.sendRequest("get_currentsensorreadings","",self.nodeStatusHandler)
            p.readAndProcess()
        else:
            log.info("Monitor Daemon is not online!") # TODO: Email
        self.__checker_lock.release()
        log.debug("Released checker lock.")
        
    def nodeStatusHandler(self,code,seq,size,payload):
        if (code != 200) or (len(payload) == 0):
            # TODO: Warn someone that monitord isn't working properly
            log.critical("Incorrect payload received from monitor daemon!")
        sensor_dom = xml.dom.minidom.parseString(payload)
        node_readings = sensor_dom.getElementsByTagName("nodereading")
        for nodereading in node_readings:
            self.checkNodeReadings(nodereading)
        sensor_dom.unlink()

    def checkNodeReadings(self, nodereading):
        nodeid = nodereading.attributes["id"].value
        overallstatus = nodereading.attributes["overallstatus"].value
        if overallstatus == 0:
            return
        readings = nodereading.getElementsByTagName("reading")
        for reading in readings:
            # (status, sensorid, sensortype, timeinsecs, sensorvalue, 
            #        sensormaxvalue)
            sdata = self.__parseXMLReading(reading)
            if sdata[0] == 0:
                continue
            elif sdata[0] == 1:
                log.critical("ALERT: [%s][%s] has WARNING status with " + \
                      "curval=[%f], highval=[%f]" % \
                      (nodeid, sdata[1], sdata[4], sdata[5]))
                self.__handleWarningStatus(nodeid, sdata)
            elif sdata[0] >= 2:
                log.critical("ALERT: [%s][%s] has CRITICAL status with " + \
                      "curval=[%f], highval=[%f]" % \
                      (nodeid, sdata[1], sdata[4], sdata[5]))
                self.__handleCriticalStatus(nodeid, sdata)
            else:
                log.critical("WARNING: [%s][%s] has UNKNOWN status %d!" \
                      % (nodeid, sdata[1], sdata[0]))
                self.__handleUnknownStatus(nodeid, sdata)
   
    def __makeEmailNodeMessage(self, status, nodeid, sdata, action):
        return (EMAIL_NODE_DETAILS % (status, nodeid, sdata[1], sdata[2], 
                status, datetime.datetime.fromtimestamp(float(sdata[3])).\
                strftime("%Y-%m-%d-%H:%M:%S"), sdata[4], sdata[5], \
                self.__run_level, action))
    
    def __handleWarningStatus(self, nodeid, sdata):
        """\brief Handles a sensor warning status, by sending out a warning 
        email to the warning_email_addresses recipients.
        """
        message = self.__makeEmailNodeMessage("WARNING", nodeid, sdata, action)

        if self.__run_level == 0:
            action = "No action - currently running in dry-run mode."
            message = self.__makeEmailNodeMessage("WARNING", nodeid, sdata, 
                                                  action)
            log.warning(message)
        elif self.__run_level >= 1:
            action = "Email warning, but no direct action."
            message = self.__makeEmailNodeMessage("WARNING", nodeid, sdata, 
                                                  action)
            log.warning(message)
            self.__sendEmail(self.__warning_email_addresses,
                     "EMERGENCYD: Node Sensor [%s][%s] in WARNING state!"\
                     % (nodeid, sdata[1]), message)
    
    def __handleCriticalStatus(self, nodeid, sdata):
        """\brief Handles a critical warning status, by attempting to shut down
        the node, and then send out an email to the critical_email_addresses 
        recipients, with the results and details.
        """
        if self.__run_level == 0:
            action = "No action - currently running in dry-run mode."
            message = self.__makeEmailNodeMessage("CRITICAL", nodeid, sdata, 
                                                  action)
            log.critical(message)
        elif self.__run_level == 1:
            action = "Email warning, but no direct action."
            message = self.__makeEmailNodeMessage("CRITICAL", nodeid, sdata, 
                                                  action)
            log.critical(message)
            self.__sendEmail(self.__critical_email_addresses,
                     "EMERGENCYD: Node Sensor [%s][%s] in CRITICAL state!"\
                     % (nodeid, sdata[1]), message)
        else:
            action = "Email warning, and attempted powerdown of node."
            message = self.__makeEmailNodeMessage("CRITICAL", nodeid, sdata, 
                                                  action)
            powerdown_status = self.__attemptPowerDown(nodeid)
            message += "Output from powerdown attempt:\n" + powerdown_status
            log.critical(message)
            self.__sendEmail(self.__critical_email_addresses,
                     "EMERGENCYD: Node Sensor [%s][%s] in CRITICAL state!"\
                     % (nodeid, sdata[1]), message)
    
    def __handleUnknownStatus(self, nodeid, sdata):
        """\brief Handles an unknown sensor status, by sending out an email to
        the warning_email_addresses recipients with details.
        """
        unknown_state_message = "A node in an UNKNOWN state indicates a system"\
                            + "error. Please notify the author immediately."
        if self.__run_level == 0:
            action = "No action - currently running in dry-run mode."
            message = self.__makeEmailNodeMessage("UNKNOWN", nodeid, sdata, 
                                                  action)
            message += unknown_state_message
            log.critical(message)
        elif self.__run_level >= 1:
            action = "Email warning, but no direct action."
            message = self.__makeEmailNodeMessage("UNKNOWN", nodeid, sdata, 
                                                  action)
            message += unknown_state_message
            log.critical(message)
            self.__sendEmail(self.__critical_email_addresses,
                     "EMERGENCYD: Node Sensor [%s][%s] in UNKNOWN state!"\
                     % (nodeid, sdata[1]), message)
            
    def __attemptPowerDown(self, nodeid):
        """\brief Attempts to power down the node specified by nodeid, and
        returns a string of the results
        \p nodeid - id of node that needs powering down
        """
        (status, output) = commands.getstatusoutput(\
                            "%s %s" % (POWERDOWN_COMMAND, nodeid))
        return output   
    
    def __sendEmail(self, recipients, subject, message):
        """\brief Sends an email with the provided message to the provided list
        of recipients
        \p recipients - list of recipients.
        \p subject - message subject
        \p message - string message to be sent.
        """
        if len(recipients) == 0:
            log.critical("__sendEmail(): Error: No recipients given.")
            return
        message = ("To: %s\r\nSubject: %s\r\n\r\n"
                   % (", ".join(recipients), subject)) + message
        try:
            server = smtplib.SMTP('localhost')
            server.sendmail("", recipients, message)
            server.quit()
        except Exception, e:
            log.critical("__sendEmail() exception: %s" % str(e))
    
    def __parseXMLReading(self, reading):
        status = int(reading.attributes["status"].value)
        sensorid = reading.attributes["id"].value
        sensortype = reading.attributes["type"].value
        timeinsecs = int(reading.attributes["time"].value)
        sensorvalue = float(reading.attributes["value"].value)
        sensormaxvalue = float(reading.attributes["max"].value)
        return (status, sensorid, sensortype, timeinsecs, sensorvalue, \
             sensormaxvalue)
    
    def __parseConfig(self, config):
        log.info("Parsing config file...")
        self.__config = ConfigParser.SafeConfigParser()
        self.__config.read(config)
        if not self.__config.has_section("EMERGENCYDAEMON"):
            log.critical("Config file (%s) has no DEFAULT section. Aborting!" \
                         % config)
        options_found = [0,0,0]
        options = self.__config.items("EMERGENCYDAEMON")
        for (name, val) in options:
            if name == "run_level":
                if not self.__validRunLevel(int(val)):
                    log.critical("Error: run_level %d invalid. " + \
                                 "Defaulting to 1." % self.__run_level)
                    self.__run_level = 1
                else:
                    self.__run_level = int(val)    
                options_found[0] = 1
            elif name == "warning_email_addresses":
                self.__warning_email_addresses = val.split(",")
                try:
                    self.__warning_email_addresses.remove('')
                except:
                    pass
                if len(self.__warning_email_addresses) == 0:
                    log.critical("warning_email_addresses has zero length!")
                options_found[1] = 1
            elif name == "critical_email_addresses":
                self.__critical_email_addresses = val.split(",")
                try:
                    self.__critical_email_addresses.remove('')
                except:
                    pass
                if len(self.__critical_email_addresses) == 0:
                    log.critical("critical_email_addresses has zero length!")
                options_found[2] = 1
        if 0 in options_found:
            log.critical("Error: Not all required config options found." + \
                         " Aborting! (options_found = %s)" % str(options_found))
            os.abort()

    def __registerMethods(self):
        log.debug("Registering method handlers...")
        self.registerMethodHandler("get_version", self.getVersion)
        #self.registerMethodHandler("test_method", self.testMethod)  
        #self.registerMethodHandler("stop_daemon", self.stopDaemon)
        #self.registerMethodHandler("kill_daemon", self.killDaemon)
        self.registerMethodHandler("get_run_level", self.getRunLevel)
        #self.registerMethodHandler("set_run_level", self.setRunLevel)
        #self.registerMethodHandler("run_checker", self.manualRunChecker)
        #self.registerMethodHandler("reload_config", self.reloadConfig)
        #self.registerMethodHandler("stop_checks", self.manualStopUpdateTimer)
        #self.registerMethodHandler("start_checks", self.manualStartUpdateTimer)
        
    def __validRunLevel(self, run_level):
        return run_level in VALID_RUN_LEVELS
    
class EmergencyDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    __bind_addr = DaemonLocations.emergencyDaemon[0]
    __port = DaemonLocations.emergencyDaemon[1]
    __sockd = None
    __emergency_checker = None
    
    def __init__(self, doFork):
        Daemonizer.__init__(self, doFork)
    
    def run(self):
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        self.__sockd.settimeout(2) # 2 second timeouts
        log.debug("Creating EmergencyChecker")
        self.__emergency_checker = EmergencyChecker()
        log.debug("Starting EmergencyChecker")
        self.__emergency_checker.startUpdateTimer()
        self.__emergency_checker.start()
        while self.__emergency_checker.isAlive():
            if self.__emergency_checker.acceptingConnections():
                # allow timeout of accept() to avoid blocking a shutdown
                try:
                    (s,a) = self.__sockd.accept()
                    log.debug("New connection established from " + str(a))
                    self.__emergency_checker.addSocket(s)
                except:
                    pass
            else:
                log.debug("EmergencyChecker still alive, but not accepting " + \
                            + "connections")
                time.sleep(2)
        log.debug("Closing socket.")
        self.__sockd.shutdown(socket.SHUT_RDWR)        
        self.__sockd.close()
        while threading.activeCount() > 1:
            cThreads = threading.enumerate()
            log.debug("Waiting on " + str(threading.activeCount()) + \
                      " active threads...")
            time.sleep(2)
        log.debug("EmergencyDaemon Finished.")
        # Now everything is dead, we can exit.  
        sys.exit(0)
        
def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    WORKDIR = '/var/hen/emergencydaemon'
    PIDDIR = '/var/run/hen'
    LOGDIR = '/var/log/hen/emergencydaemon'
    LOGFILE = 'emergencydaemon.log'
    PIDFILE = 'emergencydaemon.pid'
    GID = 17477 # schooley
    UID = 17477 # schooley
    emergencyd = EmergencyDaemon(True)
    emergencyd.setWorkingDir(WORKDIR)
    emergencyd.setPIDDir(PIDDIR)
    emergencyd.setLogDir(LOGDIR)
    emergencyd.setLogFile(LOGFILE)
    emergencyd.setPidFile(PIDFILE)
    emergencyd.setUid(UID)
    emergencyd.setGid(GID)
    emergencyd.start()
        
if __name__ == "__main__":
    main()
