############## XEN #######################

unpack-xen:
ifeq ($(XVER),3.0.4)
	[ -d build/xen-$(XVER) ] && [ -e archive/xen-3.0.4_1-src.tgz ] || tar -C build --transform 's/xen-3.0.4_1-src/xen-$(XVER)/g' -zxf archive/xen-3.0.4_1-src.tgz
else
	[ -d build/xen-$(XVER) ] && [ -e archive/xen-$(XVER).tar.gz ] || tar -C build -zxf archive/xen-$(XVER).tar.gz
endif
fetch-xen:
ifeq ($(XVER),3.0.4)
	[ -e archive/xen-3.0.4_1-src.tgz ] || wget -Parchive http://bits.xensource.com/oss-xen/release/3.0.4-1/src.tgz/xen-3.0.4_1-src.tgz
else
	[ -e archive/xen-$(XVER).tar.gz ] || wget -Parchive http://bits.xensource.com/oss-xen/release/$(XVER)/xen-$(XVER).tar.gz
endif

compile-xen:
	sudo $(MAKE) -j8 -C build/xen-$(XVER) DESTDIR=$(TARGET) xen XEN_TARGET_X86_PAE=$(XPAE)
	sudo $(MAKE) -j8 -C build/xen-$(XVER) DESTDIR=$(TARGET) tools XEN_TARGET_X86_PAE=$(XPAE)
	sudo $(MAKE) -j8 -C build/xen-$(XVER) DESTDIR=$(TARGET) install-xen install-tools XEN_TARGET_X86_PAE=$(XPAE)

genpatch-xen:
	rm -rf build/xen-$(XVER).orig
	rm -f build/vr-xen-$(XVER).patch
ifeq ($(XENDIRBASE),)
	[ -d build/xen-$(XVER).orig ] && [ -e archive/xen-$(XVER).tar.gz ] || tar -C build --transform 's/xen-$(XVER)/xen-$(XVER).orig/g' -zxf archive/xen-$(XVER).tar.gz
else
	[ -d build/xen-$(XVER).orig ] && [ -e archive/xen-$(XVER).tar.gz ] || tar -C build --transform 's/xen-$(BASE)/xen-$(XVER).orig/g' -zxf archive/xen-$(XVER).tar.gz
endif
	$(MAKE) IDIR=$(IDIR).orig info patch-xen
	if \
		cd build && diff -ru $(EXCLUDE_FLAGS) xen-$(XVER).orig xen-$(XVER) > vr-xen-$(XVER).patch ; \
	then \
		echo "The source tree's are idendical." ; \
	else \
		echo "Patch is" build/vr-xen-$(XVER).patch ; \
	fi

patch-xen:
	> build/xen-$(XVER)/series; \
	let i=0; \
	for p in ${XENPATCHES}; \
	do \
	let i=$${i}+1; \
	echo $${p} >> build/xen-$(XVER)/series; \
	cp archive/$${p} archive/$${i}-$${p}; \
	done
	cd build/xen-$(XVER);export QUILT_PATCHES=../../archive/;quilt push -a;cd ../..;
