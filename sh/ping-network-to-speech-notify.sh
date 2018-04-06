#!/bin/bash
# date 2018-04-06 07:29:10
# author calllivecn <c-all@qq.com>


say(){

	local i
	for i in {1..3}
	do
		espeak -v zh -s 100 -p 99 "哥...来网le" 2> /dev/null
		sleep 1
	done
}

network=0

while :
do

	if [ $network -eq 1 ];then
		sleep $[15*60] # 15 minute
		#sleep 5 
		network=0
		continue
	fi

	ping -c 1 -W 3 www.baidu.com &> /dev/null
	#ping -c 1 -W 3 localhost &> /dev/null
	if [ $? -eq 0 ];then
		network=1
		say
	else
		sleep 5
	fi

done
