#!/bin/bash
# date 2019-02-03 09:39:18
# author calllivecn <c-all@qq.com>
# https://github.com/calllivecn


t=0
while :;
do

	ssh -N -R 1222:localhost:22 linux@calllive.cc && t=0
	
	if [ $t -gt 5 ];then
		:
	else
		t=$[$t + 1]
	fi

	sleep $[ $t * 60 ]
done

