#!/usr/local/bin/python
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
sys.path.append("/usr/local/hen/lib")

from time import strftime
from xml.dom import minidom
from xml.dom.minidom import Element
from xml.parsers.expat import ExpatError
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

log = logging.getLogger()
log.setLevel(logging.INFO)

class ReservationRight:
    def __init__(self, username, email, devices, maxWeeks, rightID):
        self.__username = username
        self.__email = email
        self.__devices = devices
        self.__maxWeeks = maxWeeks
        self.__rightID = rightID

    def getRightID(self):
        return self.__rightID
    
    def getUsername(self):
        return self.__username

    def getEmail(self):
        return self.__email

    def getDevices(self):
        return self.__devices

    def getMaxWeeks(self):
        return self.__maxWeeks

    def getDebugStr(self):
        return "rightid=" + str(self.getRightID()) + ", " + \
               "maxweeks=" + str(self.getMaxWeeks()) + ", " + \
               "devices=" + str(self.getDevices())

    def __str__(self):
        return str(self.getUsername()) + "," + \
               str(self.getEmail()) + "," + \
               str(self.getRightID()) + "," + \
               str(self.getMaxWeeks()) + ":" + \
               str(self.getDevices())
    
class ReservationEntry:
    def __init__(self, username, email, devices, endDate, reservationID):
        self.__username = username
        self.__email = email
        self.__devices = devices
        self.__endDate = endDate
        self.__reservationID = reservationID

    def getReservationID(self):
        return self.__reservationID
    
    def getUsername(self):
        return self.__username

    def getEmail(self):
        return self.__email

    def getDevices(self):
        return self.__devices

    def getEndDate(self):
        return self.__endDate

    def setEmail(self, email):
        self.__email = email
        
    def setDevices(self, devices):
        self.__devices = devices
        
    def setEndDate(self, endDate):
        self.__endDate = endDate
        
    def getDDMMYYYYDate(self):
        return str(self.__endDate.day) + "/" + \
               str(self.__endDate.month) + "/" + \
               str(self.__endDate.year)

    def appendDevices(self, devices):
        for device in devices:
            if device not in self.__devices:
                self.__devices.append(device)
                
    def removeDevices(self, devices):
        for device in devices:
            try:
                self.__devices.remove(device)
            except:
                pass
           
    def getInfoStr(self):
        device_list =""
        for devices in self.getDevices():
            device_list = device_list + str(devices) +","
        device_list = device_list.rstrip(',')
        return "reservation id " + str(self.getReservationID()) + ": " + \
               str(device_list) + " " + \
               "(expires on " + self.getDDMMYYYYDate() + ")"
        
    def getDateDevStr(self):
        string = "until " + str(self.getEndDate()) + ": "
        for device in self.getDevices():
            string += str(device) + ","
        string = string[:len(string) - 1]
        string += "(" + str(self.getReservationID()) + ")"
        return string

    def __str__(self):
        return str(self.getUsername()) + "," + \
               str(self.getEmail()) + "," + \
               str(self.getReservationID()) + "," + \
               str(self.getEndDate()) + ":" + \
               str(self.getDevices())

class ReservationExpiryNotifier(threading.Thread):
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
        self.__parseNotifications()
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
            if (self.__reparseDBs() != -1):
                self.__sendEarlyExpiryNotifications()
            log.info("Expiry notifer: sent notifications, going to sleep for " + str(self.__sleepTime) + " seconds")
            if not self.__debug:
                time.sleep(self.__sleepTime)
            if self.__debug:
                running = 0
        log.info("Expiry notifer: finished.")

    def __parseNotifications(self):
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

    def __parseReservations(self):
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
                log.info("Expiry notifier: error while parsing reservations database!")
                return -1
        return 0

    def __reparseDBs(self):
        retCode = self.__parseNotifications()
        result = self.__parseReservations()
        if (result == -1):
            retCode = -1
        return retCode

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
                            try:
                                self.__sendEmailEarlyNotification(userReservation, notificationDay)
                                self.__notifications[int(userReservation.getReservationID())] = notificationDay
                                self.__parser.writeNotificationsDBToDisk(self.__notifications)
                            except Exception, e:
                                log.info("exception while sending email notification:\n" + str(e))
                        break

    def __alreadySent(self, reservationID, notificationDay):
        reservationID = int(reservationID)
        if (not self.__notifications.has_key(reservationID)):
            return False
        
        sentDay = self.__notifications[reservationID]
        if (int(sentDay) <= int(notificationDay)):
            return True
        return False

