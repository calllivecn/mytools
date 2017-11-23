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


check_environment(){
	if test -f $AC;then
		notify-send "$AC 不存在,exit ${0##*/}"
	fi
}


check_environment

set -e

while :
do
	status=$(cat $AC)

	test $status -eq 1 && sleep 60 || systemctl poweroff
done
