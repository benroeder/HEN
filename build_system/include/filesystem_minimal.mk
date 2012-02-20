############## FILESYSTEM ##################

clean-target:
	[ -d $(TARGET) ] || mkdir -p $(TARGET)
	[ -d $(TARGET) ] && sudo rm -rf $(TARGET) 

create-minimal-target:
	[ -d $(TARGET) ] || mkdir -p $(TARGET)
#	[ -d $(TARGET) ] && sudo debootstrap --verbose --include=python,python-pysnmp4,openssh-server,less --exclude=logrotate,at,cron,mailx,exim4,exim4-base,exim4-config,exim4-daemon-light --variant=minbase sid $(TARGET)
	[ -d $(TARGET) ] && sudo debootstrap --include=$(INSTALLPKG) --variant=minbase lenny $(TARGET) ftp://ftp.de.debian.org/debian/
# set root passwd in etc/shadow
	sudo sed -i 's/^root:[^:]*/root:$$1$$3TeiXuNC$$kuvKKFqlO2HZWBcs2\/0OD./' $(TARGET)/etc/shadow; 
# setup inittab
	sudo cp $(TARGET)/usr/share/sysvinit/inittab $(TARGET)/etc/inittab
	sudo sed -i 's/^.:23:/#&/' $(TARGET)/etc/inittab
	sudo sed -i 's/^#T0/T0/' $(TARGET)/etc/inittab
	sudo sed -i 's/ttyS0/$(CONSOLEDEV)/' $(TARGET)/etc/inittab	
# set dummy hostname
	sudo chmod 777 $(TARGET)/etc/hostname
	echo "vr-fsimage" > $(TARGET)/etc/hostname
# make devices
	cd $(TARGET)/dev && sudo MAKEDEV ttyS0 ttyS1 tty1 tty2 tty3 tty4 tty5 tty6 hda loop
# create xen console device
	[ -e $(TARGET)/dev/xvc0 ] || sudo mknod $(TARGET)/dev/xvc0 c 204 191
#loopback dns and interface.
	sudo touch $(TARGET)/etc/hosts $(TARGET)/etc/network/interfaces
	sudo chmod 777 $(TARGET)/etc/hosts $(TARGET)/etc/network/interfaces
	echo "127.0.0.1 localhost" >> $(TARGET)/etc/hosts
	echo "auto lo" >> $(TARGET)/etc/network/interfaces
	echo "iface lo inet loopback" >> $(TARGET)/etc/network/interfaces

create-minimal-initrd:
	sudo cp archive/clean_initrd.sh $(TARGET)/root/
	sudo chroot $(TARGET) /bin/bash /root/clean_initrd.sh
	cd $(TARGET) && sudo find . | sudo cpio --quiet -o -H newc | gzip -9 -n > $(TARGET_NAME)

test:
	sudo sed -i 's/ssh:x:102:/ssh:x:102:\nxorp:x:99:root/' $(TARGET)/etc/group; 




# file systems
	sudo chmod 777 $(TARGET)/etc/fstab
	echo "server1:/export/usr_local_hen /usr/local/hen nfs noatime 0 0" >> $(TARGET)/etc/fstab
	echo "server1:/export /export nfs noatime 1 1" >> $(TARGET)/etc/fstab
	echo "server1:/home/hen/u0/ /home/hen/u0/ nfs noatime 1 1" >> $(TARGET)/etc/fstab
	echo "server1:/export/usr_local_hen/etc/xen /etc/xen nfs noatime 1 1" >> $(TARGET)/etc/fstab
	echo "tmpfs                   /var/run        tmpfs           rw  0 0" >> $(TARGET)/etc/fstab
	echo "tmpfs                   /var/log        tmpfs           rw  0 0" >> $(TARGET)/etc/fstab
	echo "tmpfs                   /var/lock       tmpfs           rw  0 0" >> $(TARGET)/etc/fstab
	echo "tmpfs                   /tmp            tmpfs           rw  0 0 " >> $(TARGET)/etc/fstab
	echo "tmpfs                   /var/lib/xend   tmpfs           rw      0 0" >> $(TARGET)/etc/fstab
	echo "tmpfs                   /var/lib/xenstored tmpfs        rw      0 0" >> $(TARGET)/etc/fstab
	echo "tmpfs                   /var/xen        tmpfs           rw      0 0" >> $(TARGET)/etc/fstab
# setup local startup
	sudo bash -c "> $(TARGET)/etc/rc.local"
	sudo chmod 777 $(TARGET)/etc/rc.local
	echo "#!/bin/sh -e" > $(TARGET)/etc/rc.local
	echo "mount -a ; sleep 5" >> $(TARGET)/etc/rc.local
	echo "export PYTHONPATH=\"$$PYTHONPATH:/usr/local/hen/lib\" " >> $(TARGET)/etc/rc.local
	echo "export PATH=$$PATH:/usr/local/hen/bin" >> $(TARGET)/etc/rc.local
	echo "bash /export/machines/\`/usr/local/hen/bin/nodeid.py\`/startup.sh" >> $(TARGET)/etc/rc.local
	echo "ntpdate server2 1>&2" >> $(TARGET)/etc/rc.local
	echo "exit 0" >> $(TARGET)/etc/rc.local
# root startup
	sudo touch $(TARGET)/root/.bashrc
	sudo chmod 777 $(TARGET)/root/.bashrc
	echo "export PATH=$$PATH:/usr/local/hen/bin"  >> $(TARGET)/root/.bashrc
	echo "export PYTHONPATH=$$PYTHONPATH:/usr/local/hen/lib" >> $(TARGET)/root/.bashrc
#sort out target
	sudo chmod 777 $(TARGET)/etc/apt/sources.list
	echo "deb ftp://ftp.uk.debian.org/debian/ testing main" > $(TARGET)/etc/apt/sources.list
# fix some directory permissions
	sudo chmod -R 777 $(TARGET)/boot 
	sudo chmod 777 $(TARGET)/lib
	[ -d $(TARGET)/lib/modules ] || sudo mkdir -p $(TARGET)/lib/modules
	sudo chmod 777 $(TARGET)/lib/modules
	sudo mkdir -p $(TARGET)/usr/local/hen
	sudo mkdir -p $(TARGET)/export
	sudo mkdir -p $(TARGET)/etc/xen
	sudo mkdir -p $(TARGET)/home/hen/u0
	sudo mkdir -p $(TARGET)/var/lib/xend
	sudo mkdir -p $(TARGET)/var/lib/xenstored
	sudo mkdir -p $(TARGET)/var/xen
# clean up debs after install
	sudo rm -rf $(TARGET)/var/cache/apt/archives/


