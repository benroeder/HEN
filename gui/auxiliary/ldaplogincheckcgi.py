#!/usr/local/bin/python
##################################################################################################################
# physicallocationdaemon.py: 
#
##################################################################################################################
import sys, os, time, cgi
temp = sys.path
sys.path.append("/usr/local/hen/lib/")
from auxiliary.ldapclient import LDAPClient

###########################################################################################
#   Main execution
###########################################################################################            
print "Content-Type: text/xml"
print ""
print ""

# read data from standard in
data = sys.stdin.read()
form = cgi.parse_qs(data)

# Make sure that the necessary cgi parameters are given and retrieve them
if ( (not form.has_key("username")) or (not form.has_key("password")) ):
    sys.exit()

username = form['username'][0]
password = form['password'][0]

ldapClient = LDAPClient("ldap://henldap:389")
validLogin = ldapClient.authenticate(username, password)
groups = None
if (validLogin):
    groups =  ldapClient.getUserInfoByLogin(username).getGroups()
        
# Print the results
string = '<ldapresponse validlogin="' + str(validLogin) + '">\n'
        
if (groups):
    for group in groups:
        string += '\t<group id="' + str(group) + '" />\n'
string += '</ldapresponse>'

print string
