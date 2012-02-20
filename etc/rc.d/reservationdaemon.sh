#
# Reservation daemon start|stop script
#

case "$1" in
start)
        sudo -u hend /usr/local/bin/python /usr/local/hen/bin/daemons/reservationdaemon.py
        ;;

stop)
        PID_FILE="/var/run/hen/reservationdaemon.pid"
        NAME="reservationdaemon"
        if [ -r $PID_FILE ] ; then
                kill `cat $PID_FILE`
                rm $PID_FILE
                echo "$NAME: finished."
        else
                echo "pid file not found (are you sure the daemon is running?)"
        fi
        ;;
*)
        echo "Usage: `basename $0` {start|stop}" >&2
        ;;
esac

exit 0
