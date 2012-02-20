#! /usr/bin/env python

# outputs a dhcp.conf file updated with all required information for existing hen nodes to screen; output to be piped to file if neccessary

# module import statements
import sys
# set hen path (?) 
sys.path.append("/usr/local/hen/lib")
from henManager import HenManager
from auxiliary.hen import DHCPConfWriter

###########################################
##   main
###########################################	
def main():
    
    # when an user specified output file name is neccessary
    # inputoutputfilenames = sys.argv[1:]

    # initialise the dhcpconfwriter class: it contains all the methods required to create the dhcp.conf file
    dcw=DHCPConfWriter()

    # set output to be a file, not the terminal
    #dcw.setOutputFile("dhcp.conf")
    
    # print the starting static section of the dhcp.conf file 
    dcw.printstartingstaticblock()

    # initialise the hen wrapper class(?)
    manager = HenManager()

    # intialise the logger function(?)
    manager.initLogging()

    # retrieve existing hen node information into a dictionary object(?)
    topology = manager.getPhysical()

    # iterate through the dictionary object for each key(?)
    for d in topology.keys():

        # for each iteration call dhcpconfreader method to extract values associated with the keys
        dcw.dhcpconfreader(topology,d)

        # for each iteration call printdynamicblock method to print the extracted key values in the format acceptable for the dhcp.conf file 
        dcw.printdynamicblock()

    # print the ending static section of the dhcp.conf file
    dcw.printendingstaticblock()
    
# call main - start execution
main()
