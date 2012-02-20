#!/bin/sh

TEMP_DIR="/tmp/hen_scripts"
INSTALL_DIR="/usr/local/hen"
HOST_IP="192.168.1.1"
EXPORT_DIR="/export/usr_local_hen"
MOUNT_COMMAND="/sbin/mount $HOST_IP:$EXPORT_DIR $TEMP_DIR"
UMOUNT_COMMAND="/sbin/umount $TEMP_DIR"
SYNC_COMMAND="/usr/local/bin/rsync -av --delete $TEMP_DIR/ $INSTALL_DIR"
PING_COMMAND="/sbin/ping -c 1 -t 5 $HOST_IP"

host_is_up() {
	reply="no"
	$PING_COMMAND > /dev/null
	if [ "$?" -eq "0" ] ; then
		reply="yes"
	fi
	echo $reply
}

exit_with_error() {
	if [ "$1" = "unmount" ] ; then
		echo "Unmounting $EXPORT_DIR on host $HOST_IP"
		$UMOUNT_COMMAND
	fi
	echo "Exiting due to failure: $2"
	exit 1
}

if [ ! -r $TEMP_DIR ] ; then
	echo "Creating temp directory $TEMP_DIR"
	/bin/mkdir $TEMP_DIR
fi

host_up=`host_is_up`
echo "host_up = $host_up"

if [ $host_up = "yes" ] ; then
	echo "NFS host $HOST_IP is up, mounting export $EXPORT_DIR"
	$MOUNT_COMMAND
	if [ "$?" -ne "0" ] ; then
		exit_with_error "nomount" "Mount failed"
	fi
	echo "Syncing $INSTALL_DIR with $TEMP_DIR"
	$SYNC_COMMAND
	if [ "$?" -ne "0" ] ; then
		exit_with_error "unmount" "Sync failed"
	fi
	echo "Unmounting $EXPORT_DIR on host $HOST_IP"
	$UMOUNT_COMMAND
	if [ "$?" -ne "0" ] ; then
		exit_with_error "nomount" "Unmount failed"
	fi
	echo "Sync finished successfully. Exiting"
else
	exit_with_error "nomount" "Host $HOST_IP is not online, so cannot sync. Exiting."
fi

exit 0
