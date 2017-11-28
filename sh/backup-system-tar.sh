#!/bin/bash

set -e

if [ -z "$1" ] || [ -f "$1" ];then
	echo "using: $(basename $0) <out_file>.tar.xz"
	echo "or error exit $1 exists"
	exit 1
fi

if [ $(id -u) -ne 0 ];then
	echo need root user
	exit 1
fi

out_file="$1".tar.xz

sys_excludes='--exclude=./proc/* --exclude=./sys/* --exclude=./run/* --exclude=./tmp/* --exclude=./dev/* --exclude=./var/log/*'
#sys_excludes='./proc/* ./sys/* ./run/* ./tmp/* ./dev/*'

user_excludes='--exclude=./home/* --exclude=./mnt/* --exclude=./media/*'
#user_excludes='./home/* ./mnt/* ./media/*'

excludes="$sys_excludes $user_excludes"

tar -C / -pc .  ${excludes} |pxz |tee $out_file | sha512sum  > ${out_file}.sha512sum


