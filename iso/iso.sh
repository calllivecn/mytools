#!/bin/bash




isohdpfx_bin=/usr/lib/ISOLINUX/isohdpfx.bin
isolinux_bin=/usr/lib/ISOLINUX/isolinux.bin
vesamenu_c32=/usr/lib/syslinux/modules/bios/vesamenu.c32
ldlinux_c32=/usr/lib/syslinux/modules/bios/ldlinux.c32





xorriso -as mkisofs -o ${2} -no-pad \
    -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
    -c isolinux/boot.cat -b isolinux/isolinux.bin -no-emul-boot -boot-load-size 4 -boot-info-table \
    -eltorito-alt-boot -e boot/efi.img -no-emul-boot \
    -isohybrid-gpt-basdat -isohybrid-apm-hfsplus \ #-appid "Deepin LiveCD" -publisher "Deepin Project <http://www.deepin.org>" \
    -V "${3}" ${1}
