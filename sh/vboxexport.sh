#!/bin/bash
# date 2020-09-28 22:25:47
# author calllivecn <calllivecn@outlook.com>



if type -p vboxmanage 2>&1 > /dev/null;then
	:
else
	echo "你没有安装virtualbox"
	exit 1
fi





checkhash(){

	local yesno=

	if [ "$SPLIT"x = "yes"x ];then
		yesno=y
	else

		while :
		do

			echo -e "\033[32m本次计算sha256值吗？[y/n].\033[0m"
			read yesno
			if [ "$yesno"x = "y"x ] || [ "$yesno"x = "n"x ];then
				break
			else
				echo "请重新输入 y or n"
			fi
		done

	fi

	
	HASHSUM=
	if [ "$yesno"x == "y"x ];then
		echo -e "\033[32m本次计算sha256值.\033[0m"

		if type -p hash.py 2>&1 > /dev/null;then
			HASHSUM=hash.py
		elif type -p sha256sum 2>&1 > /dev/null;then
			HASHSUM=sha256sum
		else
			echo -e "\033[31m你没有安装sha256工具, 本次不计算hash值。\033[0m"
		fi

	else
		echo -e "\033[32m本次不计算sha256值.\033[0m"

	fi
}

SPLIT_OUTPUT_DIR="."
split_output_dir(){

	while :;
	do
		echo "请输入切割输出目录的上层目录(需要已经存在，会给出的目录中自动创建split的分割目录)："
		read SPLIT_OUTPUT_DIR

		if [ -d "$SPLIT_OUTPUT_DIR" ] && [ -w "$SPLIT_OUTPUT_DIR" ];then
			break
		else
			echo -e "\033[31m给出的目录路径不存在，请重新输入。。。\033[0m"
		fi
	done

}

checksplit(){

	local yesno=
	while :
	do
		echo -e "\033[32m需要自动创建 split 分割文件大小吗？[y/n]\033[0m"
		read yesno

		if [ "$yesno"x = "y"x ] || [ "$yesno"x = "n"x ];then
			break
		else
			echo "请重新输入 y or n"
		fi

	done

	# 看看是不是自动分割文件
	SPLIT=
	if [ "$yesno"x == "y"x ];then
		echo -e "\033[32m本次会自动分割文件, 同时也会计算sha256。\033[0m"
		split_output_dir
		SPLIT="yes"
	else
		echo -e "\033[32m本次不自动分割文件.\033[0m"
	fi
}


export_vm(){
	echo -e "\033[31m导出的虚拟文件会，放在当前执行路径下。\033[0m"

	TIMESTAMP=$(date +%F-%H-%M-%S)

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
	
	export_vmname="${VMS[$number]}-${TIMESTAMP}.ova"
	export_vmname_sha256="${export_vmname}.sha256"
	
	vboxmanage export "${VMS[$number]}" -o "${export_vmname}" --ovf20 --manifest
	
	IFS=$old_IFS
}


FIFO=$(mktemp -u --suffix fifo)
mkfifo "$FIFO"
if [ $? -eq 0 ];then
	:
else
	echo "创建临时fifo文件失败..."
	exit 1
fi

safe_exit(){
	rm -rf "$FIFO"
}

trap safe_exit ERR EXIT

main(){
	checksplit
	checkhash
	export_vm

	# 创建切割输出目录
	split_output_dir_export_vmname_timestamp="${SPLIT_OUTPUT_DIR}/${export_vmname%.ova}"
	if [ -d "${split_output_dir_export_vmname_timestamp}" ];then
		:
	else
		mkdir -v "${split_output_dir_export_vmname_timestamp}"
	fi

	echo "sha256 ...."
	if [ "$SPLIT"x = "yes"x ];then
		eval cat "${export_vmname}" |tee "$FIFO" | split -b 1G - "${split_output_dir_export_vmname_timestamp}/${export_vmname}." &

		sha256_result=$($HASHSUM "${FIFO}")
		sha256_result=${sha256_result::64}
		echo "$sha256_result ${export_vmname}" |tee "${split_output_dir_export_vmname_timestamp}/${export_vmname_sha256}"

	else

		if [ "$HASHSUM"x = x ];then
			echo "不计算sha256"
		else
			$HASHSUM "${export_vmname}" |tee "${export_vmname_sha256}"
		fi

	fi
	
}

main
