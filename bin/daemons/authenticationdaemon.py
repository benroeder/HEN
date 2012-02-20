#!/usr/local/bin/python
import sys
sys.path.append("/usr/local/hen/lib")

import socket, sys, pickle, random, datetime, logging, time
from OpenSSL import SSL

from daemonizer import Daemonizer
from daemon import Daemon
from auxiliary.daemonlocations import DaemonLocations
from auxiliary.daemonstatus import DaemonStatus
from auxiliary.protocol import Protocol
from auxiliary.ldapclient import LDAPClient

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

class LoggedInUser:

    def __init__(self, username=None, loggedInID=None, email=None, \
                   loginDate=None, groups=None):
        self.__username = username
        self.__loggedInID = loggedInID
        self.__email = email
        self.__loginDate = loginDate
        self.__groups = groups

    def getUsername(self):
        return self.__username

    def getLoggedInID(self):
        return self.__loggedInID

    def getEmail(self):
        return self.__email

    def getLoginDate(self):
        return self.__loginDate

    def getGroups(self):
        return self.__groups

    def setUsername(self, username):
        self.__username = username

    def setLoggedInID(self, loggedInID):
        self.__loggedInID = loggedInID

    def setEmail(self, email):
        self.__email = email

    def setLoginDate(self, loginDate):
        self.__loginDate = loginDate

    def setGroups(self, groups):
        self.__groups = groups

class AuthenticationHandler(Daemon):

    def __init__(self, useSSL=True):

        Daemon.__init__(self, useSSL)

        self.__MIN_ID = 100000
        self.__MAX_ID = 100000000
        self.__SESSION_TIMEOUT_HOURS = 48

        self.__loggedInUsers = {}
        self.__reverseLoggedInUsers = {}
        self.__userProtocols = {}

        self.__systemProtocol = Protocol(None)
        self.__controlProtocol = Protocol(None)

        try:
            self.__systemProtocol.open(DaemonLocations.systemDaemon[0], DaemonLocations.systemDaemon[1])
        except:
            print "warning, could not connect to system daemon"
        try:
            self.__controlProtocol.open(DaemonLocations.controlDaemon[0], DaemonLocations.controlDaemon[1])
        except:
            print "warning, could not connect to control daemon"
        
        self.registerMethodHandler("login", self.login)
        self.registerMethodHandler("logout", self.logout)
        self.registerMethodHandler("system", self.systemOperation)
        self.registerMethodHandler("control", self.controlOperation)

        self.__consoleOperationReply = None
        self.__controlOperationReply = None        
        self.__systemOperationReply = None
        
        self.__ldapClient = LDAPClient("ldap://henldap:389")

    def login(self,prot,seq,ln,payload):
        (username, password) = pickle.loads(payload)
        validLogin = self.__ldapClient.authenticate(username, password)
        groups = None
        if (validLogin):
            ldapInfo =  self.__ldapClient.getUserInfoByLogin(username)
            groups = ldapInfo.getGroups()
            email = ldapInfo.getEmail()
            loggedInID = random.randint(self.__MIN_ID, self.__MAX_ID)
            loginDate = datetime.datetime.now()
            loggedInUser =  LoggedInUser(username, loggedInID, email, \
                                         loginDate, groups)
            self.__loggedInUsers[loggedInID] = loggedInUser
            self.__reverseLoggedInUsers[username] = loggedInID
            prot.sendReply(200, seq, str(loggedInID))
        else:
            prot.sendReply(421, seq, "")
        
    def logout(self,prot,seq,ln,payload):
        loggedInID = int(pickle.loads(payload))
        if (self.__loggedInUsers.has_key(loggedInID)):
            del self.__loggedInUsers[loggedInID]

        if (self.__reverseLoggedInUsers.has_key(loggedInID)):
            del self.__reverseLoggedInUsers[loggedInID]            
        
        if (self.__userProtocols.has_key(loggedInID)):
            del self.__userProtocols[loggedInID]
            
        prot.sendReply(200,seq,"")

    def systemOperation(self,prot,seq,ln,payload):
        (loggedInID, operation, parameters) = pickle.loads(payload)        
        if (not self.__isLoggedIn(loggedInID, prot, seq)):
            return

        username = self.__loggedInUsers[loggedInID].getUsername()
        groups = self.__loggedInUsers[loggedInID].getGroups()
        
	result = self.__systemProtocol.doSynchronousCall(operation, \
                                      pickle.dumps((username, groups, parameters)))

	resID = len(result)-1
	if resID<0:
		prot.sendReply(500,seq,"Got 0 result from systemdaemon!")
		return
	else:
		prot.sendReply(result[resID][0],seq,result[resID][2])
       
        
    def controlOperation(self,prot,seq,ln,payload):
        (loggedInID, operation, parameters) = pickle.loads(payload)
        print loggedInID, operation, parameters
        
        # Special console case
        if ((operation == "console") or (operation == "console_output")):
            self.__console(prot,seq,ln,payload)
            return
        
        if (not self.__isLoggedIn(loggedInID, prot, seq)):
            return

        username = self.__loggedInUsers[loggedInID].getUsername()
        groups = self.__loggedInUsers[loggedInID].getGroups()
        
	result = self.__controlProtocol.doSynchronousCall(operation, \
                                      pickle.dumps((username, groups, parameters))) 
	resID = len(result)-1
	#print "got result",result
	if resID<0:
		prot.sendReply(500,seq,"Got 0 result from controldaemon!")
		return
	else:
		prot.sendReply(result[resID][0],seq,result[resID][2])

    def __console(self,prot,seq,ln,payload):
        (loggedInID, operation, parameters) = pickle.loads(payload)
        
        # Request from hm client
        if (operation == "console"):
            if (not self.__isLoggedIn(loggedInID, prot, seq)):
                return

            username = self.__loggedInUsers[loggedInID].getUsername()
            groups = self.__loggedInUsers[loggedInID].getGroups()
            action = parameters[0]
            
            # Record client protocol so we can later reply to it            
            if (not self.__userProtocols.has_key(loggedInID)):
                self.__userProtocols[loggedInID] = prot

            self.__controlProtocol.sendRequest("console", \
                                               pickle.dumps((username, groups, parameters)), \
                                               self.__consoleOperationReplyHandler)
            if (action == "open" or action == "close"):
                self.__controlProtocol.readAndProcess()
                prot.sendReply(self.__consoleOperationReply[0], seq, self.__consoleOperationReply[3])
            
        # Request from control daemon, forward to console client
        elif (operation == "console_output"):
            (username, operation, parameters) = pickle.loads(payload)
            consoleOutput = parameters[0]
            loggedInID = self.__reverseLoggedInUsers[username]
            payload = pickle.dumps((200, consoleOutput))
            self.__userProtocols[loggedInID].sendRequest("console", payload, self.__consoleOperationReplyHandler)
        else:
            print "unknown console operation received"
            return
        
        prot.sendRequest("console", self.__consoleOperationReply[3], self.__consoleOperationReplyHandler)    
            
    def __consoleOperationReplyHandler(self, code, seq, sz, payload):
        self.__consoleOperationReply = (code, seq, sz, payload)
        
    def __isLoggedIn(self, loggedInID, prot, seq):
        if ((not self.__loggedInUsers.has_key(loggedInID)) or \
            self.__hasSessionExpired(loggedInID)):
            print "not logged in"
            prot.sendReply(400,seq,"")
            return False
        return True
    
    def __hasSessionExpired(self, loggedInID):
        loginDate = self.__loggedInUsers[loggedInID].getLoginDate()
        now = datetime.datetime.now()

        difference = now - loginDate
        minutes, seconds = divmod(difference.seconds, 60)
        hours, minutes = divmod(minutes, 60)

        sessionTime = hours + (24 * difference.days)
        if (sessionTime > self.__SESSION_TIMEOUT_HOURS):
            return True

        return False
    
