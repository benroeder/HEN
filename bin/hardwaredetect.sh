#!/bin/bash

#This script attemtps to detect the hardware configuration of a new hen node.
#This script is linux specific and only intented to run with the file system
#gentoo-hardware-detect

export PYTHONPATH=/usr/local/hen/lib:/usr/local/hen/etc
export PATH=$PATH:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin
export USER=detect

# Work out the name of the node
name=`/usr/local/hen/bin/nodeid.py`

# Bring all ifaces up so that lshw can detect their speed
/usr/bin/python /usr/local/hen/bin/ifacesup.py

# Use lshw to detect the hardware
echo "Running lshw on $name"
/usr/sbin/lshw -xml 2>/dev/null 1>/machine_info/$name-detect.xml

# Extract the interfaces from the detected hardware
echo "Processing lshw on $name"
/usr/bin/python /usr/local/hen/bin/processlshw.py /machine_info/$name-detect.xml $name 1>/usr/local/hen/etc/physical/$name.xml.tmp
mv /usr/local/hen/etc/physical/$name.xml.tmp /usr/local/hen/etc/physical/$name.xml

