############## IXGBE #####################

IVER=1.3.56.11

tidy-ixgbe: clean-ixgbe
	rm -rf archive/$(IARCHIVE)

clean-ixgbe:
	rm -rf build/$(IDIR)
	rm -rf build/$(IDIR).orig

unpack-ixgbe:
ifeq ($(IDIRBASE),)
	[ -d build/$(IDIR) ] && [ -e archive/$(IARCHIVE) ] || tar -C build -zxf archive/$(IARCHIVE)
else
	[ -d build/$(IDIR) ] && [ -e archive/$(IARCHIVE) ] || tar -C build --transform 's/$(IDIRBASE)/$(IDIR)/g' -zxf archive/$(IARCHIVE)
endif
genpatch-ixgbe:
	rm -rf build/$(IDIR).orig
	rm -f build/vr-$(IDIR).patch
ifeq ($(IDIRBASE),)
	[ -d build/$(IDIR).orig ] && [ -e archive/$(IARCHIVE) ] || tar -C build --transform 's/$(IDIR)/$(IDIR).orig/g' -zxf archive/$(IARCHIVE)
else
	[ -d build/$(IDIR).orig ] && [ -e archive/$(IARCHIVE) ] || tar -C build --transform 's/$(IBASE)/$(IDIR).orig/g' -zxf archive/$(IARCHIVE)
endif
	$(MAKE) IDIR=$(IDIR).orig info patch-ixgbe
	if \
		cd build && diff -ru $(EXCLUDE_FLAGS) $(IDIR).orig $(IDIR) > vr-$(IDIR).patch ; \
	then \
		echo "The source tree's are idendical." ; \
	else \
		echo "Patch is" build/vr-$(IDIR).patch ; \
	fi

patch-ixgbe:
	for p in ${IPATCHES}; \
	do \
		cd build/$(IDIR) && $(PATCH) $(PATCHOPTIONS) < ../../archive/$${p} ; cd ../.. ; \
	done

fetch-ixgbe: 
	[ -e archive/$(IARCHIVE) ] || wget -Parchive $(ISRC)

compile-ixgbe:
	$(MAKE) -j8 -C build/$(IDIR)/src KVER=$(KVER) KSRC=$(PWD)/build/$(KDIR) INSTALL_MOD_PATH=$(TARGET)
	sudo $(MAKE) -j8 -C build/$(IDIR)/src KVER=$(KVER) KSRC=$(PWD)/build/$(KDIR) INSTALL_MOD_PATH=$(TARGET) install	

recompile-ixgbe:
	$(MAKE) -j8 -C build/$(IDIR)/src KVER=$(KVER) KSRC=$(PWD)/build/$(KDIR) INSTALL_MOD_PATH=$(TARGET)

