#!/bin/bash
# update 2018-04-28 23:29:32
# author calllivecn <c-all@qq.com>


set -e

mkfifo_file(){
	FIFO=$(mktemp -u)
	mkfifo $FIFO
}

clean(){
	rm $FIFO
}

using(){
echo "Using: ${0##*/} [-b <split block>] <filename>"
exit 0
}

trap "clean" SIGTERM SIGINT ERR

SPLIT=0
while getopts "b:h" args
do
	case $args in
		b)
			SPLIT=1
			SPLIT_BLOCK="$OPTARG"
			mkfifo_file
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

if [ $(id -u) -ne 0 ];then
	echo need root user
	exit 1
fi

out_file="$1".tar.xz

if [ -z "$1" ] || [ -f "$1" ];then
	echo "using: $(basename $0) <out_file>.tar.xz"
	echo "or error exit $1 exists"
	exit 1
fi


sys_excludes='--exclude=./proc/* --exclude=./sys/* --exclude=./run/* --exclude=./tmp/* --exclude=./dev/* --exclude=./var/log/*'
#sys_excludes='./proc/* ./sys/* ./run/* ./tmp/* ./dev/*'

user_excludes='--exclude=./home/* --exclude=./mnt/* --exclude=./media/*'
#user_excludes='./home/* ./mnt/* ./media/*'

excludes="$sys_excludes $user_excludes"


if [ $SPLIT = 0 ];then
	tar -C / -pc ${excludes} . |pxz |tee $out_file | sha512sum  > ${out_file}.sha512sum
elif [ $SPLIT = 1 ];then
	tar -C / -pc ${excludes} . |pxz |tee $FIFO |split -b "${SPLIT_BLOCK}" - ${out_file}. &
	sha512sum $FIFO | awk -v filename=${out_file} '{print $1,filename}' > ${out_file}.sha512sum
fi
