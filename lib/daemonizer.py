import sys
import os
import logging
import time

log = logging.getLogger()

class Daemonizer:
    """\brief Implements a Daemon with pid/log files.
    """
    __workdir = None
    __piddir = None
    __logdir = None
    __logfile = False
    __pidfile = False
    __uid = -1 # if this is false then root can not be the owner of a process since 0 evaluates to false.
    __gid = False
    __pidfd = None
    __doFork = False
    
    def __init__(self, doFork=False):
        self.__doFork = doFork
        pass

    def run(self):
        """\brief Main daemon execution method. Must be overridden."""
        log.critical("Main function run() not overridden. Exiting.")
        sys.exit(1)
    
    def checkVars(self):
        """\brief Checks that all essential internal vars are set."""
        __failure = False
        if not self.__workdir:
            log.critical("Failure: __workdir is not set.")
            __failure = True
        if not self.__logdir:
            log.critical("Failure: __logdir is not set.")
            __failure = True
        if not self.__piddir:
            log.critical("Failure: __piddir is not set.")
            __failure = True
        if not self.__logfile:
            log.critical("Failure: __logfile is not set.")
            __failure = True
        if not self.__pidfile:
            log.critical("Failure: __pidfile is not set.")
            __failure = True
        if self.__uid == -1:
            log.critical("Failure: __uid is not set.")
            __failure = True
        if not self.__gid:
            log.critical("Failure: __gid is not set.")
            __failure = True
        if not os.path.exists(self.__workdir):
            log.critical("Work directory does not exist: %s" % self.__workdir)
            __failure = True
        if not os.path.exists(self.__piddir):
            log.critical("PID directory does not exist: %s" % self.__piddir)
            __failure = True
        if not os.path.exists(self.__logdir):
            log.critical("Log directory does not exist: %s" % self.__logdir)
            __failure = True
        if __failure:
            sys.exit(1)          
        
    def start(self):
        """\brief Forks, detaches from session, and starts daemon.
        Upon execution, a pid file is created for use with init scripts.
        The std{out,err} descriptors are redirected to the log file. Both
        pid and log file paths are relative to working directory.
        """
        if self.__doFork:
            self.checkVars()
            log.info("Starting Daemon")        
            try:
                log.debug("Forking process")
                pid = os.fork()
                if pid > 0:
                    log.debug("Fork successful [Killing parent]")
                    # exit first parent
                    sys.exit(0)
            except OSError, e:
                log.critical("First fork failed: %d (%s)" % \
                             (e.errno, e.strerror))
                sys.exit(1)
    
            log.debug("Changing directory to /")
            os.chdir("/")
            log.debug("Creating a new session (setsid)")
            os.setsid()
            log.debug("Setting umask to 0")
            os.umask(0)
            pid = -1
            try:
                log.debug("Forking second process")
                pid = os.fork()
                if pid > 0:
                    log.info("Daemon created with pid %s" % str(pid))
                    log.debug("Opening pid file: %s/%s" % \
                              (self.__piddir, self.__pidfile))
                    try:
                        self.__pidfd = os.open("%s/%s" % \
                                                   (self.__piddir, self.__pidfile), \
                                                   os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0644)
                    except OSError, e:
                        log.critical("Second fork os.open failed: %d (%s)" % \
                                         (e.errno, e.strerror))
                        sys.exit(1)
                    
                    os.write(self.__pidfd, "%s\n" % str(pid))
                    os.close(self.__pidfd)
                    log.debug("Fork successful [Killing parent]")
                    sys.exit(0)
            except OSError, e:
                log.critical("Second fork failed: %d (%s)" % \
                             (e.errno, e.strerror))
                sys.exit(1)
            
            try:        
                log.debug("Opening logfile for writing: %s" % self.__logfile)
                try:
                    self.__logfd = os.open("%s/%s" % (self.__logdir, \
                      self.__logfile), os.O_WRONLY|os.O_CREAT|os.O_APPEND, 0644)
                except OSError, e:
                    log.critical("os.open failed to open log file: %d (%s)" % \
                                     (e.errno, e.strerror))
                    sys.exit(1)

            except Exception, e:
                log.critical("Failed opening log file: %d (%s)" % \
                             (e.errno, e.strerror))
                sys.exit(1)
            log.info("Redirecting stdout and stderr to log file.")
            os.dup2(self.__logfd, 1)
            os.dup2(self.__logfd, 2)
            log.debug("Changing working dir to " + self.__workdir)
            os.chdir(self.__workdir)
            #log.debug("Setting group id of process to " + str(self.__gid))
            #os.setegid(self.__gid)
            log.debug("Setting user id of process to " + str(self.__uid))
            os.seteuid(self.__uid)
            log.info("===== " + time.strftime("[%a %b %d %H:%M:%S %Y]", \
                          time.localtime()) + " Daemon Started =====")
            log.debug("Calling run()")
            self.run()
        else:
            self.run()

    def getWorkingDir(self):
        """\brief Returns working directory"""
        return self.__workdir

    def setWorkingDir(self, workDir):
        """\brief Sets working directory
        \param workDir -- working directory
        """
        self.__workdir = self.__removeTrailingSlashes(workDir)

    def getPIDDir(self):
        """\brief Returns PID directory"""
        return self.__piddir

    def setPIDDir(self, pidDir):
        """\brief Sets PID directory
        \param pidDir -- PID directory
        """
        self.__piddir = self.__removeTrailingSlashes(pidDir)

    def getLogDir(self):
        """\brief Returns logging directory"""
        return self.__logdir

    def setLogDir(self, logDir):
        """\brief Sets logging directory
        \param logDir -- logging directory
        """
        self.__logdir = self.__removeTrailingSlashes(logDir)

    def getLogFile(self):
        """\brief Returns log file path/name"""
        return self.__logfile

    def setLogFile(self, logFile):
        """\brief Sets log file path/name
        \param logFile -- name of log file
        """        
        self.__logfile = logFile

    def getPidFile(self):
        """\brief Returns pid file path/name"""        
        return self.__pidfile

    def setPidFile(self, pidFile):
        """\brief Sets pid file path/name
        \param pidFile -- name of pid file
        """      
        self.__pidfile = pidFile

    def getUid(self):
        """\brief Returns user id of process"""        
        return self.__uid

    def setUid(self, uid):
        """\brief Sets process user id
        \param uid -- user id
        """        
        self.__uid = uid

    def getGid(self):
        """\brief Returns group id of process"""        
        return self.__gid

    def setGid(self, gid):
        """\brief Sets process group id
        \param gid -- group id
        """        
        self.__gid = gid

    def __removeTrailingSlashes(self, path):
        while path.endswith("/"):
            if (len(path) - 1) <= 0:
                break
            path = path[:len(path) - 1]
        return path
