############## LIVE CD/USB ##################

# UnionFS
UFSSRC     ?= http://download.filesystems.org/unionfs/unionfs-2.x/unionfs-2.5.3_for_2.6.24.7.diff.gz
UFSARCHIVE ?= unionfs-2.5.3_for_2.6.24.7.diff

# SquashFS
# Kernels above 2.6.29 have SquasshFS built in
SQFSSRC     ?= http://sourceforge.net/projects/squashfs/files/squashfs/squashfs3.4/squashfs3.4.tar.gz/download
SQFSARCHIVE ?= squashfs3.4

BINARY_LOCAL = build/config/binary_local-includes
BINARY_HOOKS = build/config/binary_local-hooks
CHROOT_LOCAL = build/config/chroot_local-includes
CHROOT_HOOKS = build/config/chroot_local-hooks

# Explicit empty target to avoid make trying to build us
include/live.mk: ;

# Some variables to aid in a subst
comma:= ,
empty:=
space:= $(empty) $(empty)

# NOTE, locales-all is added as it improve boot time quite a lot, but adds ??mb to the ISO size
#       Even if I add it there are still locale issues :(
INSTALLPKG2=$(subst $(comma),$(space),$(INSTALLPKG))
#locales-all

.PHONY: fetch-unionfs unionfs

# Add the unionfs patches
fetch-unionfs:
	[ -e archive/$(UFSARCHIVE) ] || (wget -Parchive $(UFSSRC) && gunzip archive/$(UFSARCHIVE) )

unionfs: KPATCHES += $(UFSARCHIVE)
unionfs: KOPTIONS += CONFIG_UNION_FS=y
unionfs: fetch-unionfs patch-linux configure-linux

.PHONY: fetch-squashfs squashfs

# Add the squashfs patches
fetch-squashfs:
	[ -e archive/$(SQFSARCHIVE).tar.gz ] || wget -Parchive $(SQFSSRC)
	[ -d archive/$(SQFSARCHIVE) ] || tar -C archive -xzf archive/$(SQFSARCHIVE).tar.gz

squashfs: KPATCHES += $(SQFSARCHIVE)/kernel-patches/linux-$(KVERMAJOR).$(KVERMINOR).$(KVERBUILD)/squashfs3.4-patch
#squashfs: KOPTIONS += CONFIG_SQUASHFS=y CONFIG_SQUASHFS_EMBEDDED=n # SQUASHFS_EMBEDDED Should be no, but not set is also allowed
squashfs: KOPTIONS += CONFIG_SQUASHFS=y
squashfs: fetch-squashfs aufs patch-linux configure-linux

# Squashfs depends on aufs is a bit of a HACK to ensure the varibles KPATCHES and KOPTIONS work correctly.
# Otherwise the variables un unionfs are lost due to the wierd way the makefile works.

####### AUFS Module #######
# For the 2.6.16 ... 2.6.24 aufs1 is recommended.
# For later kernels use aufs2 (which is not setup to be built by this makefile)
# AUFS is a pain to patch into the kernel. In the future AUFS will be in mainline

.PHONY: clean-aufs fetch-aufs patch-aufs patch-linux aufs

clean-aufs:
	rm -rf archive/aufs

fetch-aufs:
	@if [ ${KVERMAJOR} -ne 2 -o ${KVERMINOR} -ne 6 -o ${KVERBUILD} -lt 16 -o ${KVERBUILD} -gt 24 ]; then \
		echo 'aufs only supports kernels 2.6.16-2.6.24, not $(KVER)'; \
		exit 1; \
	fi; \

	@echo 'Fetching aufs from CVS'; \
	if [ ! -d archive/aufs ]; then \
		cd archive; cvs -z3 -d:pserver:anonymous@aufs.cvs.sourceforge.net:/cvsroot/aufs co aufs; \
	fi

