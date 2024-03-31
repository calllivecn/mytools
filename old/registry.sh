#!/bin/bash
# date 2018-08-16 14:01:25
# author calllivecn <calllivecn@outlook.com>


REGISTRY="http://hub.bnq.com.cn"

if [ -n "$1" ];then
	REGISTRY="$1"
	shift
	curl -Ls -X GET ${REGISTRY}/v2/_catalog 
fi

while getopts ':it:' args;
do
	case "$args" in
		i)
			curl -Lfs -X GET ${REGISTRY}/v2/${OPTARG}/tags/list 
			;;
		\?)
			echo "invaild option."
			exit 2
			;;
		\:)
			echo "need parameter."
			exit 2
			;;
	esac
done


