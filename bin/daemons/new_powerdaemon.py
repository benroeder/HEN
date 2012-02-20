#!/usr/bin/env python
###############################################################################################################
#
# reservationdaemon.py: Handles all reservations for the HEN testbed. Generally users are allowed to
#                       make reservations for a period of 2 weeks (this is configurable) unless they
#                       have special permissions in the reservationrights.xml file. Users are notified
#                       via email 7, 2 and 1 (also configurable) day before a reservation expires (this
#                       process runs when the daemon starts and every hour thereafter).
#                       Email is also generated if a reservation is removed from the system because it
#                       has expired. The database is checked for expired reservations when (1) the daemon
#                       and (2) before a new reservation is made.
#
# MISC FILES
# --------------------------------------------------------------------
# /var/log/hen/reservationdaemon/reservationdaemon.log
# /var/run/hen/reservationdaemon.pid
# /usr/local/hen/etc/rc.d/reservationdaemon.sh (use this to start and stop the daemon)
# 
# XML FILES (databases)
# --------------------------------------------------------------------
# reservations.xml           Holds all information about reservations on the testbed
# reservationrights.xml      Holds extended priviledges for users (longer reservation allowances)
# notifications.xml          Used by the notification thread to keep track of expiration notices sent
#
# CLASSES
# --------------------------------------------------------------------
# ReservationRight           Holds information about an extended reservation right (beyond the default)
# ReservationEntry           Holds information about a particular reservation
# ReservationExpiryNotifier  Thread class used to notify users when reservations are about to expire
# ReservationDBParser        Parses and writes to all databases related to the reservation daemon
# ReservationDBManager       Manages reservation operations
# ReservationControl         Listens and carries out requests from clients
# ReservationDaemon          The daemon process
#
###############################################################################################################

# TODO
# specify that a machine when next released is redetected
# enable the regular cleaning and switching off of machines not allocated
# integrate reservations with power control
# clean up after a release, rebuild pxelinux.cfg/default too, turn off power.
# send file listing and contents of startup.sh and pxelinux.cfg/default in automatic clean up email
# modify hm power so that if node does not belong to user a confirmation message is shown (same for hm console)

import sys, os, time
try:
	libpath = os.environ['HENLIB']
	sys.path.append(libpath)
except:
	sys.path.append("/usr/local/hen/lib")

from xml.dom import minidom
from xml.dom.minidom import Element
from xml.dom.minidom import Node
from daemonizer import Daemonizer
from daemon import Daemon
import logging, threading, socket, pickle, datetime
from henmanager import HenManager
from auxiliary.timer import GracefulTimer
from auxiliary.daemonlocations import DaemonLocations
from auxiliary.smtpclient import SMTPClient
import commands, re, shutil
from datetime import timedelta

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

class PowerEntry:
    def __init__(self, username, device, device_state):
        self.__username = username
        self.__device = device
	self.__device_state = device_state

    def getUsername(self):
        return self.__username

    def getDevice(self):
        return self.__device

    def getDeviceState(self):
        return self.__device_state

    def getInfoStr(self):
        return "Device : " + str(self.getDevice()) + " - " + \
               str(self.getDeviceState()) + " " + \
               "(username " + self.getUsername() + ")"
        
    def __str__(self):
        return str(self.getDevice()) + "," + \
               str(self.getDeviceState()) + "," + \
	       str(self.getUsername())

