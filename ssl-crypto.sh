#!/bin/bash

program=$(basename $0)

using(){
	echo "Using : $program <enc|dec> [out filename] <crypto file or directory>"
	exit -1
}

option="$1"

out_file="$2"

arg3="${3%/}"


if [ "$option"x != "enc"x -a "$option"x != "dec"x ];then
	
	using

fi


if [ "$#" -lt 3 ];then
	arg3=${out_file%/}
	
	out_file=${arg3##*/}.tar.xz.pw

fi



if [ "$option"x == "enc"x ];then

	tar -c $arg3 | xz | openssl aes-256-cbc -salt -out $out_file

elif [ "$option"x == "dec"x ];then

	openssl aes-256-cbc -salt -d -in $arg3 |xz -d |tar -x

fi
