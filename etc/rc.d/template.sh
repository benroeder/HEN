#!/bin/sh

#
# If you have kept roughly to the naming conventions, you
# will only need to set DAEMONNAME.
#

DAEMONNAME=""

NAME="$DAEMONNAME"
DAEMON_BIN="/usr/local/hen/bin/daemons/$DAEMONNAME.py"
PID_FILE="/var/run/hen/$DAEMONNAME.pid"

. /usr/local/hen/etc/rc.d/hen_startup
