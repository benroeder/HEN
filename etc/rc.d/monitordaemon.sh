#!/bin/sh
DAEMONNAME="monitordaemon"

NAME="$DAEMONNAME"
DAEMON_BIN="/usr/local/hen/bin/daemons/$DAEMONNAME.py"
PID_FILE="/var/run/hen/$DAEMONNAME.pid"

. /usr/local/hen/etc/rc.d/hen_startup
