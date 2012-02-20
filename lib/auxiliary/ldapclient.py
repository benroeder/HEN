#########################################################################################################
# ldapclient.py: Implements a simple LDAP client
#
###########################################################################################################
import ldap
from auxiliary.hen import LDAPInfo

class LDAPClient:
    """\brief This class implements a simple LDAP client that allows searching and authentication via login name
    """
    def __init__(self, serverURL=None, baseDN="dc=cs,dc=ucl,dc=ac,dc=uk"):
        """\brief Initializes class
        \param serverURL (\c string) The URL for the ldap server, for instance ldap://henldap:389
        \param baseDN (\c string) The base distinguished name, default is dc=cs,dc=ucl,dc=ac,dc=uk
        """
        self.__serverURL = serverURL
        self.__baseDN = baseDN
        
        try:
            self.__ldapServer = ldap.initialize(self.__serverURL)
        except ldap.LDAPError, e:
            print "LDAPCLient::__init__: error while initiliazing"
            print e

    def setServerURL(self, serverURL):
        """\brief Sets the server URL
        \param serverURL (\c string) The URL for the ldap server
        """
        self.__serverURL = serverURL

    def getServerURL(self):
        """\brief Gets the server URL
        \return (\c string) The URL for the ldap server
        """
        return self.__serverURL

    def setBaseDN(self, baseDN):
        """\brief Sets the base distinguished name
        \param serverURL (\c string) The URL for the base distinguished name
        """        
        self.__baseDN = baseDN

    def getBaseDN(self):
        """\brief Gets the base distinguished name
        \return (\c string) The base distinguished name
        """        
        return self.__baseDN
    
    def authenticate(self, login, password):
        """\brief Authenticates against the LDAP server based on the given login and password
        \param login (\c string) The user's login
        \param password (\c string) The user's password
        \return (\c Boolean) False if the authentication failed, True otherwise or -1 if error
        """
        searchFilter = "uid=" + str(login)
        try:
            resultID = self.__ldapServer.search(self.__baseDN, ldap.SCOPE_SUBTREE, \
                                                searchFilter, ['objectclass'], 1)
            resultType, resultData = self.__ldapServer.result(resultID, 0)
            if (len(resultData) == 0):
                return False
            username = resultData[0][0]

        except ldap.LDAPError, e:
            print "LDAPCLient::authenticate: error while retrieving username"
            print e
            return -1

        try:
            self.__ldapServer.bind_s(username, password, ldap.AUTH_SIMPLE)
        except ldap.INVALID_CREDENTIALS:
            return False
        else:
            return True

    def getUserInfoByLogin(self, login):
        """\brief Given a user's login, this function returns all of the user's LDAP information
        \param login (\c string) The user's login
        \return (\c LDAPInfo) An object with the user's information
        """
        try:
            searchFilter = "uid=" + str(login)
            resultID = self.__ldapServer.search(self.__baseDN, ldap.SCOPE_SUBTREE, \
                                                searchFilter, None)
            resultType, resultData = self.__ldapServer.result(resultID, 0)
            ldapInfo = LDAPInfo()

            #print resultData
            # Parse the results and display them
            for result in resultData:
                #print result
                try:                
                    ldapInfo.setBaseDN(result[0])
                except:
                    pass
                try:                
                    ldapInfo.setUID(result[1]["uid"][0])
                except:
                    pass
                try:
                    ldapInfo.setUIDNumber(int(result[1]["uidNumber"][0]))
                except:
                    pass
                try:                
                    ldapInfo.setGIDNumber(int(result[1]["gidNumber"][0]))
                except:
                    pass
                try:                
                    ldapInfo.setCN(result[1]["cn"][0])
                except:
                    pass
                try:                
                    ldapInfo.setFirstName(result[1]["givenName"][0])
                except:
                    pass
                try:                
                    ldapInfo.setLastName(result[1]["sn"][0])
                except:
                    pass
                try:                
                    ldapInfo.setLoginShell(result[1]["loginShell"][0])
                except:
                    pass
                try:                
                    ldapInfo.setHomeDir(result[1]["homeDirectory"][0])
                except:
                    pass
                try:                
                    ldapInfo.setEmail(result[1]["mail"][0])
                except:
                    pass                

            # To retrieve the user's groups, first retrieve all group names, then use
            # that as the baseDN to match against the user's uid. There's probably a
            # better way to do this, but I haven't figured out how (fhuici)
            userGroups = []

            searchFilter = "cn=*"
            resultID = self.__ldapServer.search(self.__baseDN, ldap.SCOPE_SUBTREE, \
                                                "(objectClass=posixgroup)", ['cn'])
            groupNameList = []
            resultData = []
            resultType, resultData = self.__ldapServer.result(resultID, 0)            
            while(len(resultData) != 0):
                for key in resultData[0][1].keys():
                    if (resultData[0][1][key][0] not in groupNameList):
                        groupNameList.append(resultData[0][1][key][0])
                resultType, resultData = self.__ldapServer.result(resultID, 0)

            for groupName in groupNameList:
                baseDN = "cn=" + str(groupName) + ",ou=Groups,dc=cs,dc=ucl,dc=ac,dc=uk"
                searchFilter = "memberUid=" + str(login)
                
                resultID = self.__ldapServer.search(baseDN, ldap.SCOPE_SUBTREE, searchFilter, None)
                try:
                    resultType, resultData = self.__ldapServer.result(resultID, 0)
                except:
                    pass
                
                # For some reason the search filter does not seem to work and all logins are returned.
                # We must search to ensure that the given login is in the list
                if ((resultData != []) and (login in resultData[0][1]["memberUid"])):
                    userGroups.append(groupName)

            ldapInfo.setGroups(userGroups)
            return ldapInfo
            
        except ldap.LDAPError, e:
            print "LDAPCLient::searchByLogin: error while searching"
            print e
            return -1

        return 0

