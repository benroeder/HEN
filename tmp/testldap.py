from auxiliary.ldapclient import LDAPClient

serverURL = "ldap://henldap:389"
#login = "fhuici"
login = "fedlipe"
password = "test"

ldapClient = LDAPClient(serverURL)

print ldapClient.authenticate(login, password)

#ldapInfo = ldapClient.getUserInfoByLogin("fhuici")

#print str(ldapInfo)
#print ldapInfo.getMD5Object().digest()

#ldapInfo = ldapClient.getUserInfoByLogin("fhuici")
#print ldapInfo.getGroups()
