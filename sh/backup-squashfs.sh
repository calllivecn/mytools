#!/usr/bin/bash
# create 2024-08-01 03:15:43
# author calllivecn <calllivecn@outlook.com>



HOSTNAME=$(hostname)
DATETIME=$(date +%F-%H-%M-%S)

BACKUP_NAME=


backup_filename_or_dirname(){
    local ID VERSION_ID
    local OS="/etc/os-release"
    if [ -r $OS ];then
        eval $(grep -E "^ID=|^VERSION_ID=" $OS)
        BACKUP_NAME="${ID}-${VERSION_ID}-${HOSTNAME}-${DATETIME}"
    else
        BAKCUP_NAME="Linux-${HOSTNAME}-${DATETIME}"
    fi

    # echo "使用这个备份名字: $BACKUP_NAME"
}

backup_filename_or_dirname


HASH=1
sha(){
	local data backup_filename
	echo "本次需要计算sha256吗？[Y/n]"
	read data
	if [ "$data"x = "y"x ] || [ "$data"x = "Y"x ];then
		#echo "算计sha256 ... "
		:
	else
		HASH=0
	fi

}


BACKUP_SQUASHFS="${BACKUP_NAME}.squashfs"

backup(){
	local output_squahfs="$1"
	
	EXCLUDE_SYS='-e proc/* -e sys/* -e run/* -e tmp/* -e dev/* -e var/log/* -e home/* -e mnt/* -e media/*'
	
	# mksquashfs / ${BACKUP_SQUASHFS} -b 1M -comp zstd -Xcompression-level 7 -wildcards ${EXCLUDE_SYS}
	mksquashfs / ${output_squahfs} -b 1M -comp zstd -Xcompression-level 7 -wildcards ${EXCLUDE_SYS}
	
}


temp_fifo=$(mktemp -qu -t squashfs-XXXXX)

mkfifo "$temp_fifo"

safe_exit(){

	rm -v "$temp_fifo"
}


trap safe_exit ERR EXIT SIGTERM SIGINT

split_func(){
	local tmp="$(basename "$1")"
	local DIR="${tmp%.squashfs}"
	local DIR2="${2}/$DIR"
	mkdir -v "$DIR2"
	cat "$1" | tee "$temp_fifo" | split -b 1G - "${DIR2}/squashfs." &
	sha256sum "$temp_fifo" |tee "${DIR2}/sha256.txt"
}


printusage(){
	echo "Usage: ${0} <--squashfs output_dir> [--split <split output_dir>]"
}


main(){

	#echo "请选择任务，切分文件计算sha值"

	if [ "$1"x != "--squashfs"x ];then
			printusage
			exit 1
	fi

	if [ -d "$2" ];then
		OUTPUT_SQUASHFS="$(realpath "${2}")/${BACKUP_SQUASHFS}"
		
		echo "输出到: ${OUTPUT_SQUASHFS}"
	else
		echo "给出的路径不存在。"
		exit 1
	fi


    echo "使用这个备份名字: $BACKUP_NAME"
	backup "${OUTPUT_SQUASHFS}"
    echo "使用这个备份名字: $BACKUP_NAME ... done"


	if [ "$3"x = "--split"x ];then

		if [ -d "$4" ];then
			output_dir="$(realpath "${4}")"
			echo "--split 输出到：${output_dir}"
			split_func "${OUTPUT_SQUASHFS}" "${output_dir}"
		else
			echo "--split 的输出目录不存在..."
			exit 1
	
		fi
	fi


}


main "$@"

