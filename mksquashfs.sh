#!/bin/bash

set -e
#mount |awk '{if($3~/^\// && $1!~/^\//)print $3}' |awk -F'/' '{print $2}' |sort |uniq

tmpsys=$(mktemp)

tmp=$(mktemp)

echo 'proc/
sys/
dev/
run/
tmp/
' > $tmpsys

echo 'mnt/wind/
' >> $tmp

outfilename="$1"

tmpdir=$(mktemp -d)

mount --bind / "$tmpdir"

mksquashfs "$tmpdir" "$1" -ef $tmp -ef $tmpsys -comp xz

umount $tmpdir

for dir in $(cat $tmpsys);do mkdir ${tmpdir}/${dir};done

chmod 755 ${tmpdir}/*

chmod 1777 ${tmpdir}/tmp

mksquashfs "$tmpdir" "$1" 

rm -f $tmp $tmpsys
rm -rf $tmpdir