class REMOVEReservationExpiryNotifier(threading.Thread):
    def __init__(self, daemonEmail, smtpServerName, filename, rightsFilename, notificationsFilename, dbsRoot, debug):
        self.__filename = filename
        self.__rightsFilename = rightsFilename
        self.__notificationsFilename = notificationsFilename
        self.__daemonEmail = daemonEmail
        self.__smtpServerName = smtpServerName
        self.__reservations = {}
        self.__sleepTime = 3600
        self.__parser = ReservationDBParser(filename, rightsFilename, notificationsFilename,dbsRoot)
        self.__notifications = {}
        self.__notificationDays = [1, 2, 7]
        self.__initNotifications()
        self.__debug = debug
        self.mytime = datetime.date.today()
        
        if not self.__debug:
            threading.Thread.__init__(self)

    def step(self):
        self.run()
        
    def run(self):
        # initally sleep to enable other events to occur
        if not self.__debug:
            time.sleep(30)
        running = 1
        while(running):
            if (self.__reparseDB() == 0):
                self.__sendEarlyExpiryNotifications()
            log.info("Expiry notifer: sent notifications, going to sleep for " + str(self.__sleepTime) + " seconds")
            if not self.__debug:
                time.sleep(self.__sleepTime)
            if self.__debug:
                running = 0
        log.info("Expiry notifer: finished.")

    def __initNotifications(self):
        (result, xmldoc) = self.__parser.openDB(self.__notificationsFilename)
        if (result < 0):
            log.info("Expiry notifier: error while opening notifications database!")
            return -1        
        elif (result == 1):
            log.info("Expiry notifier: warning, no notifications database file found")
            return 1
        else:
            (result, self.__notifications) = self.__parser.parseNotificationsDB(xmldoc)
            # ignore -1, this means that there are no 'notifications' tags
            if (result < 0 and result != -1):
                log.info("Expiry notifier: error while parsing notifications database!")
                return -1

        return 0
        
    def __reparseDB(self):
        (result, xmldoc) = self.__parser.openDB(self.__filename)
        if (result < 0):
            log.info("Expiry notifier: error while opening database!")
            return -1        
        elif (result == 1):
            log.info("Expiry notifier: warning, no database file found")
            return 1
        else:
            (result, self.__reservations) = self.__parser.parseDB(xmldoc)
            # ignore -1, this means that there are no 'reservations' tags
            if (result < 0 and result != -1):
                log.info("Expiry notifier: error while parsing database!")
                return -1
        return 0

    def testSendEmailEarlyNotification(self, reservation, notificationDay):
        self.__sendEmailEarlyNotification(reservation, notificationDay)
    
    def __sendEmailEarlyNotification(self, reservation, notificationDay):
        subject = "Your reservation (id = " + str(reservation.getReservationID()) + \
                  ") expires in " + str(notificationDay) + " days"
        body = "The reservation you made will expire in " + str(notificationDay) + " days. " + \
               "Please renew it by logging on to hen.cs.ucl.ac.uk and running the command 'hm reservation'. " + \
               "Failure to do so will result in its automatic deletion from the testbed."
        if not self.__debug:
            log.info("Sent email to "+str(reservation.getEmail())+" via "+str(self.__smtpServerName)+" at "+str(datetime.datetime.now()))
            smtpClient = SMTPClient(self.__smtpServerName)
            smtpClient.sendEmail(reservation.getEmail(), self.__daemonEmail, subject, body)
            smtpClient.close()
        else:
            print "would send email."
            print "to :"+str(reservation.getEmail())
            print "subject :"+subject
            print "via :"+self.__smtpServerName
            print "body :"+body

    def __getCurrentDate(self):
        if not self.__debug:
            return datetime.date.today()
        else:
            return self.mytime
            
    def __sendEarlyExpiryNotifications(self):
        currentDate = self.__getCurrentDate()
        
        for username in self.__reservations.keys():
            userReservations = self.__reservations[username]
            for userReservation in userReservations:
                endDate = userReservation.getEndDate()
                # Loop ensures that notice includes shortest expiry date
                for notificationDay in self.__notificationDays:
                    if (endDate < currentDate + timedelta(days=notificationDay)):
                        if (not self.__alreadySent(userReservation.getReservationID(), notificationDay)):
                            log.info("Expiry notifier: sent mail for:: " + str(userReservation) + \
                                  " (expires in " + str(notificationDay) + " days)")
                            self.__sendEmailEarlyNotification(userReservation, notificationDay)
                            self.__notifications[int(userReservation.getReservationID())] = notificationDay
                            self.__parser.writeNotificationsDBToDisk(self.__notifications)
                        break

    def __alreadySent(self, reservationID, notificationDay):
        reservationID = int(reservationID)
        if (not self.__notifications.has_key(reservationID)):
            return False
        
        sentDay = self.__notifications[reservationID]
        if (int(sentDay) <= int(notificationDay)):
            return True
        return False

