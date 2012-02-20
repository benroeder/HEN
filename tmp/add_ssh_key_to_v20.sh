#!/usr/local/bin/bash

scp /usr/local/hen/etc/ssh/controller_dsa.pub manager@$1:/tmp
ssh manager@$1 access add public key -k /tmp/controller_dsa.pub
ssh manager@$1 rm /tmp/controller_dsa.pub
