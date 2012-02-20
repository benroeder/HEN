##!/bin/bash

cd / && ln -s sbin/init init
apt-get clean
rm -f /var/lib/apt/lists/*
for i in af ar as be bg bn_IN bs ca cs cy da de dz el eo es et eu fi fr ga gl gu he hi hr hu id it ja km kn ko ku ky lg lt ml mr ms nb ne nl nn no or pa pl pt pt_BR ro ru rw si sk sl sq sr sv ta th tl tr vi zh_CN zh_TW zu 
do
rm -rf /usr/share/locale/$i
done
rm -rf /usr/share/doc
rm -rf /usr/share/man
rm -rf /usr/share/info
rm -rf /tmp/*
rm -rf /etc/udev/rules.d/*persistent* 
#mv /lib/tls /lib/tls.disabled  
