# Class to store the port numbers for the various testbed daemons

class DaemonLocations:

    # Switchdaemon 
    try:
        __switchdip = os.environ['SWITCHDIP']
        log.debug("Setting non standard switchd ip "+str(__switchdip))
    except:
        __switchdip = "server1.infrastructure-hen-net"
    try:
        __switchdport = os.environ['SWITCHDPORT']
        log.debug("Setting non standard switchd port "+str(__switchdport))
    except:
        __switchdport = 56000    
    switchDaemon = (__switchdip,__switchdport)
    
    # Switchdaemon 2
    try:
        __switchd2ip = os.environ['SWITCHD2IP']
        log.debug("Setting non standard switchd2 ip "+str(__switchd2ip))
    except:
        __switchd2ip = "server2.infrastructure-hen-net"
    try:
        __switchd2port = os.environ['SWITCHD2PORT']
        log.debug("Setting non standard switchd2 port "+str(__switchd2port))
    except:
        __switchd2port = 90000    
    switchDaemon2 = (__switchd2ip,__switchd2port)
    
    autodetectDaemon = ("server2.hen-net", 56001)
    monitorDaemon = ("server1.infrastructure-hen-net", 56002)
    authenticationDaemon = ("server1.infrastructure-hen-net", 56003)
    controlDaemon = ("server1.infrastructure-hen-net", 56004)
    systemDaemon = ("server1.infrastructure-hen-net", 56005)
    powerDaemon = ("server1.infrastructure-hen-net", 56016)
    emergencyDaemon = ("server4.infrastructure-hen-net", 56007)
    henstatusDaemon = ("server4.infrastructure-hen-net", 56008)
    computerDaemon = ("localhost", 56009)
    consoleDaemon = ("server1.infrastructure-hen-net", 56010)
    configDaemon = ("server1.hen-net", 56011)
    switchMonitorDaemon = ("server1.infrastructure-hen-net", 56012)
    moteDaemon = ("localhost", 56011)
    reservationDaemon = ("server1.infrastructure-hen-net", 56013)
    autodetectClientDaemon = ("0.0.0.0", 56014)	