patch-aufs: fetch-aufs unpack-linux

	@# We have to ensure the kernel is somewhat configured before we can patch aufs \
	# We can't depend on the configure-linux target as we need to executre configure-linux after aufs is patched in \
	echo 'Pre-configuring Linux for AUFS patching'; \
	if [ -e build/$(KDIR)/.config ]; then \
		echo 'Using existing .config'; \
		configexists=1; \
	else \
		echo 'Using a defconfig .config'; \
		# Make a default config file (which we later remove) \
		${MAKE} -C build/$(KDIR) defconfig; \
	fi; \
	${MAKE} -f $(word 1, $(MAKEFILE_LIST)) configure-linux; \
	\
	# Ensure there a version.h \
	${MAKE} -C build/$(KDIR) include/linux/version.h include/linux/utsrelease.h; \
	\
	# Build the aufs config stuff \
	${MAKE} -C archive/aufs KDIR=../../build/$(KDIR) -f local.mk kconfig; \
	\
	# Wipe out the config if it didn't already exist \
	if [ ! $$configexists ]; then \
		echo 'Removing defconfig .config'; \
		rm build/$(KDIR)/.config; \
	fi;

	echo 'Patching linux for AUFS';

	@# TODO if we are using kernel 25 or later we need to copy auf25 not aufs
	cp -upr archive/aufs/fs build/$(KDIR)
	cp -upr archive/aufs/include build/$(KDIR)
	if [ -z '$(shell grep 'obj-$$(CONFIG_AUFS)' build/$(KDIR)/fs/Makefile)' ]; then \
		echo 'obj-$$(CONFIG_AUFS)		+= aufs/' >> build/$(KDIR)/fs/Makefile; \
	fi

	@# Add AUFS into the Kconfig
	if [ -z "$(shell grep source\ \"fs\/aufs\/Kconfig\" build/$(KDIR)/fs/Kconfig)" ]; then \
		# Some versions of Linux don't have the Layered filesystems menu \
		if [ ! -z "$(shell grep "Layered filesystems" build/$(KDIR)/fs/Kconfig)" ]; then \
			sed -i 's/menu "Layered filesystems"/menu "Layered filesystems"\n\nsource "fs\/aufs\/Kconfig"/g' build/$(KDIR)/fs/Kconfig; \
		else \
			sed -i 's/menu "Miscellaneous filesystems"/menu "Miscellaneous filesystems"\n\nsource "fs\/aufs\/Kconfig"/g' build/$(KDIR)/fs/Kconfig; \
		fi; \
	fi


aufs: KOPTIONS += CONFIG_AUFS=y
# AUFS also needs ALL these options :(
#aufs: KOPTIONS += CONFIG_AUFS_BRANCH_MAX_127=y CONFIG_AUFS_SYSAUFS=y CONFIG_AUFS_INO_T_64=y CONFIG_AUFS_RR_SQUASHFS=y 
#aufs: KOPTIONS += CONFIG_AUFS_BR_XFS=y CONFIG_AUFS_DEBUG=n CONFIG_AUFS_MAGIC_SYSRQ=y CONFIG_ECRYPT_FS=m
aufs: fetch-aufs patch-aufs patch-linux configure-linux

# Crafty override of pathc-linux to ensure patch-aufs is ran before the kernel is built
#patch-linux:: patch-aufs

.PHONY: pre-iso test-iso mount-iso create-iso clean-iso

pre-iso: KOPTIONS += CONFIG_EXT2_FS=y CONFIG_TMPFS=y CONFIG_BLK_DEV_RAM=y CONFIG_BLK_DEV_INITRD=y
pre-iso: squashfs aufs patch-linux configure-linux
# We have a choice of either aufs or unionfs

test-iso:
ifeq ($(ARCH),)
	qemu-system-x86_64 -m 256 -cdrom build/binary.iso -curses
else
	qemu-system-$(ARCH) -m 256 -cdrom build/binary.iso -curses
endif

