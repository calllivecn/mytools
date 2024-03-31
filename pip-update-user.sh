#!/bin/bash
# date 2019-02-24 14:28:22
# author calllivecn <calllivecn@outlook.com>


PIP="pip3"

manual_installed_packages=$($PIP list --user --not-required --format=freeze |awk -F'=' '{print $1}')

for pack in $manual_installed_packages
do

	if [ -n $VIRTUAL_ENV ];then
		$PIP install --upgrade "$pack"
	elif [ $EUID -ne 0 ];then
		sudo $PIP install --upgrade "$pack"
	elif [ $UID -eq 0 ];then
		$PIP install --upgrade "$pack"
	else
		echo "你这好像不行啊。"
	fi

done
