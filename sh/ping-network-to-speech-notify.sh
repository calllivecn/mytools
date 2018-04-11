#!/bin/bash
# date 2018-04-06 07:29:10
# author calllivecn <c-all@qq.com>



if [ "$1"x = "-q"x -o "$1"x = "quiet"x ];then
	cmd(){
		notify-send "${USER} ...来网啦"
		sleep 10
		}
else
	cmd(){
		espeak -v zh -s 100 -p 99 "${USER} ...来网la" 2> /dev/null
		sleep 1
		}
fi

say(){

	local i

	for i in {1..3}
	do
		echo "${USER} ...来网le" 
		cmd
	done
}


network=0

while :
do

	if [ $network -eq 1 ];then
		sleep $[5*60] # 5 minute
		network=0
		continue
	fi

	ping -c 1 -W 3 www.baidu.com &> /dev/null && ping -c 1 -W 3 1.1.1.1 &> /dev/null

	if [ $? -eq 0 ];then
		network=1
		say
	else
		sleep 5
	fi

done
