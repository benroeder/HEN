from pysnmp.proto.rfc1902 import ObjectName

class OID:

    sysName = ObjectName("1.3.6.1.2.1.1.5.0")
    sysDescr = ObjectName("1.3.6.1.2.1.1.1.0")
    sysUpTimeInstance = ObjectName("1.3.6.1.2.1.1.3.0")
    sysContact = ObjectName("1.3.6.1.2.1.1.4.0")
    sysLocation = ObjectName("1.3.6.1.2.1.1.6.0")
    
    dot1dBaseNumPorts = ObjectName("1.3.6.1.2.1.17.1.2.0")
    dot1dBasePortIfIndex = ObjectName("1.3.6.1.2.1.17.1.4.1.2")

    dot1dTpFdbAddress = ObjectName("1.3.6.1.2.1.17.4.3.1.1")
    dot1dTpFdbPort = ObjectName("1.3.6.1.2.1.17.4.3.1.2")
    dot1dTpFdbStatus = ObjectName("1.3.6.1.2.1.17.4.3.1.3")

    ifAdminStatus = ObjectName("1.3.6.1.2.1.2.2.1.7")
    ifOperStatus = ObjectName("1.3.6.1.2.1.2.2.1.8")
    ifDescr = ObjectName("1.3.6.1.2.1.2.2.1.2")
    ifIndex = ObjectName("1.3.6.1.2.1.2.2.1.1")
    ifType = ObjectName("1.3.6.1.2.1.2.2.1.3")
    ifAlias = ObjectName("1.3.6.1.2.1.31.1.1.1.18")
                         
    ifName = ObjectName("1.3.6.1.2.1.31.1.1.1.1")
    ifStackStatus = ObjectName("1.3.6.1.2.1.31.1.2.1.3")
    ifInOctects = ObjectName("1.3.6.1.2.1.2.2.1.10")
    ifInUcastPkts = ObjectName("1.3.6.1.2.1.2.2.1.11")
    ifOutUcastPkts = ObjectName("1.3.6.1.2.1.2.2.1.17")
    ifSpeed = ObjectName("1.3.6.1.2.1.2.2.1.5")

    dot1qTpFdbEntry = ObjectName("1.3.6.1.2.1.17.7.1.2.2.1")
    dot1qTpFdbPort = ObjectName("1.3.6.1.2.1.17.7.1.2.2.1.2")
    dot1qTpFdbStatus = ObjectName("1.3.6.1.2.1.17.7.1.2.2.1.3")
    
    dot1qVlanStaticEntry = ObjectName("1.3.6.1.2.1.17.7.1.4.3.1") # Dot1qVlanStaticEntry 
    dot1qVlanStaticName = ObjectName("1.3.6.1.2.1.17.7.1.4.3.1.1")
    dot1qVlanFdbId = ObjectName("1.3.6.1.2.1.17.7.1.4.2.1.3")
    dot1qVlanStaticEgressPorts = ObjectName("1.3.6.1.2.1.17.7.1.4.3.1.2") # portlist
    dot1qVlanForbiddenEgressPorts  = ObjectName("1.3.6.1.2.1.17.7.1.4.3.1.3") # portlist
    dot1qVlanStaticUntaggedPorts  = ObjectName("1.3.6.1.2.1.17.7.1.4.3.1.4") # portlist
    dot1qVlanStaticRowStatus  = ObjectName("1.3.6.1.2.1.17.7.1.4.3.1.5") #    RowStatus 1:active, 2:notInService, 3:notReady, 4:createAndGo, 5:createAndWait, 6:destroy
    dot1qPvid = ObjectName("1.3.6.1.2.1.17.7.1.4.5.1.1")

    linksysGeneralPortAccess = ObjectName("1.3.6.1.4.1.89.48.22.1.1")

    force10chSysCardUpperTemp = ObjectName("1.3.6.1.4.1.6027.3.1.1.2.3.1.8")
    force10chSerialNumber = ObjectName("1.3.6.1.4.1.6027.3.1.1.1.2.0")

    # 4526.1.2.13.1.1.1.<vlan id> = i <vlan id>
    # 4526.1.2.13.1.1.2.<vlan id> = s <vlan name>
    # 4526.1.2.13.1.1.3.<vlan id> = i <active 1 ? >
    netgearVlanStaticId = ObjectName("1.3.6.1.4.1.4516.1.2.13.1.1.1")
    netgearVlanStaticName = ObjectName("1.3.6.1.4.1.4526.1.2.13.1.1.2")
    netgearVlanStaticRowStatus = ObjectName("1.3.6.1.4.1.4526.1.2.13.1.1.3") # i 6 destroy, i 1 active , 5 create (and wait ? ) 4 works too
    # pvid 1.3.6.1.4.1.4526.1.2.11.6.1.12.<pid> i <vlan id>
    netgearGeneralPortAccess = ObjectName("1.3.6.1.4.1.4526.1.2.11.6.1.12")
    # port member
    #4526.1.2.13.2.1.1.<pid>.<vlan id> = i <pid>
    #4526.1.2.13.2.1.2.<pid>.<vlan id> = i <vlan id>
    #4526.1.2.13.2.1.3.<pid>.<vlan id> = i 1
    #4526.1.2.13.2.1.4.<pid>.<vlan id> = i <tagged = 2, untagged = 1>
    netgearVlanTaggedTable = ObjectName("1.3.6.1.4.1.4526.1.2.13.2.1")
    netgearVlanTaggedPortId = ObjectName("1.3.6.1.4.1.4526.1.2.13.2.1.1")
    netgearVlanTaggedVlanId = ObjectName("1.3.6.1.4.1.4526.1.2.13.2.1.2")
    # guess work about this row
    netgearVlanTaggedRowStatus = ObjectName("1.3.6.1.4.1.4526.1.2.13.2.1.3")
    netgearVlanTaggedType  = ObjectName("1.3.6.1.4.1.4526.1.2.13.2.1.4")

    ciscoVtpVlanState = ObjectName("1.3.6.1.4.1.9.9.46.1.3.1.1.2")
    ciscoVtpVlanEditTable = ObjectName("1.3.6.1.4.1.9.9.46.1.4.2")
    ciscoVtpVlanEditOperation = ObjectName("1.3.6.1.4.1.9.9.46.1.4.1.1.1") #.1
    ciscoVtpVlanEditBufferOwner = ObjectName("1.3.6.1.4.1.9.9.46.1.4.1.1.3") # .1
    ciscoVtpVlanEditRowStatus = ObjectName("1.3.6.1.4.1.9.9.46.1.4.2.1.11") #.1.<vlan id>
    ciscoVtpVlanEditType = ObjectName("1.3.6.1.4.1.9.9.46.1.4.2.1.3") #.1.<vlan id>
    ciscoVtpVlanEditName = ObjectName("1.3.6.1.4.1.9.9.46.1.4.2.1.4") #.1.<vlan id>
    ciscoVtpVlanEditDot10Said = ObjectName(" 1.3.6.1.4.1.9.9.46.1.4.2.1.6") #.1.<vlan id>
    ciscoVtpVlanType = ObjectName("1.3.6.1.4.1.9.9.46.1.3.1.1.3")
    ciscoVtpVlanName = ObjectName("1.3.6.1.4.1.9.9.46.1.3.1.1.4")
    ciscoVtpVlanifIndex = ObjectName("1.3.6.1.4.1.9.9.46.1.3.1.1.18")
    ciscoVmVlan = ObjectName("1.3.6.1.4.1.9.9.68.1.2.2.1.2")
    ciscoVmMembershipSummaryMemberPorts = ObjectName("1.3.6.1.4.1.9.9.68.1.2.1.1.2")
    
    ciscoVlanTrunkPortEncapsulationType = ObjectName("1.3.6.1.4.1.9.9.46.1.6.1.1.3")
    ciscoVlanTrunkPortVlansEnabled = ObjectName("1.3.6.1.4.1.9.9.46.1.6.1.1.4")
    ciscoVlanTrunkPortVlansPruningEligible = ObjectName("1.3.6.1.4.1.9.9.46.1.6.1.1.10")
    
    extremeVlanStaticName = ObjectName("1.3.6.1.4.1.1916.1.2.1.2.1.2")
    extremeVlanStaticType = ObjectName("1.3.6.1.4.1.1916.1.2.1.2.1.3")
    extremeVlanStaticExternalID = ObjectName("1.3.6.1.4.1.1916.1.2.1.2.1.4")
    extremeVlanStaticRowStatus = ObjectName("1.3.6.1.4.1.1916.1.2.1.2.1.6")
    extremeVlanNextAvailableIndex = ObjectName("1.3.6.1.4.1.1916.1.2.2.1.0")
    extremeVlanTaggedType = ObjectName("1.3.6.1.4.1.1916.1.2.3.1.1.2")
    extremeVlanTaggedTag = ObjectName("1.3.6.1.4.1.1916.1.2.3.1.1.3")
    extremeVlanTaggedRowStatus = ObjectName("1.3.6.1.4.1.1916.1.2.3.1.1.4")
    extremeOverTemperatureAlarm = ObjectName("1.3.6.1.4.1.1916.1.1.1.7.0")
    extremeCurrentTemperature = ObjectName("1.3.6.1.4.1.1916.1.1.1.8.0")
    extremeFanStatusTable = ObjectName("1.3.6.1.4.1.1916.1.1.1.9.1.2")
    extremeSystemID = ObjectName("1.3.6.1.4.1.1916.1.1.1.18.0")
    
    threecomVlanStaticName = ObjectName("1.3.6.1.4.1.43.10.1.14.1.2.1.2")
    threecomVlanStaticType = ObjectName("1.3.6.1.4.1.43.10.1.14.1.2.1.3")
    threecomVlanStaticExternalID = ObjectName("1.3.6.1.4.1.43.10.1.14.1.2.1.4")
    threecomVlanStaticRowStatus = ObjectName("1.3.6.1.4.1.43.10.1.14.1.2.1.6")
    threecomVlanNextAvailableIndex = ObjectName("1.3.6.1.4.1.43.10.1.14.3.1.0")
    threecomVlanTaggedType = ObjectName("1.3.6.1.4.1.43.10.1.14.4.1.1.2")
    threecomVlanTaggedTag = ObjectName("1.3.6.1.4.1.43.10.1.14.4.1.1.3")
    threecomVlanTaggedRowStatus = ObjectName("1.3.6.1.4.1.43.10.1.14.4.1.1.4")
    threecomStackUnitSerialNumber = ObjectName("1.3.6.1.4.1.43.10.27.1.1.1.13.1")

    hpPoeTable = ObjectName("1.3.6.1.2.1.105.1.1.1.3.1")
    hpPoeDeliveringStatusTable = ObjectName("1.3.6.1.2.1.105.1.1.1.6.1")
    hpPoePowerPriorityTable = ObjectName("1.3.6.1.2.1.105.1.1.1.7.1")
    hpPoeOverloadCounterTable = ObjectName("1.3.6.1.2.1.105.1.1.1.13.1")
    hpPoeNominalPower = ObjectName("1.3.6.1.2.1.105.1.3.1.1.2.1")
    hpPoeOperationalStatus = ObjectName("1.3.6.1.2.1.105.1.3.1.1.3.1")
    hpPoePowerConsumption = ObjectName("1.3.6.1.2.1.105.1.3.1.1.4.1")

    apcSerialNumber = ObjectName("1.3.6.1.4.1.318.1.1.12.1.6.0")
    apcCurrent = ObjectName("1.3.6.1.4.1.318.1.1.12.2.3.1.1.2.1")
    apcControl = ObjectName( "1.3.6.1.4.1.318.1.1.12.3.3.1.1.4")
    apcStatus = ObjectName("1.3.6.1.4.1.318.1.1.12.3.5.1.1.4")
    
    sensatronicsProbe = ObjectName("1.3.6.1.4.1.16174.1.1.1.3")
