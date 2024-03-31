#!/bin/bash
# date 2018-12-07 15:39:07
# author calllivecn <calllivecn@outlook.com>

set -e

logfile="$0".logs

logs(){

echo "$1"
echo "$1" >> "$0".logs

}

pwddir=$(pwd)

if [ "$1"x = "--help"x ];then
	echo "${0##*/} [压缩测试文件]"
	echo ""
	exit 0
fi

if [ -n "$1" ];then
	if [ -f "$1" ];then
		tmpfile="$1"
	else
		echo "$1: No such file"
		exit 1
	fi
else
	tmpfile=$(mktemp -p "${pwddir}")
	dd if=/dev/urandom bs=1M count=64 | base64 > "${tmpfile}"
fi

safe_exit(){
	rm "${tmpfile}" ${tmpfile}-*
}

trap safe_exit ERR 


BaseSize=$(du -b "${tmpfile}" |awk '{print $1}')
BaseSizeHuman=$(du -h "${tmpfile}" |awk '{print $1}')

printf "命令\tlevel\t原始大小\t压缩大小\t压缩耗时s\t解压耗时s\t压缩比\n" |tee -a "$logfile"

for compress in pigz pbzip2 pxz;
do
	for level in $(seq 1 9)
	do
		
		outfile="${tmpfile}-level${level}.${compress}"

		#logs "$compress -k -c -${level} "${tmpfile}" > ${outfile}"
		printf "%s\t%s\t%s\t" $compress $level $BaseSizeHuman |tee -a "$logfile"

		start_=$(date +%s)

		$compress -k -c -${level} "${tmpfile}" > "${outfile}"

		compress_size=$(du -b "${outfile}" |awk '{print $1}')
		compress_size_human=$(du -h "${outfile}" |awk '{print $1}')

		end=$(date +%s)

		#logs "压缩耗时：$[ end - start_]"
		printf "%s\t%ss\t" $compress_size_human $[end - start_] |tee -a "$logfile"

		start_=$(date +%s)
		
		$compress -k -dc "${outfile}" > /dev/null
		
		end=$(date +%s)
		
		#logs "解压耗时：$[end - start_]"
		printf "%ss\t%s.%s%%\n" $[end - start_] $[compress_size*100 / BaseSize] $[compress_size*10000 / BaseSize % 100] | tee -a "$logfile"
	done
done

safe_exit
