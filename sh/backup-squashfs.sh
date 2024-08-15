#!/usr/bin/bash
# create 2024-08-01 03:15:43
# author calllivecn <calllivecn@outlook.com>


exclude_sys="proc/*
sys/*
run/*
tmp/*
dev/*
var/log/*
home/*
mnt/*
media/*
"

HOSTNAME=$(hostname)
DATETIME=$(date +%F-%H-%M-%S)

BACKUP_NAME=

backup_filename_or_dirname(){
    local ID VERSION_ID
    local OS="/etc/os-release"
    if [ -r $OS ];then
        eval $(grep -E "^ID=|^VERSION_ID=" $OS)
        BACKUP_NAME="${ID}-${VERSION_ID}-${HOSTNAME}-${DATETIME}"
    else
        BAKCUP_NAME="Linux-${HOSTNAME}-${DATETIME}"
    fi

    echo "使用这个备份名字: $BACKUP_NAME"
}

HASH=1
# 需要sha256吗？
sha(){
	local data backup_filename
	echo "本次需要计算sha256吗？[Y/n]"
	read data
	if [ "$data"x = "y"x ] || [ "$data"x = "Y"x ];then
		#echo "算计sha256 ... "
		:
	else
		HASH=0
	fi

}

sha

echo "备份文件路径为当前目录"

backup_filename_or_dirname

EXCLUDE_SYS='-e proc/* -e sys/* -e run/* -e tmp/* -e dev/* -e var/log/* -e home/* -e mnt/* -e media/*'

#mksquashfs / ${BACKUP_NAME}.squashfs -b 1M -comp zstd -Xcompression-level 7 -wildcards -ef exclude.sys

mksquashfs / ${BACKUP_NAME}.squashfs -b 1M -comp zstd -Xcompression-level 7 -wildcards ${EXCLUDE_SYS}

if [ "$HASH" = 1 ];then
	sha256sum "${BACKUP_NAME}.squashfs" |tee "${BACKUP_NAME}.squashfs.sha256"
fi


