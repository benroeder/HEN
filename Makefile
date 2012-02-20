DESTINATION=/usr/local/hen
CGI_DESTINATION=/home/arkell/u0/www/cgi-bin/hen
GROUP=hen
PERMISSIONS=775

# Uncomment bottom line to test
TEST=
TEST=echo

MKDIR=mkdir
CHMOD=chmod
CHGRP=chgrp
FIND=find
XARGS=xargs
CP=cp
RM=rm

.SILENT :

all :
	echo "Usage : gmake install"

install :
        # Create directories
	${TEST} ${MKDIR} -p ${DESTINATION}
	${TEST} ${MKDIR} -p ${CGI_DESTINATION}

        # Copy fles
	${TEST} ${CP} -R lib ${DESTINATION}
	${TEST} ${CP} -R bin ${DESTINATION}
	${TEST} ${CP} cgi/*py ${CGI_DESTINATION}

        # Remove CVS directories and files
	${TEST} ${FIND} ${DESTINATION} -name CVS -print | ${XARGS} rm -rf
	${TEST} ${FIND} ${DESTINATION} -name .cvsignore -print | ${XARGS} rm -rf

        # Set permissions
	${TEST} ${CHGRP} -R ${GROUP} ${DESTINATION}
	${TEST} ${CHMOD} -R ${PERMISSIONS} ${DESTINATION}
	${TEST} ${CHGRP} -R ${GROUP} ${CGI_DESTINATION}
	${TEST} ${CHMOD} -R ${PERMISSIONS} ${CGI_DESTINATION}
