#!/bin/bash
# date 2020-04-22 21:45:45
# author calllivecn <c-all@qq.com>

# 编写git credential 插件文档
# https://git-scm.com/book/zh/v2/Git-%E5%B7%A5%E5%85%B7-%E5%87%AD%E8%AF%81%E5%AD%98%E5%82%A8


action="$2"

token="$1"

stores='protocol=https
host=github.com
username=<un>
password=<pw>'

echo "action=$2" "token=$1" >&2

get(){
	local keys

	while read arg;
	do
		if [ "$arg"x == x ];then
			break
		else
			keys="$keys ""$arg"
		fi
	done

	echo "$stores" |tr ' ' '\n'
}

get
