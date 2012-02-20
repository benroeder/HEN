############## XENIO Channel #####################

clean-xenio:
	rm -rf build/$(IODIR)
	rm -rf build/$(IODIR).orig

unpack-xenio:
ifeq ($(IODIRBASE),)
	[ -d build/$(IODIR) ] && [ -e archive/$(IOARCHIVE) ] || tar -C build -jxf archive/$(IOARCHIVE)
else
	[ -d build/$(IODIR) ] && [ -e archive/$(IOARCHIVE) ] || tar -C build --transform 's/$(IODIRBASE)/$(IODIR)/g' -jxf archive/$(IOARCHIVE)
endif
genpatch-xenio:
	rm -rf build/$(IODIR).orig
	rm -f build/vr-$(IODIR).patch
ifeq ($(IODIRBASE),)
	[ -d build/$(IODIR).orig ] && [ -e archive/$(IOARCHIVE) ] || tar -C build --transform 's/$(IODIR)/$(IODIR).orig/g' -jxf archive/$(IOARCHIVE)
else
	[ -d build/$(IODIR).orig ] && [ -e archive/$(IOARCHIVE) ] || tar -C build --transform 's/$(IOBASE)/$(IODIR).orig/g' -jxf archive/$(IOARCHIVE)
endif
	$(MAKE) IODIR=$(IODIR).orig info patch-xenio
	if \
		cd build && diff -ru $(EXCLUDE_FLAGS) $(IODIR).orig $(IODIR) > vr-$(IODIR).patch ; \
	then \
		echo "The source tree's are idendical." ; \
	else \
		echo "Patch is" build/vr-$(IODIR).patch ; \
	fi

patch-xenio:
	for p in ${IOPATCHES}; \
	do \
		cd build/$(IODIR) && $(PATCH) $(PATCHOPTIONS) < ../../archive/$${p} ; cd ../.. ; \
	done

#fetch-xenio: 
#	no fetch needed checked in code

#compile-xenio:
#	$(MAKE) -j8 -C build/$(IODIR)/src KVER=$(KVER) KSRC=$(PWD)/build/$(KDIR) INSTALL_MOD_PATH=$(TARGET)
#	sudo $(MAKE) -j8 -C build/$(IODIR)/src KVER=$(KVER) KSRC=$(PWD)/build/$(KDIR) INSTALL_MOD_PATH=$(TARGET) install	


