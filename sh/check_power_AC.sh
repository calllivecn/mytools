#!/bin/bash
# date 2017-11-23 12:58:36
# author calllivecn <c-all@qq.com>



############################
#
# 测试笔记本是否有AC电源
# 没有就关机
#
############################

AC=/sys/class/power_supply/AC/online
touch_file=/tmp/cancel.ac


check_environment(){
	if ! test -f $AC;then
		notify-send "$AC 不存在,exit ${0##*/}"
		exit 1
	fi
}

cancel_notify(){
	notify-send "AC下线，5分钟后关机！取消命令 touch $touch_file"
}

cancel(){
	for i in {1..300}
	do
		if test -f $touch_file;then
			rm $touch_file
			exit 0
		else
			sleep 1
		fi
	done

}

check_environment

set -e

while :
do
	status=$(cat $AC)

	if test $status -eq 1;then
		sleep 5
	else
		cancel_notify
		cancel
		systemctl poweroff
	fi
done