class ReservationDBParser:
    def __init__(self, filename=None, rightsFilename=None, notificationsFilename=None, dbsRoot=None):
        self.__filename = filename
        self.__rightsFilename = rightsFilename
        self.__notificationsFilename = notificationsFilename
        self.__dbsRoot = dbsRoot
#        self.__theFile = None
                
    def openDB(self, filename):
        try:
            return (0, minidom.parse(filename))
        except IOError, e:
            # File missing
            log.info(e.errno)
            if (e.errno == 2):
                return (1, None)
            return (-1, None)
        except ExpatError, e:
            # File missing
            if (e.code == 3):
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
class ReservationDBManager:
    def __init__(self, filename, rightsFilename, notificationsFilename, dbsRoot, maxNumWeeks=2,debug=False):
        self.__daemonEMail = "hend@cs.ucl.ac.uk"        
        self.__filename = filename
        self.__rightsFilename = rightsFilename
        self.__notificationsFilename = notificationsFilename
        self.__notifications = {}        
        self.__dbsRoot = dbsRoot
        self.__maxNumWeeks = maxNumWeeks
        self.__reservations = {}
        self.__rights = {}
        self.__nextID = 0
        self.__xmldoc = None
        self.__rightsXmldoc = None
        self.__henManager = HenManager()
        self.__symlinksRoot = "/export/machines/"
        self.__smtpServerName = "smtp.cs.ucl.ac.uk"
        self.__parser = ReservationDBParser(filename, rightsFilename, notificationsFilename, self.__dbsRoot)
        self.__notifier = None        
        self.__debug = debug
        self.mytime = datetime.date.today()
        
        # Start the early notification thread
        self.__notifier = ReservationExpiryNotifier(self.__daemonEMail, \
                                                    self.__smtpServerName, \
                                                    self.__filename, \
                                                    self.__rightsFilename, \
                                                    self.__notificationsFilename, \
                                                    self.__dbsRoot,
                                                    self.__debug)
        if not self.__debug:
            self.__notifier.start()
        
    # used to test email sending
    def getNotifier(self):
        return self.__notifier

    def reloadHenDB(self):
        self.__henManager = HenManager()
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

        self.cleanExpired()

        # Now parse reservation rights database
        (result, self.__rightsXmldoc) = self.__parser.openDB(self.__rightsFilename)
        if (result < 0 or result == 1):
            log.info("error while opening reservation rights database!")
            return -1

        (result, self.__rights) = self.__parser.parseRightsDB(self.__rightsXmldoc)
        if (result < 0):
            log.info("error while parsing rights database!")
            return -1

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
                self.__removeNotifications(userReservation.getReservationID())
                released = True
                break

        if (not released):
            return "reservation id not found"
        
        if (self.__parser.writeDBToDisk(self.__reservations) < 0):
            self.__reservations = reservationsBackup
            return "error while writing to database, release failed"            

        self.__nextID = self.__findHighestID() + 1
        return "reservation released"
        
    def releaseDevices(self, username, devices):
        if (not self.__reservations.has_key(username)):
            return "unknown user"
        
        reservationsBackup = self.__reservations
        released = []
        userReservations = self.__reservations[username]
        for userReservation in userReservations:
            for device in userReservation.getDevices():
                if (device in devices):
                    userReservation.getDevices().remove(device)
                    released.append(device)

        # Remove any reservations with no devices in them
        for x in range(len(userReservations) - 1, -1, -1):
            if (len(userReservations[x].getDevices()) == 0):
                del userReservations[x]
        
        if (len(released) == 0):
            return "none of the devices were found in your reservations"
        
        if (self.__parser.writeDBToDisk(self.__reservations) < 0):
            self.__reservations = reservationsBackup
            return "error while writing to database, release failed"

        self.__nextID = self.__findHighestID() + 1
        string = "released: "
        for device in released:
            string += str(device) + ", "
        string = string[:len(string) - 2]
        return string
        
    def renew(self, username, reservationID, endDate):
        # Check for expired reservations first and release them
        self.cleanExpired()
        
        currentDate = self.__getCurrentDate() #datetime.date.today()
        if (endDate <= currentDate):
            return "renewal failed: supplied end date is in the past"

        maxDate = currentDate + timedelta(weeks=self.__getMaxWeeks(username, self.__getReservedDevicesByID(reservationID)))
        trimmedDate = False
        if (endDate > maxDate):
            endDate = maxDate
            trimmedDate = True

        if (self.__reservations.has_key(username)):
            for userReservation in self.__reservations[username]:
                if (int(userReservation.getReservationID()) == int(reservationID)):
                    oldDate = userReservation.getEndDate()
                    userReservation.setEndDate(endDate)
                    self.__removeNotifications(userReservation.getReservationID())
                    if (self.__parser.writeDBToDisk(self.__reservations) < 0):
                        userReservation.setEndDate(oldDate)
                        return "error while writing to database, renew failed"
                    message = "reservation renewed (new end date=" + str(self.__convertDateToString(endDate)) + ")"
                    if (trimmedDate):
                        message += "\nnote: the desired date was ignored because the max allocation period is " + \
                                   str(self.__maxNumWeeks) + " week(s)"
                    return message
                                    
        return "no reservation found for id=" + str(reservationID) + " and username=" + str(username)                    

    def update(self, username, reservationID, opType, devices, email):
        # Check for expired reservations first and release them
        self.cleanExpired()

        # First make sure that the devices are free
        if (opType == "add"):
            for device in devices:
                if (self.__isDeviceInUse(device)):
                    return "reservation failed: " + str(device) + " already reserved"
            
        if (self.__reservations.has_key(username)):
            for userReservation in self.__reservations[username]:
                if (int(userReservation.getReservationID()) == int(reservationID)):
                    
                    oldDevices = userReservation.getEndDate()
                    oldEmail = userReservation.getEmail()
                    if (opType == "add"):
                        userReservation.appendDevices(devices)
                    elif (opType == "remove"):
                        userReservation.removeDevices(devices)
                        
                    if (email != None):
                        userReservation.setEmail(email)
                    if (self.__parser.writeDBToDisk(self.__reservations) < 0):
                        userReservation.setDevices(oldDevices)
                        if (email != None):
                            userReservation.setEmail(oldEmail)
                        return "error while writing to database, update failed"
                    message = "reservation updated"
                    return message
                                    
        return "no reservation found for id=" + str(reservationID) + " and username=" + str(username)

    def reserve(self, username, email, endDate, devices):
        # Check for expired reservations first and release them
        self.cleanExpired()
        
        currentDate = self.__getCurrentDate() #datetime.date.today()
        if (endDate <= currentDate):
            return "reservation failed: supplied end date is in the past"
        maxDate = currentDate + timedelta(weeks=self.__getMaxWeeks(username, devices))
        trimmedDate = False
        if (endDate > maxDate):
            endDate = maxDate
            trimmedDate = True
        
        # First make sure that the devices are free
        for device in devices:
            if (self.__isDeviceInUse(device)):
                return "reservation failed: " + str(device) + " already reserved"

        # Add to in-memory db
        reservationID = self.__getNextID()
        if (not self.__reservations.has_key(username)):
            self.__reservations[username] = []
        entry = ReservationEntry(username, email, devices, endDate, reservationID)
        self.__reservations[username].append(entry)
        
        # Write-out to on-disk db
        if (self.__parser.writeDBToDisk(self.__reservations) < 0):
            self.__reservations[username].remove(entry)
            return "reservation failed: could not write database to disk"

        message = "reservation succeeded (id = " + str(reservationID) + ", " + \
                  "end date=" + str(self.__convertDateToString(endDate)) + ")"
        if (trimmedDate):
            message += "\nnote: the desired date was ignored because the max allocation period is " + \
                       str(self.__maxNumWeeks) + " week(s)"

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
        allDevices.extend(self.__henManager.getNodes("virtualcomputer").keys())
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
                    self.__removeNotifications(userReservation.getReservationID())
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

    def __parseNotifications(self):
        (result, xmldoc) = self.__parser.openDB(self.__notificationsFilename)
        if (result < 0):
            log.info("error while opening notifications database!")
            return -1        
        elif (result == 1):
            log.info("warning, no notifications database file found")
            return 1
        else:
            (result, self.__notifications) = self.__parser.parseNotificationsDB(xmldoc)
            # ignore -1, this means that there are no 'notifications' tags
            if (result < 0 and result != -1):
                log.info("error while parsing notifications database!")
                return -1
        return 0
    
    def __removeNotifications(self, reservationID):
        if (self.__parseNotifications() != 0):
            return
        try:
            del self.__notifications[int(reservationID)]
        except:
            log.info("warning: no notifications to delete for id=" + str(reservationID))
        self.__parser.writeNotificationsDBToDisk(self.__notifications)

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
        # temp suspend clearing links , adam 12/08/2008
        return
        for device in devices:
            if not self.__debug:
                os.system("rm " + self.__symlinksRoot + device + "/*")
            else:
                print "would run : rm " + self.__symlinksRoot + device + "/*"

    def __poweroff(self, devices):
        # temp suspend poweroff , adam 12/08/2008
        return
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


