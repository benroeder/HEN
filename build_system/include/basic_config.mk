# Useful xen url
#http://wiki.xensource.com/xenwiki/XenParavirtOps

KVER=
ifeq ($(KVER),)
KVER=2.6.18-xen-3.2.0
endif

KPATCHES=
ifeq ($(KPATCHES),)
KPATCHES="linux-2.6.18-xen-click.patch vr-linux-2.6.18-xen-3.2.0.patch skb_over_panic.patch"
endif

KSRC=
ifeq ($(KSRC),)
KSRC=http://www.kernel.org/pub/linux/kernel/v2.6/linux-$(KVER).tar.bz2
endif

KBASEDIR=
ifeq ($(KBASEDIR),)
KBASEDIR=linux-$(KVER)
endif

KDIR=
ifeq ($(KDIR),)
KDIR=$(KDIRBASE)
endif

KCONFIG=
ifeq ($(KCONFIG),)
KCONFIG=config-$(KVER)
endif

KARCHIVE=
ifeq ($(KARCHIVE),)
KARCHIVE=$(KBASEDIR).tar.bz2
endif

# IXGBE setup

IVER=
ifeq ($(IVER),)
IVER=1.3.31.5
endif

ISRC=
ifeq ($(ISRC),)
ISRC=http://switch.dl.sourceforge.net/sourceforge/e1000/ixgbe-$(IVER).tar.gz
endif

IDIR=
ifeq ($(IDIR),)
IDIR=ixgbe-$(IVER)
endif

IARCHIVE=
ifeq ($(IARCHIVE),)
IARCHIVE=$(IDIR).tar.gz
endif

IPATCHES=
ifeq ($(IPATCHES),)
IPATCHES=vr-ixgbe-$(IVER).patch
endif

# XENIO Channel

IOVER=
ifeq ($(IOVER),)
IOVER=2.6.18-xen-3.2.0
endif

IODIR=
ifeq ($(IODIR),)
IODIR=xenio-$(IOVER)
endif

IOARCHIVE=
ifeq ($(IOARCHIVE),)
IOARCHIVE=$(IODIR).tar.bz2
endif

XENPATCHES=
ifeq ($(XENPATCHES),)
XENPATCHES=xen-3.2.1-directmap.patch hostinfo.patch
endif

IOPATCHES=
ifeq ($(IOPATCHES),)
IOPATCHES=xenio-2.6.18-xen-3.2.0-modular.patch xenio-2.6.18-xen-3.2.0-fixsharedskb.patch patch_linux2.6.24_xenionetback.patch xenio-2.6.18-xen-3.2.0-vrviftovif.patch
endif

# FILESYSTEM SETTINGS
TARGET=
ifeq ($(TARGET),)
TARGET=/export/filesystems/$(USER)/vr-system
endif
TARGET_NUMA=
ifeq ($(TARGET_NUMA),)
TARGET_NUMA=$(TARGET)-64bits
endif
#TARGET=target/vr-$(KVER)-$(CVER)
SSHKEY=
ifeq ($(SSHKEY),)
SSHKEY=~/.ssh/authorized_keys
endif

# CLICK SETTINGS

CVER=
ifeq ($(CVER),)
CVER=git-20080715
#GITCVER=101fa5468518150c798ca14181e75dc59a0aa917
endif

GITCVER=
ifeq ($(GITCVER),)
GITCVER=101fa5468518150c798ca14181e75dc59a0aa917
endif

CDIR=
ifeq ($(CDIR),)
CDIR=click-$(CVER)
endif

CPATCHES=
ifeq ($(CPATCHES),)
CPATCHES=vr-click-git-20080715.patch
endif

CPREFIX=
ifeq ($(CPREFIX),)
CPREFIX=$(TARGET)
endif

# XORP SETTINGS

XRVER=
ifeq ($(XRVER),)
XRVER=1.5
endif

XRSRC=
ifeq ($(XRSRC),)
XRSRC=http://www.xorp.org/releases/$(XRVER)/xorp-$(XRVER).tar.gz
endif

XRDIR=
ifeq ($(XRDIR),)
XRDIR=xorp-$(XRVER)
endif

XRPATCHES=
ifeq ($(XRPATCHES),)
XRPATCHES=xorp_clickfastpath.patch
endif

XRPREFIX=
ifeq ($(XRPREFIX),)
XRPREFIX=$(TARGET)/usr/local/xorp
endif

# QUAGGA SETTINGS

QVER=
ifeq ($(QVER),)
QVER=0.99.10
endif

QSRC=
ifeq ($(QSRC),)
QSRC=http://www.quagga.net/download/quagga-$(QVER).tar.gz
endif

QDIR=
ifeq ($(QDIR),)
QDIR=quagga-$(QVER)
endif

QPATCHES=
ifeq ($(QPATCHES),)
QPATCHES=
endif

QPREFIX=
ifeq ($(QPREFIX),)
QPREFIX=$(TARGET)/usr/local/quagga
endif

# Openflow settings
#http://openflowswitch.org/downloads/openflow-v0.8.1.tar.gz

OVER=
ifeq ($(OVER),)
OVER=0.8.1
endif

OSRC=
ifeq ($(OSRC),)
OSRC=http://openflowswitch.org/downloads/openflow-$(OVER).tar.gz
endif

ODIR=
ifeq ($(ODIR),)
ODIR=openflow-$(OVER)
endif

OPATCHES=
ifeq ($(OPATCHES),)
OPATCHES=
endif

OPREFIX=
ifeq ($(OPREFIX),)
OPREFIX=$(TARGET)/usr/local/openflow
endif

# XEN SETTINGS 
# if XVER >= 3.3 PAE cannot be disabled.
XVER=
ifeq ($(XVER),)
XVER=3.3.1
#XVER=3.3.0
#XVER=3.2.1
#XVER=3.0.4
#XPAE=n
endif

# Dom0 XEN kernel SETTINGS 
# if XVER >= 3.3 PAE cannot be disabled.
XKVER-SHORT=
ifeq ($(XKVER-SHORT),)
#XKVER-SHORT=3.0.4
#XKVER-SHORT=3.1.3
#XKVER-SHORT=3.2.0
#XKVER-SHORT=3.1.3
XKVER-SHORT=3.3.0
endif

# BUSY BOX
BBVER=1.11.1

# BNX2
B2VER=1.4.51b-xen

# MAKEFILE SETTINGS ( modify with extreme care )
CONSOLEDEV=ttyS0
KDIRBASE=
CDIRBASE=
MENUCONFIG=
TAROPTIONS=
MAKE=nice make
EXCLUDE_FLAGS=--exclude=.depend --exclude='*.o' --exclude='*.orig' --exclude='*.flags' --exclude='*.rej' --exclude='*.o.d' --exclude='*.a' --exclude='*.gz' --exclude='.*.d' --exclude='*.so.*' --exclude='*.ol' --exclude='*.so' --exclude='*.opic' --exclude='*.cmd' --exclude='*.tmp_versions' --exclude='*~' --exclude='*.ko' --exclude='.*' --exclude='Module.symvers' --exclude='*.mod.c'
ifeq ($(TAROPTIONS),)
TAROPTIONS=-jxf
endif
SHELL=/bin/bash
PATCHOPTIONS=-N -p1 -F 0
PATCH=/usr/bin/patch