class PowerDBParser:
    def __init__(self, filename=None, dbsRoot=None):
        self.__filename = filename
        self.__dbsRoot = dbsRoot
                
    def openDB(self, filename):
        try:
            return (0, minidom.parse(filename))
        except Exception, e:
            # File missing
            if (e.errno == 2):
                return (1, None)
            return (-1, None)
        
    def parseDB(self, xmldoc):
        reservations = {}
        rootXML = xmldoc.getElementsByTagName("reservations")[0]
        reservationsXML = rootXML.getElementsByTagName("reservation")
        if (not reservationsXML):
            return (-1, reservations)

        for reservationXML in reservationsXML:
            reservationID = self.__getLabel("id", reservationXML)
            username = self.__getLabel("username", reservationXML)            
            email = self.__getLabel("email", reservationXML)
            endDate = self.__convertToDate(self.__getLabel("enddate", reservationXML))
            
            devices = []
            devicesXML = reservationXML.getElementsByTagName("device")
            if (devicesXML):
                for deviceXML in devicesXML:
                    deviceID = self.__getLabel("id", deviceXML)
                    devices.append(deviceID)

            if (not reservations.has_key(username)):
                reservations[username] = []
            reservations[username].append(ReservationEntry(username, email, devices, endDate, reservationID))

        return (0, reservations)

    def parseRightsDB(self, xmldoc):
        rights = {}
        rootXML = xmldoc.getElementsByTagName("rights")[0]
        rightsXML = rootXML.getElementsByTagName("right")
        if (not rightsXML):
            return (-1, rights)

        for rightXML in rightsXML:
            rightID = self.__getLabel("id", rightXML)
            username = self.__getLabel("username", rightXML)            
            email = self.__getLabel("email", rightXML)
            maxWeeks = self.__getLabel("maxweeks", rightXML)
            
            devices = []
            devicesXML = rightXML.getElementsByTagName("device")
            if (devicesXML):
                for deviceXML in devicesXML:
                    deviceID = self.__getLabel("id", deviceXML)
                    devices.append(deviceID)

            if (not rights.has_key(username)):
                rights[username] = []
            rights[username].append(ReservationRight(username, email, devices, maxWeeks, rightID))

        return (0, rights)

    def parseNotificationsDB(self, xmldoc):
        notifications = {}
        rootXML = xmldoc.getElementsByTagName("notifications")[0]
        notificationsXML = rootXML.getElementsByTagName("notification")
        if (not notificationsXML):
            return (-1, notifications)

        for notificationXML in notificationsXML:
            reservationID = int(self.__getLabel("reservationid", notificationXML))
            lastNotified = self.__getLabel("lastnotified", notificationXML)
            notifications[reservationID] = lastNotified

        return (0, notifications)
    
    def writeDBToDisk(self, reservations):
        string = '<reservations>\n'
        for key in reservations.keys():
            userReservations = reservations[key]
            for userReservation in userReservations:
                string += '\t<reservation ' + \
                          'id="' + str(userReservation.getReservationID()) + '" ' + \
                          'username="' + str(userReservation.getUsername()) + '" ' + \
                          'email="' + str(userReservation.getEmail()) + '" ' + \
                          'enddate="' + str(userReservation.getDDMMYYYYDate()) + '">\n'
                for device in userReservation.getDevices():
                    string += '\t\t<device id="' + str(device) + '" />\n'
                string += '\t</reservation>\n'
        string += '</reservations>\n'

        # First write to a temp file. This is done to prevent corrupting the database file
        # if the operation fails halfway through
        try:
            theFile = open(self.__dbsRoot + "reservations-temp.xml", "w")
            theFile.write(string)
            theFile.close()
        except Exception, e:
            log.info("error while writing to temp db file")
            log.info(str(e))
            return -1

        shutil.move(self.__dbsRoot + "reservations-temp.xml", self.__filename)
        return 0

    def writeNotificationsDBToDisk(self, notifications):
        string = '<notifications>\n'
        for reservationID in notifications.keys():
            lastNotified = notifications[reservationID]
            string += '\t<notification ' + \
                      'reservationid="' + str(reservationID) + '" ' + \
                      'lastnotified="' + str(lastNotified) + '" />\n'
        string += '</notifications>\n'            

        # First write to a temp file. This is done to prevent corrupting the database file
        # if the operation fails halfway through
        try:
            theFile = open(self.__dbsRoot + "notifications-temp.xml", "w")
            theFile.write(string)
            theFile.close()
        except Exception, e:
            log.info("error while writing to temp notifications db file to root "+str(self.__dbsRoot))
            log.info(str(e))            
            return -1
        log.info("trying to move notifications file")
        shutil.move(self.__dbsRoot + "notifications-temp.xml", self.__notificationsFilename)
        return 0
    def __getLabel(self, key, xmlObject):
        if xmlObject.attributes.has_key(key):
            return xmlObject.attributes[key].value
        else:
            return None

    def __convertToDate(self, string):
        dates = string.split("/")
        return datetime.date(int(dates[2]), int(dates[1]), int(dates[0]))


