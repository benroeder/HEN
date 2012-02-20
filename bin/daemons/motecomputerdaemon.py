#!/usr/bin/env python

import sys, socket, commands, signal, re, os, pickle
#sys.path.append("/usr/local/hen/lib")

from daemonizer import Daemonizer
from daemon import Daemon
import logging, threading, socket
#from henmanager import HenManager
from auxiliary.timer import GracefulTimer
from auxiliary.daemonlocations import DaemonLocations

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

class HmProxy :
    """
      phony hm daemon, all calls here are race conditions unless
      this central arbitur exists
    """
    pass

class MoteInstallError(Exception):
    def __init__(self,message):
        Exception.__init__(self, message)

class UnknownActionError(Exception):
    def __init__(self,message):
        Exception.__init__(self, message)

class LogError(Exception):
    def __init__(self,message):
        Exception.__init__(self, message)

class ProtocolHelper :
    def __init__(self,prot,seq):
        self.__prot = prot
        self.__seq = seq

    def reply(s) :
        self.__prot.sendReply(200,seq,s)

# give unneeded ones as 'None'
# XXX needs to be some sanity checking of arguments here
class MoteImage:
    def __init__(self, dir, addr, kern) :
        self.dir = dir
        self.short_addr = addr
        self.kernel = kern

class MoteListParser:
    def __init__(self, motelist="/export/mote/tools/tinyos/bin/motelist -c"):
        self.__motes = {}
        self.__motelist = motelist
        self.parse()

    def parse(self):
        #self.__motes.clear()
        tmp = {}
        status,output = commands.getstatusoutput(self.__motelist)
        if status != 0 :
            log.critical("motelist: Not found")
            sys.exit(1)
        if output == "No devices found." :
            self.__motes.clear()
            return
        lines = output.split('\n')
        for line in lines :
            #log.debug("motelist : " + line)
            (id,device,desc) = line.split(',')
            tmp[id] = Mote(device)
        # update local copy
        #for m in set(self.__motes.keys() + tmp.keys()):
        for m in tmp:
            if self.__motes.has_key(m) :
                mote = self.__motes[m]
                newmote = tmp[m]
                newmote.lastos = mote.lastos
                newmote.image = mote.image
                newmote.loggerpid = mote.loggerpid
                newmote.username = mote.username
        self.__motes = tmp
        
#            # if not present before, add it
#            if not self.__motes.has_key(m): 
#                self.__motes[m] = Mote(tmp[m].device)
#                continue
#            # ensure device info is correct
#            if not tmp.has_key(m):
#                self.__motes[m].setdevice( None )
#            else:
#                self.__motes[m].setdevice( tmp[m].device )

    def getmotes(self):
        self.parse()
        return self.__motes

class Mote:
    def __init__(self, device) :
        self.device = device
        self.loggerpid = -1
        self.image = None
        self.lastos = None
        self.username = None

    def __str__(self):
        return "device=%s logpid=%i image=%s lastos=%s" % \
            (self.device,self.loggerpid,self.image,self.lastos)
    
    def install(self, moteos, image) :
        """install throws an exception on failure"""
        self.__stoplog()
        moteos.install(self.device, image)
        self.image = image
        self.lastos = moteos

    def log(self, moteos, file, action="start") :
        """log throws an exception on failure"""
        if action == "start" and self.__stoplog() :
            self.loggerpid = moteos.logtofile(self.device, file)
            if (0,0) != os.waitpid(self.loggerpid, os.WNOHANG) :
                #log.debug("problem with logging")
                # exception? this is a race condition, right?
                self.loggerpid = -1
                raise LogError("log " + action + " failed")
        elif action == "stop" :
            self.__stoplog()
        else :
            raise UnknownActionError(action)

    def __stoplog(self) :
        if self.loggerpid != -1 :
            try :
                os.kill(self.loggerpid, signal.SIGTERM)
                os.waitpid(self.loggerpid, 0)
            except :
                # if this is thrown it just implies
                # that the process did not exist anyway
                pass
        self.loggerpid = -1
        return True

    def currentimage(self):
        return self.image

    def currentos(self):
        return self.lastos

    def currentuser(self):
        return self.username

    def loggingactive(self):
        return self.loggerpid != -1

    def getdevice(self):
        return self.device

    def setdevice(self, dev):
        self.device = dev

# what does this mean?
# could be useful for establishing that the correct target was built...
class TmoteSkyMote(Mote):
    pass