class ReservationControl(Daemon):
    """\brief Implements basic reservation daemon functionality.
    """
    __version = "Reservation Daemon v0.1 (simple)"
    
    def __init__(self,debug):
        Daemon.__init__(self)
        maxWeeksReservationTime = 2
        self.__debug = debug
        self.mytime = datetime.date.today()

        if self.__debug:
            etcRoot = "/usr/local/hen/etc/daemons/reservationd/debug/"
        else:
            etcRoot = "/usr/local/hen/etc/daemons/reservationd/"
        self.__dbManager = ReservationDBManager(etcRoot + "reservations.xml", \
                                                etcRoot + "reservationrights.xml", \
                                                etcRoot + "notifications.xml", \
                                                etcRoot, \
                                                maxWeeksReservationTime,
                                                self.__debug)
        if (self.__dbManager.startDB() < 0):
            os._exit(1)
        self.__registerMethods()

    def __registerMethods(self):
        self.registerMethodHandler("reserve", self.reserve)
        self.registerMethodHandler("update", self.update)        
        self.registerMethodHandler("release", self.release)
        self.registerMethodHandler("renew", self.renew)
        self.registerMethodHandler("whohas", self.whohas)
        self.registerMethodHandler("inuseby", self.inuseby)
        self.registerMethodHandler("notinuse", self.notinuse)
        self.registerMethodHandler("cleanexpired", self.cleanexpired)
        self.registerMethodHandler("reloadhendb", self.reloadhendb)
        self.registerMethodHandler("show", self.show)
        if self.__debug:
            self.registerMethodHandler("emailtest", self.emailtest)
            self.registerMethodHandler("settime", self.settime)
            self.registerMethodHandler("step", self.step)
        
    def __sendReply(self,prot,code,seq,payload):
        if (code == 0):
            code = 200
        else:
            code = 422 # returnCodes[422] = "error executing command"
        prot.sendReply(code, seq, payload)

    def __log(self, msg):
        log.info("CALL " + strftime("%Y-%m-%d %H:%M:%S") + ": " + msg)
        
    def notinuse(self,prot,seq,ln,payload):
        self.__log("notinuse")
        freeDevices = self.__dbManager.getFreeDevices()
        response = pickle.dumps((freeDevices))
        self.__sendReply(prot,"100",seq,response)

    def cleanexpired(self,prot,seq,ln,payload):
        self.__log("cleanexpired")        
        result = self.__dbManager.cleanExpired()
        response = pickle.dumps((result))
        self.__sendReply(prot,"100",seq,response)

    def reloadhendb(self,prot,seq,ln,payload):
        self.__log("reloadhendb")        
        result = self.__dbManager.reloadHenDB()
        response = pickle.dumps((result))
        self.__sendReply(prot,"100",seq,response)                

    def update(self,prot,seq,ln,payload):
        (username, reservationID, opType, devices, email) = pickle.loads(payload)
        self.__log("reserve: " + \
                 "username=" + str(username) + \
                 " devices=" + str(devices) + \
                 " reservationid=" + str(reservationID) + \
                 " opType=" + str(opType) + \
                 " email=" + str(email))
        result = self.__dbManager.update(username, reservationID, opType, devices, email)
        response = pickle.dumps((result))
        self.__sendReply(prot,"100",seq,response)
        
    def reserve(self,prot,seq,ln,payload):
        (username, devices, endDate, email) = pickle.loads(payload)
        self.__log("reserve: " + \
                 "username=" + str(username) + \
                 " devices=" + str(devices) + \
                 " endDate=" + str(endDate) + \
                 " email=" + str(email))
        result = self.__dbManager.reserve(username, email, endDate, devices)
        response = pickle.dumps((result))
        self.__sendReply(prot,"100",seq,response)

    def release(self,prot,seq,ln,payload):
        (username, param) = pickle.loads(payload)
        self.__log("release: " + \
                 "username=" + str(username) + \
                 " param=" + str(param))        
        result = None
        try:
            reservationID = int(param)
            result = self.__dbManager.release(username, reservationID)            
        except:
            devices = param.split(",")
            result = self.__dbManager.releaseDevices(username, devices)            

        response = pickle.dumps((result))
        self.__sendReply(prot,"100",seq,response)        

    def renew(self,prot,seq,ln,payload):
        (username, reservationID, endDate) = pickle.loads(payload)
        self.__log("renew: " + \
                 "username=" + str(username) + \
                 " reservationID=" + str(reservationID) + \
                 " endDate=" + str(endDate))
        result = self.__dbManager.renew(username, reservationID, endDate)
        response = pickle.dumps((result))
        self.__sendReply(prot,"100",seq,response)        

    def whohas(self,prot,seq,ln,payload):
        devices = pickle.loads(payload)
        self.__log("whohas: " + \
                 "devices=" + str(devices))
        result = self.__dbManager.getOwners(devices)
        response = pickle.dumps((result))
        self.__sendReply(prot,"100",seq,response)        

    def inuseby(self,prot,seq,ln,payload):
        username = pickle.loads(payload)
        self.__log("inuseby: " + \
                 "username=" + str(username))        
        devices = self.__dbManager.inUseBy(username)
        response = pickle.dumps((devices))
        self.__sendReply(prot,"100",seq,response)
 
    def show(self,prot,seq,ln,payload):
        username = pickle.loads(payload)
        self.__log("show: " + \
                 "username=" + str(username))                
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
        log.info("Stopping ReservationDaemon (self)")
        self.stop()

