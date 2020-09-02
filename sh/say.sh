#!/bin/bash
# date 2018-03-08 20:13:05
# author calllivecn <c-all@qq.com>

set -e

if [ -z "$1" ];then
	echo "$(basename $0)" text
	exit 1
fi


espeak -s 150 -v zh "$1" &> /dev/null
