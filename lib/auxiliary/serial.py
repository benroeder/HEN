#!/usr/bin/env python
import __builtin__, sys, os, threading, termios, select, re, struct, array
sys.path.append("/usr/local/hen/lib")

HEADER_LENGTH = 14
PKT_TYPE_INDEX = 0
MSG_LENGTH_INDEX = 1
AM_MSGTYPE_INDEX = 9

BUFSIZE = 256
MTU = 256
ACK_TIMEOUT = 1000000 # in us

SYNC_BYTE = 0x7e
ESCAPE_BYTE = 0x7d

P_ACK = 0x40
P_PACKET_ACK = 0x41
P_PACKET_NO_ACK = 0x42
P_UNKNOWN = 0xFF

SETRFCHANNEL = 1
SETRFFREQUENCY = 2
SETRFPOWER = 3
SETLEDS = 4
INTROSPECT = 5

def bits(n, offset=0, size=8):
    bstring = ''
    for i in range(offset, size):
        bstring = str((n >> i) & 1) + bstring
    return bstring

def calc_byte(crc, b):
    crc = crc ^ b << 8
    
    for i in range(0, 8):
        if (crc & 0x8000) == 0x8000:
            crc = crc << 1 ^ 0x1021
        else:
            crc = crc << 1
    
    return crc & 0xffff

def calcn(packet, index, count):
    crc = 0
    
    while count > 0:
        crc = calc_byte(crc, packet[index])
        index += 1; count -= 1
    
    return crc;

def calc(packet, count):
    return calcn(packet, 0, count)
    
def set(packet):
    l = len(packet)
    crc = calc(packet, l - 2)
    
    packet[l - 2] = (crc & 0xff)
    packet[l - 1] = ((crc >> 8) & 0xff)

class IntrospectData:
    src = None
    maccrc = None
    mac = None
    smac = None
    macfamily = None
    rfpower = None
    rfpreset = None
    rffreq = None
    
