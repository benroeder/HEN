import logging
import socket
from ConfigParser import SafeConfigParser
from Ft.Xml.XPath import Conversions
import Ft.Xml
import Ft.Xml.Domlette
import pickle
import cStringIO
import ConfigParser

from Ft.Xml.XPath.Context import Context
from Ft.Xml import EMPTY_NAMESPACE
from auxiliary.hmd.nodeidentity import NodeIdentity
import re
from auxiliary.hmd.nodeconstraint import NodeConstraints
from auxiliary.hmd.trigger import ActionTriggers, trigger_cmp
from cStringIO import StringIO
from auxiliary.hmd.initdata import InitData
from auxiliary.hen import NetbootInfo

from daemon import Daemon
from auxiliary.daemonlocations import DaemonLocations
from operatingsystem.confignetboot import ConfigNetboot
from auxiliary.protocol import Protocol

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

class ControlDaemon(Daemon):
    """\brief Implements the management daemon that computes config changes, checks security clearance, checks the sanity of the operations and calls the proper functions in the backend
    """     

    ######################################################################################
    #
    #  INIT FUNCTIONS
    #
    ######################################################################################
    def __init__(self, hardConfig='/usr/local/hen/etc/physical/topology.xml', softConfig='/usr/local/hen/etc/configs/henmanagementdaemon/soft.xml', constraints='/usr/local/hen/etc/configs/henmanagementdaemon/extra.xml', configFilePath='/usr/local/hen/etc/configs/config'):
        Daemon.__init__(self)
        
        self.__initHardConfig(hardConfig)
        self.__nodeIdentity = NodeIdentity(constraints)
        
        ctx = Context(None, extFunctionMap={(None, u'check-uniqueness'): self.__nodeIdentity.check_uniqueness})

        self.__initData = InitData(constraints,ctx,self.__hardConfig)
        self.__initSoftConfig(softConfig,constraints)

        self.__constraints = NodeConstraints(self,constraints,ctx)
        self.__triggers = ActionTriggers(self,constraints)

        self.__configFilePath = configFilePath
        self.__configFile = ConfigParser.ConfigParser()
        self.__configFile.read(configFilePath)
        self.__configNetboot = None
        self.__initNetboot()

        self.registerMethodHandler("get_state", self.getState) # debug command
	self.registerMethodHandler("acquire", self.acquireNodes) # done
	self.registerMethodHandler("release", self.releaseNodes) # done
        self.registerMethodHandler("power", self.power) # pending power daemon api definition
	self.registerMethodHandler("console", self.console) # 2-way traffic works, but still buggy
	self.registerMethodHandler("owner", self.owner) # done
	self.registerMethodHandler("is_owner", self.isOwner) # done
	self.registerMethodHandler("inventory", self.inventory) # to be implemented
	self.registerMethodHandler("node", self.node) # cat command implemented, others still to do
        self.registerMethodHandler("create_vlan", self.createVlan) # pending switch daemon
        self.registerMethodHandler("delete_vlan", self.deleteVlan) # pending switch daemon
        self.registerMethodHandler("show_vlan", self.showVlan) # pending switch daemon
        self.registerMethodHandler("add_vlan_ports", self.addVlanPorts) # pending switch daemon
        self.registerMethodHandler("remove_vlan_ports", self.removeVlanPorts) # pending switch daemon
        self.registerMethodHandler("netboot", self.configNetboot) # done
        
        self.deleteTextElements()
        self.updateOwnerData()

        self.__computerDaemonConnections = {}
        self.__nodeReply = None

        self.__consoleOperationReply = None
        self.__consoleDaemon = None
        self.__authenticationDaemon = None
        self.__stateSet = False

    def __initNetboot(self):
        self.__configNetboot = ConfigNetboot(NetbootInfo(\
                  self.__configFile.get('NETBOOT', 'AUTODETECT_LOADER'), \
                  self.__configFile.get('NETBOOT', 'AUTODETECT_FILESYSTEM'), \
                  self.__configFile.get('NETBOOT', 'AUTODETECT_KERNEL')), \
                  self.__configFile.get('NETBOOT', 'GROUP'), \
                  self.__configFile.get('NETBOOT', 'NFS_ROOT'), \
                  self.__configFile.get('NETBOOT', 'SERIAL_SPEED'), \
                  self.__configFile.get('NETBOOT', 'PXE_LINUX_DIRECTORY'), \
                  self.__configFile.get('NETBOOT', 'PXE_LINUX_FILE'), \
                  self.__configFile.get('NETBOOT', 'STARTUP_FILE'), \
                  self.__configFile.get('NETBOOT', 'INTERFACE_CONFIG_SCRIPT'), \
                  self.__configFile.get('NETBOOT', 'CONSOLE'), \
                  self.__configFile.get('MAIN','EXPORT_PATH'), \
                  self.__configFile.get('MAIN','PYTHON_BIN'))

    def __initHardConfig(self, hardConfigFile):
        self.__hardConfig = Ft.Xml.Domlette.implementation.createDocument(EMPTY_NAMESPACE, "hardconfig", None)
        
        config = Ft.Xml.Parse(hardConfigFile)    
        for x in config.xpath("/topology/node"):
            if (x.attributes.has_key((None,u'status')) and x.attributes.has_key((None,u'file')) and x.attributes[(None,u'status')].value=="operational"):
                try:
			nodeDoc = Ft.Xml.Parse(x.attributes[(None,u'file')].value)
                	self.__hardConfig.importNode(nodeDoc.documentElement)
                	self.__hardConfig.documentElement.appendChild(nodeDoc.documentElement)
		except Exception,e:
			print str(e)

        #Ft.Xml.Domlette.PrettyPrint(self.__hardConfig)
        #TODO: check uniqueness!

    def __initSoftConfig(self,softConfigFile,constraints):
        self.__softConfig = Ft.Xml.Parse(softConfigFile)
        
        for x in self.__softConfig.xpath("/softconfig/node"):
            if (len(self.__hardConfig.xpath('/hardconfig/node[@id="'+x.attributes[(None,'id')].value+'"]'))==0):
                print "removing node "+str(x)
                parent = x.parentNode
                parent.removeChild(x)

        for x in self.__hardConfig.xpath("/hardconfig/node"):
        	print x.attributes[(None,u'id')].value	    
		if (len(self.__softConfig.xpath('/softconfig/node[@id="'+x.attributes[(None,'id')].value+'"]'))==0):
                	node = x.cloneNode(0)
                	print "adding node "+str(x)
                	node.setAttributeNS(None, "owner", "")
                	self.__softConfig.importNode(node)
                	self.__softConfig.documentElement.appendChild(node)
                
                	#initialize it if needed
                	#...
			toAddList = self.__initData.getAddList(node)

			for t in toAddList:
				self.__softConfig.importNode(t)
				node.appendChild(t)

       	#Ft.Xml.Domlette.PrettyPrint(self.__softConfig) 

    ######################################################################################
    #
    #  REGISTERED FUNCTIONS (PROTOCOL CALLABLE)
    #
    ######################################################################################
    def acquireNodes(self,prot,seq,ln,payload):
        (username, groups, parameters) = pickle.loads(payload)
 	print "acquire called with params " + str(parameters)      

        result = []
        message = ""
        for id in parameters:
            if (self.__isOwner(username, id)):
                result.append((id, 404, "node is already owned by you"))                
            elif (self.__hasOwner(id)):
                result.append((id, 404, "node is owned by another user or does not exist"))

        if (len(result) != 0):
            prot.sendReply(404, seq, pickle.dumps(result))
            return
        
        #should add synchronization code here
	for id in parameters:
            try:
                self.__softConfig.xpath('/softconfig/node[@id="'+id+'"]')[0].attributes[(None,u'owner')].value = username
                self.__hardConfig.xpath('/hardconfig/node[@id="'+id+'"]')[0].attributes[(None,u'owner')].value = username
                result.append((id,200,"acquired"))
            except Exception,e:
                prot.sendReply(500, seq, "synchronization error, nodes locked before I could get to them"+str(e))
                return   	

	print len(self.__softConfig.xpath('/softconfig/node[@owner="'+username+'"]'))
        prot.sendReply(200,seq,pickle.dumps(result))

    def releaseNodes(self,prot,seq,ln,payload):
        (username, groups, parameters) = pickle.loads(payload)
 	print "release called with params "+str(parameters)      


        result = []
        message = ""
        for id in parameters:
            if (not self.__isOwner(username, id)):
                result.append((id, 404, "node not owned by user or does not exist"))                

        if (len(result) != 0):
            prot.sendReply(404, seq, pickle.dumps(result))
            return

        #should add synchronization code here
        for id in parameters:
            try:
                self.__softConfig.xpath('/softconfig/node[@id="'+id+'"]')[0].attributes[(None,u'owner')].value = ""
                self.__hardConfig.xpath('/hardconfig/node[@id="'+id+'"]')[0].attributes[(None,u'owner')].value = ""
                result.append((id, 200, "released"))
            except Exception,e:
                prot.sendReply(500, seq, "synchronization error, nodes locked before I could get to them"+str(e))
                return
            
        prot.sendReply(200,seq,pickle.dumps(result))

    def power(self,prot,seq,ln,payload):
        (username, groups, parameters) = pickle.loads(payload)        
        action = parameters[0]

        results = []
        overallCode = 200
        for target in parameters[1:]:
            path = '/softconfig/node[@id="' + str(target) + '"]/powerstate'
            newconfig = ""
            if (action == "status"):
                (returnCode, msg) = self.__getState(username, path)
                results.append((target, returnCode, msg))
                if (returnCode != 200):
                    overallCode = returnCode                    
            else:
                # Restarting consists of turning the node off, then on
                if (action == "restart"):
                    newconfig = '<state><powerstate value="off" /></state>'
                    #returnCode =  self.__controlOperation(operation, path, newconfig)
                    (returnCode, msg) = self.__changeState(username, path, newconfig)
                    if (returnCode != 200):
                        overallCode = returnCode
                        results.append((target, returnCode, msg))
                        continue
                    newconfig = '<state><powerstate value="on" /></state>'
                    (returnCode, msg) = self.__changeState(username, path, newconfig)
                    results.append((target, returnCode, msg))
                    if (returnCode != 200):
                        overallCode = returnCode                                        

                # Power on/off
                newconfig = '<powerstate value="' + str(action) + '" />'
                (returnCode, msg) = self.__changeState(username, path, newconfig)
                results.append((target, returnCode, msg))
                if (returnCode != 200):
                    overallCode = returnCode                

        prot.sendReply(overallCode , seq, pickle.dumps(results))

    def owner(self,prot,seq,ln,payload):
        (username, groups, parameters) = pickle.loads(payload)

        reply = []
        # Retrieve what the user owns
        if (len(parameters) == 0):
            results = self.__getOwnees(username)
            for result in results:
                reply.append((result,200,username))
            prot.sendReply(200,seq,pickle.dumps(reply))                
            return

        # Retrieve owners of given nodes
        print "owner called with parameters", parameters
        results = self.__getOwners(parameters)
        for result in results:
            reply.append((result[0], 200, result[1]))
        prot.sendReply(200,seq,pickle.dumps(reply))                

    def isOwner(self,prot,seq,ln,payload):
        (username, groups, parameters) = pickle.loads(payload)                
        nodeID = parameters[0]
        if (self.__isOwner(username, nodeID)):
            prot.sendReply(200, seq, "True")
        else:
            prot.sendReply(200, seq, "False")            

    def inventory(self,prot,seq,ln,payload):
        (username, groups, parameters) = pickle.loads(payload)        

    def node(self,prot,seq,ln,payload):
        (username, groups, parameters) = pickle.loads(payload)        
        print "got node command:", parameters

        # Must look up IP address of node and connect to its daemon
        nodeID = parameters[0]
        ipAddress = self.__getAddress(nodeID)

        if (not self.__computerDaemonConnections.has_key(nodeID)):
            computerDaemon = Protocol(None)
            computerDaemon.open(ipAddress, DaemonLocations.computerDaemon[1])
            self.__computerDaemonConnections[nodeID] = computerDaemon

        # We now have a connection open, forward request
        method = parameters[1]
        params = []
        for x in range(2, len(parameters)):
            params.append(parameters[x])

        self.__computerDaemonConnections[nodeID].sendRequest(method, pickle.dumps(params), self.__nodeReplyHandler)
        self.__computerDaemonConnections[nodeID].readAndProcess()
        print self.__nodeReply[3]
        prot.sendReply(self.__nodeReply[0], seq, self.__nodeReply[3])

    def __nodeReplyHandler(self, code, seq, sz, payload):
        self.__nodeReply = (code, seq, sz, payload)
                
    def createVlan(self,prot,seq,ln,payload):
        (username, groups, parameters) = pickle.loads(payload)
        prot.sendReply(200, seq, "")

    def deleteVlan(self,prot,seq,ln,payload):
        (username, groups, parameters) = pickle.loads(payload)
        
    def showVlan(self,prot,seq,ln,payload):
        (username, groups, parameters) = pickle.loads(payload)

    def addVlanPorts(self,prot,seq,ln,payload):
        (username, groups, parameters) = pickle.loads(payload)

    def removeVlanPorts(self,prot,seq,ln,payload):
        (username, groups, parameters) = pickle.loads(payload)

    def __consoleOperationReplyHandler(self, code, seq, sz, payload):
        self.__consoleOperationReply = (code, seq, sz, payload)
                
    def console(self,prot,seq,ln,payload):
        username = groups = parameters = None

        if (self.__consoleDaemon == None):
            self.__consoleDaemon = Protocol(None)
            self.__consoleDaemon.open(DaemonLocations.consoleDaemon[0], DaemonLocations.consoleDaemon[1])
        
        (username, groups, parameters) = pickle.loads(payload)
        action = parameters[0]
        if (action == "console_output"):
            # request from console daemon, forward back to authentication daemon
            # make sure connection is open first
            (username, consoleOutput, operation) = pickle.loads(payload)
            if (self.__authenticationDaemon == None):
                # Second parameter is SSL, must use it since authentication daemon is an SSL server
                self.__authenticationDaemon = Protocol(None, True)
                self.__authenticationDaemon.open(DaemonLocations.authenticationDaemon[0], \
                                                 DaemonLocations.authenticationDaemon[1])

            self.__authenticationDaemon.sendRequest("control", \
                                                    pickle.dumps((username, "console_output", [consoleOutput])), \
                                                    self.__consoleOperationReplyHandler)
            return

        # Request came from client console
        nodeID = parameters[1]
        consoleInput = parameters[2]
        
        if (not self.__isOwner(username, nodeID)):
            prot.sendReply(404, seq, pickle.dumps((404, "you do not own the node")))
            return

        if (action == "open"):
            retValue = self.__consoleDaemon.doSynchronousCall("console", pickle.dumps((action, username, nodeID, "")))
            if (retValue[0][0] != 200):
                print "error while opening console"
                return            
            self.__stateSet = True
            prot.sendReply(200, seq, pickle.dumps((200, "")))
        elif (action == "forward"):
            # if no state set in xpath for open console, send this open command
            # NOTE: self.__stateSet IS A HACK, should be replaced with xpath state
            if (not self.__stateSet):
                print "error, tried to forward to unopened console"
                return
            self.__consoleDaemon.sendRequest("console", \
                                             pickle.dumps((action, username, nodeID, consoleInput)), \
                                             self.__consoleOperationReplyHandler)
            
        elif (action == "close"):
            # Unset xpath state
            retValue = self.__consoleDaemon.doSynchronousCall("console", pickle.dumps((action, username, nodeID, "")))
            if (retValue[0][0] != 200):
                print "error while closing console"
                return                        
            self.__stateSet = False
            prot.sendReply(200, seq, pickle.dumps((200, "")))            
        else:
            print "unrecognized function:", action
        
    def configNetboot(self,prot,seq,ln,payload):
        (username, groups, parameters) = pickle.loads(payload)

        print parameters
        netbootConfigs = []
        for x in range(0, len(parameters), 4):
            # netbootConfigs is a list of tuples: (nodeid, loader, filesystem, kernel)
            netbootConfigs.append((parameters[x], parameters[x + 1], parameters[x + 2], parameters[x + 3]))

        overallCode = 200
        response = []
        for netbootConfig in netbootConfigs:
            (nodeID, loader, filesystem, kernel) = netbootConfig
            if (not self.__isOwner(username, nodeID)):
                response.append((nodeID, 500, "user does not own node"))
                overallCode = 500
                continue

            netbootInfo = NetbootInfo(loader, filesystem, kernel)
            code = self.__configNetboot.createNetbootInfo(nodeID, netbootInfo)
            if (code != 200):
                response.append((nodeID, code, "error while creating sym links"))
                overallCode = code
                continue
            else:
                response.append((nodeID, code, "netboot config created"))

        prot.sendReply(overallCode, seq, pickle.dumps(response))

    ######################################################################################
    #
    #  XPATH FUNCTIONS
    #
    ######################################################################################
    def deleteTextElements(self):
        #deletes text elements that only contain newlines and tabs (introduced by PrettyPrint)
    	for x in self.__softConfig.xpath("//text()"):
    	    if (re.compile("\n\t*").match(x.data)!=None):
    		y = x.parentNode
    		y.removeChild(x)
	    
    def updateOwnerData(self):
        for x in self.__softConfig.xpath("/softconfig/node"):
            node = self.__hardConfig.xpath('/hardconfig/node[@id="'+x.attributes[(None,u'id')].value+'"]')[0]
            if (node.hasAttributeNS(None,u'owner')):
                node.attributes[(None,u'owner')].value = x.attributes[(None,u'owner')].value
            else:
                node.setAttributeNS(None,u'owner',x.attributes[(None,u'owner')].value)
        
    def getSoftConfig(self):
        return self.__softConfig

    def getHardConfig(self):
        return self.__hardConfig
    
    def cloneConfigTree(self,node,stopTag="softconfig"):
        #clone deep from node below
        #clone shallow from node above
        x = node
        node = node.cloneNode(1)
        toAppend = node
        #copy everything until topmost node
        while (x.localName!=stopTag):
            y = x.parentNode.cloneNode(0)
            y.appendChild(toAppend)
            toAppend = y
            x = x.parentNode

        copyOnWrite = self.__softConfig.createDocumentFragment()
        copyOnWrite.appendChild(toAppend)
        
        return (copyOnWrite,node)

    ######################################################################################
    #
    #  STATE FUNCTIONS
    #
    ######################################################################################    
 
	   
    def getState(self,prot,seq,ln,payload):
        (username, groups, parameters) = pickle.loads(payload)
        (ret,state) = self.__getState(username,parameters[0])
	prot.sendReply(200,seq,pickle.dumps([(ret,parameters[0],state)]))

    def __getState(self, username, path):
        try:
		s = cStringIO.StringIO() 
		for r in self.__softConfig.xpath(path):
			Ft.Xml.Domlette.Print(r,s)

		sr = s.getvalue()
		s.close()
		return (200, sr)
	except Exception,e:
		return (404,str(e))

    def __changeState(self, username, path, newconfig):
        print "changeState called"
        (result, msg) = self.__setState(username, path, newconfig, "update")
        if (result == 0):
            return (404, msg)
        else:
            return (200, msg)

    def __addState(self, username, path, newconfig):
        print "add state called"
        (result, msg) = self.__setState(username, path, newconfig, "add")
	if (result == 0):
		return (404,msg)
	else:
		return (200,"")

    def __removeState(self, username, path, newconfig):
        print "remove state called"
        (result, msg) = self.__setState(username, path, newconfig, "remove")        
	if (result == 0):
		return (404, msg)
	else:
		return (200, "")

    def __setState(self,user, path, newconfig, operation):
        nodeToChange = self.__softConfig.xpath(path)
            
        try:
            if (len(nodeToChange)!=1):
                print "Wrong number of nodes selected by xpath!"+path
                return (0, "Wrong number of nodes selected by xpath:"+path) 
            (copyOnWrite,node) = self.cloneConfigTree(nodeToChange[0])

