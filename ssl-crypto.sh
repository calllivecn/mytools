#!/bin/bash

program=${0##*/}

using(){
	echo "Using : $program [-dzjJa] <-f crypto file> [crypto file or directory ...]"
	echo "-f	crypto filename"
	echo "-d	decrypto (defalut is crypto)"
	echo "-z	filter the archive through gzip"
	echo "-j	filter the archive through bzip2"
	echo "-J	filter the archive through xz"
	echo "-a	Accelerated archive compression"
	echo "  	(requires support pigz and pbzip2 and pxz)"
	exit -1
}

check_accelerated(){
	if ! type -p $1 &> /dev/null ;then
		echo "argument -a accelerated need install $1"
		exit 1
	fi
}

crypto_decrypto(){
	if [ "$crypto" == "T" ];then
		echo "$1"
	else
		echo "$1 -d"
	fi
}

build_outfile__(){
	if [ -z "$1" ];then
		out_file__='.tar.pw'
	elif [ "$1" == "-z" ];then
		out_file__='.tar.gz.pw'
	elif [ $1 == "-j" ];then
		out_file__='.tar.bz2.pw'
	elif [ $1 == "-J" ];then
		out_file__='.tar.xz.pw'
	fi
}

out_file__=
out_file=
crypto=T
tar_crypto='-c'
tar_C=
compress=
accelerated=F

while getopts ":aC:df:zjJ" opt
do
	case $opt in
		f)
			out_file=$OPTARG
			;;
		C)
			tar_C="-C $OPTARG"
			;;
		d)
			crypto=F
			tar_crypto='-x'
			;;
		a)
			accelerated=T
			;;
		z)
			compress='-z'
			;;
		j)
			compress='-j'
			;;
		J)
			compress='-J'
			;;
		*)
			echo "Unknown option:$opt"
			using
			exit 1
			;;
	esac
done

shift $[ $OPTIND - 1 ]


# 参数检查
if [ -z $out_file ];then
	using
fi

if [ $crypto == "T" ];then
	if [ "$#" -lt 1 ];then
		echo "crypto mode required crypto file or directoy"
		echo
		using
	fi
fi

target_files="$@"

#####

# 构建和检查加速命令
if [ $accelerated == "T" ];then
	if [ $compress == "-z" ];then
		check_accelerated "pigz"
		accelerated_cmd=$(crypto_decrypto pigz)
		echo $accelerated_cmd
	elif [ $compress == "-j" ];then
		check_accelerated "pbzip2"
		accelerated_cmd=$(crypto_decrypto pbzip2)
	elif [ $compress == "-J" ];then
		check_accelerated "pxz"
		accelerated_cmd=$(crypto_decrypto pxz)
	fi
else
	accelerated_cmd=''
fi

# 构建加密命令
if [ $crypto == "T" ];then
	crypto_cmd='openssl aes-256-cbc -salt -out '"$out_file"
else
	crypto_cmd='openssl aes-256-cbc -salt -d -in '"$out_file"
fi

# 构建tar命令
if [ -z $compress ];then
	compress_cmd="tar $tar_C $tar_crypto $target_files"
elif [ -n $compress -a $accelerated == "F" ];then
	compress_cmd="tar $tar_C $compress $tar_crypto $target_files"
elif [ -n $compress -a $accelerated == "T" ];then
	compress_cmd="tar $tar_C $tar_crypto $target_files"
fi

#判断加密，解密
if [ $crypto == "T" ];then
	if [ "$accelerated" == "T" ];then
		execute_cmd="$compress_cmd | $accelerated_cmd | $crypto_cmd"
	else
		execute_cmd="$compress_cmd | $crypto_cmd"
	fi
else
	if [ "$accelerated" == "T" ];then
		execute_cmd="$crypto_cmd | $accelerated_cmd | $compress_cmd"
	else
		execute_cmd="$crypto_cmd | $compress_cmd"
	fi
fi

#执行
#echo $execute_cmd
echo "outfile --> $outfile"
eval $execute_cmd

