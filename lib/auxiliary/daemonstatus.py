import socket
from auxiliary.daemonlocations import DaemonLocations

class DaemonStatus:
    
    def isOnline(self, (host,port), timeout=5):
        """\brief Checks whether given host/port accepts connections. If so,
            returns true, else returns false.
            \param (host,port) - host/port tuple to check
            \return result - true if host/port accepts a connection, and
                            responds to the standard "get_supported_methods"
                            rpc call. False otherwise.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        online = False
        try:
            s.connect((host, port))
            s.send("\rREQ get_supported_methods 1 0\r")
            reply = s.recv(1024)
            if len(reply) > 0:
                online = True
            s.close()
        except Exception:
            pass
        return online
       
    """ Wrappers for convenience """
    
    def switchDaemonIsOnline(self, timeout=5):
        return self.isOnline(DaemonLocations.switchDaemon, timeout)

    def autodetectDaemonIsOnline(self, timeout=5):
        return self.isOnline(DaemonLocations.autodetectDaemon, timeout)
    
    def monitorDaemonIsOnline(self, timeout=5):
        return self.isOnline(DaemonLocations.monitorDaemon, timeout)
    
    def authenticationDaemonIsOnline(self, timeout=5):
        return self.isOnline(DaemonLocations.authenticationDaemon, timeout)
    
    def controlDaemonIsOnline(self, timeout=5):
        return self.isOnline(DaemonLocations.controlDaemon, timeout)
    
    def systemDaemonIsOnline(self, timeout=5):
        return self.isOnline(DaemonLocations.systemDaemon, timeout)
    
    def powerDaemonIsOnline(self, timeout=5):
        return self.isOnline(DaemonLocations.powerDaemon, timeout)
    
    def emergencyDaemonIsOnline(self, timeout=5):
        return self.isOnline(DaemonLocations.emergencyDaemon, timeout)

    def henStatusDaemonIsOnline(self, timeout=5):
        return self.isOnline(DaemonLocations.henstatusDaemon, timeout)
    
    def getAllDaemonStatusMethods(self):
        """\brief Returns a list of tuples of the form:
                ((daemonName, statusMethodRef),..)
        """
        return (("SwitchDaemon", self.switchDaemonIsOnline), \
                ("AutodetectDaemon", self.autodetectDaemonIsOnline), \
                ("MonitorDaemon", self.monitorDaemonIsOnline), \
                ("AuthenticationDaemon", self.authenticationDaemonIsOnline), \
                ("ControlDaemon", self.controlDaemonIsOnline), \
                ("SystemDaemon", self.systemDaemonIsOnline), \
                ("PowerDaemon", self.powerDaemonIsOnline), \
                ("EmergencyDaemon", self.emergencyDaemonIsOnline), \
                ("HenStatusDaemon", self.henStatusDaemonIsOnline)
                )