# The main data structure is a dictionary whose keys are user names, and whose
# values are lists of ReservationEntry objects
class PowerDBManager:
    def __init__(self, filename, dbsRoot,debug=False):
        self.__daemonEMail = "hend@cs.ucl.ac.uk"        
        self.__filename = filename
        self.__dbsRoot = dbsRoot
        self.__devices = {}
	self.__unpowered_devices = {}
	self.__power_devices = {}
        self.__rights = {}
        self.__nextID = 0
        self.__xmldoc = None
        self.__rightsXmldoc = None
	if debug:
	   	try:
			config = os.environ['HENCONFIG']
			self.__henManager = HenManager(config)		
		except KeyError, e:
			log.info("Falling back to defaults for config file")
			self.__henManager = HenManager()
	else:
		self.__henManager = HenManager()
        self.__symlinksRoot = "/export/machines/"
        self.__smtpServerName = "smtp.cs.ucl.ac.uk"
        self.__parser = PowerDBParser(filename, self.__dbsRoot)
        #self.__notifier = None
        self.__debug = debug
        self.mytime = datetime.date.today()
	self.loadHenDB()
	
    def loadHenDB(self):
	# load all devices
	self.__device_types = self.__henManager.getNodes("all").keys()
        for device_type in self.__device_types:
	    for device in self.__henManager.getNodes(device_type).values():
	    	try:
			if device.getPowerNodes() == None:
				self.__unpowered_devices[str(device.getNodeID())] = device
			else:
				self.__devices[str(device.getNodeID())] = device
		except:
			self.__unpowered_devices[str(device.getNodeID())] = device
		try:
			if device_type == "powerswitch" or device_type == "serviceprocessor":
				self.__power_devices[(str(device.getNodeID()))] = device
				#print "powerdevice : "+str(device.getNodeID())
			elif device_type == "switch":
				if (device.getSingleAttribute("poe") == "yes"):
					self.__power_devices[(str(device.getNodeID()))] = device
					#print "powerdevice : "+str(device.getNodeID())
			else:
				pass
		except:
			pass
					
    # used to test email sending
    #def getNotifier(self):
    #    return self.__notifier

    def reloadHenDB(self):
        self.__henManager = HenManager()
	self.__device_types = self.__henManager.getNodes("all").keys()
        self.__devices = {}
	self.__unpowered_devices = {}
	self.loadHenDB()
	return 0
    
    def startDB(self):
        # First parse reservations database
        (result, self.__xmldoc) = self.__parser.openDB(self.__filename)
        if (result < 0):
            log.info("error while opening database!")
            return -1
        elif (result == 1):
            log.info("warning: no database file found (one will be created when a reservation is made)")
            self.__nextID = 1
        else:
            (result, self.__reservations) = self.__parser.parseDB(self.__xmldoc)
            # ignore -1, this means that there are no 'reservations' tags
            if (result < 0 and result != -1):
                log.info("error while parsing database!")
                return -1
            else:
                self.__nextID = self.__findHighestID() + 1

        # Now parse reservation rights database
        #(result, self.__rightsXmldoc) = self.__parser.openDB(self.__rightsFilename)
        #if (result < 0 or result == 1):
        #    log.info("error while opening reservation rights database!")
        #    return -1

        #(result, self.__rights) = self.__parser.parseRightsDB(self.__rightsXmldoc)
        #if (result < 0):
        #    log.info("error while parsing rights database!")
        #    return -1

        return 0

    def release(self, username, reservationID):
        if (not self.__reservations.has_key(username)):
            return "unknown user"

        released = False
        reservationsBackup = self.__reservations
        userReservations = self.__reservations[username]
        for userReservation in userReservations:
            if (str(userReservation.getReservationID()) == str(reservationID)):
                userReservations.remove(userReservation)
                released = True
                break

        if (not released):
            return "reservation id not found"
        
        if (self.__parser.writeDBToDisk(self.__reservations) < 0):
            self.__reservations = reservationsBackup
            return "error while writing to database, release failed"            

        self.__nextID = self.__findHighestID() + 1
        return "reservation released"

    def __powerAction(self,targetInstance,action,port):
	if action == "poweron" or action == "softpoweron" :
		return targetInstance.poweron(port)
	elif action == "poweroff" or action == "softpoweroff":
		return targetInstance.poweroff(port)
	elif action == "restart" or action == "softrestart" :
		return targetInstance.restart(port)
	elif action == "status":
		return targetInstance.status(port)
	elif action == "startup":
		return targetInstance.startup(port)
	elif action == "info":
		return (0,str(targetInstance.getNodeID())+" "+str(port))
	return (-1, "Unknown action %s" % str(action))
								    
    def powerinfo(self,action, username, mode, devices):
        currentDate = self.__getCurrentDate() #datetime.date.today()
        unknown_devices = []
	uncontrolled_devices = []
	targets = {} # list of (targetid,port,error state,value)
	#print "mode : "+str(mode)
	actions = []
	if action == "fullinfo":
		actions.append('status')
		actions.append('info')
		actions.append('startup')
	else:
		actions.append('status')
	for device in devices:
        	if (not (self.__devices.has_key(str(device)) or self.__unpowered_devices.has_key(str(device)))):
            	   unknown_devices.append(device)
		   #print "unknown device "+str(device)
		elif (not self.__devices.has_key(device)):
		   uncontrolled_devices.append(device)
		   #print "uncontrolled device "+str(device)
		else:
			try:
				for (powerNodeID,PowerNodePort) in self.__devices[device].getPowerNodes():
					if powerNodeID and self.__power_devices.has_key(powerNodeID):
						if not targets.has_key(device):
							targets[device] = []
						targets[device].append((self.__power_devices[str(powerNodeID)],str(PowerNodePort),None,[],[]))
			except Exception,e :
				#print str(e)
				return (-1, "Could not find power switch for node %s." % str(device))

	# find out if device has any more devices to power
	# this needs additions to correctly support peripherals
	# loop through peripherals for a device
	# check wether this device has control of the peripheral
	# if so add it to the targets list.
	
	for d in targets:
		for i in range(0,len(targets[d])):
			val = []
			res = []
			for a in range(0,len(actions)):
				
				targetInstance = self.__henManager.getNodeInstance(targets[d][i][0])
				if targetInstance != None:
					(v,r) =  (-1, "Can't create powernode instance.")
					try:
						(v,r) = self.__powerAction(targetInstance,actions[a],targets[d][i][1])
					except Exception, e:
						r = "Exception thrown: %s" % str(e)
						v = -1
					val.append(v)
					res.append(r)
			targets[d][i] = (targets[d][i][0],targets[d][i][1],val,res)

	message = "known devices:"
	for d in targets:
		message += "\n"
		message += str(d) + " ->"
		for a in range(0,len(actions)):
			message += " " + str(actions[a]) + " : "
			for i in range(0, len(targets[d])):
				
				message += str(targets[d][i][3][a])
				if i != (len(targets[d])-1):
					message += ","
	if len(unknown_devices) > 0:
		message += "\nunknown devices:\n"
		for d in unknown_devices:
			message += d+"\n"
        return message

    def poweraction(self, action, username, mode, devices):
        currentDate = self.__getCurrentDate() #datetime.date.today()
        unknown_devices = []
	uncontrolled_devices = []
	targets = {} # list of (targetid,port,error state,value)
	print "mode : "+str(mode)
	for device in devices:
		
        	if (not (self.__devices.has_key(str(device)) or self.__unpowered_devices.has_key(str(device)))):
            	   unknown_devices.append(device)
		   print "unknown device "+str(device)
		elif (not self.__devices.has_key(device)):
		   uncontrolled_devices.append(device)
		   print "uncontrolled device "+str(device)
		else:
			print "turn on "+str(device)
			try:
				for (powerNodeID,PowerNodePort) in self.__devices[device].getPowerNodes():
					if powerNodeID and self.__power_devices.has_key(powerNodeID):
						if not targets.has_key(device):
							targets[device] = []
						targets[device].append((self.__power_devices[str(powerNodeID)],str(PowerNodePort),None,None,str(device)))
			except Exception,e :
				#print str(e)
				return (-1, "Could not find power switch for node %s." % str(device))

	# find out if device has any more devices to power
	# this needs additions to correctly support peripherals
	# loop through peripherals for a device
	# check wether this device has control of the peripheral
	# if so add it to the targets list.
	
	for d in targets:
		for i in range(0,len(targets[d])):
			targetInstance = self.__henManager.getNodeInstance(targets[d][i][0])
			if targetInstance != None:
				(val,res) =  (-1, "Can't create powernode instance.")
				try:
					(val,res) = self.__powerAction(targetInstance,action,targets[d][i][1])
				
				except Exception, e:
					res = "Exception thrown: %s" % str(e)
					val = -1
				targets[d][i] = (targets[d][i][0],targets[d][i][1],val,res)

	message = "powered on:"
	for d in targets:
		message += "\n"
		message += str(d) + " : "
		for i in range(0, len(targets[d])):
			message += targets[d][i][3]
			if i != (len(targets[d])-1):
				message += ","
	message += "unknown devices:\n"
	for d in unknown_devices:
		message += d+"\n"
        return message

    def getReservationsInfo(self, username):
        if username == "all":
            info = ""
            for name in self.__reservations:
                for reservation in self.__reservations[name]:
                    info += reservation.getInfoStr() +" "+str(name)+"\n"
            return info
        if (not self.__reservations.has_key(username)):
            return "no info"
        info = ""
        if len(self.__reservations[username]) == 0:
            return "no info"
        for reservation in self.__reservations[username]:
            info += reservation.getInfoStr() + "\n"
        info.rstrip('\n')
        return info
    
    def inUseBy(self, username):
        devices = []
        if (not self.__reservations.has_key(username)):
            return devices
        for reservation in self.__reservations[username]:
            for reservedDevice in reservation.getDevices():
                devices.append(reservedDevice)
        return devices
    
    def getFreeDevices(self):
        allDevices = self.__henManager.getNodes("computer").keys()
        freeDevices = []
        reservedDevices = self.__getReservedDevices()
        for device in allDevices:
            if (device not in reservedDevices):
                freeDevices.append(device)
        return freeDevices

    def cleanExpired(self):
        currentDate = self.__getCurrentDate() #datetime.date.today()
        for username in self.__reservations.keys():
            userReservations = self.__reservations[username]
            for userReservation in userReservations:
                if (userReservation.getEndDate() < currentDate):
                    self.release(username, userReservation.getReservationID())
                    dirListing = self.__listDirectory(userReservation.getDevices())
                    self.__clearSymLinks(userReservation.getDevices())
                    self.__poweroff(userReservation.getDevices())
                    self.__sendEmailExpired(userReservation,dirListing)
                    log.info("cleaned expired reservation: " + str(userReservation))
        return 0
    
    def getOwners(self, devices):
        results = []
        for device in devices:
            owner = self.__getOwner(device)
            results.append((device, owner))
        return results

    def __getCurrentDate(self):
        if not self.__debug:
            return datetime.date.today()
        else :
            return self.mytime
        
    def __getMaxWeeks(self, username, devices):
        if (not self.__rights.has_key(username) or len(devices) == 0):
            return self.__maxNumWeeks

        minRightWeeks = 99999
        foundDevs = []
        rights = self.__rights[username]        
        for device in devices:
            for right in rights:
                if (device in right.getDevices()):
                    foundDevs.append(device)
                    if (right.getMaxWeeks() < minRightWeeks):
                        minRightWeeks = right.getMaxWeeks()

        if (set(devices) == set(foundDevs)):
            return minRightWeeks
        
        return self.__maxNumWeeks

    def __listDirectory(self, devices):
        dirListing = ""
        for device in devices:
            dirListing += str(device)+" :\n"
            dirListing += commands.getoutput('find ' + self.__symlinksRoot + device + ' -print ')
            dirListing += "\n"
        return dirListing
        
    def __clearSymLinks(self, devices):
        for device in devices:
            if not self.__debug:
                os.system("rm " + self.__symlinksRoot + device + "/*")
            else:
                print "would run : rm " + self.__symlinksRoot + device + "/*"

    def __poweroff(self, devices):
        for device in devices:
            if not self.__debug:
                self.__henManager.powerSilent(device, "poweroff")
            else:
                print "would turn off "+str(device)
    
    def __sendEmailExpired(self, reservation,dirListing=None):
        subject = "Your reservation (id = " + str(reservation.getReservationID()) + ") has expired"
        body = "The reservation you had made has expired and has been removed from the system. " + \
               "If you still wish to use the devices you had reserved you will have to create a new " + \
               "reservation by logging on to hen.cs.ucl.ac.uk and running the command 'hm reservation'."
        if dirListing != None:
            body += "The directory listings for your machines were :\n"
            body += dirListing
        if not self.__debug:
            smtpClient = SMTPClient(self.__smtpServerName)
            smtpClient.sendEmail(reservation.getEmail(), self.__daemonEMail, subject, body)
            smtpClient.close()
        else:
            print "would send email."
            print "to :"+str(reservation.getEmail())
            print "subject :"+subject
            print "via :"+self.__smtpServerName
            print "body :"+body
        
    def __findHighestID(self):
        highestID = 0
        for username in self.__reservations.keys():
            userReservations = self.__reservations[username]
            for userReservation in userReservations:        
                if (int(userReservation.getReservationID()) > highestID):
                    highestID = int(userReservation.getReservationID())
        return highestID
    
    def __getNextID(self):
        theID = self.__nextID
        self.__nextID += 1
        return theID
        
    def __isDeviceInUse(self, device):
        return (self.__getOwner(device) != None)
    
    def __getOwner(self, device):
        for username in self.__reservations.keys():
            userReservations = self.__reservations[username]
            for userReservation in userReservations:
                for reservedDevice in userReservation.getDevices():
                    if (reservedDevice == device):
                        return username
        return None
    
    def __getReservedDevices(self):
        reservedDevices = []
        for username in self.__reservations.keys():
            userReservations = self.__reservations[username]
            for userReservation in userReservations:
                for device in userReservation.getDevices():
                    reservedDevices.append(device)
        return reservedDevices

    def __getReservedDevicesByID(self, reservationID):
        for username in self.__reservations.keys():
            userReservations = self.__reservations[username]
            for userReservation in userReservations:
                if (userReservation.getReservationID() == reservationID):
                    return userReservation.getDevices()
        return []
    
    def __printReservations(self):
        for username in self.__reservations.keys():
            userReservations = self.__reservations[username]
            email = userReservations[0].getEmail()
            log.info("\nuser: " + str(username) + "(" + str(email) + ")" + \
                  "\n---------------------------------")
            for userReservation in userReservations:
                log.info(userReservation.getDateDevStr())

    def __printRights(self):
        for username in self.__rights.keys():
            userRights = self.__rights[username]
            email = userRights[0].getEmail()
            log.info("\nuser: " + str(username) + "(" + str(email) + ")" + \
                  "\n---------------------------------")
            for userRight in userRights:
                log.info(userRight.getDebugStr())
                
    def __convertDateToString(self, date):
        return str(date.day) + "/" + str(date.month) + "/" + str(date.year)


