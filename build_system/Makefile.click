all: system
#.SILENT :

include include/basic_config.mk
include include/filesystem_minimal.mk
include include/linux_basic.mk
include include/click_basic.mk
include include/ixgbe_basic.mk
include include/info.mk
include include/live.mk

# Explicit empty target to avoid make trying to build us
Makefile.click: ;

TARGET=/export/filesystems/$(USER)/click/
#TARGET=$(PWD)/build/click/
INSTALLPKG=python,vim-nox,iproute,net-tools,pciutils,module-init-tools,openssh-server,udev,openssh-server,portmap,nfs-common,bridge-utils,lshw,iputils-ping,grub

ifeq ($(ARCH),i386)
	INSTALLPKG:=$(INSTALLPKG),libc6-xen
endif

KVER=2.6.24
KDIRBASE=linux-2.6.24
KDIR=linux-2.6.24
KSRC=http://www.kernel.org/pub/linux/kernel/v2.6/linux-2.6.24.tar.bz2
KARCHIVE=linux-2.6.24.tar.bz2
KPATCHES=0000-Oneshot-linux-2.6.24.patch mq-linux-2.6.24.patch linux-2.6.24-booth-fix.patch 
#KPATCHES=
#KPATCHES += $(UFSARCHIVE) # Add the unionfs patches
#KPATCHES += $(SQFSARCHIVE)/kernel-patches/linux-$(KVER)/squashfs3.4-patch # Add the squashfs patches

#KCONFIG=config-2.6.24-basic
KCONFIG=config-2.6.24

# Default kernel get these options enabled
KOPTIONS += CONFIG_NETDEVICES_MULTIQUEUE=y

#CVER=git-master
#CDIR=click-master
CPATCHES=0000-oneshot-click-1.6.patch e1000-7.x-linux-2.6.24.patch mq-click-git-20080715.patch 
CPREFIX=$(TARGET)/usr/local/click
#GITCVER=master

IVER=1.3.31.5
IARCHIVE=ixgbe-$(IVER).tar.gz
IDIR=ixgbe-$(IVER)
IPATCHES=mq-ixgbe-1.3.31.5.patch kver-ixgbe-1.3.31.5.patch

CONSOLEDEV=ttyS0

configure-minimal-target:
# set hostname
	echo "basictesting" > $(TARGET)/etc/hostname
# setup resolve.conf
	sudo chmod 777 $(TARGET)/etc/resolv.conf
	echo "search hen-net" > $(TARGET)/etc/resolv.conf
	echo "nameserver 192.168.0.1" >> $(TARGET)/etc/resolv.conf
#copy ssh keys
	sudo mkdir -p $(TARGET)/root/.ssh
	sudo cp $(SSHKEY) $(TARGET)/root/.ssh/authorized_keys
#platform store
	sudo mkdir -p $(TARGET)/platform
	sudo chmod 777 $(TARGET)/etc/fstab
	echo "server1:$(TARGET) / nfs noatime 1 1" >> $(TARGET)/etc/fstab
	echo "server1:/export/usr_local_hen /usr/local/hen nfs noatime	0 0" >> $(TARGET)/etc/fstab
	echo "server1:/export /export nfs noatime 1 1" >> $(TARGET)/etc/fstab
	echo "server1:/home/hen/u0/ /home/hen/u0/ nfs noatime 1 1" >> $(TARGET)/etc/fstab
	echo "tmpfs                   /var/run        tmpfs	rw  0 0" >> $(TARGET)/etc/fstab
	echo "tmpfs                   /var/log        tmpfs	rw  0 0" >> $(TARGET)/etc/fstab
	echo "tmpfs                   /var/lock       tmpfs	rw  0 0" >> $(TARGET)/etc/fstab
	echo "tmpfs                   /tmp            tmpfs	rw  0 0 " >> $(TARGET)/etc/fstab

# setting up rc.local
	sudo bash -c "> $(TARGET)/etc/rc.local"
	sudo chmod 777 $(TARGET)/etc/rc.local
	echo "#!/bin/sh -e" > $(TARGET)/etc/rc.local
	echo "mount -a ; sleep 5" >> $(TARGET)/etc/rc.local
	#echo "/platform/bin/pmd.py start" >> $(TARGET)/etc/rc.local
	echo "exit 0" >> $(TARGET)/etc/rc.local
	sudo rm $(TARGET)/etc/udev/rules.d/*persistent*

.PHONY: click e1000 ixgbe kernel system iso clean

click : fetch-click unpack-click patch-click compile-click

e1000 : compile-click-e1000

ixgbe : fetch-ixgbe unpack-ixgbe patch-ixgbe compile-ixgbe

kernel : fetch-linux unpack-linux patch-linux compile-linux 

system : create-minimal-target configure-minimal-target kernel click ixgbe 

iso : pre-iso system create-iso

clean: clean-target clean-linux clean-click clean-iso
