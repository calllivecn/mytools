#!/bin/bash

using(){
    echo 'using: <source> <out file> [iso label]'
    exit 2
}

if [ -d "$1" ];then
    sour="$1"
    oldpath=`pwd`
#    cd "$1"
else
    using
fi

if [ -z "$2" ];then
    outfile="$2"
    using
fi

cd "$sour"


find -type f -print0 |xargs -0 md5sum |grep -v isolinux/ |tee md5sum.txt

cd $oldpath

echo `pwd`
read debug

date=$(date +%F-%H%m)


xorriso -as mkisofs -o ${outfile} -no-pad \
    -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
    -c isolinux/boot.cat -b isolinux/isolinux.bin -no-emul-boot -boot-load-size 4 -boot-info-table \
    -eltorito-alt-boot -e boot/efi.img -no-emul-boot \
    -append_partition 2 0x01 boot/efi.img \
    -isohybrid-gpt-basdat -isohybrid-apm-hfsplus \
    -appid "Deepin LiveCD" -publisher "Deepin Project <http://www.deepin.org>" \
    -V "${3:-atm-deepin 2014.3}"  ${sour}


#mkisofs -V ${3:-build-iso-${date}} -J -cache-inodes \
#-l -b isolinux/isolinux.bin -c isolinux/boot.cat \
#-no-emul-boot -eltorito-alt-boot -e boot/efi.img -no-emul-boot -R -o ${outfile} ${sour}

#echo "isohybrid $outfile"
#isohybrid $outfile
