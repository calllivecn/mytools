#!/bin/bash
# date 2021-01-11 21:57:09
# author calllivecn <c-all@qq.com>


# system boot beep --> SBB.sh

# 0. 怎么使用主板上的蜂鸣器(主板要支持，且已启用)
#
# 1. linux 需要加载 pcspkr 模块
# ubuntu 默认是把它加入了/etc/modprobe.d/blacklist.conf
#
# 2. 使用root用户执行
# echo -an '\a' > /dev/console
#
# 3. install --> /usr/local/sbin/

c=3
while [ $c -gt 0 ]
do
	echo -en '\a' > /dev/console
	sleep 0.2
	c=$[c - 1]
done
