#!/bin/bash
# date 2020-09-28 22:25:47
# author calllivecn <c-all@qq.com>



if type -p vboxmanage 2>&1 > /dev/null;then
	:
else
	echo "你没有安装virtualbox"
	exit 1
fi

HASHSUM=
if [ "$1"x == "--sha256"x ];then
	echo "本次计算sha256值."

	if type -p hash.py 2>&1 > /dev/null;then
		HASHSUM=hash.py
	elif type -p sha256sum 2>&1 > /dev/null;then
		HASHSUM=sha256sum
	else
		echo "你没有安装sha256工具, 本次不计算hash值。"
	fi

else
	echo -e "\033[32m本次不计算sha256值.\033[0m"

fi

# 看看是不是自动分割文件
SPLIT=
if [ "$1"x == "--split"x ];then
	echo "本次会自动分割文件, 同时也会计算sha256。"
	SPLIT="yes"
else
	echo -e "\033[32m本次不自动分割文件.\033[0m"
fi


export_vm(){
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
	export_vmname_sha256="${export_vmname}.sha256"
	
	vboxmanage export "${VMS[$number]}" -o "${export_vmname}" --ovf20 --manifest
	
	IFS=$old_IFS
}


main(){
	export_vm
	
	echo "sha256 ...."
	
	if [ "$HASHSUM"x = x ];then
		echo "不计算sha256"
	else
		$HASHSUM "${export_vmname}" |tee "${export_vmname_sha256}"
	fi
}

main
