import logging
import os.path
import pickle
from stat import *
from auxiliary.daemonlocations import DaemonLocations
from auxiliary.protocol import Protocol
import datetime

powerdaemon = Protocol(None)
powerdaemon.open(DaemonLocations.powerDaemon[0], DaemonLocations.powerDaemon[1])
version = powerdaemon.doSynchronousCall("get_config_version","")
print "Version is "+str(version[0][2])
tics = os.stat('/usr/local/hen/etc/physical/topology.xml')[ST_MTIME]
t = datetime.datetime.fromtimestamp(tics)
lastAccess=str(t.strftime('%Y-%m-%d'))
print "Last access time is "+lastAccess
if (str(lastAccess)!=str(version[0][2])):
	print "Setting new config"
	from henmanager import HenManager
	hm = HenManager()
	payload = lastAccess + ","+ pickle.dumps(hm.getNodes("all"))
	print "Result is:"+str(powerdaemon.doSynchronousCall("set_config",payload))
	

def addLink(tag,action,old,new):
    print "AddLink got "+tag,action,old,new

def removeLink(tag,action,old,new):
    print "RemoveLink got "+tag,action,old,new
    
def changePowerState(tag,action,node,attr):
	print "changePowerState got "+tag,action,node,attr
	id = node.xpath("ancestor::node")[0].attributes[(None,'id')].value

	param = str(id)+","+str(attr.value)
	print "Calling powerdaemon power with param "+param
	if (powerdaemon is None):
		return (500,"connection to powerdaemon is null")
	else:
		ret = powerdaemon.doSynchronousCall("set_port_state",str(id)+","+str(attr.value))
		print ret

	return (ret[0][0],ret[0][2])
    
def openConsole(tag,action,old,new):
    print "Open console got "+tag,action,old,new

def closeConsole(tag,action,old,new):
    print "Close console got "+tag,action,old,new

def sendCharConsole(tag,action,old,new):
    print "Send console got "+tag,action,old,new
