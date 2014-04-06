Name:       kernel-adaptation-rpi


%define shorttag 7193cfe
%define kernel_version %{version}
%define kernel_devel_dir %{_prefix}/src/kernels/%{kernel_version}

Summary:    Kernel Adaptation RaspberryPi
Version:    3.10.36
Release:    1
Group:      System/Kernel
License:    GPLv2
ExclusiveArch:  %{arm}
URL:        https://github.com/raspberrypi/linux/
Source0:    kernel-adaptation-rpi-%{version}.tar.xz
Requires(post): kmod >= 9

BuildRequires:  mkimage-rpi
BuildRequires:  pkgconfig(ncurses)
BuildRequires:  mer-kernel-checks
BuildRequires:  kmod >= 9
BuildRequires:  perl
BuildRequires:  fdupes

Provides:   kernel = %{version}

%description
Kernel for RaspberryPi.

%package devel
Summary:    Devel files for RaspberryPi kernel
Group:      Development/System
Requires:   %{name} = %{version}-%{release}
Provides:   kernel-devel = %{version}

%description devel
Devel for RaspberryPi kernel



%prep
%setup -q -n %{name}-%{version}/raspberrypi-linux


%build
make %{?jobs:-j%jobs} bcmrpi_defconfig

# Fix default configuration
sed -i 's/CONFIG_DUMMY=m/CONFIG_DUMMY=n/' .config
sed -i 's/^# CONFIG_HOTPLUG is not set$/CONFIG_HOTPLUG=y/' .config
make listnewconfig
make oldconfig

# Verify the config meets the current Mer requirements
/usr/bin/mer_verify_kernel_config .config || /bin/true

make %{?jobs:-j%jobs} zImage
make %{?jobs:-j%jobs} modules

%install
rm -rf %{buildroot}

# Modules
make INSTALL_MOD_PATH=%{buildroot} modules_install
mkdir -p %{buildroot}/boot/
make INSTALL_PATH=%{buildroot}/boot/ install
install -m 755 arch/arm/boot/zImage %{buildroot}/boot/
install -m 755 arch/arm/boot/Image %{buildroot}/boot/
mkdir -p %{buildroot}/lib/modules/%{kernel_version}/
touch %{buildroot}/lib/modules/%{kernel_version}/modules.dep

# Config
cp .config %{buildroot}/boot/config-%{kernel_version}

# And save the headers/makefiles etc for building modules against
#
# This all looks scary, but the end result is supposed to be:
# * all arch relevant include/ files
# * all Makefile/Kconfig files
# * all script/ files



#rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/source
mkdir -p %{buildroot}/%{kernel_devel_dir}
#(cd $RPM_BUILD_ROOT/lib/modules/$KernelVer ; ln -s build source)
# dirs for additional modules per module-init-tools, kbuild/modules.txt
# first copy everything
cp --parents `find  -type f -name "Makefile*" -o -name "Kconfig*"` %{buildroot}/%{kernel_devel_dir}
cp Module.symvers %{buildroot}/%{kernel_devel_dir}
cp System.map %{buildroot}/%{kernel_devel_dir}
if [ -s Module.markers ]; then
cp Module.markers %{buildroot}/%{kernel_devel_dir}
fi
# then drop all but the needed Makefiles/Kconfig files
rm -rf %{buildroot}/%{kernel_devel_dir}/Documentation
rm -rf %{buildroot}/%{kernel_devel_dir}/scripts
rm -rf %{buildroot}/%{kernel_devel_dir}/include
cp .config %{buildroot}/%{kernel_devel_dir}
cp -a scripts %{buildroot}/%{kernel_devel_dir}
if [ -d arch/%{_arch}/scripts ]; then
cp -a arch/%{_arch}/scripts %{buildroot}/%{kernel_devel_dir}/arch/%{_arch} || :
fi
if [ -f arch/%{_arch}/*lds ]; then
cp -a arch/%{_arch}/*lds %{buildroot}/%{kernel_devel_dir}/arch/%{_arch}/ || :
fi
rm -f %{buildroot}/%{kernel_devel_dir}/scripts/*.o
rm -f %{buildroot}/%{kernel_devel_dir}/scripts/*/*.o
cp -a --parents arch/arm/include %{buildroot}/%{kernel_devel_dir}
cp -a --parents arch/arm/mach-*/include %{buildroot}/%{kernel_devel_dir}
cp -a --parents arch/arm/plat-*/include %{buildroot}/%{kernel_devel_dir}
mkdir -p %{buildroot}/%{kernel_devel_dir}/include
cd include
cp -a acpi asm-generic config crypto drm generated keys linux math-emu media mtd net pcmcia rdma rxrpc scsi sound video trace %{buildroot}/%{kernel_devel_dir}/include

# Make sure the Makefile and version.h have a matching timestamp so that
# external modules can be built
touch -r %{buildroot}/%{kernel_devel_dir}/Makefile %{buildroot}/%{kernel_devel_dir}/include/linux/version.h
touch -r %{buildroot}/%{kernel_devel_dir}/.config %{buildroot}/%{kernel_devel_dir}/include/linux/autoconf.h
# Copy .config to include/config/auto.conf so "make prepare" is unnecessary.
cp %{buildroot}/%{kernel_devel_dir}/.config %{buildroot}/%{kernel_devel_dir}/include/config/auto.conf
cd ..
cd /boot
cp args-uncompressed.txt %{buildroot}/boot
cp boot-uncompressed.txt %{buildroot}/boot
cp first32k.bin %{buildroot}/boot
cp imagetool-uncompressed.py %{buildroot}/boot
cd %{buildroot}/boot
python imagetool-uncompressed.py Image
rm image*
rm first32k.bin
rm *.txt

# rm .gitignore leackage and remove bad +x
find %{buildroot}/usr/src/kernels/%{kernel_version} -name ".gitignore" -type f -exec rm {} \;
find %{buildroot}/usr/src/kernels/%{kernel_version} -name "*.h" -type f -exec chmod a-x {} \;

# mark modules executable so that strip-to-file can strip them
find %{buildroot}/lib/modules/%{kernel_version} -name "*.ko" -type f -exec chmod u+x {} \;

%fdupes %{buildroot}/lib/firmware
%fdupes %{buildroot}/usr/src/kernels/%{kernel_version}

%post

/sbin/depmod -a %{kernel_version}


%files
%defattr(-,root,root,-)
/lib/modules/%{kernel_version}/
/boot/System.map-%{kernel_version}
/boot/vmlinux-%{kernel_version}
/boot/Image
/boot/kernel.img
/boot/config-%{kernel_version}
/lib/firmware/*
/boot/documentation.list
/boot/zImage

%files devel
%defattr(-,root,root,-)
/%{_prefix}/src/kernels/%{kernel_version}/*
/%{_prefix}/src/kernels/%{kernel_version}/.config
