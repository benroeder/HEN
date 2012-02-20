import socket
import select
import threading
import protocol
import sys
import logging

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

class Server(threading.Thread):
    __sock_list = []
    __protocol_list = []
    __handlers = {}
    __stop = False
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.__handlers["get_supported_methods"] = self.listHandlers
        
    def addSocket(self,sock):
        self.__sock_list.append(sock)
        prot = protocol.Protocol(sock)

        for i in self.__handlers:
            prot.registerMethodHandler(i,self.__handlers[i])
            
        self.__protocol_list.append(prot)
    
    def registerMethodHandler(self,method,handler):
        self.__handlers[method] = handler;
    
    def listHandlers(self,prot,seq,ln,payload):
        payload = ""
        for i in self.__handlers.keys():
            payload = payload + i+"\n"
        prot.sendReply(200, seq, payload)

    def run(self):
        while (not self.__stop):
            #select sockets
            (read,write,exc) = select.select(self.__sock_list,[],self.__sock_list,2)
            for i in read:
                try:
                    s = i.recv(4096,0)
                    
                    log.debug("Read from socket:"+s.replace("\r","\\r"))

                    if (len(s)==0):
                        log.debug("removing")
                        idx = self.__sock_list.index(i)
                        del self.__sock_list[idx]
                        del self.__protocol_list[idx]
                    else:
                        self.__protocol_list[self.__sock_list.index(i)].processPacket(s)
                except Exception,e:
                    log.debug ("removing because of ",e)
                    idx = self.__sock_list.index(i)
                    del self.__sock_list[idx]
                    del self.__protocol_list[idx]
            for i in exc:
                log.debug ("exc",i)

            

#main server loop
#creating listening socket
sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)

port = 1105
if len(sys.argv)>1:
    port = int(sys.argv[1])
    
log.debug("Binding to port:"+str(port))

sock.bind(("localhost",port))
sock.listen(10)
server = Server()
server.start()

while True:
    (s,a) = sock.accept()
    log.debug("accept")
    server.addSocket(s)

sock.close()