class ReservationDaemon(Daemonizer):
    """\brief Creates sockets and listening threads, runs main loop"""
    __bind_addr = DaemonLocations.reservationDaemon[0]
    __port = DaemonLocations.reservationDaemon[1]
    __sockd = None
    __reservationControl = None
    
    def __init__(self, doFork,debug):
        self.__debug = debug
        if self.__debug:
           self. __port = self.__port + 100000
        Daemonizer.__init__(self, doFork)

    def run(self):
        log.debug("Creating ReservationDaemon")
        self.__reservationControl = ReservationControl(self.__debug)
        # Creating socket
        self.__sockd = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        self.__sockd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        log.debug("Binding to port: " + str(self.__port))
        self.__sockd.bind((self.__bind_addr, self.__port))
        log.info("Listening on " + self.__bind_addr + ":" + str(self.__port))
        self.__sockd.listen(10)
        #self.__sockd.settimeout(2) # 2 second timeouts
        log.info("Starting ReservationDaemon")
        self.__reservationControl.start()
        while self.__reservationControl.isAlive():
            if self.__reservationControl.acceptingConnections():
                # allow timeout of accept() to avoid blocking a shutdown
                try:
                    (s,a) = self.__sockd.accept()
                    log.debug("New connection established from " + str(a))
                    self.__reservationControl.addSocket(s)
                except KeyboardInterrupt:
                    break
            else:
                log.warning(\
                      "ReservationDaemon still alive, but not accepting connections")
                time.sleep(2)
        log.info("Closing socket.")
        self.__sockd.shutdown(socket.SHUT_RDWR)
        self.__sockd.close()
        self.__reservationControl.stopDaemon()
        while threading.activeCount() > 1:
            cThreads = threading.enumerate()
            log.warning("Waiting on " + str(threading.activeCount()) + \
                        " active threads...")
            time.sleep(2)
        log.info("ReservationDaemon Finished.")
        # Now everything is dead, we can exit.
        sys.exit(0)

