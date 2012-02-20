############## QUAGGA #######################

tidy-quagga: clean-quagga
	case $(QVER) in \
	cvs*) rm -rf archive/quagga-$(QVER) ;; \
	*) rm -rf quagga-$(QVER).tar.gz ;; \
	esac

clean-quagga:
	rm -rf build/$(QDIR)

unpack-quagga:
	case $(QVER) in \
	*) [ -d build/$(QDIR) ] && [ -e archive/quagga-$(QVER).tar.gz ] || tar -C build -zxf archive/quagga-$(QVER).tar.gz ;; \
	esac 

fetch-quagga:
	case $(QVER) in \
	*) [ -e archive/quagga-$(QVER).tar.gz ] || wget -Parchive $(QSRC);; \
	esac

compile-quagga:
	[ -e build/$(QDIR)/configure ] || ( cd build/$(QDIR) && autoconf )
	[ -e build/$(QDIR)/Makefile ] || ( cd build/$(QDIR) && ./configure --prefix=$(QPREFIX) )
	$(MAKE) -j8 -C build/$(QDIR) 
	sudo mkdir -p $(QPREFIX)
	sudo $(MAKE) -j8 -C build/$(QDIR) install

genpatch-quagga:
	rm -rf build/$(QDIR).orig
	rm -f build/vr-$(QDIR).patch
	case $(QVER) in \
	*) [ -d build/$(QDIR).orig ] && [ -e archive/quagga-$(QVER).tar.gz ] || tar -C build --transform 's/$(QDIR)/$(QDIR).orig/g' -zxf archive/quagga-$(QVER).tar.gz ;; \
	esac
	$(MAKE) CDIR=$(QDIR).orig patch-quagga
	if \
		cd build && diff -ru $(EXCLUDE_FLAGS) $(QDIR).orig $(QDIR) > vr-$(QDIR).patch ; \
	then \
		echo "The source tree's are idendical." ; \
	else \
		echo "Patch is" build/vr-$(QDIR).patch ; \
	fi

patch-quagga:
	for p in ${QPATCHES}; \
	do \
		cd build/$(QDIR) && patch -N -p1 < ../../archive/$${p} ; cd ../.. ; \
	done
