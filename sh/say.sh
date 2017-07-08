#!/bin/sh



if [ -z "$1" ];then
	echo "$(basename $0)" text
	exit 1
fi



cmd='espeak -s 130 -v zh '"$1"' &> /dev/null'

eval $cmd

