############## BUSYBOX #######################

fetch-busybox:
	[ -e archive/busybox-$(BBVER).tar.bz2 ] || wget -Parchive http://busybox.net/downloads/busybox-$(BBVER).tar.bz2

unpack-busybox:
	[ -d build/busybox-$(BBVER) ] && [ -e archive/busybox-$(BBVER).tar.bz2 ] || tar -C build -jxf archive/busybox-$(BBVER).tar.bz2

compile-busybox:
	[ -e build/busybox-$(BBVER)/.config ] || cp config/busybox-$(BBVER) build/busybox-$(BBVER)/.config

	[ -d build/busybox-$(BBVER) ] && $(MAKE) -C build/busybox-$(BBVER) 

