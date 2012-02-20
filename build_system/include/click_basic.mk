############## CLICK #######################
tidy-click: clean-click
	case $(CVER) in \
	git*) rm -rf archive/click-$(CVER) ;; \
	*) rm -rf click-$(CVER).tar.gz ;; \
	esac

clean-click:
	rm -rf build/$(CDIR)

unpack-click:
	case $(CVER) in \
	git*) [ -d build/$(CDIR) ] && [ -d archive/click-$(CVER) ] || cp -R archive/click-$(CVER) build/$(CDIR) ;; \
	*) [ -d build/$(CDIR) ] && [ -e archive/click-$(CVER).tar.gz ] || tar -C build $(TAROPTIONS) archive/click-$(CVER).tar.gz ;; \
	esac 

genpatch-click:
	rm -rf build/$(CDIR).orig
	rm -f build/vr-$(CDIR).patch
	case $(CVER) in \
        git*) [ -d build/$(CDIR).orig ] && [ -d archive/click-$(CVER) ] || cp -R archive/click-$(CVER) build/$(CDIR).orig ;; \
	*) [ -d build/$(CDIR).orig ] && [ -e archive/click-$(CVER).tar.bz2 ] || tar -C build --transform 's/$(CDIR)/$(CDIR).orig/g' -jxf archive/click-$(CVER).tar.bz2 ;; \
	esac
	$(MAKE) CDIR=$(CDIR).orig patch-click
	if \
		cd build && diff -crN $(EXCLUDE_FLAGS) --exclude=Makefile --exclude='*.d' --exclude='*.hd' --exclude='*.conf' --exclude='*.mk' --exclude='*.in' --exclude='stamp-h' --exclude='*.log' --exclude='*config*.h' --exclude='pathvars.h' --exclude='ksyms.c' --exclude='kcompat.h' --exclude='click-buildtool' --exclude='*.xml' --exclude='installch' --exclude='configure' --exclude='click-compile' --exclude='config.status' $(CDIR).orig $(CDIR) > vr-$(CDIR).patch ; \
	then \
		echo "The source tree's are idendical." ; \
	else \
		echo "Patch is" build/vr-$(CDIR).patch ; \
	fi

patch-click:
	> build/$(CDIR)/series; \
	let i=0; \
	for p in ${CPATCHES}; \
	do \
	let i=0; \
	echo $${p} >> build/${CDIR}/series; \
	cp archive/$${p} archive/$${i}-$${p}; \
	done
	cd build/$(CDIR);export QUILT_PATCHES=../../archive/;quilt push -a;cd ../..;

fetch-click:
	case $(CVER) in \
	git*)  [ -d archive/click-$(CVER) ] ||  git clone git://read.cs.ucla.edu/git/click archive/click-$(CVER) ;cd archive/click-$(CVER); git checkout $(GITCVER);cd ../..;; \
	*) [ -e archive/click-$(CVER).tar.gz ] || wget -Parchive http://read.cs.ucla.edu/click/click-$(CVER).tar.gz ;; \
	esac


compile-click:
	[ -e build/$(CDIR)/Makefile ] || ( cd build/$(CDIR) && ./configure --enable-linuxmodule --enable-multithread=8 --with-linux=$(PWD)/build/$(KDIR) --prefix=$(CPREFIX) )
	$(MAKE) -j8 -C build/$(CDIR) XVER=$(XVER)
	sudo mkdir -p $(CPREFIX)
	sudo $(MAKE) -j8 -C build/$(CDIR) install

recompile-click:
	cd build/$(CDIR) && ./configure --enable-linuxmodule --enable-multithread=8 --with-linux=$(PWD)/build/$(KDIR) --prefix=$(CPREFIX) 
	$(MAKE) -j8 -C build/$(CDIR) elemlists
	$(MAKE) -j8 -C build/$(CDIR) 
	sudo $(MAKE) -j8 -C build/$(CDIR) install

compile-click-e1000:
	$(MAKE) -C build/$(CDIR)/drivers/e1000-7.x/src KVER=$(KVER) KSRC=$(PWD)/build/$(KDIR) 
	sudo mkdir -p $(TARGET)/lib/modules/$(KVER)/kernel/drivers/net/e1000/
	sudo cp build/$(CDIR)/drivers/e1000-7.x/src/e1000.ko $(TARGET)/lib/modules/$(KVER)/kernel/drivers/net/e1000/
