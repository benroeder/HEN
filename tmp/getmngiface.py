#!/usr/bin/env python
"""
returns mng interface
"""
import commands,re,auxiliary.hen,sys,string,os

ifconfig="/sbin/ifconfig -a"

#these functions bring up the interfaces

s=commands.getoutput(ifconfig)
p = re.compile('^(...\d) .*? (HWaddr) (..:..:..:..:..:..)',re.DOTALL|re.MULTILINE)
if p.match(s)==None:
	p = re.compile('(\w?..\d): .*?(ether) (..:..:..:..:..:..)',re.DOTALL|re.MULTILINE)

# these loops should be rearranged, combined, and changed to exploit dict keys 

topology =hen.parse()
for d in topology.physicalDevices.values():  
	for i in d.mngInterface.values():
		mac=string.upper(i.mac)
		for x in p.finditer(s):
			mymac = string.upper(x.group(3))
			if mymac==mac:
				print x.group(1)
		
