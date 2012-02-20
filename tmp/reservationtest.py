#!/usr/local/bin/python
import logging
import auxiliary.protocol
import pickle
import hashlib
import time
import os
import sys
import datetime
from auxiliary.daemonlocations import DaemonLocations
from daemonclients.reservationclient import ReservationClient

###########################################################
#   MAIN EXECUTION
###########################################################
def help():
    print "Usage: python reservationclient.py [command] [(options)]\n" + \
          "(devices should be comma-separated, date in dd/mm/yyyy format)\n" + \
          "--------------------------------------------------------\n\n" + \
          "reserve\t<device> <end date> <email>\n" + \
          "release\t<reservation id|devices>\n" + \
          "renew\t<reservation id> <end date>\n" + \
          "whohas\t<device>\n" + \
          "inuseby\t<username>\n" + \
          "show <username>\n" + \
          "email_test <email address> <random reservation id>\n" + \
          "notinuse\n"    

def error(message):
    print message + "\n"
    help()
    os._exit(1)

def convertToDate(string):
    dates = string.split("/")
    return datetime.date(int(dates[2]), int(dates[1]), int(dates[0]))



if (len(sys.argv) < 2):
    error("missing parameter(s)")

HOST = DaemonLocations.reservationDaemon[0]
PORT = DaemonLocations.reservationDaemon[1] + 100000
client = ReservationClient()
client.connect(HOST, PORT)

username = os.environ['USER']
command = sys.argv[1]
payload = None

#command = "cleanexpired"
#payload = pickle.dumps(())    
#client.sendRequest(command, payload)
#os._exit(1)

#command = "reloadhendb"
#payload = pickle.dumps(())    
#client.sendRequest(command, payload)
#os._exit(1)

if (command == "reserve"):
    if (len(sys.argv) < 5):
        error("missing parameter(s)")
    devices = sys.argv[2].split(",")
    endDate = convertToDate(sys.argv[3])
    email = sys.argv[4]
    payload = pickle.dumps((username, devices, endDate, email))
elif (command == "release"):
    if (len(sys.argv) < 3):
        error("missing parameter(s)")    
    reservationID = sys.argv[2]
    payload = pickle.dumps((username, reservationID))    
elif (command == "renew"):
    if (len(sys.argv) < 4):
        error("missing parameter(s)")
    reservationID = sys.argv[2]    
    endDate = convertToDate(sys.argv[3])    
    payload = pickle.dumps((username, reservationID, endDate))        
elif (command == "whohas"):
    if (len(sys.argv) < 3):
        error("missing parameter(s)")    
    devices = sys.argv[2].split(",")    
    payload = pickle.dumps((devices))            
elif (command == "inuseby"):
    if (len(sys.argv) < 3):
        error("missing parameter(s)")
    username = sys.argv[2]
    payload = pickle.dumps((username))
elif (command == "show"):
    if (len(sys.argv) < 3):
        error("missing parameter(s)")
    username = sys.argv[2]
    payload = pickle.dumps((username))
elif (command == "emailtest"):
    if (len(sys.argv) < 4):
        error("missing parameter(s)")
    email = sys.argv[2]
    reservation_id = sys.argv[3]
    payload = pickle.dumps((email,reservation_id))    
elif (command == "notinuse"):
    payload = pickle.dumps(())
elif (command == "step"):
    payload = pickle.dumps(())
elif (command == "settime"):
    mydate = datetime.date(int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]))
    payload = pickle.dumps((mydate))
elif (command == "stopDaemon"):
    payload = pickle.dumps(())
else:
    print "unrecognized command"
    os._exit(1)

print client.sendRequest(command, payload)
    