#################################################################
# MAIN EXECUTION
#################################################################
class AuthenticationDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    __bind_addr = DaemonLocations.authenticationDaemon[0]
    __port = DaemonLocations.authenticationDaemon[1]
    __sockd = None
    __auth_handler = None
    
    def __init__(self, doFork):
        Daemonizer.__init__(self, doFork)
    
    def run(self):
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        fpem = "/usr/local/hen/bin/daemons/server.pem"
        ctx.use_privatekey_file(fpem)
        ctx.use_certificate_file(fpem)
        self.__sockd = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0))
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        #self.__sockd.settimeout(2) # 2 second timeouts
        log.debug("Creating Authentication Handler")
        self.__auth_handler = AuthenticationHandler()
        log.info("Starting Authentication Handler")
        self.__auth_handler.start()
        while self.__auth_handler.isAlive():
            if self.__auth_handler.acceptingConnections():
                # allow timeout of accept() to avoid blocking a shutdown
                try:
                    (s,a) = self.__sockd.accept()
                    log.debug("New connection established from " + str(a))
                    print "New connection established from " + str(a)
                    self.__auth_handler.addSocket(s)
                except:
                    pass
            else:
                log.warning("AuthenticationHandler still alive, but not " + \
                          "accepting connections")
                time.sleep(2)
        log.debug("Closing socket.")
        self.__sockd.shutdown(socket.SHUT_RDWR)        
        self.__sockd.close()
        while threading.activeCount() > 1:
            cThreads = threading.enumerate()
            log.warning("Waiting on " + str(threading.activeCount()) + \
                      " active threads...")
            time.sleep(2)
        log.info("AuthenticationDaemon Finished.")
        # Now everything is dead, we can exit.  
        sys.exit(0)
        
def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    WORKDIR = '/var/hen/authenticationdaemon'
    PIDDIR = '/var/run/hen'
    LOGDIR = '/var/log/hen/authenticationdaemon'
    LOGFILE = 'authenticationdaemon.log'
    PIDFILE = 'authenticationdaemon.pid'
    GID = 17477 # schooley
    UID = 17477 # schooley
    authenticationd = AuthenticationDaemon(False)
    authenticationd.setWorkingDir(WORKDIR)
    authenticationd.setPIDDir(PIDDIR)
    authenticationd.setLogDir(LOGDIR)
    authenticationd.setLogFile(LOGFILE)
    authenticationd.setPidFile(PIDFILE)
    authenticationd.setUid(UID)
    authenticationd.setGid(GID)
    authenticationd.start()
        
if __name__ == "__main__":
    main()
