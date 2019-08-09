#!/bin/bash
# date 2019-06-11 14:52:06
# author calllivecn <c-all@qq.com>


PROXY_ADDR="http://127.0.0.1:9999"

URLs="ppa.launchpad.net
linux.teamviewer.com
packages.microsoft.com"

APT_OPTION=""
for http in $URLs
do
	for scheme in http https
	do
		APT_OPTION="$APT_OPTION -o Acquire::${scheme}::Proxy::${http}=$PROXY_ADDR "
	done
done


if [ "$1"x = "debug"x ];then
	shift
	echo apt $APT_OPTION "$@"
else
	apt $APT_OPTION "$@"
fi

