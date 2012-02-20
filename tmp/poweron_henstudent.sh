#!/bin/bash

ssh -i /usr/local/hen/etc/ssh/controller_dsa manager@192.168.1.11 platform set power state -f -q on 
./powerstate_henstudent.sh
