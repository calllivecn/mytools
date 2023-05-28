#!/bin/bash
# update 2018-04-28 23:29:32
# update 2022-08-18 09:24:24
# author calllivecn <c-all@qq.com>


set -e
MK_FILE=0
mk_file(){

	MK_FILE=1

	FIFO=$(mktemp -u)
	mkfifo $FIFO

	TAR_USE=$(mktemp --suffix=.sh)
	chmod u+x "$TAR_USE"

	if [ $SPLIT = 1 ];then
		mkdir "${out_dir}"
	fi
}

PROGRAM="${0##*/}"

SHA_SUFFIX="sha256"

HOSTNAME=$(hostname)
DATETIME=$(date +%F-%H-%M-%S)

# global varible
AES_PATH=

clear_tmp(){
	if [ $MK_FILE = 1 ];then
		rm $FIFO
		rm $TAR_USE
	fi
}

TRAP=0
error_exit_clear(){

	if [ $TRAP = 1 ];then
		return
	fi

	if [ $SPLIT = 0 ];then

		rm "$out_file"
		#rm "${out_file}.${SHA_SUFFIX}"

	elif [ $SPLIT = 1 ];then

		kill $TAR_PID
		rm -r "${out_dir}"
	fi

	TRAP=1
}

LOGLEVEL=info
debug(){
	if [ $LOGLEVEL = "debug" ];then
		echo "$1" >&2
	fi
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
	
	debug "使用这个备份名字: $BACKUP_NAME"
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
	if type -p zstd 2>&1 > /dev/null;then
		:
	else
		echo "需要 apt install zstd"
		exit 1
	fi 
}

# ase.py -- 2022-06-02 改为备用，优先使用 crypto.py
AES_PY="aes.py"
CRYPTO_PY="crypto.py"
aes_type(){
	if type -p ${CRYPTO_PY} 2>&1 > /dev/null;then
		AES_PATH="${CRYPTO_PY}"

	elif type -p aes.py 2>&1 > /dev/null;then
		AES_PATH="${AES_PY}"
	else
		echo "需要 ${CRYPTO_PY} 下载地址 https://github.com/calllivecn/mytools/${CRYPTO_PY}"
		echo "使用 --aes-path /path/to/${CRYPTO_PY} 指定."
		exit 1
	fi
	debug "aes_type() --> AES_PATH: ${AES_PATH}"
}


