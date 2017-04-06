#!/bin/sh -x
xorriso -as mkisofs -o ${2} -no-pad \
    -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
    -c isolinux/boot.cat -b isolinux/isolinux.bin -no-emul-boot -boot-load-size 4 -boot-info-table \
    -eltorito-alt-boot -e boot/efi.img -no-emul-boot \
    -append_partition 2 0x01 boot/efi.img \
    -isohybrid-gpt-basdat -isohybrid-apm-hfsplus \
    -appid "Deepin LiveCD" -publisher "Deepin Project <http://www.deepin.org>" \
    -V "${3}" ${1}