class Serial:
    """\brief This class provides an interface to read from motes devices attached to serial ports. It
              supports file operations and thus instances can be treated as a file-like object.
    """
    
    def __init__(self, port, baudrate, msgfiles=[]):
        """\brief Initializes an instance in preparation for communication with the device on the specifeid
                  port at the given baud rate.
        \param port (\c string) the /dev node name of the serial device
        \param baudrate (\c int) the rate at which to communicate with the device
        \param msgfiles (\c list) the paths to C header files that define TinyOS message
        """
        self.__fd = None
        self.__port = port
        self.__baudrate = 'B'+str(baudrate)
	self.__msgfiles = msgfiles
        self.__seqno = 20
        self.__logger = None
	self.__exit_on_mac = False;
        
        # {amfilepath: ({enumname: enumvalue}, {amenumname: amenumvalue}, {structname:}, {amstructname:})
        self.__hfiles = {}
        for file in msgfiles: self.__parseHeaderFile(file)
        self.__handlers = {}
        self.__listening = 0
        self.addMessageListener(15, self.logReceived)
        self.addMessageListener(27, self.introspectReceived)
    
    def __getAMMsgName(self, msgtype):
        """\brief Returns a 2-tuple which contains the path of the C header file that defines
                  the AM message type corresponding to msgtype.
        \param msgtype (\c int) an int that indicates the type of the AM message to check.
        \return (\c tuple) the C header filepath defining and the name of the AM meesge type.
        """
        for file in self.__hfiles:
            for ammsgname in self.__hfiles[file][1]:
                if self.__hfiles[file][1][ammsgname] == str(msgtype):
                    ammsgname = ammsgname[3:-3].title()+ammsgname[-3:].title()
                    return file, ammsgname
        return None, None
    
    def __parseHeaderFile(self, filename):
        """\brief Parses the specified C header file, interating over and inturn delegating the parsing
                  of enums and structs contained within.
        \param Filename (\c sting) the file path to the C header file
        """
        self.__hfiles[filename] = ({}, {}, {}, {})
        headert = self.__hfiles[filename]
        enumMatcher = re.compile(r'enum(?: {)?')
        msgStructMatcher = re.compile(r'(?:typedef\s+)?struct ([\w]+Msg)(?: {)?')
        f = open(filename)
        lines = "".join(f.readlines()).split('\n')
        enum = struct = -1
        name = ''
        for i in range(0, len(lines)):
            if enum < 0 and enumMatcher.match(lines[i]):
                enum = i
                continue
            m = msgStructMatcher.match(lines[i])
            if struct < 0 and m:
                name = m.group(1)
                struct = i
                continue
            if re.match(r'}(\s?\w+)?\s?;', lines[i]):
                if enum >= 0:
                    self.__parseEnum(lines[enum:i+1], headert)
                if struct >= 0:
                    self.__parseStruct(lines[struct:i+1], name, headert)
                enum = struct = -1
    
    def __parseEnum(self, lines, headert):
        """\brief Parses the lines of a C header file, predetermined to contain an enum definition.
                  It extracts the name and (generated) value pairs and inserts them into one of two
                  enum dictionaries based on whether the pairing specifies a normal constant value or
                  an AM message type.
        \param lines (\c list) a list of consecutive lines of a C header file defining an enum.
        \param headert (\c dictionary) the dictionary of dictionaries containing all enums and structs
               defined in all parsed C header files.
        """
        enums, amenums = headert[:2]
        for i in range(0, len(lines)):
            m = re.match('\s+([\w\d_]+)(?:\s*=\s*([\d]+))[,;]?', lines[i])
            if m:
                e = enums
                if  m.group(1).startswith('AM'): e = amenums
                try:
                    e[m.group(1)] = m.group(2)
                except IndexError:
                    e[m.group(1)] = max(e.values())
    
    def __parseStruct(self, lines, structname, headert):
        """\brief Parses the lines of a C header file, predetermined to contain a struct definition.
                  It extracts the type/name pairs and inserts them into one of two struct dictionaries
                  based on whether the struct specifies a normal type or an AM message.
        \param lines (\c list) a list of consecutive lines of a C header file defining a struct.
        \param structname (\c string) the predetermined name of theis struct.
        \param headert (\c dictionary) the dictionary of dictionaries containing all enums and structs
               defined in all parsed C header files.
        """
        # mote data comes off the wire in LSB
        structs, amstructs = headert[2:]
        format = '<'
        fields = []
        for line in lines:
            m = re.match('\s+([\w\d]+)_t\s(\w+);', line)
            if m:
                if m.group(1) == 'char':
                    format += 'c'
                if m.group(1) == 'uint8':
                    format += 'B'
                if m.group(1) == 'uint16':
                    format += 'H'
                fields.append(m.group(2))
            m = re.match('\s+([\w\d]+)_t\s(\w+)\[([\w\d]+)\];', line)
            if m:
                size = m.group(3)
                if not size.isdigit():
                    size = headert[0][size]
                if m.group(1) == 'char':
                    format += (size+'s')
                if m.group(1) == 'uint8':
                    format += (size+'B')
                if m.group(1) == 'uint16':
                    format += (size+'H')
                fields.append(m.group(2)+"["+size+"]")
        if structname.endswith('Msg'):
            amstructs[structname] = [format, fields]
        else:
            structs[structname] = [format, fields]
    
    def __extractMsg(self, packet, msglen):
        """\brief Extracts the (application level) active message from the packet.
        \param packet (\c array.array) the packet data as an array of bytes.
        \param msglen (\c int) the length of the active message to be extracted.
        \return (\c array.array) the extracted active message as an array of bytes.
        """
        msg = packet[11:-2]
        return msg
       
    def setLogger(self, logger):
        """\brief Sets the logger of this Serial instance.
        \param logger (\c logging.Logger) the logger to disseminate serial device output.
        """
        self.__logger = logger
    
    def getLogger(self):
        """\brief Gets the logger of this Serial instance.
        \return (\c logging.Logger) the logger used to disseminate serial device output.
        """
        return self.__logger
    
    def addMessageListener(self, ammsgtype, handler):
        """\brief Adds a message handler for a specific message type.
                  Please see logReceived for an example of the expected
                  signature.
        \param ammsgtype (\c int) The Active Message type of the message to be handled.
        \param handler (\c callable) The handler to be called on arrival of a message.
        """
        if ammsgtype in self.__handlers:
            self.__handlers[ammsgtype].append(handler)
        else:
            self.__handlers[ammsgtype] = [handler]
        
    def removeMessageListener(self, ammsgtype, handler):
        """\brief Removes a message handler for a specific message type.
        \param ammsgtype (\c int) The Active Message type of the message that is being handled.
        \param handler (\c callable) The handler to be removed.
        """
        if ammsgtype not in self.__handlers:
            return
        else:
            self.__handlers[ammsgtype].remove(handler)
    
    def messageReceived(self, ammsgtype, msg):
        """\brief Generic method called when message arrives.
                  This method will find the list of handlers base on the message type
                  and dispatch copies of the message.
        \param ammsgtype (\c int) The Active Message type of the message.
        \param msg (\c array) The binary message.
        """
	#print "serial.messageReceived - %s" % msg.tostring()
        if ammsgtype in self.__handlers:
            for handler in self.__handlers[ammsgtype]:
                handler(ammsgtype, msg[:])
        else:
            self.__logger.debug(msg.tostring())
   
    def logReceived(self, ammsgtype, msg):
        """\brief Process log messages as sent by the THENUtilC mote utility.
                  This method converts the binary message in to asci and makes a log record
                  via the logger assigned to the serial port.
                  This method also returns the message as ascii text so can be called to parse
                  a binary log message.
        \param ammsgtype (\c int) The Active Message type of the message.
        \param msg (\c array) The binary message.
        \return (\c string) The ascii log message.
        """
        logmsg = struct.unpack("%ds" % len(msg), msg)[0]
        self.__logger.info(logmsg)
        return logmsg
    
    def introspectReceived(self, ammsgtype, msg):
        """\brief Process introspect messages as sent by the THENUtilC mote utility.
                  This method converts the binary message in an instance of IntrospectData.
                  The inforamtion is logged via the logger assigned to this serial port.
                  via the logger assigned to the serial port.
                  This method also returns the message as an IntrospectData instance so can be
                  called to parse binary introspect messages.
        \param ammsgtype (\c int) The Active Message type of the message.
        \param msg (\c array) The binary message.
        \return (\c IntrospectData) The parse inrospect data.
        """
        file, ammsgname = self.__getAMMsgName(ammsgtype)
        if ammsgname:
            fmt = self.__hfiles[file][3][ammsgname][0]
            fmtlen = struct.calcsize(fmt)
            data = struct.unpack(fmt, msg)
            # data[0:2] => src, maccrc
            # data[2:8] => mac
            # data[8:] => macfamily, rfpower, rfpreset, rffreq
            self.__logger.debug("Fields: %s (%s %d)" % (map("%s".__mod__, self.__hfiles[file][3][ammsgname][1]), fmt, fmtlen))
            self.__logger.debug(data[0:2]+tuple([":".join(map("%02x".__mod__, data[2:8]))])+data[8:])
            idata = IntrospectData()
            idata.src, idata.maccrc = data[0:2]
            idata.mac = data[2:8]
            idata.smac = ":".join(map("%02x".__mod__, data[2:8]))
            idata.macfamily, idata.rfpower, idata.rfpreset, idata.rffreq = data[8:]

            if self.__exit_on_mac :
	        print idata.smac
	    	sys.exit(0)
		
            return idata
            
    
    def introspect(self):
        """\brief Sends an introspect request to the mote and waits with a timeout
                  for a reply.
        \return (\c IntrospectData) An introspect data if the request could be serviced;
                                    None otherwise
        """
        file, ammsgname = self.__getAMMsgName(20)
        fmt = self.__hfiles[file][3][ammsgname][0]
        txmsg = struct.pack(fmt, 5, 32768, 0)
        #timer = threading.Timer(2, self.writeMsg, [txmsg, 20, 0x7d])
        #timer.start()
	
	self.__exit_on_mac = True
	self.writeMsg(txmsg, 20, 0x7d)
	self.listen()
        #rxmsg = self.readMsg(27, 4)
        #if rxmsg:
        #    return self.introspectReceived(27, rxmsg)
        #return None

    def open(self):
        self.__fd = os.open(self.__port, os.O_RDWR|os.O_NOCTTY)
        iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(self.__fd)
        cflag = termios.CS8 | termios.CLOCAL | termios.CREAD
        iflag = termios.IGNPAR | termios.IGNBRK
        oflag = 0
        ispeed = vars(termios)[self.__baudrate]
        ospeed = vars(termios)[self.__baudrate]

        termios.tcflush(self.__fd, termios.TCIFLUSH)
        termios.tcsetattr(self.__fd, termios.TCSANOW, [iflag, oflag, cflag, lflag, ispeed, ospeed, cc])
    
    def close(self):
        self.__listening = 0
        try: os.close(self.__fd)
        except: pass
    
    def writePkt(self, msg, length):
        smsg = " ".join(map("%02x".__mod__, msg))
        self.__logger.debug("Message: %s", smsg)
        
        bytes = array.array('B')
        
        bytes.append(P_PACKET_NO_ACK)
        
        bytes.append(length)
        bytes.append(0x01)                  # fcn_hi
        bytes.append(0x08)                  # fcn_lo
        bytes.append(self.__seqno % 256)    # seq #
        bytes.append(0xff)                  # dsn
        bytes.append(0xff)                  # dsn
        bytes.append(0xff)                  # bcast addr
        bytes.append(0xff)                  # bcast addr
        
        bytes.extend(msg)
        
        bytes.extend([0]*2)             	# crc placeholder
        set(bytes)
        
        packet = array.array('B')
        
        packet.append(SYNC_BYTE)
        
        for byte in bytes:
            if byte == ESCAPE_BYTE or byte == SYNC_BYTE:
                packet.append(ESCAPE_BYTE)
                packet.append(byte ^ 0x20)
                continue
            packet.append(byte)
        
        packet.append(SYNC_BYTE)
        
        try:
            self.__logger.debug("Packet: %s", " ".join(map("%02x".__mod__, packet)))
            return os.write(self.__fd, packet)
            print "Done"
            self.__seqno += 1
        except msg:
            print msg
            return -1
    
    def writeMsg(self, msg, ammsgtype, groupid):
        from fcntl import fcntl, F_SETFL
        if (fcntl(self.__fd, F_SETFL, 0) < 0):
            return 1;
        
        self.__logger.debug("Data: %s", " ".join(map("%02x".__mod__, map(ord, msg))))
        
        bytes = array.array('B')
        
        bytes.append(int(ammsgtype))
        bytes.append(groupid)
        
        if type(msg) == type(bytes) \
        and msg.typecode == bytes.typecode:
            bytes.extend(msg)
        elif type(msg) == type(''):
            bytes.fromstring(msg)
        elif type(msg) == type([]):
            if len(msg) == 0:
                return -1
            for char in msg:
                if (type(msg[0]) != type(char)):
                    return -1
            if type(msg[0]) == type(''):
                bytes.extend(map(ord, msg))
            elif type(msg[0]) == type(0):
                bytes.extend(msg)
        else:
            return -1
        
        return self.writePkt(bytes, len(msg))
    
    def read(self, timeout=None):
        ready,_,_ = select.select([self.__fd],[],[self.__fd])
        if not ready:
            raise RuntimeError("some error occured")
        char = os.read(self.__fd, 1)
        if char == '': # EOF
            raise EOFError
        return ord(char)
        
    def readPkt(self, frames=0):
        bytes = array.array('B')
        insync = False
        escaped = False
        escapedbyte = 0
        pkttype = ammsgtype = length = crc = count = 0
        while True:
            byte = self.read()
            if byte == SYNC_BYTE:
                if frames > 1:
                    bytes.append(SYNC_BYTE)
                if not insync:
                    if count > 0:
                        bytes = array.array('B')
                    insync = True
                    crc = 0
                    count = 0
                     # start of frame
                    continue
                if (len(bytes) < 2 and frames < 2) or len(bytes) < 5:
                    insync = False
                    escaped = False
                    crc = 0
                    count = 0
                    continue
                if frames < 2:
                    crc_lo = bytes[-2]
                    crc_hi = bytes[-1]
                else:
                    crc_bytes = bytes[-5:-1]
                    if crc_bytes[2] == ESCAPE_BYTE:
                        crc_hi = crc_bytes[3] ^ 0x20
                        if crc_bytes[0] == ESCAPE_BYTE:
                            crc_lo = crc_bytes[1] ^ 0x20
                        else:
                            crc_lo = crc_bytes[1]
                    else:
                        crc_hi = crc_bytes[3]
                        if crc_bytes[1] == ESCAPE_BYTE:
                            crc_lo = crc_bytes[2] ^ 0x20
                        else:
                            crc_lo = crc_bytes[2]

                if crc != (crc_lo | (crc_hi << 8)):
                    if count > 0:
                        bytes = array.array('B')
                    insync = False
                    escaped = False
                    crc = 0
                    count = 0
                    continue
                    
                # end of frame
                return pkttype, ammsgtype, bytes, length, crc
            if not insync:
                continue
            if byte == ESCAPE_BYTE and not escaped:
                if frames > 1:
                    bytes.append(ESCAPE_BYTE)
                escaped = True
                continue
            escapedbyte = byte
            if escaped:
                escaped = False
                if byte == ESCAPE_BYTE or byte == SYNC_BYTE:
                    insync = False
                    continue
                escapedbyte = byte ^ 0x20
                if frames < 2:
                    byte = escapedbyte
            if count == PKT_TYPE_INDEX: pkttype = escapedbyte
            if count == MSG_LENGTH_INDEX: length = escapedbyte
            if count == AM_MSGTYPE_INDEX: ammsgtype = escapedbyte
            if count < HEADER_LENGTH + length - 3:
                crc = calc_byte(crc, escapedbyte)
            bytes.append(byte)
            count += 1
        
    def readMsg(self, ammsgtype, timeout=None):
        self.__listening += 1
        event = threading.Event()
        def listenHook(ammsgtype, msg):
            if not event.isSet():
                listenHook.func_dict["MESSAGE"] = msg
                event.set()
        listenHook.func_dict["MESSAGE"] = None
        self.addMessageListener(ammsgtype, listenHook)
        event.wait(timeout)
        self.__listening -= 1
        self.removeMessageListener(ammsgtype, listenHook)
        return listenHook.func_dict["MESSAGE"]
    
    def listen(self, frames=0):
        """\brief Listens to the mote device for ever until some error occurs or the thread
                  is interupted.
        \param frame (\c int) The levels of framing to preserve on the packet;
                              0 means de-frame upto and including the TinyOS message frame.
        """
	#print "listening"
        try:
            self.__listening += 1 
            attempts = 0
            while self.__listening:
                try:
                    pkttype, ammsgtype, packet, length, crc = self.readPkt(frames)
                    attempts = 0
                except EOFError:
                    #self.__logger.error("EOF detected (serial device may have been detached); closing")
                    #if attempts > 5:
                    #    self.__listening = 0
                    #attempts += 1
