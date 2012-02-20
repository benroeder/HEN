############## INITRD ########################

compile-initrd:
#	build/$(KDIR)/usr/gen_init_cpio config/initrd.config > build/initrd/initrd.gz
	[ -d build/initrd/initrd.dir ] || mkdir -p build/initrd/initrd.dir
#   Replace bnx2 module from the kernel with a more recent one
	$(MAKE) -C build/bnx2-$(B2VER)/src KVER=$(KVER) LINUX=$(PWD)/build/$(KDIR)
	cp build/bnx2-$(B2VER)/src/bnx2.ko build/$(KDIR)/drivers/net/bnx2.ko
	$(MAKE) -j8 -C build/$(KDIR) INSTALL_MOD_PATH=../initrd/initrd.dir/  modules_install
	mkdir -p build/initrd/initrd.dir/lib/modules/$(KNAME)/kernel/drivers/net

	cat config/initrd.config > build/initrd/file_list
	cd build/initrd/initrd.dir && ./modules_gen.sh build/initrd/initrd.dir >> ../file_list
	./build/$(KDIR)/usr/gen_init_cpio build/initrd/file_list > $(TARGET)/boot/initrd.gz

