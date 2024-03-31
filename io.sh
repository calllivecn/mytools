#!/bin/bash
# date 2017-10-28 20:07:53
# author calllivecn <calllivecn@outlook.com>

error(){
echo "error exit"
exit 1
}

trap "error" ERR

set -e

being=
end=

block=1M
count=256
work_dir=$(pwd)

using(){
local str="Using : $(basename $0)"
str="$str"'
-h		print this information
-d		work_dir in directoy (default: `pwd`)
-s		test file size, unit MB (default: 256)
'
#-b		I/O block size (default: 1M)

echo "$str"
}

while getopts ':hs:d:' opt
do
	case "$opt" in
		h)
			using
			exit 0
			;;
		#b)
		#	block="$OPTARG"
		#	;;
		s)
			count="$OPTARG"
			;;
		d)
			work_dir="$OPTARG"
			;;
		\?)
			echo "-${OPTARG} invalid option"
			exit 1
			;;
		\:)
			echo "-${OPARG} need a argument"
			exit 1
			;;
	esac
done
shift $[ OPTIND - 1 ]

filename=$(mktemp -p "$work_dir")

safe_exit(){
	rm -f "$filename"
	exit 0
}


trap "safe_exit" SIGINT SIGTERM

echo -e "\033[31mtest writing ...\033[0m"
#dd if=/dev/zero of="$filename" bs=$block count=$count oflag=direct conv=fsync status=progress 2>&1 |tail -n 1
dd if=/dev/zero of="$filename" bs=$block count=$count oflag=direct conv=fsync status=progress
echo -e "\033[31mtest reading ...\033[0m"
#dd if="$filename" of=/dev/null ibs=$block iflag=direct status=progress 2>&1 |tail -n 1
dd if="$filename" of=/dev/null ibs=$block iflag=direct status=progress

# clear filename
safe_exit
