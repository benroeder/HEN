dom0-kernel:
ifeq ($(XKVER-SHORT),3.0.4)
	$(MAKE) \
	KVER=2.6.16.33 \
	KDIRBASE=linux-2.6.16.33 \
	KDIR=linux-2.6.16.33-xen-$(XKVER-SHORT)-dom0 \
	KSRC=http://www.kernel.org/pub/linux/kernel/v2.6/linux-2.6.16.33.tar.gz \
	KARCHIVE=linux-2.6.16.33.tar.gz \
	KPATCHES="patch_linux2.6.16.33_xen-3.0.4.patch \
	          linux-2.6.16.33-xen-$(XKVER-SHORT)-click.patch \
			  vr-linux-2.6.16.33-xen-$(XKVER-SHORT).patch \
			  linux-2.6.16.33-xen-$(XKVER-SHORT)-fixsharedskb-netback.patch \
			  disablecksumoffload.patch" \
    TAROPTIONS=-zxf \
	KCONFIG=config-2.6.16.33-xen-$(XKVER-SHORT)-dom0 linux
endif
ifeq ($(XKVER-SHORT),3.1.0)
	$(MAKE) \
	KVER=2.6.18.8 \
	KDIRBASE=linux-2.6.18.8 \
	KDIR=linux-2.6.18-xen-$(XKVER-SHORT)-dom0 \
	KSRC=http://www.kernel.org/pub/linux/kernel/v2.6/linux-2.6.18.8.tar.gz \
	KARCHIVE=linux-2.6.18.8.tar.gz \
	KPATCHES="patch_linux2.6.18.8_xen-3.1.0.patch \
	          linux-2.6.18-xen-click.patch \
			  vr-linux-2.6.18-xen.patch \
			  linux-2.6.18-xen-fixsharedskb-netback.patch \
			  disablecksumoffload.patch" \
    TAROPTIONS=-zxf \
	KCONFIG=config-2.6.18-xen-dom0 linux
endif
ifeq ($(XKVER-SHORT),3.1.1)
	$(MAKE) \
	KVER=2.6.18.8 \
	KDIRBASE=linux-2.6.18.8 \
	KDIR=linux-2.6.18-xen-$(XKVER-SHORT)-dom0 \
	KSRC=http://www.kernel.org/pub/linux/kernel/v2.6/linux-2.6.18.8.tar.gz \
	KARCHIVE=linux-2.6.18.8.tar.gz \
	KPATCHES="patch_linux2.6.18.8_xen-3.1.0.patch \
			  patch_linux2.6.18.8_xen-3.1.1.patch \
	          linux-2.6.18-xen-click.patch \
			  vr-linux-2.6.18-xen.patch \
			  linux-2.6.18-xen-fixsharedskb-netback.patch \
			  disablecksumoffload.patch \
			  remove_spinlock_intimexen.patch" \
	TAROPTIONS=-zxf \
	KCONFIG=config-2.6.18-xen-dom0 linux
endif
ifeq ($(XKVER-SHORT),3.1.2)
	$(MAKE) \
	KVER=2.6.18.8 \
	KDIRBASE=linux-2.6.18.8 \
	KDIR=linux-2.6.18-xen-$(XKVER-SHORT)-dom0 \
	KSRC=http://www.kernel.org/pub/linux/kernel/v2.6/linux-2.6.18.8.tar.gz \
	KARCHIVE=linux-2.6.18.8.tar.gz \
	KPATCHES="patch_linux2.6.18.8_xen-3.1.0.patch \
			  patch_linux2.6.18.8_xen-3.1.1.patch \
			  patch_linux2.6.18.8_xen-3.1.2.patch \
	          linux-2.6.18-xen-click.patch \
			  vr-linux-2.6.18-xen.patch \
			  linux-2.6.18-xen-fixsharedskb-netback.patch \
			  disablecksumoffload.patch \
			  remove_spinlock_intimexen.patch" \
    TAROPTIONS=-zxf \
	KCONFIG=config-2.6.18-xen-dom0 linux
