import select
import threading
from auxiliary.protocol import Protocol
import logging
import traceback
import sys, gc, inspect, types, pickle,hashlib

log = logging.getLogger()

class Daemon(threading.Thread):
    version = None
    """\brief Implements basic daemon functionality to deal with multiple 
    customers as they arrive.
    """    
    def __init__(self, useSSL=False):
        """\brief Inits the daemon, adds get_supported_methods as a default
        method to allow some sort of reflection
        """
        self.__useSSL = useSSL
        self.__accept_connections = True
        self.__handlers = {}

        # These need to be public so that run method can be overridden
        self.isStopped = False
        self.protocol_list = []        
        self.sock_list = []
        
        threading.Thread.__init__(self)
        self.__handlers["get_supported_methods"] = self.listHandlers
        self.__handlers["get_garbagedump"] = self.getGarbageDump
        self.__handlers["get_refcounts"] = self.getRefCounts
        self.__handlers["get_cli_commands"] = self.getCLICommands

    def setVersion(self, version):
        self.version = version
        
    def getCLICommands(self,prot,seq,ln,payload):
        """\brief RPC call to retrieve CLI commands via XML.
        XXX: See http://arkell.cs.ucl.ac.uk/hen/commands.xml for syntax
        NOTE: This function needs overriding if your daemon is to have any CLI
        functionality.
        """
        prot.sendReply(404, seq, \
                       "get_cli_commands not implemented on this daemon.")
   
    def addSocket(self,sock):
        """\brief Accepts a new customer
        \param socket (\c socket) The opened socket
        """
        self.sock_list.append(sock)
        prot = Protocol(sock, self.__useSSL)

        for i in self.__handlers:
            prot.registerMethodHandler(i,self.__handlers[i])
            
        self.protocol_list.append(prot)

    def setConfig(self,prot,seq,ln,payload):
        """\brief Parses state from the hen manager.
        The payload is a pickled version of all the nodes in the hardware hen config. In the future
        it must support delta updates and versioning
        """
        try:
           i = payload.index(",")
           version = payload[0:i]

           if version==str(self.version):
                prot.handleError(404,seq,"Current version "+str(self.version)+" is equal to supplied argument "+version)
		return

           nodes = pickle.loads(payload[i+1:])

           self.version = version
           log.debug("Got version %s and config with len %d",str(self.version), len(payload[i+1:]))
	   
	   (ret,string) = self.setConfigHandler(nodes)
	   if (ret==0):
		prot.sendReply(404,seq,string)
	   else:
           	m = md5.new()
          	m.update(payload)
           	prot.sendReply(200, seq, m.digest())
	except Exception,e:
		prot.sendReply(404,seq,str(e))

    def setConfigHandler(self,nodes):
	log.debug("SetConfigHandler not implemented!")
	return (0,"SetConfigHandler not implemented!")
    
    def registerMethodHandler(self,method,handler):
        """\brief Registers methods that will be available to clients. 
       	These are passed to the protocols when clients show up see protocol 
        setMethodHandler for more details.
        """
        self.__handlers[method] = handler;
    
    def listHandlers(self,prot,seq,ln,payload):
        """\brief Implements the get_supported_methods rpc
        """
        payload = ""
        for i in self.__handlers.keys():
            payload = payload + i+"\n"
        prot.sendReply(200, seq, payload)

    def acceptingConnections(self):
        """\brief To question whether the daemon is accepting connections"""
        return self.__accept_connections
    
    def acceptConnections(self, enable):
        """\brief Sets the accept_connections boolean to the value given"""
        self.__accept_connections = enable

    def stop(self):
        
        self.__accept_connections = False
        self.isStopped = True
      
    def run(self):
        """\brief Main daemon loop
        Waits for messages from clients and processes them. Only sleeps for two 
        seconds, to accept new clients also.
        """

        while not self.isStopped:
            read = []
            write = []
            exc = []
            try:
                #select sockets
                (read,write,exc) = \
                                 select.select(self.sock_list,[],self.sock_list,2)

            except select.error, v:
                if v[0] == 4:
                    self.stop()
                    pass


            for i in read:
                s = None

                # Process regular socket
                try:
                    s = i.recv(1000000,0)
                # Process SSL socket
                except:
                    try:
                        s = i.read(1000000)
                    except:
                        s = []
                try:
                    #log.debug("Read from socket:"+s.replace("\r","\\r"))

                    if (len(s)==0):
                        #log.debug("removing")
                        idx = self.sock_list.index(i)
                        del self.sock_list[idx]
                        del self.protocol_list[idx]
                    else:
                        self.protocol_list[self.sock_list.index(i)].\
                                                                processPacket(s)
                except Exception,e:
                    idx = self.sock_list.index(i)
                    del self.sock_list[idx]
                    del self.protocol_list[idx]
                    traceback.print_exc()
            for i in exc:
                log.debug ("exc",i)
#            if self.isStopped:
#                self.__accept_connections = False
#                break
                
    def getGarbageDump(self,prot,seq,ln,payload):
        payload = str(gc.garbage) + "\n\n"
        exclude = ["function","type","list","dict","tuple",
                   "wrapper_descriptor","module","method_descriptor",
                   "member_descriptor","instancemethod",
                   "builtin_function_or_method","frame","classmethod",
                   "classmethod_descriptor","_Environ","MemoryError",
                   "_Printer","_Helper","getset_descriptor"]
        gc.collect()
        oo = gc.get_objects()
        fileDict = {}
        objDict = {}

        for o in oo:
            if getattr(o, "__class__", None):
                name = o.__class__.__name__
                if name not in exclude:
                    try:
                        filename = inspect.getabsfile(o.__class__)
                        fileDict[name] = filename
                    except:
                        pass
                if not objDict.has_key(name):
                    objDict[name] = 0
                objDict[name] += 1
        sortedObjList = []
        for name in objDict.keys():
            sortedObjList.append((objDict[name], name))
        sortedObjList.sort()
        for (count, name) in sortedObjList:
            if fileDict.has_key(name):
                payload += "["+str(count)+"] "+str(name)+" {"+ \
                                str(fileDict[name])+"}\n"
            else:
                payload += "["+str(count)+"] "+str(name)+"\n"
        prot.sendReply(200, seq, payload)

    def getRefCounts(self,prot,seq,ln,payload):
        d = {}
        payload = ""
        sys.modules
        for m in sys.modules.values():
            for sym in dir(m):
                o = getattr (m, sym)
                if type(o) is types.ClassType:
                    d[o] = sys.getrefcount (o)
        pairs = map (lambda x: (x[1],x[0]), d.items())
        pairs.sort()
        pairs.reverse()
        for n, c in pairs:
            payload += '%10d %s\n' % (n, c.__name__)
        prot.sendReply(200, seq, payload)

