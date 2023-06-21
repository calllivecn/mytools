#!/bin/bash
# date 2020-09-28 22:25:47
# author calllivecn <c-all@qq.com>



if type -p vboxmanage 2>&1 > /dev/null;then
	:
else
	echo "你没有安装virtualbox"
	exit 1
fi

old_ifs=$IFS

VMS=()
c=1
IFS=$'\n'
for line in $(vboxmanage list vms |grep -oE '"(.*)"'| sed 's/"//g')
do
	echo "$c) $line" 
	VMS[$c]="$line"
	c=$[c+1]
done


echo "默认保存到当前目录"
echo -n "选择导出哪个虚拟机(0 退出): "
read number

# 默认是 0 退出脚本
number=${number:-0}


if [ $number = "0" ];then
	exit 0
fi

export_vmname="${VMS[$number]}-$(date +%F-%H-%M-%S).ova"
export_vmname_sha256="${export_vmname_sha256}.sha256"

vboxmanage export "${VMS[$number]}" -o "${export_vmname}" --ovf20 --manifest

IFS=$old_IFS

echo "sha256 ...."

hash.py --sha256 "${export_vmname}" |tee "${export_vmname_sha256}"