#		    print "*err (EOFError)"
                    continue
                if not packet:
                    #self.__listening = 0
#		    print "*err (null)"
                    continue
                if frames < 2:
                    if pkttype == P_PACKET_ACK:
                        # should send acknowledgement with packet[1]
                        print "Imaginary acknowledgement sent"
                        #self.write_framed_packet(P_ACK, None, 1)
                        pass
                    msg = self.__extractMsg(packet, length)
                    # need to swap the crc bytes LSB -> MSB
                    if frames == 0:
                        self.messageReceived(ammsgtype, msg)
                    else:
                        self.__logger.debug("Raw message:%s" % " ".join(map("%02x".__mod__, packet)))
                else:
                    self.__logger.debug("Raw packet:%s" % " ".join(map("%02x".__mod__, packet)))
        except KeyboardInterrupt:
            return self.close()
    
if __name__ == '__main__':
    import logging
    from optparse import OptionParser
    from glob import glob
    
    parser = OptionParser()
    parser.add_option("-d", "--device",
                      help="the serial DEVICE to read/write to")
    parser.add_option("-b", "--baud",
                      choices=["57600"], default="57600",
                      help="specify the BAUD rate to read write to DEVICE")
    parser.add_option("-l", "--listen", action="store_true", default=False,
                      help="indicate whether to LISTEN to the port for output")
    parser.add_option("-p", "--path",
                      help="specify the PATH to the XxxMsg.h header file(s)")
    parser.add_option("-m", "--msg", action="append",
                      choices=["IntrospectMsg", "LoggingMsg", "OscopeMsg"], default=[],
                      help="filter input data for messages of type MSG")
    parser.add_option("-f", "--frame", action="count",
                      dest="frames", default=0,
                      help="leave the n * -f levels of framing intact; -f:AM packet; -f -f:HDLC frame")
    parser.add_option("-g", "--debug",
                      choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"], default="INFO",
                      help="the DEBUG level to use for this serial connection; one of: %s" % \
                      ", ".join(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]))
    parser.add_option("-i", "--mac", action="store_true", default=False, help="indicate whether to exit \
    	after a MAC address is returned")
    (options, args) = parser.parse_args(sys.argv[1:])
    
    msgfiles = glob(options.path+"*Msg.h")
    
    s = Serial(options.device, options.baud, msgfiles)
    levels = dict(zip(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
                 [logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]))
    logging.basicConfig(level=levels[options.debug], stream=sys.stdout)
    s.setLogger(logging.getLogger(options.device))
    
    s.open()
    if len(args) > 1:
        data = []
        fmt = "<" # LSB-little endian
        amtype, groupid = args[0:2]
        for arg in args[2:]:	
            if arg.isdigit():
                data.append(int(arg, 0))
                fmt += "H"
            elif arg.isalnum():
                if type(arg) == str:
                    data.extend(map(ord, arg))
                    fmt += "%ds" % len(arg)
                else:
                    print "Error: unicode is not supported. use 8-bit ascii."
                    data = None
                    break
            else:
                data.insert(0, fmt)
                txmsg = apply(struct.pack, data)
		s.writeMsg(txmsg, int(amtype, 0), int(groupid, 0))
    if options.listen:
        s.listen(options.frames)
    elif options.mac :
        s.introspect()
	  
    try: s.close()
    except: pass