class MoteOS :
    def __init__(self, name, install_command, log_path):
        self.name = name
        self.install_command = install_command
        self.log_path = log_path
        self.log_app = log_path[log_path.rfind('/')+1 :]
        
    def getname(self):
      return self.name

    def getlogcommand(self):
        return self.log_path

    def getinstallcommand(self):
        return self.install_command

    def getinstallargs(self, device, image):
        """must be defined in a superclass"""
        raise NotImplementedError

    def setenv(self):
        """must be defined in a superclass"""
        raise NotImplementedError

    def install(self, device, image): 
        self.setenv()
        status, output = commands.getstatusoutput( \
            self.getinstallcommand() % self.getinstallargs(device, image) \
        )
        if status != 0 : raise MoteInstallError(output)
    
    def logtofile(self, device, file):
        # this does not throw any exceptions if it was in error ^^;;
        return os.spawnlp(os.P_NOWAIT, self.log_path, self.log_app, device, file)

    def checkrequirements(self, image):
        """
          so rpcs can fail fast ;-)
          eg:  build dir exists
            build dir is readable
            built for correct platform
            log dir exists
            log dir is writable (rw?)
            log file does not already exist? (give it new name?)
        """
        raise NotImplementedError
    
class BaseTinyosPlatform(MoteOS) :
    # might want to add "nice -n -20" to make line?
    #
    # ENVIRONMENTAL VARIABLES IS A HACK THAT RELIES ON A SYMLINK 
    # IN THE TOS2 DIR, CHANGE SO THAT THIS COMES FROM THE SUPERCLASS AND 
    # HAVE THE SUPERCLASS GET IT FROM A CLASS THAT READS A CONFIG FILE...
    def __init__(self, name, version=1, install_command="make -C %s tmote reinstall.%i bsl,%s", \
                log_command="/export/mote/tools/tinyos/bin/serial2file"):
        self.tosroot    = "/export/mote/tinyos/tinyos-%d.x/" % version
        #self.tosroot    = "/opt/tinyos-%i.x/" % version
        self.tosdir     = self.tosroot + "tos"
        self.makerules  = self.tosroot + "tools/make/Makerules"
        #self.makerules  = self.tosroot + "support/make/Makerules" # will not work for tos1
        MoteOS.__init__(self, name, install_command, log_command)

    def getinstallargs(self, device, image):
        return (image.dir, int(image.short_addr), device)
    
    def serialforwarder(self):
        raise NotImplementedError
    
    def setenv(self):
        os.putenv("TOSDIR",     self.tosdir)
        os.putenv("MAKERULES",  self.makerules)
    
class Tinyos1Platform(BaseTinyosPlatform) :
    def __init__(self, name="tinyos1") :
        BaseTinyosPlatform.__init__(self, name, 1)
    
class Tinyos2Platform(BaseTinyosPlatform) :
    def __init__(self, name="tinyos2"):
        BaseTinyosPlatform.__init__(self, name, 2)

class ContikiPlatform(MoteOS) :
    def __init__(self, name="contiki", install_command="COMPORT=%s make -C %s %s", log_command="/usr/local/hen/bin/contiki_serial2file"):
        MoteOS.__init__(self, name, install_command, log_command)

    def getinstallargs(self, device, image):
        return  (device, image.dir, image.kernel.replace('contiki.', '', 1 ))

    def setenv(self):
        """no special requirements"""
        pass

    def tunslip(self):
        raise NotImplementedError

    def codeprop(self):
        raise NotImplementedError
        
