#!/bin/bash

set -e

if [ -z "$1" ];then
	echo "using: $0 <out_file>"
	exit -1
fi

out_file="$1"

sys_excludes='--exclude=./proc/* --exclude=./sys/* --exclude=./run/* --exclude=./tmp/* --exclude=./dev/*'
#sys_excludes='./proc/* ./sys/* ./run/* ./tmp/* ./dev/*'

user_excludes='--exclude=./home/* --exclude=./mnt/* --exclude=./media/*'
#user_excludes='./home/* ./mnt/* ./media/*'

excludes="$sys_excludes $user_excludes"

for arg in $excludes
do
	echo $arg
done

#exit 1

set -x

tar -C / -pc .  ${excludes} |pxz > $out_file

set +x

sha512sum $out_file > ${out_file}.sha512sum





