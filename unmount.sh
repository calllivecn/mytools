#!/bin/bash
# date 2019-10-10 21:39:52
# author calllivecn <c-all@qq.com>



if type -p udisksctl >/dev/null;then
	:
else
	echo "需要安装udisks2, sudo apt install udisks2"
	exit 1
fi


