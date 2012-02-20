#/usr/bin/env bash

scp -r serial-master/etc root@$1:/ 
ssh root@$1 chown serial /etc/config/users/serial/.ssh/authorized_keys
ssh root@$1 /sbin/reboot