# Useful for debugging
mount-iso:
	@[ -d iso ] || mkdir iso; \
	sudo umount iso; \
	sudo mount -o loop build/binary.iso iso;

clean-iso:
	sudo rm -f $(TARGET).iso
	if [ -d build ]; then \
		cd build; sudo lh clean --all --cache; \
	fi
	sudo rm -rf build/config

create-iso: build-kernel-package
	-cd build; sudo lh clean
	cd build; lh config \
		--bootappend-live "locale=en_GB.UTF-8 keyb=uk" \
		--bootloader grub \
		--mirror-bootstrap "$(APTREPO)" \
#		--mirror-chroot "$(APTREPO)"
# mirror-chroot is not available on old lh

	# Setup binary settings
	cd build; lh config \
		--distribution lenny \
		--hostname vrouter-live \
		--iso-application "VRouter LiveCD" \
		--iso-publisher "Lancaster University and University College London" \
		--iso-volume "VRouter $(shell date --rfc-3339=date)" \
		--username root \
#		--debian-installer live

	# Setup chroot settings
	cd build; lh config \
		--packages "$(INSTALLPKG2)" \
		--union-filesystem unionfs \
		--linux-packages="none" \
#		--architecture $(ARCH) \

	# Some options don't seem configuable from lh config so lets use sed
	sed -i 's/.*\(LH_SYSLINUX_MENU_LIVE_ENTRY=\)\(.*\)/\1"VRouter"/g' build/config/binary

# Do some symlink fun to change the root filesystem
	sudo rm -rf $(CHROOT_LOCAL); \
	mkdir $(CHROOT_LOCAL); \
#	ln -s $(TARGET) $(CHROOT_LOCAL); \
	sudo cp -upr $(TARGET)/* $(CHROOT_LOCAL);

# Leave /dev and /etc/resolv.conf up to the live CD
	sudo rm -rf $(CHROOT_LOCAL)/dev
	sudo rm -rf $(CHROOT_LOCAL)/etc/resolv.conf

# A bit of a hack, but copy the /boot into BINARY_LOCAL (this copy the Xen image)
	sudo cp -upr $(TARGET)/boot $(BINARY_LOCAL);
	sudo mv $(BINARY_LOCAL)/boot $(BINARY_LOCAL)/live;

	# Move custom packages into chroot_local-packages (such as linux-image...)
#	cp build/*.deb build/config/chroot_local-packages

	# I couldn't get make-kpkg to include the initrd hookscript, so I'm hacking it this way:
	echo "#!/bin/sh"                        > $(CHROOT_HOOKS)/01_build_initrd.sh
	echo "cd /lib/modules/"                >> $(CHROOT_HOOKS)/01_build_initrd.sh
	echo "for file in * ; do"              >> $(CHROOT_HOOKS)/01_build_initrd.sh
	echo "update-initramfs -c -k \$$file"  >> $(CHROOT_HOOKS)/01_build_initrd.sh
	echo "done"                            >> $(CHROOT_HOOKS)/01_build_initrd.sh

	chmod +x $(CHROOT_HOOKS)/01_build_initrd.sh

	# Add a script that fixes the syslinux menu
	#echo "#!/bin/sh"                                                      > $(BINARY_HOOKS)/01-fix_syslinux.sh
	#echo "SYSLINUXCFG=binary/isolinux/live.cfg"                          >> $(BINARY_HOOKS)/01-fix_syslinux.sh
	#echo "sed -i 's|/vmlinuz|/vmlinuz_$(KVER)|g' \$${SYSLINUXCFG}"       >> $(BINARY_HOOKS)/01-fix_syslinux.sh
	#echo "sed -i 's|/initrd.img|/initrd.img_$(KVER)|g' \$${SYSLINUXCFG}" >> $(BINARY_HOOKS)/01-fix_syslinux.sh

# Always clean before build (this seems to fix build problems)
	cd build; sudo lh clean; sudo lh build
