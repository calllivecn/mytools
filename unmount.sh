#!/bin/bash
# date 2019-10-10 21:39:52
# author calllivecn <c-all@qq.com>


PROGRAM="${0##*/}"

if type -p udisksctl >/dev/null;then
	:
else
	echo "需要安装udisks2, sudo apt install udisks2"
	exit 1
fi

usage(){

	echo "Usage: $PROGRAM <block device>"
	echo "例如："
	echo "$PROGRAM /dev/sdb"
}

case "$1" in 
	-h|--help)
		usage
		exit 0
		;;
esac

if [ -z "$1" ];then
	echo "${1} 块设备不存在。"
	exit 2
fi


for part in $(echo "${1}[0-9]*")
do
	udisksctl unmount -b "$part"
done

udisksctl power-off -b "${1}"
