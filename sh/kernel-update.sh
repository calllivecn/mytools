#!/bin/bash
# date 2018-11-24 17:26:43
# author calllivecn <c-all@qq.com>


set -xe

KERNEL="4.18.0"
KERNEL="4.15.0"
KERNEL="5.3.0"

if echo "$1" | grep -qE '[0-9]{2,3}';then
	kernel_version="$1"
else
	echo "需要一个内核版本号。"
	exit 1
fi

if [ "$2"x == "update"x ];then
	sudo apt install linux-image-${KERNEL}-${kernel_version}-generic linux-modules-${KERNEL}-${kernel_version}-generic linux-modules-extra-${KERNEL}-${kernel_version}-generic linux-headers-${KERNEL}-"${kernel_version}"{,-generic}
elif [ "$2"x == "remove"x ];then
	sudo apt autoremove --purge linux-image-${KERNEL}-${kernel_version}-generic linux-modules-${KERNEL}-${kernel_version}-generic linux-modules-extra-${KERNEL}-${kernel_version}-generic linux-headers-${KERNEL}-"${kernel_version}"{,-generic}
else
	sudo apt install linux-image-${KERNEL}-${kernel_version}-generic linux-modules-${KERNEL}-${kernel_version}-generic linux-modules-extra-${KERNEL}-${kernel_version}-generic linux-headers-${KERNEL}-"${kernel_version}"{,-generic}
fi
