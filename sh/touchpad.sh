#!/bin/bash
# date 2018-02-20 18:27:45
# author calllivecn <c-all@qq.com>




STATUS=$(xinput list-props 16 |grep  -i enable |awk -F':' '{print $2}')

STATUS=$(echo $STATUS |tr -d ' ' )

if [ "$STATUS"x == "1"x ];then
	xinput disable 16
elif [ "$STATUS"x == "0"x ];then
	xinput enable 16
else
	echo "$0 status Error : $STATUS"
fi
