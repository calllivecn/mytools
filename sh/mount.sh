#!/bin/bash



if [ -z "$2" ];then
	echo "using: chroot directory"
	exit 2
fi


case "$1" in

	mount)

	mount -vt devtmpfs none "$2"/dev
	mount -vt devpts none "$2"/dev/pts
	mount -vt proc none "$2"/proc
	mount -vt sysfs none "$2"/sys
	mount -vt tmpfs none "$2"/run
	;;


	umount)

	umount -v "$2"/sys
	umount -v "$2"/proc
	umount -v "$2"/dev/pts
	umount -v "$2"/dev
	umount -v "$2"/run
	;;

	*)
	echo "using: <mount|umount> <chroot>"
	exit 2
esac


	