class PowerControl(Daemon):
    """\brief Implements basic reservation daemon functionality.
    """
    __version = "Power Daemon v0.1 (simple)"
    
    def __init__(self,debug):
        Daemon.__init__(self)
        self.__debug = debug
        self.mytime = datetime.date.today()

        if self.__debug:
	   try:
		libpath = os.environ['HENPOWERETC']
		etcRoot = "/tmp/daemons/powerdaemon/debug/"
           except:
		etcRoot = "/usr/local/hen/etc/daemons/powerdaemons/debug/"
        else:
            etcRoot = "/usr/local/hen/etc/daemons/powerdaemons/"
        self.__dbManager = PowerDBManager(etcRoot + "state.xml", \
                                                etcRoot, \
                                                self.__debug)
        if (self.__dbManager.startDB() < 0):
            os._exit(1)
        self.__registerMethods()

    def __registerMethods(self):
        self.registerMethodHandler("poweron", self.poweron)
        self.registerMethodHandler("poweroff", self.poweroff)
        self.registerMethodHandler("restart", self.restart)
        self.registerMethodHandler("status", self.status)
        self.registerMethodHandler("fullinfo", self.fullinfo)
	#self.registerMethodHandler("inuseby", self.inuseby)
        #self.registerMethodHandler("notinuse", self.notinuse)
        #self.registerMethodHandler("cleanexpired", self.cleanexpired)
        self.registerMethodHandler("reloadhendb", self.reloadhendb)
        self.registerMethodHandler("show", self.show)
        if self.__debug:
            #self.registerMethodHandler("emailtest", self.emailtest)
            self.registerMethodHandler("reload", self.settime)
            #self.registerMethodHandler("step", self.step)
        
    def __sendReply(self,prot,code,seq,payload):
        if (code == 0):
            code = 200
        else:
            code = 422 # returnCodes[422] = "error executing command"
        prot.sendReply(code, seq, payload)

    def __parse_args(self,args):
	    # add support for location, priority, mode (ipmi etc), all
	    mode = "standard"
	    devices = []
	    if args[0] == "range":
		    print "working out range"
	    #elif args[0] 
	    else:
		    for device in args:
			    devices.append(device)
	    return mode,devices

    def reloadhendb(self,prot,seq,ln,payload):
        result = self.__dbManager.reloadHenDB()
        response = pickle.dumps((result))
        self.__sendReply(prot,"100",seq,response)                
        
    def poweron(self,prot,seq,ln,payload):
        (username, args) = pickle.loads(payload)
	# assume just a list of devices
	mode,devices = self.__parse_args(args)
        result = self.__dbManager.poweraction("poweron",username, mode, devices)
	response = pickle.dumps((result))
        self.__sendReply(prot,"100",seq,response)

    def poweroff(self,prot,seq,ln,payload):
        (username, args) = pickle.loads(payload)
	# assume just a list of devices
	mode,devices = self.__parse_args(args)
        result = self.__dbManager.poweraction("poweroff",username, mode, devices)
	response = pickle.dumps((result))
        self.__sendReply(prot,"100",seq,response)

    def fullinfo(self,prot,seq,ln,payload):
        (username, args) = pickle.loads(payload)
	# assume just a list of devices
	mode,devices = self.__parse_args(args)
        result = self.__dbManager.powerinfo("fullinfo",username, mode, devices)
	#result = "hey earth!"
	response = pickle.dumps((result))
        self.__sendReply(prot,"100",seq,response)

    def status(self,prot,seq,ln,payload):
        (username, args) = pickle.loads(payload)
	# assume just a list of devices
	mode,devices = self.__parse_args(args)
        result = self.__dbManager.poweraction("status",username, mode, devices)
	response = pickle.dumps((result))
        self.__sendReply(prot,"100",seq,response)

    def restart(self,prot,seq,ln,payload):
        (username, args) = pickle.loads(payload)
	# assume just a list of devices
	mode,devices = self.__parse_args(args)
        result = self.__dbManager.poweraction("restart",username, mode, devices)
	response = pickle.dumps((result))
        self.__sendReply(prot,"100",seq,response)

    def show(self,prot,seq,ln,payload):
        username = pickle.loads(payload)
        info = self.__dbManager.getReservationsInfo(username)
        if info == "no info":
            info = str(username) + " has no machines."
        response = pickle.dumps((info))
        self.__sendReply(prot,"100",seq,response)

    def step(self,prot,seq,ln,payload):
        note = self.__dbManager.getNotifier()
        note.step()
        response = pickle.dumps(("ok"))
        self.__sendReply(prot,"100",seq,response)
        
    def settime(self,prot,seq,ln,payload):
        self.mytime = pickle.loads(payload)
        self.__dbManager.mytime = self.mytime
        note = self.__dbManager.getNotifier()
        note.mytime = self.mytime
        response = pickle.dumps(("ok"))
        self.__sendReply(prot,"100",seq,response)
        
    def emailtest(self,prot,seq,ln,payload):
        email,reservation_id = pickle.loads(payload)
        re = ReservationEntry("test", email, "no devices", "none", reservation_id)
        note = self.__dbManager.getNotifier()
        note.testSendEmailEarlyNotification(re,"today")
        info = "sent"
        response = pickle.dumps((info))
        self.__sendReply(prot,"100",seq,response)

    def stopDaemon(self,prot,seq,ln,payload):
        """\brief Stops the daemon and all threads
        This method will first stop any more incoming queries, then wait for
        any update tasks to complete, before stopping itself.
        """
        self.__dbManager.stop()
        log.info("stopDaemon called.")
        prot.sendReply(200, seq, "Accepted stop request.")
        log.debug("Sending stopDaemon() response")
        self.acceptConnections(False)
        log.info("Stopping PowerDaemon (self)")
        self.stop()

    def localStopDaemon(self):
        """\brief Stops the daemon and all threads
        This method will first stop any more incoming queries, then wait for
        any update tasks to complete, before stopping itself.
        """
        #self.__dbManager.stop()
        log.info("stopDaemon called.")        
        log.debug("Sending stopDaemon() response")
	self.acceptConnections(False)
	log.info("Stopping PowerDaemon (self)")
	self.stop()
	time.sleep(4)

class PowerDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    #__bind_addr = DaemonLocations.powerDaemon[0]
    __bind_addr = "localhost"
    __port = DaemonLocations.powerDaemon[1]
    __sockd = None
    __powerControl = None
    
    def __init__(self, doFork,debug):
        self.__debug = debug
        if self.__debug:
           self.__port = self.__port + 100000
        Daemonizer.__init__(self, doFork)

    def run(self):
        log.debug("Creating PowerDaemon")
        self.__powerControl = PowerControl(self.__debug)
        # Creating socket
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        self.__sockd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        self.__sockd.settimeout(2) # 2 second timeouts
        log.info("Starting PowerDaemon")
	
	self.__powerControl.start()
	while not self.__powerControl.isStopped:
		if self.__powerControl.acceptingConnections():
			# allow timeout of accept() to avoid blocking a shutdown
			try:
				(s,a) = self.__sockd.accept()
				log.debug("New connection established from " + str(a))
				self.__powerControl.addSocket(s)
			except socket.timeout:
				pass
		else:
			log.warning("PowerDaemon still alive, but not accepting connections")
	time.sleep(2)
	log.info("Closing socket.")
	self.stop()
	
    def stop(self):
        self.__sockd.shutdown(socket.SHUT_RDWR)
        self.__sockd.close()
        self.__powerControl.localStopDaemon()
        while threading.activeCount() > 1:
            cThreads = threading.enumerate()
            log.warning("Waiting on " + str(threading.activeCount()) + \
                        " active threads...")
            time.sleep(2)
        log.info("PowerDaemon Finished.")
        # Now everything is dead, we can exit.
        sys.exit(0)