class MoteControl(Daemon):
    """\brief Implements basic computer daemon functionality."""
    __version = "Mote Daemon v0.1 (borked)"
    
    def __init__(self):
        Daemon.__init__(self)
        self.__initOperatingSystems()
        self.__initMotes()
        self.__registerMethods()

    def __initOperatingSystems(self):
        self.__moteOS = {}
        tos1 = Tinyos1Platform()
        self.__moteOS["tinyos"]  = tos1
        self.__moteOS["tinyos1"] = tos1
        self.__moteOS["tinyos2"] = Tinyos2Platform()
        self.__moteOS["contiki"] = ContikiPlatform()

    # DON'T DO THIS, THE OPERATION IS CHEAP ENOUGH TO DO EVERYTIME IT IS NEEDED
    # AND IT WILL MAKE THE CODE MORE ROBUST...
    def __initMotes(self):
        self.__motelist = MoteListParser("motelist -c")

    def __registerMethods(self):
        self.registerMethodHandler("execute_command", self.executeCommand)
        self.registerMethodHandler("install",   self.installImage)
        self.registerMethodHandler("log",       self.logToFile)
        self.registerMethodHandler("history",   self.history)
        self.registerMethodHandler("motelist",  self.motelist)
        self.registerMethodHandler("shutdown",  self.stopDaemon)
 
        self.registerMethodHandler("mote_usb",  self.moteusb)
  
    def executeCommand(self,prot,seq,ln,payload):
        """\brief Attempts to switch on the specified node in the payload.
        Payload format: nodeid
        """
        (code, payload) = commands.getstatusoutput(payload)
        if (code == 0):
            code = 200
        else:
            code = 422 # returnCodes[422] = "error executing command"
        
        prot.sendReply(code, seq, payload)

    def moteusb(self,prot,seq,ln,payload) :
        payload = pickle.loads(payload)
        try :
            ref,args = payload
            args = map(str,args)
        except :
            prot.sendReply(422,seq,"bad args to rpc")
            return

        motes = self.__motelist.getmotes()
        device = motes[ref].device
        bin = "/export/mote/tools/tinyos/bin/generic_msg"
        command = " ".join([bin, device] + args)

        log.debug("""moteusb:
  %s""" % command)

        self.executeCommand(prot,seq,ln,command)

    def installImage(self,prot,seq,ln,payload):
        # payload format = [platform, kernel, shortaddr, directory, mote id, log file, hen id]+
        args = pickle.loads(payload)
        installs = []
        motes = self.__motelist.getmotes()

        #for mote in motes.values() :
        #    log.debug(str(mote))

        # parse arguments
        for entry in args:
            try :
                platform,kernel,shortaddr,dir,id,logfile,henid,userid = entry
                log.debug("""install:
  platform =   %s
  kernel =     %s
  short addr = %s
  bin dir =    %s
  mote id =    %s
  log file =   %s
  hen id =     %s 
  user id =    %s""" % (platform, str(kernel), str(shortaddr), dir, id, logfile, henid, userid))
                os = self.__moteOS[platform]
                mote = motes[id]
                image = MoteImage(dir,shortaddr,kernel)
                installs.append([henid,os,mote,image,logfile])
            except ValueError:
                prot.sendReply(422,seq,"error parsing arguments: %s" % str(entry))
            except KeyError:
                prot.sendReply(422,seq,"error addressing mote%s: disconnected?" % shortaddr)

        # MUST ADD:
        # try to ensure that calls will succeed
        # (ie: checkrequirements method on mote object)
        # XXX: this has sort of been done in 'hm'...
    
        # install software requested
        for i in installs:
            try :
                henid,os,mote,image,logfile = i
                mote.install(os,image)
                mote.username = userid
                if logfile : 
                    mote.log(os, logfile)
                #log.debug("install: os=%s node=%s dir=%s log=%s" % (os.getname(),henid,image.dir,str(logfile)))
                log.debug("installation success: %s" % henid)
                prot.sendReply(200,seq,"installation complete on %s" % henid)
                #prot.sendReply(200,seq,"message two...")
                #prot.sendReply(200,seq,"message three...")
            except MoteInstallError, e:
                error = str(e)
                error = error.split('\n')
                ret = ""
                for line in error :
                    ret += ("\t%s\n" % line)
                log.error("install failed: %s %s" % (henid,ret))
                prot.sendReply(422,seq,"installation failed on %s: \n%s" % (henid,ret))
            except LogError, e:
                log.error("log failed: %s %s" % (henid,str(e)))
                prot.sendReply(422,seq,"logging failed on %s: %s" % (henid,str(e)))
    
    def logToFile(self,prot,seq,ln,payload):
        # payload format = [(start|stop), mote id, hen id, log file]+
        payload = pickle.loads(payload)
        motes = self.__motelist.getmotes()

        for request in payload:
            try :
                logaction,moteid,henid,logfile = request
                log.debug("""log:
  action =    %s
  mote id =   %s
  hen id =    %s
  log file =  %s """ % (logaction,moteid,henid,logfile))
            except ValueError:
                prot.sendReply(422,seq,"error parsing arguments: %s" % str(request))

            if not motes.has_key(moteid) :
                prot.sendReply(422,seq,"%s not present on %s" % (henid, socket.gethostname()))
                continue

            os = motes[moteid].currentos()
            if os == None :
                prot.sendReply(422,seq,"nothing installed on %s, not starting log" % henid)
                continue

            try :
                motes[moteid].log(os,logfile,action=logaction)
                log.debug("log %s success: %s" % (logaction,henid))
                prot.sendReply(200,seq,"logging %sed on %s" % (logaction, henid))
            except LogError, e:
                log.error("log failed: %s %s" % (henid,str(e)))
                prot.sendReply(422,seq,"logging failed on %s: %s" % (henid,str(e)))

    def history(self,prot,seq,ln,payload): 
        motes = self.__motelist.getmotes()
        result = []
        for m in motes:
            img = motes[m].currentimage()
            user = motes[m].currentuser()
            if img != None : 
                imgname = img.dir[img.dir.rfind('/')+1 :]
            else :   
                imgname = "none"
            if user == None :
                user = "none"
            result.append((m, imgname, user))

        log.debug("history: " + str(result))
        prot.sendReply(200,seq,pickle.dumps(result))

    def motelist(self,prot,seq,ln,payload):
        motes = self.__motelist.getmotes()
        result = []
        # motes is a dictionary
        # keyed by the mote id
        for m in motes:
            result.append(m)

        prot.sendReply(200,seq,pickle.dumps(result))
  
    def stopDaemon(self,prot,seq,ln,payload):
        """\brief Stops the daemon and all threads
        This method will first stop any more incoming queries, then wait for
        any update tasks to complete, before stopping itself.
        """
        log.info("stopDaemon called.")
        prot.sendReply(200, seq, "Accepted stop request.")
        log.debug("Sending stopDaemon() response")
        self.acceptConnections(False)
        log.info("Stopping ComputerDaemon (self)")
        self.stop()

class MoteDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    __bind_addr = "0.0.0.0" #DaemonLocations.computerDaemon[0]
    __port = DaemonLocations.moteDaemon[1] #computerDaemon[1]
    __sockd = None
    __computercontrol = None

    def __init__(self, doFork):
        Daemonizer.__init__(self, doFork)

    def run(self):
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        self.__sockd.settimeout(2) # 2 second timeouts
        log.debug("Creating MoteDaemon")
        self.__computercontrol = MoteControl()
        log.info("Starting MoteDaemon")
        self.__computercontrol.start()
        while self.__computercontrol.isAlive():
            if self.__computercontrol.acceptingConnections():
                # allow timeout of accept() to avoid blocking a shutdown
                try:
                    (s,a) = self.__sockd.accept()
                    log.debug("New connection established from " + str(a))
                    self.__computercontrol.addSocket(s)
                except:
                    pass
            else:
                log.warning(\
                    "MoteDaemon still alive, but not accepting connections")
                time.sleep(2)
        log.debug("Closing socket.")
        self.__sockd.shutdown(socket.SHUT_RDWR)
        self.__sockd.close()
        while threading.activeCount() > 1:
            cThreads = threading.enumerate()
            log.warning("Waiting on " + str(threading.activeCount()) + \
                    " active threads...")
            time.sleep(2)
        log.info("MoteDaemon Finished.")
        # Now everything is dead, we can exit.
        sys.exit(0)

def main():
    """\brief Creates, configures and runs the main daemon
        TODO: Move config variables to main HEN config file.
    """
    ROOTDIR = '/var/'
    WORKDIR = ROOTDIR+'tmp/'
    PIDDIR  = ROOTDIR+'run/'
    LOGDIR =  ROOTDIR+'log/'
    #LOGFILE = 'motedaemon_%s.log' % socket.gethostname()
    #PIDFILE = 'motedaemon_%s.pid' % socket.gethostname()
    LOGFILE = 'motedaemon.log'
    PIDFILE = 'motedaemon.pid'
    GID = 3000 # hen
    UID = 0 # root
    #GID = 1000
    #UID = 1000
    moted = MoteDaemon(True)
    moted.setWorkingDir(WORKDIR)
    moted.setPIDDir(PIDDIR)
    moted.setLogDir(LOGDIR)
    moted.setLogFile(LOGFILE)
    moted.setPidFile(PIDFILE)
    moted.setUid(UID)
    moted.setGid(GID)
    moted.start()

if __name__ == "__main__":
    main()

