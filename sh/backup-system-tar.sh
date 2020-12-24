#!/bin/bash
# update 2018-04-28 23:29:32
# author calllivecn <c-all@qq.com>


set -e

mk_file(){
	FIFO=$(mktemp -u)
	mkfifo $FIFO
	mkdir "${out_dir}"
}

TRAP=0
clean(){

	if [ $TRAP = 1 ];then
		return
	fi

	if [ $SPLIT = 0 ];then
		rm "$out_file"
		rm "${out_file}.sha512sum"
	elif [ $SPLIT = 1 ];then
		rm $FIFO
		kill $PID
		rm -r "${out_dir}"
	fi

	TRAP=1
}

show_speed(){
	
	if type -p pv 2>&1 > /dev/null;then
		CMD="pv -ba"
	else
		CMD=cat
	fi

$CMD
}

xz_tool(){
	# pxz 命令从ubuntu 19.04 改为 pixz 
	if type -p pxz 2>&1 > /dev/null;then
		XZ=pxz
	elif type -p pixz 2>&1 > /dev/null;then
		XZ=pixz
	elif type -p xz 2>&1 > /dev/null;then
		XZ=xz
	else
		echo "需要xz-utils OR pixz"
		exit 1
	fi
}

using(){
echo "Using: ${0##*/} [[-b <split block>] | <output diectory name> ] | <filename>"
exit 0
}

xz_tool

trap "clean" SIGTERM SIGINT ERR

SPLIT=0
while getopts "b:h" args
do
	case $args in
		b)
			SPLIT=1
			SPLIT_BLOCK="$OPTARG"
			;;
		h)
			using
			;;
		\:)
			echo "-${OPTARG} 需要一个参数"
			exit 1
			;;
		\?)
			echo "不认得的选项"
			exit 1
			;;

	esac
done

shift $[ OPTIND - 1 ]

out_file="${1%/}".tar.xz

out_dir="${1%/}"

out_filename="${out_dir##*/}".tar.xz

if [ -z "$1" ] || [ -f "$1" ] || [ -d "$out_dir" ];then
	echo "using: $(basename $0) <out_file>"
	echo "or error exit $1 exists"
	exit 1
fi

if [ $SPLIT = 1 ];then
	mk_file
fi

if [ $(id -u) -ne 0 ];then
	echo need root user
	exit 1
fi


sys_excludes='--exclude=./proc/* --exclude=./sys/* --exclude=./run/* --exclude=./tmp/* --exclude=./dev/* --exclude=./var/log/* --exclude=./snap/*'
#sys_excludes='./proc/* ./sys/* ./run/* ./tmp/* ./dev/*'

user_excludes='--exclude=./home/* --exclude=./mnt/* --exclude=./media/*'
#user_excludes='./home/* ./mnt/* ./media/*'

excludes="$sys_excludes $user_excludes"


if [ $SPLIT = 0 ];then
	tar -C / --acls -pc ${excludes} . 2> /dev/null |$XZ |show_speed |tee $out_file | sha512sum > ${out_file}.sha512sum
elif [ $SPLIT = 1 ];then
	tar -C / --acls -pc ${excludes} . 2>/dev/null |$XZ |show_speed |tee $FIFO |split -b "${SPLIT_BLOCK}" - "${out_dir}"/"${out_filename}". &
	sha512sum $FIFO | awk -v filename=${out_filename} '{print $1,filename}' > "${out_dir}"/"${out_filename}".sha512sum
fi

# 恢复 pixz < *.tar.xz | tar -vx -C /tmp/<***>
