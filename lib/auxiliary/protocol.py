import logging
import socket

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

#MAX_PACKET_SIZE = 4096
MAX_PACKET_SIZE = 8194

class Protocol:
    """\brief Implements the simple RPC protocol, deals with message reassembly and structure verification. Is used by daemons and clients alike
    """
    def __init__(self,socket,useSSL=False):
        """\brief Inits the protocol
        \param socket (\c socket) The opened socket used for the protocol
        """
        self.__socket = socket
        self.__fileNumber = None
        self.__useSSL = useSSL
        
        self.__handlers = {}
        self.__callbacks = {}
        self.__seqNumbers = 0
        self.__returnValues = {}

        self.__payload = None
        self.__packetInFlight = None


    def open(self,host,port):
        """\brief Opens a (TCP) connection
        \param host (\c string) The destination host name
        \param port (\c string) The destination port
        """
        if (self.__useSSL):
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__fileNumber = self.__socket.fileno()
            self.__socket.connect((host,port))
            self.__socket = socket.ssl(self.__socket)
        else:
            self.__socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
            self.__fileNumber = self.__socket.fileno()            
            self.__socket.connect((host,port))

    def close(self):
        """\brief Closes the socket
        """
        self.__socket.close()

    def readAndProcess(self):
        """\brief Reads a packet from the connection and processes it
        """
        buf = None
        if (self.__useSSL):
            buf = self.__socket.read(MAX_PACKET_SIZE)
        else:
            buf = self.__socket.recv(MAX_PACKET_SIZE,0)
        packet = buf
        while True:
            pkt = self.getPacketType(packet)
            plen = pkt[3]+pkt[4]
            while plen > len(packet):
                if (self.__useSSL):
                    buf = self.__socket.read(MAX_PACKET_SIZE)
                else:
                    buf = self.__socket.recv(MAX_PACKET_SIZE,0)
                packet = packet + buf

            self.processPacket(packet[:plen])
            if (plen<len(packet)):
                packet = packet[plen:]
            else:
                break
    
    def registerMethodHandler(self,method,handler):
        """\brief Registers a method handler that will be called when a packet for that method arrives or when a response arrives for a given message
        \param method (\c string) Method name
        \param handler (\c function pointer) A pointer to a method that takes, besides the self pointer, 3 parameters
        """
        self.__handlers[method] = handler;

    def handleError(self,code,seq,message):
        """\brief Returns an error code and message to the endpoint
        \param code (\c int) Error code. e.g. 500 Internal server error, etc
        \param seq (\c int) Sequence number, used to denote the call this answer corresponds to
        """
        self.sendReply(code, seq, message)

    def sendRequest(self,method,payload,callback):
        """\brief Packs and sends a method call request
        \param method (\c string) Method name
        \param payload (\c string) Method parameters, can be anything serialized in string form
        \param callback (\c function pointer) Callback function for response messages
        """
        self.__seqNumbers += 1

        self.__callbacks[self.__seqNumbers] = callback

        packet = "\rREQ "+method+" "+str(self.__seqNumbers)+" "+str(len(payload))+"\r"+payload

        if (self.__useSSL):
            self.__sslSendAll(packet)
        else:
            self.__socket.send(packet)

        return self.__seqNumbers

    def synchronousCallback(self,code,seq,sz,payload):
        self.__returnValues[seq].append((code,sz,payload))

    def doSynchronousCall(self,method,payload):
        seqNo = self.sendRequest(method,payload,self.synchronousCallback)
        self.__returnValues[seqNo] = []

        resultCount = 0
        while True:
            self.readAndProcess()
            if (len(self.__returnValues[seqNo])<=resultCount):
                log.error("Send synchronous request failed")
                return
            (code,sz,payload) = self.__returnValues[seqNo][resultCount]
            if (code!=100):
                retValue = self.__returnValues[seqNo]
                del self.__returnValues[seqNo]
                return retValue
            else:
                log.debug("Synchronous request 100, going on")
                resultCount+=1

    def sendReply(self,code, seq, payload):
        """\brief Packs and sends a method call reply
        \param code (\c int) Return code
        \param seq (\c int) Sequence number, identifies the request
        \param payload (\c string) Return value of the function
        """
        packet = "\rRESP " + str(code) + " " + str(seq) + " " + \
                 str(len(payload)) + "\r" + payload

        if (self.__useSSL):
            self.__sslSendAll(packet)
            return

        while len(packet) > MAX_PACKET_SIZE:
            try:
                self.__socket.send(packet[:MAX_PACKET_SIZE])
                packet = packet[MAX_PACKET_SIZE:]
            except Exception, e:
                log.debug("Error sending packet: %s" % str(e))
        if len(packet) > 0:
            try:
                self.__socket.send(packet)
            except Exception, e:
                log.debug("Error sending packet: %s" % str(e))

    def getPacketType(self,packet):
        """\brief Returns packet type by inspecting the first bytes of the packet. If type is unknown, raises an error
        \param packet (\c string) Packet header
        """
        if packet[0:5]=="\rREQ ":
            try:
                i = packet.index(" ",5)
                method = packet[5:i]
                j = packet.index(" ",i+1)
                seq = int(packet[i+1:j])

                k = packet.index("\r",j+1)
                ln = int(packet[j+1:k])

                return (1,method,seq,ln,k+1)
            except Exception,e:
                log.error(e)
        elif packet[0:6]=="\rRESP ":
            try:
                i = packet.index(" ",6)
                code = int(packet[6:i])

                j = packet.index(" ",i+1)
                seq = int(packet[i+1:j])

                k = packet.index("\r",j+1)
                ln = int(packet[j+1:k])

                return (2,code,seq,ln,k+1)

            except Exception,e:
                log.error(e)
                return None

        else:
            log.error("Packet does not start with REQ or RESP, instead %s",packet[0:6].replace("\r","\\r"))
            return None

    def processRequest(self, pkt, payload):
        """\brief Processes a request received from the wire by calling the appropriate handlers
        \param pkt (\c int) tuple describing packet type, method or return code, payload length and start of payload in the packet
        \param payload (\c string) Payload
        """
        if pkt[0]==1:
            if not self.__handlers.has_key(pkt[1]):
                self.handleError(404,pkt[2],"No such method "+pkt[1]+"\nTry get_supported_methods for a list of options");
            else:
                self.__handlers[pkt[1]](self,pkt[2],pkt[3],payload)
        elif pkt[0]==2:
            self.__callbacks[pkt[2]](pkt[1],pkt[2],pkt[3],payload)
        else:
            log.error("Wrong type of packet received %d",pkt[0])

    def processPacket(self,packet):
        """\brief Bundles packets into full request and passes them to the processRequest function
        \param packet (\c int) stuff received from the wire
        """
        if self.__packetInFlight==None:
            pkt = self.getPacketType(packet)
            if pkt==None:
                return
            if len(packet)-pkt[4]<pkt[3]:
                self.__payload = packet[pkt[4]:]
                self.__packetInFlight = pkt
            elif len(packet)-pkt[4]==pkt[3]:
                self.processRequest(pkt,packet[pkt[4]:])
            else:
                log.error("WEIRD: Packet length is %d payload len is %d  and k is %d",len(packet),pkt[3],pkt[4])
                pass
        else:
            toAdd = self.__packetInFlight[3] - len(self.__payload)
            if (toAdd<=0):
                log.error("WEIRD toadd is not strictly positive %d", toAdd)
                return
            self.__payload = self.__payload + packet[0:min(toAdd,len(packet))]

            if len(self.__payload)==self.__packetInFlight[3]:
                #print "process packet on retry"
                self.processRequest(self.__packetInFlight,self.__payload)
                self.__payload = None
                self.__packetInFlight = None

                if toAdd<len(packet):
                    self.processPacket(packet[toAdd+1:])

    def __sslSendAll(self, buf):
        bytesWritten = 0
        while bytesWritten < len(buf):
            try:
                bytesWritten += self.__socket.write(buf[bytesWritten:])
            except Exception, e:
                log.debug("Error sending packet: %s" % str(e))

    def getSocket(self):
        return self.__socket

    def getFileNumber(self):
        return self.__fileNumber