endif
ifeq ($(XKVER-SHORT),3.1.3)
	$(MAKE) \
	KVER=2.6.18.8 \
	KDIRBASE=linux-2.6.18.8 \
	KDIR=linux-2.6.18-xen-$(XKVER-SHORT)-dom0 \
	KSRC=http://www.kernel.org/pub/linux/kernel/v2.6/linux-2.6.18.8.tar.gz \
	KARCHIVE=linux-2.6.18.8.tar.gz \
	KPATCHES="patch_linux2.6.18.8_xen-3.1.0.patch \
			  patch_linux2.6.18.8_xen-3.1.1.patch \
			  patch_linux2.6.18.8_xen-3.1.2.patch \
			  patch_linux2.6.18.8_xen-3.1.3.patch \
	          linux-2.6.18-xen-click.patch \
			  vr-linux-2.6.18-xen.patch \
			  linux-2.6.18-xen-fixsharedskb-netback.patch \
			  disablecksumoffload.patch \
			  remove_spinlock_intimexen.patch" \
    TAROPTIONS=-zxf \
	KCONFIG=config-2.6.18-xen-dom0 linux
endif
ifeq ($(XKVER-SHORT),3.2.0)
	$(MAKE) \
	KVER=2.6.18.8 \
	KDIRBASE=linux-2.6.18.8 \
	KDIR=linux-2.6.18-xen-$(XKVER-SHORT)-dom0 \
	KSRC=http://www.kernel.org/pub/linux/kernel/v2.6/linux-2.6.18.8.tar.gz \
	KARCHIVE=linux-2.6.18.8.tar.gz \
	KPATCHES="patch_linux2.6.18.8_xen-3.1.0.patch \
			  patch_linux2.6.18.8_xen-3.1.1.patch \
			  patch_linux2.6.18.8_xen-3.1.2.patch \
			  patch_linux2.6.18.8_xen-3.1.3.patch \
			  patch_linux2.6.18.8_xen-3.2.0.patch \
	          linux-2.6.18-xen-click.patch \
			  vr-linux-2.6.18-xen.patch \
			  linux-2.6.18-xen-fixsharedskb-netback.patch \
			  disablecksumoffload.patch \
			  remove_spinlock_intimexen.patch" \
    TAROPTIONS=-zxf \
	KCONFIG=config-2.6.18-xen-dom0 linux
endif
ifeq ($(XKVER-SHORT),3.3.0)
	$(MAKE) \
	KVER=2.6.18.8 \
	KDIRBASE=linux-2.6.18.8 \
	KDIR=linux-2.6.18-xen-$(XKVER-SHORT)-dom0 \
	KSRC=http://www.kernel.org/pub/linux/kernel/v2.6/linux-2.6.18.8.tar.gz \
	KARCHIVE=linux-2.6.18.8.tar.gz \
	KPATCHES="patch_linux2.6.18.8_xen-3.1.0.patch \
	          patch_linux2.6.18.8_xen-3.1.1.patch \
	          patch_linux2.6.18.8_xen-3.1.2.patch \
	          patch_linux2.6.18.8_xen-3.1.3.patch \
	          patch_linux2.6.18.8_xen-3.2.0.patch \
	          patch_linux2.6.18.8_xen-3.3.0.patch \
	          linux-2.6.18-xen-3.3.0-click.patch \
			  vr-linux-2.6.18-xen.patch \
			  linux-2.6.18-xen-fixsharedskb-netback.patch \
			  disablecksumoffload.patch \
			  click-napi-linux-kernel.patch \
			  remove_spinlock_intimexen.patch \
			  limits.patch" \
    TAROPTIONS=-zxf \
	KCONFIG=config-2.6.18-xen-$(XKVER-SHORT)-dom0 linux
endif
dom0-initrd:
ifeq ($(XKVER-SHORT),3.0.4)
	$(MAKE) KVER=2.6.16.33 \
	KDIR=linux-2.6.16.33-xen-$(XKVER-SHORT)-dom0 \
	KNAME=2.6.16.33-dom0 initrd
else
	$(MAKE) KVER=2.6.18.8 \
	KDIR=linux-2.6.18-xen-$(XKVER-SHORT)-dom0 \
	KNAME=2.6.18.8-dom0 initrd
endif
