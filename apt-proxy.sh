#!/bin/bash
# date 2019-06-11 14:52:06
# author calllivecn <c-all@qq.com>


PROXY_ADDR="$(grep -oP '(?<=http_proxy=")(.*)(?=")' $HOME/.config/xiyou)"

URLs="ppa.launchpad.net
linux.teamviewer.com
packages.microsoft.com
dl.google.com"

APT_OPTION=""
for http in $URLs
do
	for scheme in http https
	do
		APT_OPTION="$APT_OPTION -o Acquire::${scheme}::Proxy::${http}=$PROXY_ADDR "
	done
done

SUDO(){
	if [ $EUID -ne 0 ];then
		sudo apt $APT_OPTION "$@"
	else
		apt $APT_OPTION "$@"
	fi  
}



if [ "$1"x = "debug"x ];then
	shift
	echo apt $APT_OPTION "$@"
else
	SUDO "$@"
fi

