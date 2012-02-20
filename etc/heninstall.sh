# arkell (server1)
sudo bin/hm node server create rack2 serial1 1 00:60:08:71:93:7b 00:26:54:0a:a4:13 00:01:03:ce:19:5f 128.16.10.12 255.255.240.0 dnsalias arkell
# cockerel (server2)
sudo bin/hm node server create rack2 serial1 2 00:11:D8:31:74:BA 00:01:03:CE:19:3F 00:09:5B:1D:A5:6E 128.16.12.203 255.255.240.0 dnsalias cockerel
# henldap (server3)
sudo bin/hm node server create rack2 serial1 21 00:03:47:6D:48:1E 00:A0:0C:C0:03:4A 00:60:97:82:5B:03 128.16.13.115 255.255.240.0 dnsalias henldap
# opengear serial console
sudo bin/hm node serial create opengear cm4148 00:13:c6:00:05:04 none none serial serial rack2 numports 48
# black box master power switch
sudo bin/hm node powerswitch create blackbox master 00:01:9A:F1:13:18 serial1 22 rack2 numports 8
# threecom 3300 switches
sudo hm node switch create yes threecom superstack 00:90:04:46:9d:18 none none serial1 3 rack2 snmpreadcommunity public snmpwritecommunity private
sudo hm node switch create yes threecom superstack 00:90:04:9b:6b:d8 none none serial1 4 rack2 snmpreadcommunity public snmpwritecommunity private
sudo hm node switch create yes threecom superstack 00:90:04:9b:6d:b8 none none serial1 5 rack2 snmpreadcommunity public snmpwritecommunity private
sudo hm node switch create yes threecom superstack 00:90:04:46:f5:b8 none none serial1 6 rack2 snmpreadcommunity public snmpwritecommunity private
# extreme switch
sudo hm node switch create yes extreme summit 00:e0:2b:17:c7:00 none none serial1 7 rack2 snmpreadcommunity public snmpwritecommunity private
# cisco switch
sudo hm node switch create yes cisco catalyst 00:05:9b:ab:b0:80 none none none none upstairs snmpreadcommunity public snmpwritecommunity private
# huawei switch
sudo hm node switch create yes huawei quidway 00:0F:E2:12:6B:24 none none serial1 48 rack2 snmpreadcommunity public snmpwritecommunity private
# force10 switch
sudo hm node switch create yes force10 e600 00:01:e8:0d:68:c2 none none serial1 44 rack2 snmpreadcommunity public snmpwritecommunity private
# hp pro-curves switch
sudo hm node switch create yes hp procurve2626 00:13:21:a2:e5:80 none none serial1 43 rack2 snmpreadcommunity public snmpwritecommunity private
# power switch 2 , slave
sudo bin/hm node powerswitch create blackbox slave 00:01:9A:F1:13:18 serial1 22 rack2 numports 8 slaveid 2
# power switch 3 , apc
sudo bin/hm node powerswitch create apc rackpdu 00:c0:b7:78:ea:94 serial1 77 rack3 numports 24 snmpreadcommunity public snmpwritecommunity private
# serviceprocessor 1
sudo hm node serviceprocessor create 00:09:3D:13:2B:79 powerswitch3 7 none none rack2
# serviceprocessor 2
sudo hm node serviceprocessor create 00:09:3D:13:2D:02 powerswitch3 2 none none rack2
# serviceprocessor 3
sudo hm node serviceprocessor create 00:09:3D:13:64:9C powerswitch3 3 none none rack2
# serviceprocessor 4
sudo hm node serviceprocessor create 00:09:3D:13:2C:B1 powerswitch3 4 none none rack2
# serviceprocessor 5
sudo hm node serviceprocessor create 00:09:3D:13:2D:27 powerswitch3 5 none none rack2 
# serviceprocessor 6
sudo hm node serviceprocessor create 00:09:3D:13:29:cf powerswitch3 6 none none rack2
# old hen3, computer1
sudo hm node computer create yes no rack2 00:C0:4F:7E:01:80 powerswitch1 3 serial1 20
# old hen4, computer2
sudo hm node computer create yes no rack2 00:C0:4F:7E:01:63 powerswitch1 4 serial1 19
# old hen5, computer3
sudo hm node computer create yes no rack2 00:0e:0c:66:1a:e0 powerswitch1 5 serial1 18
# old hen6, computer4
sudo hm node computer create yes no rack2 00:0e:0c:64:2e:e2 powerswitch1 6 serial1 17
# old hen7, computer5
sudo hm node computer create yes no rack2 00:0E:0C:64:28:12 powerswitch1 7 serial1 16
# old hen8, computer6
sudo hm node computer create yes no rack2 00:c0:4f:7e:00:e1 powerswitch1 8 serial1 15
# old hen9, computer7
sudo hm node computer create yes no rack2 00:C0:4F:7E:00:DE powerswitch2 1 serial1 14
# old hen10, computer8
sudo hm node computer create yes no rack2 00:09:3D:13:2B:77 powerswitch3 7 serial1 8 serviceprocessor1
# old hen11, computer9
sudo hm node computer create yes no rack2 00:09:3D:13:2D:00 powerswitch3 2 serial1 9 serviceprocessor2
# old hen12, computer10
sudo hm node computer create yes no rack2 00:09:3D:13:64:9A powerswitch3 3 serial1 10 serviceprocessor3
# old hen13, computer11
sudo hm node computer create yes no rack2 00:09:3D:13:2C:AF powerswitch3 4 serial1 11 serviceprocessor4
# old hen14, computer12
sudo hm node computer create yes no rack2 00:09:3D:13:2D:25 powerswitch3 5 serial1 12 serviceprocessor5
# old hen15, computer13
sudo hm node computer create yes no rack2 00:09:3D:13:29:cd powerswitch3 6 serial1 13 serviceprocessor6
#old hen16 (Sun Desktop)
sudo hm node computer create yes no rack3 00:0A:E4:29:EA:FA powerswitch2 3 serial1 24
# old hen18
sudo hm node computer create yes no adamdesk 00:0e:0c:64:2f:38 none none none none
# procket router
sudo hm node router create procket 8801 00:01:02:87:83:27 none none serial1 20 rack3 operatingsystemtype procket operatingsystemversion 0.1
# power switch 4 , apc
sudo bin/hm node powerswitch create apc rackpdu 00:c0:b7:78:8f:86 serial1 78 rack3 numports 24 snmpreadcommunity public snmpwritecommunity private
# power switch 5 , apc
sudo bin/hm node powerswitch create apc rackpdu 00:c0:b7:79:96:7b serial1 79 rack3 numports 24 snmpreadcommunity public snmpwritecommunity private
# power switch 6 , apc
sudo bin/hm node powerswitch create apc rackpdu 00:c0:b7:79:63:84 serial1 80 rack3 numports 24 snmpreadcommunity public snmpwritecommunity private
# power switch 7 , apc
sudo bin/hm node powerswitch create apc rackpdu 00:c0:b7:79:62:33 serial1 81 rack3 numports 24 snmpreadcommunity public snmpwritecommunity private
# power switch 8 , apc
sudo bin/hm node powerswitch create apc rackpdu 00:c0:b7:79:62:fd serial1 82 rack3 numports 24 snmpreadcommunity public snmpwritecommunity private
# power switch 9 , apc
sudo bin/hm node powerswitch create apc rackpdu 00:c0:b7:79:63:70 serial1 83 rack3 numports 24 snmpreadcommunity public snmpwritecommunity private
# solcrist
sudo hm node computer create yes no adamdesk 00:00:24:c0:3e:28 none none none none
# power switch 10 , apc
sudo bin/hm node powerswitch create apc rackpdu 00:c0:b7:79:0b:31 serial1 83 rack3 numports 24 snmpreadcommunity public snmpwritecommunity private
# switch 9 , netgear
sudo bin/hm node switch create netgear fsm700s 00:09:5b:58:fb:77 serial1 48 rack3 numports 50 snmpreadcommunity public snmpwritecommunity private
# computer 19
hm node computer create yes no marksoffice 00:00:24:C5:C8:F8 none none none none
# rack 1
sudo bin/hm infrastructure rack create apc vt description maletplaceUCL 4 4.02 1 1 199 75 107 2 2 42
# rack 2
sudo bin/hm infrastructure rack create apc vt description maletplaceUCL 4 4.02 1 2 199 75 107 2 2 42
# rack 3
sudo bin/hm infrastructure rack create apc vt description maletplaceUCL 4 4.02 1 3 199 60 107 2 2 42
# rack 4
sudo bin/hm infrastructure rack create apc vt description maletplaceUCL 4 4.02 1 4 199 75 107 2 2 42
# rack 5
sudo bin/hm infrastructure rack create apc vt description maletplaceUCL 4 4.02 1 5 199 75 107 2 2 42
# rack 6
sudo bin/hm infrastructure rack create apc vt description maletplaceUCL 4 4.02 1 6 199 60 107 2 2 42
# rack 7
sudo bin/hm infrastructure rack create apc vt description maletplaceUCL 4 4.02 1 7 199 60 107 2 2 42
