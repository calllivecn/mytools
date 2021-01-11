#!/bin/bash
# date 2021-01-10 17:49:49
# author calllivecn <c-all@qq.com>


# 0. 怎么使用主板上的蜂鸣器
#
# 1. linux 需要加载 pcspkr 模块
# ubuntu 默认是把它加入了/etc/modprobe.d/blacklist.conf
#
# 2. 使用root用户执行
# echo -an '\a' > /dev/console
#
# 3. install --> /usr/local/sbin/

beep(){
while [ $count -gt 0 ]
do
	echo -en '\a' > /dev/console
	sleep 0.5
	count=$[count - 1]
done
}

count=0
interval=1
t1=$(date +%s)

notify(){

	if [ $count -ne 0 ];then
		echo "电源键被按下了 ${count} 次."
		beep
	fi

	case $count in
		0)
			#这里就说明没有按下
			:
			;;
		1)
			;;
		2)
			systemctl poweroff
			;;
		3)
			systemctl poweroff -i
			;;
	esac
}

journalctl -n 0 -f _COMM=systemd-logind |while read -t 2 log || true;
do
	if [ "$log"x = x ];then
		# powerkey超时
		notify
		count=0
	else
		echo "journald log: $log"
	fi

	if echo "$log" |grep -q "Power key pressed";then

		t2=$(date +%s)
		tmp=$[t2 - t1]
		t1=$t2
	
		# flag 着2秒计时开始
		if [ $count -eq 0 ];then
			t1=$(date +%s)
			count=$[count + 1]
		elif [ $tmp -le $interval ];then
			count=$[count + 1]
		else
			count=0
		fi
	
	fi

done 
