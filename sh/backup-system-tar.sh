#!/bin/bash
# update 2018-04-28 23:29:32
# author calllivecn <c-all@qq.com>


set -e

mk_file(){
	FIFO=$(mktemp -u)
	mkfifo $FIFO

	TAR_USE=$(mktemp --suffix=.sh)

	if [ $SPLIT = 1 ];then
		mkdir "${out_dir}"
	fi
}

PROGRAM="${0##*/}"

SHA_SUFFIX="sha256"

HOSTNAME=$(hostname)
DATETIME=$(date +%F-%H-%M-%S)

clear_tmp(){
	rm $FIFO
	rm $TAR_USE
}

TRAP=0
error_exit_clear(){

	if [ $TRAP = 1 ];then
		return
	fi

	if [ $SPLIT = 0 ];then

		rm "$out_file"
		rm "${out_file}.${SHA_SUFFIX}"

	elif [ $SPLIT = 1 ];then

		kill $TAR_PID
		rm -r "${out_dir}"
	fi

	TRAP=1
}

backup_filename_or_dirname(){
	local ID VERSION_ID 
	local OS="/etc/os-release"
	if [ -r $OS ];then
		eval $(grep -E "^ID=|^VERSION_ID=" $OS)
		BACKUP_NAME="${ID}-${VERSION_ID}-${HOSTNAME}-${DATETIME}"
	else
		BAKCUP_NAME="Linux-${HOSTNAME}-${DATETIME}"
	fi
	
	echo "使用这个备份名字: $BACKUP_NAME"
}

show_speed(){
	
	local CMD

	if type -p pv 2>&1 > /dev/null;then
		CMD="pv -ba"
	else
		CMD=cat
	fi

$CMD
}

# 弃用
xz_tool(){
	# pxz 命令从ubuntu 19.04 改为 pixz 
	if type -p pxz 2>&1 > /dev/null;then
		XZ=pxz
	elif type -p pixz 2>&1 > /dev/null;then
		XZ=pixz
	else
		echo "需要 apt install xz-utils OR pxz OR pixz"
		exit 1
	fi

	echo "X"
}

# 改为使用
zstd_tool(){
	if type -p pzstd 2>&1 > /dev/null;then

		if [ "$RESTORE"x = "1"x ];then
			ZSTD="pzstd -d -c"
		else
			ZSTD="pzstd -10 -c"
		fi

	else
		echo "需要 apt install zstd"
		exit 1
	fi 
	#echo "$ZSTD"
}

# ase.py
aes_type(){
	if type -p aes.py 2>&1 > /dev/null;then
		AES="aes.py"
	else
		echo "需要 aes.py 下载地址 https://github.com/calllivecn/mytools/aes.py"
		exit 1
	fi
}

check_aes_password(){
	local p1 p2
	read -s -p "password: " p1
	echo
	read -s -p "password(agent): " p2
	echo

	if [ "$p1"x = ""x ] || [ "$p2"x = ""x ];then
		echo "两次输入的密码不能为空."
		exit 1

	elif [ "$p1"x != "$p2"x ];then
		echo "两次输入的密码不一样."
		exit 1
	else
		AES_PASSWORD="$p1"
	fi

}

aes_type
zstd_tool
compress_program_and_suffix(){


chmod u+x "$TAR_USE"

if [ "$ENCRYPTO"x = "0"x ];then

# 这是不加密的
cat >"${TAR_USE}"<<EOF
#!/bin/sh
case "\$1" in
	-d)
		${ZSTD}
		;;
	'')
		${ZSTD}
		;;
	*)
		echo "Unknown option $1" >&2
		exit 1
		;;

esac
EOF

else

check_aes_password

# 这是加密的
cat >>"${TAR_USE}"<<EOF
#!/bin/sh
case "\$1" in
	-d)
		${AES} -d -k "${AES_PASSWORD}" | ${ZSTD}
		;;
	'')
		${ZSTD} | ${AES} -p "系统备份" -k "${AES_PASSWORD}"
		;;
	*)
		echo "Unknown option $1" >&2
		exit 1
		;;

esac
EOF

fi
}


usage(){
echo "Usage: ${PROGRAM} [-d] [-e] [-b <split block>] <directory path>"
echo "-d 还原备份."
echo "-e 使用 aes.py 加密文件."
echo "-b 使用 split 切片块大小, 例：256M  512M 1G 5G"
echo
}


trap "error_exit_clear" SIGTERM SIGINT ERR

trap "clear_tmp" EXIT

SPLIT=0
ENCRYPTO=0
RESTORE=0
while getopts "b:edh" args
do
	case $args in
		b)
			SPLIT=1
			SPLIT_BLOCK="$OPTARG"
			;;
		e)
			ENCRYPTO=1
			;;
		d)
			RESTORE=1
			;;
		h)
			usage
			exit 0
			;;
		\:)
			echo "-${OPTARG} 需要一个参数"
			exit 1
			;;
		\?)
			echo "未知选项"
			exit 1
			;;

	esac
done

shift $[ OPTIND - 1 ]


if [ -d "$1" ] && [ -w "$1" ];then
	:
else
	usage
	echo
	echo "or error exit $1 exists"
	exit 1
fi

backup_filename_or_dirname

T=${1%/}

out_file="${T}/${BACKUP_NAME}".tar.zst

out_dir="${T}/${BACKUP_NAME}"

out_filename="${out_dir##*/}".tar.zst

# 如果加密，就别上后缀
if [ $ENCRYPTO = 1 ];then

	out_file="${T}/${BACKUP_NAME}".tar.zst.aes

	out_dir="${T}/${BACKUP_NAME}"

	out_filename="${out_dir##*/}".tar.zst.aes

fi


if [ $(id -u) -ne 0 ];then
	echo need root user
	exit 1
fi

if [ $SPLIT = 1 ];then
	mk_file
fi


# 生成 tar use-compress-program sh
compress_program_and_suffix

# main process

sys_excludes='--exclude=proc/* --exclude=sys/* --exclude=run/* --exclude=tmp/* --exclude=dev/* --exclude=var/log/* --exclude=snap/*'
#sys_excludes='./proc/* ./sys/* ./run/* ./tmp/* ./dev/*'

user_excludes='--exclude=home/* --exclude=mnt/* --exclude=media/*'
#user_excludes='./home/* ./mnt/* ./media/*'

excludes="$sys_excludes $user_excludes"


if [ $SPLIT = 0 ];then
	time { tar -C / --acls -pc ${excludes} -I "$TAR_USE" . |show_speed |tee $out_file | sha256sum > ${out_file}.${SHA_SUFFIX}; }
elif [ $SPLIT = 1 ];then
	tar -C / --acls -pc ${excludes} -I "$TAR_USE" . |show_speed |tee $FIFO |split -b "${SPLIT_BLOCK}" - "${out_dir}/${out_filename}." &
	TAR_PID=$!
	time { SHA256=$(sha256sum $FIFO); }
	echo "${SHA256::64} ${out_filename}" > "${out_dir}/${out_filename}.${SHA_SUFFIX}"
fi

# 之前的这么: 恢复 pixz < *.tar.xz | tar -vx -C /tmp/<***>
