#!/usr/bin/env python

import os, sys, string, commands;

images_dir= "/export/filesystems/tar-images"
install_dir= "/export/filesystems"

def printFileDescription(filename):
	try:
		input = open(images_dir + "/" + filename, 'r')
	except IOError:
		return

	print "-----------------------------------------------"
	lines = input.readlines()
	for x in range (0, len(lines)):
		print lines[x],
	print "-----------------------------------------------"		
	
def selectFileSystem():
	filenames = os.listdir(images_dir);
	count=1;
	for i in filenames:
		if (i.find("txt") == -1):
			filename = i[:i.find(".")] + ".txt"		
			print str(count) + ".",
			print i;
			printFileDescription(filename)
			count=count+1;
	print "0. None";
	print ""
	print "Which filesystem would you like to use ?"

	selected=0
	while 1:
		next = sys.stdin.read(1)
		if not next:
			break
		if next == '0':
			print "Not installing anything"
			return -1
			break
		try:
			if string.atoi(next) < count:
				selected = string.atoi(next)
				break
		except ValueError:
			print "Please enter a number in the range 0 to "+str(count-1)
	count=1;
	for i in filenames:
		if (count == selected):
			return images_dir+"/"+i
			break
		count=count+1;

def checkStatus(status, cmd):
	if (status != 0):
		print "Error while executing command: " + cmd
		sys.exit()
	
file = selectFileSystem()
if (file == -1):
	sys.exit(1)

new_dir = sys.stdin.readline()
new_dir = raw_input("Please enter the directory name to install to: ")

answer = raw_input( "I'm about to install " + file + " to " + install_dir + "/" + new_dir + ", do you want to continue? (y/n): ")
if (answer == 'y'):
	cmd = "sudo mkdir " + install_dir + "/" + new_dir
	print "executing: " + cmd
	checkStatus(commands.getstatusoutput(cmd)[0], cmd)
	
	cmd = "sudo tar -xvzf "+file+" -C "+install_dir+"/"+new_dir
	print "executing: " + cmd
	checkStatus(commands.getstatusoutput(cmd)[0], cmd)

	print "Done."
else:
	print "Action cancelled."