def main():
    """\brief Creates, configures and runs the main daemon
    TODO: Move config variables to main HEN config file.
    """
    DEBUG = False
    doFork = True
    if len(sys.argv) > 1:
        if sys.argv[1] == "--debug":
            DEBUG=True
            doFork = False
            print "RUNNING IN DEBUG MODE"
    
    if not DEBUG:
        WORKDIR = '/var/hen/reservationdaemon'
        PIDDIR = '/var/run/hen'
        LOGDIR = '/var/log/hen/reservationdaemon'
    else:
        WORKDIR = '/var/hen/reservationdaemon/debug'
        PIDDIR = '/var/run/hen/debug'
        LOGDIR = '/var/log/hen/reservationdaemon/debug'
    LOGFILE = 'reservationdaemon.log'
    PIDFILE = 'reservationdaemon.pid'
    GID = 3000 # hen
    UID = 527 # hend
    
    reservationd = ReservationDaemon(doFork,DEBUG)
    reservationd.setWorkingDir(WORKDIR)
    reservationd.setPIDDir(PIDDIR)
    reservationd.setLogDir(LOGDIR)
    reservationd.setLogFile(LOGFILE)
    reservationd.setPidFile(PIDFILE)
    reservationd.setUid(UID)
    reservationd.setGid(GID)
    reservationd.start()

if __name__ == "__main__":
    main()
