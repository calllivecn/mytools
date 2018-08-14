#!/bin/bash
# date 2018-02-20 18:27:45
# author calllivecn <c-all@qq.com>

set -e

# 需要你配置，xinput list --name-only 查看你想操作的设备
DEVICE_NAME=""

if [ -z "${DEVICE_NAME}" ];then
	echo "需要你配置 ${0##*/} 里面的 DEVICE_NAME 变量，"
	echo "xinput list --name-only 查看你想操作的设备"
	exit 2
fi

device=$(xinput list --id-only "${DEVICE_NAME}")

STATUS=$(xinput list-props $device |grep  -i enable |awk -F':' '{print $2}' |tr -d '\t ' )

if [ "$STATUS"x == "1"x ];then
	xinput disable $device
elif [ "$STATUS"x == "0"x ];then
	xinput enable $device
else
	echo "$0 status Error : $STATUS"
fi
