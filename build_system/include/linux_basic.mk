############## LINUX #######################

tidy-linux: clean-linux
	rm -rf archive/$(KARCHIVE)

clean-linux:
	rm -rf build/$(KDIR)
	rm -rf build/$(KDIR).orig

unpack-linux:
#ifneq ($(KDIR),)
#	[ -d build/$(KDIRBASE) ] && [ -e archive/$(KARCHIVE) ] || tar -C build $(TAROPTIONS) archive/$(KARCHIVE)
#else
	[ -d build/$(KDIR) ] && [ -e archive/$(KARCHIVE) ] || tar -C build --transform 's/$(KDIRBASE)/$(KDIR)/g' $(TAROPTIONS) archive/$(KARCHIVE)
#endif
genpatch-linux:
#	rm -rf build/$(KDIR).orig
	rm -f build/vr-$(KDIR).patch
#ifeq ($(KDIRBASE),)
	[ -d build/$(KDIR).orig ] && [ -e archive/$(KARCHIVE) ] || tar -C build --transform 's/$(KDIR)/$(KDIR).orig/g' $(TAROPTIONS) archive/$(KARCHIVE)
#else
#	[ -d build/$(KDIR).orig ] && [ -e archive/$(KARCHIVE) ] || tar -C build --transform 's/$(KBASE)/$(KDIR).orig/g' $(TAROPTIONS) archive/$(KARCHIVE)
#endif
	$(MAKE) KDIR=$(KDIR).orig info patch-linux
	if \
		cd build && diff -ru $(EXCLUDE_FLAGS) $(KDIR).orig $(KDIR) > vr-$(KDIR).patch ; \
	then \
		echo "The source tree's are idendical." ; \
	else \
		echo "Patch is" build/vr-$(KDIR).patch ; \
	fi

patch-linux:
	> build/$(KDIR)/series; \
	let i=0; \
	for p in ${KPATCHES}; \
	do \
	echo $${p} >> build/${KDIR}/series; \
	cp archive/$${p} archive/$${i}-$${p}; \
	let i=$${i}+1; \
	done
	cd build/$(KDIR);export QUILT_PATCHES=../../archive/;quilt push -a;cd ../..;

fetch-linux: 
	[ -e archive/$(KARCHIVE) ] || wget -Parchive $(KSRC)

compile-linux:
#ifeq ($(KDIRBASE),)
	[ -e build/$(KDIR)/.config ] || cp config/$(KCONFIG) build/$(KDIR)/.config
#else
#	[ -e build/$(KDIRBASE)/.config ] || cp config/$(KCONFIG) build/$(KDIRBASE)/.config
#endif
	[ -d $(TARGET)/boot ] || mkdir -p $(TARGET)/boot
ifneq ($(MENUCONFIG),)
	echo "Not running menuconfig"
else
	$(MAKE) -j8 -C build/$(KDIR) menuconfig
endif

ifeq ($(ARCH),)
#ifeq ($(KDIRBASE),)
	$(MAKE) -j8 -C build/$(KDIR) INSTALL_PATH=$(TARGET)/boot/ INSTALL_MOD_PATH=$(TARGET)/ 
#else
#	$(MAKE) -j8 -C build/$(KDIRBASE) INSTALL_PATH=$(TARGET)/boot/ INSTALL_MOD_PATH=$(TARGET)/
#endif
else
#ifeq ($(KDIRBASE),)
	$(MAKE) -j8 -C build/$(KDIR) ARCH=$(ARCH) INSTALL_PATH=$(TARGET)/boot/ INSTALL_MOD_PATH=$(TARGET)/ 
#else
#	$(MAKE) -j8 -C build/$(KDIRBASE) ARCH=$(ARCH) INSTALL_PATH=$(TARGET)/boot/ INSTALL_MOD_PATH=$(TARGET)/ 
#endif
endif
#ifeq ($(KDIRBASE),)
	sudo $(MAKE) -j8 -C build/$(KDIR) INSTALL_PATH=$(TARGET)/boot/ INSTALL_MOD_PATH=$(TARGET)/ install modules_install
	sudo cp build/$(KDIR)/vmlinux $(TARGET)/boot/`echo $(KDIR) | sed 's/linux/vmlinux/'`
#else
#	sudo $(MAKE) -j8 -C build/$(KDIRBASE) INSTALL_PATH=$(TARGET)/boot/ INSTALL_MOD_PATH=$(TARGET)/ install modules_install
#	sudo cp build/$(KDIRBASE)/vmlinux $(TARGET)/boot/`echo $(KDIRBASE) | sed 's/linux/vmlinux/'`
#endif

recompile-linux:
ifeq ($(MENUCONFIG),)
	echo "Not running menuconfig"
else
	$(MAKE) -j8 -C build/$(KDIR) menuconfig
endif
	$(MAKE) -j8 -C build/$(KDIR) INSTALL_PATH=$(TARGET)/boot/ INSTALL_MOD_PATH=$(TARGET)/ 
	sudo $(MAKE) -j8 -C build/$(KDIR) INSTALL_PATH=$(TARGET)/boot/ INSTALL_MOD_PATH=$(TARGET)/ install modules_install
	cp build/$(KDIR)/vmlinux $(TARGET)/boot/`echo $(KDIR) | sed 's/linux/vmlinux/'`