#            print "Initial soft config is:"
#            Ft.Xml.Domlette.PrettyPrint(self.__softConfig)
    
#            print "Node to modify"
#            Ft.Xml.Domlette.PrettyPrint(node)
    
            if (operation=="update" or operation=="add"):
                update = Ft.Xml.Domlette.NonvalidatingReader.parseString(newconfig,'http://').firstChild
                print operation
                Ft.Xml.Domlette.PrettyPrint(update)
            else:
                print operation
                Ft.Xml.Domlette.PrettyPrint(node)
            
    #            print "Full state"
    #            Ft.Xml.Domlette.PrettyPrint(self.__softConfig)
    #            print "Update state"
    #            Ft.Xml.Domlette.PrettyPrint(copyOnWrite)
                
        except Exception,e:
            print "eroare frate",e
            return (0, str(e))
    
            
        modifList = {}
        if (operation=="update"):
            ret = self.detectNodeChange(node,update,modifList, 0)
            if (ret!=200):
                return (0,"detect config change failed")
        elif (operation=="add"):
            self.appendToDo(modifList, 0, node, update, "add")
        elif (operation=="remove"):
            self.appendToDo(modifList, 0, node.parentNode, node, "remove")
                
    #        print modifList

	if (not modifList.has_key("backend")):            
		return (0,"No changes selected!")

        handlers = modifList["backend"]
        del modifList["backend"]
    
        (ret,msg) = self.operationsAllowed(user,modifList)
        if (ret==1):
            print "All modifications are allowed "+msg
        else:
            print "Not all modifs are allowed because "+msg
            return (0,"Modifs are not allowed because "+msg)
    	
            