check_aes_password(){
	if [ "${AES_PATH}"x = x ];then
		echo "${AES_PATH} 没有找到，可以 --aes-path /path/to/${AES_PATH} 指定." >&2
		exit 1
	fi
	local p1 p2
	read -s -p "password: " p1
	echo
	read -s -p "password(again): " p2
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

usage(){
echo "Usage: ${PROGRAM} [-r] [-e] [-b <split block>] <directory path>"
echo "-r, --restore                  还原备份.(还未实现)"
echo "-e, --encrypt                  使用 ${CRYPTO_PY} or ${AES_PY} 加密文件."
echo "-b, --split-block              使用 split 切片块大小, 例：256M  512M 1G 5G"
#echo "--zstd                        选择压缩方式： zstd. 默认：zstd"
#echo "--gzip                        选择压缩方式： gzip"
#echo "--bzip                        选择压缩方式： bzip2" 
#echo "--xz                          选择压缩方式： xz"
echo "--aes-path                     ${AES_PATH} 如果不在PATH里, 可以使用这个选项指定。"
#echo "--aes-password                非交互式输入密码。"
echo "--aes-prompt                   ${AES_PATH}的提示。"
echo "--debug                        debug."
echo
}


trap "error_exit_clear" SIGTERM SIGINT ERR

trap "clear_tmp" EXIT


param(){
	if [ "${2}"x = x ] || [ ${2::1} = "-" ] || [ ${2::2} = "--" ];then
		echo "${1} 选项需要参数。"
		exit 1
	fi
}

SPLIT=0
RESTORE=0
ENCRYPT=0
AES_CMD=
AES_PASSWORD=
COMP_CMD="zstd -T0 -7 -c"
COMP_SUFFIX="zst"

argc=0
ARGS=()
while :
do
	case "$1" in
		# 如果后面的选项，依赖这个选项，那这选项就是有解析顺序的了。
		# 放前面。
		-r|--rstore)
			RESTORE=1
			echo "还原功能还未实现。"
			echo "可以手动恢复。"
			exit 0
			;;

		-b|--split-block)
			param "$1" "$2"
			SPLIT=1
			SPLIT_BLOCK="$2"
			shift
			;;

		#--zstd)
		#	if [ $RESTORE = 0 ];then
		#		COMP="pzstd"
		#	else
		#		COMP="pzstd -13 -c"
		#	fi
		#	COMP_SUFFIX="zst"
		#	;;
		#--gzip)
		#	COMP="gzip"
		#	if [ $RESTORE = 0 ];then
		#		COMP=""
		#	else
		#		COMP="pzstd -13 -c"
		#	fi
		#	COMP_SUFFIX="gz"
		#	;;
		#--xz)
		#	COMP="xz"
		#	COMP_SUFFIX="xz"
		#	;;
		#--bzip2)
		#	COMP="bzip2"
		#	COMP_SUFFIX="bz2"
		#	;;
		
		-e|--encrypt)
			ENCRYPT=1
			aes_type
			;;

		--aes-path)
			param "$1" "$2"
			if [ -x ${1} ];then
				AES_PATH="$2"
			else
				echo "加密文件 ${2} 不存在或者是不可执行文件。"
				exit 1
			fi
			shift
			;;

		--aes-prompt)
			param "$1" "$2"
			AES_PROMPT="$2"
			shift
			;;

		#--aes-password)
		#	param "$1" "$2"
		#	AES_PASSWORD="$2"
		#	shift
		#	;;

		-h|--help)
			usage
			exit 0
			;;
		--debug)
			LOGLEVEL="debug"
			;;
		--)
			break
			;;

		*)
			#echo "添加到位置参数。"
			ARGS[$argc]="$1"
			argc=$[argc + 1]
			;;
	esac
	shift
	if [ $# -eq 0 ];then
		break
	fi
done
set -- "${ARGS[@]}"
unset ARGS argc


T=${1%/}
if [ "$T"x = ""x ];then
	echo "备份路径是必须的。${PROGRAM} </path/dir/>"
	exit 1
fi

if [ -d "$T" ] && [ -w "$T" ];then
	:
else
	usage
	echo
	echo "Or error exit $T exists"
	exit 1
fi

backup_filename_or_dirname

if [ $ENCRYPT = 1 ];then

	AES_CMD="${AES_PATH}"

	if [ "${AES_PROMPT}"x != x ];then
		AES_CMD="${AES_CMD} -p ""${AES_PROMPT}"	
	fi

	check_aes_password
fi

out_file="${T}/${BACKUP_NAME}".tz

out_dir="${T}/${BACKUP_NAME}"

out_filename="${out_dir##*/}".tz

# 如果加密，就加上后缀
if [ $ENCRYPT = 1 ];then

	out_file="${T}/${BACKUP_NAME}".tza

	out_dir="${T}/${BACKUP_NAME}"

	out_filename="${out_dir##*/}".tza

fi


if [ $EUID -ne 0 ];then
	echo need root user
	exit 1
fi


mk_file

#################
# main process
#################

#sys_excludes='./proc/* ./sys/* ./run/* ./tmp/* ./dev/*'
sys_excludes='--exclude=proc/* --exclude=sys/* --exclude=run/* --exclude=tmp/* --exclude=dev/* --exclude=var/log/* --exclude=snap/*'

#user_excludes='./home/* ./mnt/* ./media/*'
user_excludes='--exclude=home/* --exclude=mnt/* --exclude=media/*'

# 添加 /var/log/journal/
var_log_journal='--exclude=var/log/journal/* --add-file=var/log/journal/'

excludes="$var_log_journal $sys_excludes $user_excludes"

# 一个段一个段的添加 成指令(未开发完成)
BACKUP_CMD="tar -C / --format=posix --acls --selinux --xattrs -pc ${excludes} . 2>/dev/null "

# test
#BACKUP_CMD="tar -C /home/zx/work/ --format=posix --acls --selinux --xattrs -pc ${excludes} . 2>/dev/null "


# 添加压缩方式
BACKUP_CMD="$BACKUP_CMD""| ${COMP_CMD} "

# 添加加密码
if [ $ENCRYPT = 1 ];then
	BACKUP_CMD="$BACKUP_CMD""| ${AES_CMD} -k ${AES_PASSWORD}"
fi

# 添加 show speed
if type -p pv 2>&1 >/dev/null;then
	BACKUP_CMD="$BACKUP_CMD""| pv -ab "
else
	echo "如果要查看进度条， 可以安装 pv 工具" >&2
fi


if [ $SPLIT = 0 ];then
	#tar -C / --acls -pc ${excludes} -I "$TAR_USE" . 2>/dev/null |show_speed |tee $out_file > $FIFO &
	debug "$BACKUP_CMD | tee $out_file > $FIFO &"
	eval $BACKUP_CMD | tee $out_file > $FIFO &
	TAR_PID=$!
	time { SHA256="$(sha256sum $FIFO)"; }
	echo "${SHA256::64} ${out_file}" > "${out_file}.${SHA_SUFFIX}"

elif [ $SPLIT = 1 ];then

	#tar -C / --acls -pc ${excludes} -I "$TAR_USE" . 2>/dev/null |show_speed |tee $FIFO |split -b "${SPLIT_BLOCK}" - "${out_dir}/${out_filename}." &
	debug "$BACKUP_CMD |tee $FIFO |split -b "${SPLIT_BLOCK}" - "${out_dir}/${out_filename}." &"
	eval $BACKUP_CMD |tee $FIFO |split -b "${SPLIT_BLOCK}" - "${out_dir}/${out_filename}." &
	TAR_PID=$!
	time { SHA256="$(sha256sum $FIFO)"; }
	echo "${SHA256::64} ${out_filename}" > "${out_dir}/${out_filename}.${SHA_SUFFIX}"

fi

# 之前的这么: 恢复 pixz < *.tar.xz | tar -vx -C /tmp/<***>
