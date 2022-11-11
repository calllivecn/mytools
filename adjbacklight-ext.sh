#!/bin/bash
# date 2021-10-17 20:42:56
# author calllivecn <c-all@qq.com>

# X11 下的
# SELECT_MONITOR: 外接显示器(使用randr, 命令查看), $1: 0 ~ 1 之间的值，亮度。
# xrandr --output "$SELECT_MONITOR" --brightness "$1"

# 调整外接显示的亮度, 用户需要在 i2c 用户组里, 否则需要root执行。
# apt install ddcutil
# ddcutil getvcp 0x10: --> VCP code 0x10 (Brightness): current value =    17, max value =   100


SUDO=0
if groups |grep -q i2c;then
	:	
else
	SUDO=1
fi

if [ "$1"x = x ];then
	if [ $SUDO = 0 ];then
		ddcutil getvcp 0x10
	else
		sudo ddcutil getvcp 0x10
	fi
else
	if [ $SUDO = 0 ];then
		ddcutil setvcp 0x10 "$1"
	else
		sudo ddcutil setvcp 0x10 "$1"
	fi
fi


