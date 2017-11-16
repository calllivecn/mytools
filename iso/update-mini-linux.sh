#!/bin/bash
# 2017-10-19
# author calllivecn <c-all@qq.com>
#
#
#1.    mount -o loop $isofile /tmp/iso
#
#2.    cp -a /tmp/iso $work_dir/iso
#    mkdir $taget/root
#
#3.    unsquashfs $filesystem.squashfs -d $work_dir/root
#
#4.    mv $work_dir/root/etc/resolv.conf{,.bak}
#    cp /etc/resolv.conf $work_dir/root/etc/
#
#5.    mount 必要的文件系统 --> mount_sh()
#
#6.    chroot $work_dir/root 
#    请开始你的操作～～～
#
#7. apt clean && unchroot
#    mv -f $work_dir/root/etc/resolv.conf{.bak,}
#    rm -rf /var/lib/apt/lists
#
#8.    查看 /lib/systemd/system/getty@.service 更新没有，
#    如果更新 修改之：
#        ExecStart=-/sbin/agetty --noclear %I $TERM
#        ExecStart=-/sbin/agetty --noclear %I $TERM -a root
#
#9. mksquahfs $work_dir/root $work_dir/iso/casper/filesystem.squashfs 
#
#10.移动vmlinuz.efi ,initrd.lz 到 $work_dir/iso/casper/
#
#11.mkisofs
#
#12.isohybrid $outiso

VERSION='ubuntu16.04'

######################
#
# 用户输入参数
#
#####################

export LANG=en_US.UTF-8 LANGUAGE=en_US.UTF-8

if [ "$(id -u)" -ne 0 ];then
    echo must be root user
    echo or sudo -i 
    exit 1
fi

work_dir=
old_iso=
new_iso="$(date +%F-%H%M%S).iso"
iso_label="ISO $(date +%F-%H%M%S)"

exit_rm(){
    rm -rf "$work_dir"
}

using(){
    program=${0##*/}

    local str="Using: $program [-dlo] <-i>"
    str="$str"'
-d        work directory (default:./)
-i        old iso
-l        new iso volume label name
-o        new iso filename
'
    echo "$str"
    exit 0
}

flag_i=true
while getopts ':d:i:l:o:h' opt
do
    case "$opt" in
        d)
            if [ -d "$OPTARG" ];then
                echo "$OPTARG" directory not exists
                exit 1
            fi
            work_dir="$OPTARG"
            ;;
        i)
            if [ ! -f "$OPTARG" ];then
                echo "$OPTARG not exists"
                exit 1
            fi
            old_iso="$OPTARG"
            flag_i=false
            ;;
        l)
            if [ -n "$OPTARG" ];then
                iso_label="$OPTARG"
            fi
            ;;
        o)
            if [ -f "$OPTARG" ];then
                echo "$OPARG" already exists
                exit 1
            fi
            new_iso="$OPTARG"
            ;;
        h)
            using
            exit 1
            ;;
        \:)
            echo "-${OPTARG} option requires an argument"
            exit 1
            ;;
        \?)
            echo "invalid option : -${OPTARG}"
            exit 1
            ;;
    esac
done

if $flag_i ;then
    echo "-i option requires"
    exit 1
fi

if [ ! -d "$work_dir" ];then
    work_dir=$(mktemp -d -p "$(pwd -P)")
fi

# testing being
#echo "$old_iso"
#echo $work_dir
#echo $iso_label
#echo $new_iso
#exit 0
# testing end

########################
#
# 函数定义区
#
#######################

set -e

init_iso(){
    mkdir "$work_dir"/old_iso
    mkdir "$work_dir"/root
    mount -o loop "$old_iso" "$work_dir"/old_iso
    cp -a "$work_dir"/old_iso "$work_dir"/iso
    unsquashfs -f -d "$work_dir/root" "$work_dir/iso/casper/filesystem.squashfs" 
    mv "$work_dir"/iso/casper/vmlinuz.efi "$work_dir"/root/$(readlink "$work_dir"/root/vmlinuz)
    mv "$work_dir"/iso/casper/initrd.lz "$work_dir"/root/$(readlink "$work_dir"/root/initrd.img)
    umount "$old_iso"
}




mount_sh(){
    mount -vt devtmpfs none "$work_dir"/root/dev
    mount -vt devpts none "$work_dir"/root/dev/pts
    mount -vt proc none "$work_dir"/root/proc
    mount -vt sysfs none "$work_dir"/root/sys
    mount -vt tmpfs none "$work_dir"/root/run
}

umount_sh(){
    umount -v $work_dir/root/proc
    umount -v $work_dir/root/dev/pts
    umount -v $work_dir/root/dev
    umount -v $work_dir/root/run
    umount -v $work_dir/root/sys
}

resolv(){
    mv $work_dir/root/etc/resolv.conf{,.bak}
    cp /etc/resolv.conf $work_dir/root/etc/
}

unresolv(){
    mv -f $work_dir/root/etc/resolv.conf{.bak,}
}

rm_var_lib_apt_lists(){

    rm -rf $work_dir/root/var/lib/apt/lists

}

chroot_sh(){
    echo "already chroot ."
    echo "Please proceed with your operation."
    chroot "$work_dir"/root
}

# 退出 chroot 后的工作

build_iso(){
    rm "$work_dir"/iso/casper/filesystem.squashfs
    mv "$work_dir"/root/$(readlink "$work_dir"/root/vmlinuz) "$work_dir"/iso/casper/vmlinuz.efi
    mv "$work_dir"/root/$(readlink "$work_dir"/root/initrd.img) "$work_dir"/iso/casper/initrd.lz
    mksquashfs "$work_dir"/root "$work_dir"/iso/casper/filesystem.squashfs -comp xz -b 1M
}

mkiso(){

mkisofs -V "$iso_label" \
-J -b isolinux/isolinux.bin \
-c isolinux/boot.cat \
-boot-load-size 4 \
-boot-info-table \
-no-emul-boot \
-eltorito-alt-boot \
-e efi.img \
-no-emul-boot \
-o "$new_iso" \
-R "$work_dir"/iso
    
}

mkiso_v2(){
xorriso -as mkisofs -o "$new_iso" -no-pad \
    -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
    -c isolinux/boot.cat -b isolinux/isolinux.bin \
    -no-emul-boot -boot-load-size 4 -boot-info-table \
    -eltorito-alt-boot -e efi.img -no-emul-boot \
    -isohybrid-gpt-basdat \
    -V "$iso_label" "$work_dir"/iso
    #-isohybrid-apm-hfsplus \

}

clear_sh(){

    rm -rf "$work_dir"

}

signal_exit(){
    set +e
    umount "$old_iso"
    set -e
    clear_sh
    exit 1
}

err_exit(){
    echo "ERROR EXIT"
    signal_exit
    exit 1
}
set +e
########################
#
# 函数定义区
#
#######################


main(){

set -e 

    init_iso
    
    mount_sh

    resolv

    chroot_sh

    umount_sh

    unresolv

    rm_var_lib_apt_lists

    build_iso

    mkiso_v2

    #isohybrid "$new_iso"

    clear_sh

set +e

}

trap "signal_exit" SIGINT SIGTERM ERR

main