#        print "modified node is:"
#        Ft.Xml.Domlette.PrettyPrint(node)       
        
        (ret,msg) = self.isStructureOk(node)
        if (ret==1):
            print "Structure is ok"
        else:
            print "Structure is not ok because "+msg
            return (0,"Structure is not ok because "+msg)
        
        #sort hand::nodelers
        handlers.sort(trigger_cmp)
        
        for t in handlers:
		(code,string) = t.executeTrigger()
		if (code!=200):
			return (0,string+" code is "+str(code))

        #propagate changes in tree
        if (operation=="add"):
            nodeToChange[0].appendChild(update)
        elif (operation=="update"):
            parent = nodeToChange[0].parentNode
            parent.replaceChild(node,nodeToChange[0])
        elif (operation=="remove"):
            parent = nodeToChange[0].parentNode
            parent.removeChild(nodeToChange[0])

        #print "Updated soft config is:"
        #Ft.Xml.Domlette.PrettyPrint(self.__softConfig)       
	
	return (1,"ok")

    #security check!
    def operationsAllowed(self, user, modifList):
        for level in sorted(modifList.keys(),self.__mycmp):
            print "Level "+str(level)

            for node in modifList[level].keys():
                print node
                for (value,action) in modifList[level][node]:
                    print (value,action)
                    (ret,msg) = self.__constraints.actionAllowed(node,value,action)
                    if (ret==0):
                        return (0,msg)

                    if (action=="add"):
                        nValue = node.ownerDocument.importNode(value,1)
                        node.appendChild(nValue)
                        
                        (ret,msg) = self.__constraints.checkPermissions(user,nValue)
                        if (ret==0):
                            return (ret,msg)

                    elif (action=="update"):
                        (ret,msg) = self.__constraints.checkPermissions(user,node)
                        if (ret==0):
                            return (ret,msg)

                    elif (action=="remove"):
                        (ret,msg) = self.__constraints.checkPermissions(user,value)
                        if (ret==0):
                            return (ret,msg)
                        node.removeChild(value)

                    elif (action=="addAttribute"):
                        (ret,msg) = self.__constraints.checkPermissions(user,node)
                        if (ret==0):
                            return (ret,msg)
                        node.setAttributeNS(None,value.name,value.value)

                    elif (action=="removeAttribute"):
                        (ret,msg) = self.__constraints.checkPermissions(user,node)
                        if (ret==0):
                            return (ret,msg)
                        node.removeAttributeNodeNS(value)

                    elif (action=="updateAttribute"):
                        (ret,msg) = self.__constraints.checkPermissions(user,node)
                        if (ret==0):
                            return (ret,msg)
                        node.setAttributeNS(None,value.name,value.value)
                    
                    
            
        return (1,"Ok")
        #check to see if the changes are allowed
        #check to see if the changes are correct
        #order them
        #call backend
        
    def nodesEqual(self,nodeA,nodeB):
        return self.__nodeIdentity.nodeUID(nodeA)==self.__nodeIdentity.nodeUID(nodeB)
    
    def listContainsNode(self,list,node):
        i = 0
        for x in list:
            if (self.nodesEqual(node,x)):
                return (1,i)
            i = i+1
            
        return (0,-1)
        
    def appendToDo(self, dict, level, node,what, action):
        if (not dict.has_key(level)):
            dict[level] = {}
        
        if not dict[level].has_key(node):
            dict[level][node] = []
            
        dict[level][node].append((what,action))
        
        if (not dict.has_key("backend")):
            dict["backend"] = []

        if (action=="add" or action=="remove"):
            dict["backend"].extend(self.__triggers.instantiateTriggers(what.localName, action, node, what))
        else:
            dict["backend"].extend(self.__triggers.instantiateTriggers(node.localName, action, node, what))
        
    def detectNodeChange(self,node, update, toModify,level):
        if not self.nodesEqual(node,update):
            print "Trying to change two incompatible nodes!"
            return (404)
        
        used = {}
        ret = 200
        
        #iterate attributes in update
        for key in update.attributes.keys():
            used[key] = 1
            if (node.attributes.has_key(key)):
                if (node.attributes[key].value!=update.attributes[key].value):
                    self.appendToDo(toModify,level,node,update.attributes[key],"updateAttribute")
            else:
                self.appendToDo(toModify,level,node,update.attributes[key],"addAttribute")
            
        for key in node.attributes.keys():
            if (not used.has_key(key)):
                self.appendToDo(toModify,level,node,node.attributes[key],"removeAttribute")
        
        used = {}
        for updateChild in update.childNodes:
            used[self.__nodeIdentity.nodeUID(updateChild)] = 1
            
            (cont,id) = self.listContainsNode(node.childNodes, updateChild)
            if cont==1:
                self.appendToDo(toModify,level,node,node.childNodes[id],"update")
                ret = self.detectNodeChange(node.childNodes[id],updateChild,toModify,level+1)
            else:
                self.appendToDo(toModify,level,node,updateChild,"add")

        for nodeChild in node.childNodes:
            if (not used.has_key(self.__nodeIdentity.nodeUID(nodeChild))):
                self.appendToDo(toModify,level,node,nodeChild,"remove")
        
        return ret
        #iterate children in update

    def isStructureOk(self, node):
    	(ret,msg) = self.__constraints.checkNode(node)
    	if (ret==0):
        	    return (ret,msg)
    	if (node.childNodes!=None):
    	    for x in node.childNodes:
    		(ret,msg) = self.isStructureOk(x)
    		if (ret==0):
    	    	    return (ret,msg)
    	return (1,"")        
            

    ######################################################################################
    #
    #  HELPER FUNCTIONS
    #
    ######################################################################################
    def __isOwner(self, username, nodeID):
        return (len(self.__softConfig.xpath('/softconfig/node[@id="' + nodeID + '" and @owner="' + username + '"]')) != 0)

    def __hasOwner(self, nodeID):
        return (len(self.__softConfig.xpath('/softconfig/node[@id="' + nodeID + '" and @owner=""]')) == 0)

    def __getOwners(self, nodeIDs):
        results = []
        for nodeID in nodeIDs:
            owner = self.__softConfig.xpath('/softconfig/node[@id="' + nodeID + '"]')[0].getAttributeNS(None, "owner")
            if (owner == ""):
                owner = "no owner"
            results.append((nodeID, owner))
        return results

    def __getOwnees(self, ownerID):
        results = []
        tempResults = self.__softConfig.xpath('/softconfig/node[@owner="' + ownerID + '"]')
        for tempResult in tempResults:
            results.append(tempResult.getAttributeNS(None, "id"))
        return results

    def __getAddress(self, nodeID):
        test = self.__hardConfig.xpath('/hardconfig/node[@id="' + nodeID + '"]')[0]

        for childNode in test.childNodes:
            try:
                if ((childNode.tagName == "interface") and (childNode.getAttributeNS(None, "type") == "management")):
                    return childNode.getAttributeNS(None, "ip")
            except:
                pass

        return None
        
    def __mycmp(self,x,y):
        return -cmp(x,y)
    
    #def getOwner(self, node):
    #    nodes = node.xpath("ancestor::node")
    #    if (len(nodes)!=1):
    #        log.error("Tag %s has %d node ancestors",node.localName,len(nodes))
    #        raise Exception("aa")
    #    
    #    return nodes[0].attributes[(None,u'owner')].value;

    #def __changeState(self,prot,seq,ln,payload):
    #    print "changeState called"
    #    (username, path, newconfig) = pickle.loads(payload)
    #    (result, msg) = self.__setState(username, path, newconfig, "update")
    #	if (result==0):
    #		prot.sendReply(404,seq,msg)
    #	else:
    #		prot.sendReply(200,seq,"")

    #def addState(self,prot,seq,ln,payload):
    #     print "add state called"
    #     (username, path, newconfig) = pickle.loads(payload)
    #     (result,msg) = self.__setState(username, path, newconfig, "add")
    #	if (result==0):
    #		prot.sendReply(404,seq,msg)
    #	else:
    #		prot.sendReply(200,seq,"")

    #def removeState(self,prot,seq,ln,payload):
    #    print "remove state clled"
    #    (username, path, newconfig) = pickle.loads(payload)
    #    (result,msg) = self.__setState(username, path, newconfig, "remove")        
    #	if (result==0):
    #		prot.sendReply(404,seq,msg)
    #	else:
    #		prot.sendReply(200,seq,"")


#################################################################
# MAIN EXECUTION
#################################################################
def main():
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
    sock.bind((DaemonLocations.controlDaemon[0], DaemonLocations.controlDaemon[1]))
    sock.listen(10)
    server = ControlDaemon()
    server.start()

    while True:
        (s,a) = sock.accept()
        server.addSocket(s)
        
    sock.close()

if __name__ == "__main__":
    main()
