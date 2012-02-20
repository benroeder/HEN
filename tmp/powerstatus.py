#!/usr/local/bin/python

import sys, os
sys.path.append("/usr/local/hen/lib")
os.environ["PATH"] += ":/usr/local/bin:/usr/bin"

print "Content-type: text/html\n\n"
		
for x in range(3,11):
	cmd = "hm power hen"+str(x)+" status"
	
	print "hen"+str(x)+" "
	res=os.system(cmd)
