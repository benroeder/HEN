############## Openflow Linux Implementation #####

#http://openflowswitch.org/downloads/openflow-v0.8.1.tar.gz

fetch-openflow:
	[ -e archive/openflow-$(OVER).tar.gz ] || wget -Parchive $(OSRC)

unpack-openflow:
	[ -d build/$(ODIR) ] && [ -e archive/openflow-v$(OVER).tar.gz ] || tar -C build -zxf archive/openflow-$(OVER).tar.gz

compile-openflow:
	cd build/$(ODIR) && dpkg-buildpackage -rfakeroot
	cp build/openflow*.deb $(TARGET)/tmp/
	[ -e build/$(ODIR)/configure ] || ( cd build/$(ODIR) && autoconf )
	[ -e build/$(ODIR)/Makefile ] || ( cd build/$(ODIR) && ./configure --prefix=$(OPREFIX) --with-l26=$(PWD)/build/$(KDIR) )	
	nice $(MAKE) -C build/$(ODIR) 

install-openflow:
	sudo mkdir -p $(OPREFIX)/lib/
	sudo cp build/$(ODIR)/datapath/linux-2.6/openflow_mod.ko $(TARGET)/lib/modules/2.6.24-idd/kernel/drivers/net/
	sudo cp archive/install_openflow_switch.sh $(TARGET)/root/
	sudo touch $(TARGET)/root/kver
	sudo chmod 777 $(TARGET)/root/kver
	echo "2.6.24-idd" > $(TARGET)/root/kver 
	sudo chroot $(TARGET) /bin/bash /root/install_openflow_switch.sh

install-openflow-controller:
	sudo mkdir -p $(OPREFIX)/lib/
	sudo cp archive/install_openflow_controller.sh $(TARGET)/root/
	sudo chroot $(TARGET) /bin/bash /root/install_openflow_controller.sh

compile-openflow_old:
	[ -e build/$(ODIR)/configure ] || ( cd build/$(ODIR) && autoconf )
	[ -e build/$(ODIR)/Makefile ] || ( cd build/$(ODIR) && ./configure --prefix=$(OPREFIX) --with-l26=$(PWD)/build/$(KDIRBASE) )
	nice $(MAKE)  -C build/$(ODIR) 
	sudo mkdir -p $(OPREFIX)/lib/
	sudo $(MAKE) -j8 -C build/$(ODIR) install
	sudo cp build/$(ODIR)/datapath/linux-2.6/openflow_mod.ko $(OPREFIX)/lib/