def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    DEBUG = False
    FORK = True
    if len(sys.argv) > 1:
        if sys.argv[1] == "--debug":
            DEBUG=True
	    FORK=False
            print "RUNNING IN DEBUG MODE"
    
    if not DEBUG:
        WORKDIR = '/var/hen/powerdaemon'
        PIDDIR = '/var/run/hen'
        LOGDIR = '/var/log/hen/powerdaemon'
    else:
        WORKDIR = '/tmp/var/hen/powerdaemon/debug'
        PIDDIR = '/tmp/var/run/hen/debug'
        LOGDIR = '/tmp/var/log/hen/powerdaemon/debug'
    LOGFILE = 'powerdaemon.log'
    PIDFILE = 'powerdaemon.pid'
    if DEBUG:
	GID = int(commands.getoutput('id -g'))
       	UID = int(commands.getoutput('id -u'))
    else:
	GID = 3000 # hen
    	UID = 527 # hend
    
    powerd = PowerDaemon(FORK,DEBUG)
    powerd.setWorkingDir(WORKDIR)
    powerd.setPIDDir(PIDDIR)
    powerd.setLogDir(LOGDIR)
    powerd.setLogFile(LOGFILE)
    powerd.setPidFile(PIDFILE)
    powerd.setUid(UID)
    powerd.setGid(GID)
    try:
	    powerd.start()
    except KeyboardInterrupt:
	    powerd.stop()

if __name__ == "__main__":
    main()
