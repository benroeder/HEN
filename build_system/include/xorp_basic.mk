############## XORP #######################

tidy-xorp: clean-xorp
	case $(XRVER) in \
	cvs*) rm -rf archive/xorp-$(XRVER) ;; \
	*) rm -rf xorp-$(XRVER).tar.gz ;; \
	esac

clean-xorp:
	rm -rf build/$(XRDIR)

unpack-xorp:
	case $(XRVER) in \
	cvs*) [ -d build/$(XRDIR) ] && [ -d archive/xorp-$(XRVER) ] || cp -R archive/xorp-$(XRVER) build/$(XRDIR) ;; \
	*) [ -d build/$(XRDIR) ] && [ -e archive/xorp-$(XRVER).tar.gz ] || tar -C build -zxf archive/xorp-$(XRVER).tar.gz ;; \
	esac 

fetch-xorp:
	case $(XRVER) in \
	cvs*)  [ -d archive/xorp-$(XRVER) ] || cvs -d :pserver:xorpcvs@anoncvs.xorp.org:/cvs co -d archive/xorp-$(XRVER) xorp ;; \
	*) [ -e archive/xorp-$(XRVER).tar.gz ] || wget -Parchive $(XRSRC);; \
	esac

compile-xorp:
	[ -e build/$(XRDIR)/Makefile ] || ( cd build/$(XRDIR) && ./configure --prefix=$(XRPREFIX) )
	$(MAKE) -j8 -C build/$(XRDIR) 
	sudo mkdir -p $(XRPREFIX)
	sudo $(MAKE) -j8 -C build/$(XRDIR) install

genpatch-xorp:
	rm -rf build/$(XRDIR).orig
	rm -f build/vr-$(XRDIR).patch
	case $(XRVER) in \
        git*) [ -d build/$(XRDIR).orig ] && [ -d archive/xorp-$(XRVER) ] || cp -R archive/xorp-$(XRVER) build/$(XRDIR).orig ;; \
	*) [ -d build/$(XRDIR).orig ] && [ -e archive/xorp-$(XRVER).tar.gz ] || tar -C build --transform 's/$(XRDIR)/$(XRDIR).orig/g' -zxf archive/xorp-$(XRVER).tar.gz ;; \
	esac
	$(MAKE) CDIR=$(XRDIR).orig patch-xorp
	if \
		cd build && diff -ru $(EXCLUDE_FLAGS) $(XRDIR).orig $(XRDIR) > vr-$(XRDIR).patch ; \
	then \
		echo "The source tree's are idendical." ; \
	else \
		echo "Patch is" build/vr-$(XRDIR).patch ; \
	fi

patch-xorp:
	> build/$(XRDIR)/series; \
	for p in ${XRPATCHES}; \
	do \
	echo $${p} >> build/${XRDIR}/series; \
	done
	cd build/$(XRDIR);export QUILT_PATCHES=../../archive/;quilt push -a;cd ../..;
