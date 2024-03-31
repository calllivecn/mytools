#!/bin/bash
# date 2018-07-18 15:08:07
# author calllivecn <calllivecn@outlook.com>

#C=cn
#ST=hubei
#O=calllive
#OU=calllive.cc
#CN=localhost

# -newkey ed25519 # 可以其他非对称加密算法
# rsa:2048 or ed25519
NEWKEY="rsa:2048"


##########################
#
# define functions end
#
##########################

####
# openssl x509 选项。
# -signkey filename：使用这个option同时必须提供私有密钥文件。
# 这样把输入的文件变成字签名的证书。如果输入的文件是一个证书，
# 那么它的颁发者会被set成其拥有者.其他相关的项也会被改成符合自签名特征的证书项。
# 如果输入的文件是CSR, 那么就生成自签名文件。
###

# 查看openssl 配置文件
# openssl version -a 
# OPENSSLDIR: "/usr/lib/ssl" 在这里 openssl.conf

# 一步完成。
# 同时生成 RSA私钥和自签名证书, CA:True, x509v3
SelfCA(){
	local ca_crt="$1" ca_key="$2" days="$3"
	openssl req -newkey $NEWKEY -x509 -nodes -keyout "$ca_key" -days "$days" -out "$ca_crt" \
	-subj "/CN=calllivecn CA tool"
}


# 分二步完成。(同上)
# x509v3， CA:True , 
SelfCA2(){
	openssl genrsa -out ca.key 2048
	openssl req -new -x509 -key ca.key -days 3650 -in ca.key -out ca.crt
}



# 一步，生成csr。
# 此后输入密码、server证书信息完成，也可以命令行指定各类参数
generate2csr(){
	local out_csr="$1" out_key="$2"
	openssl req -newkey $NEWKEY -nodes -keyout "$out_key" -out "$out_csr" \
		-subj "/CN=generate CSR"
}

# 分二步，生成csr(同上)
# 使用已有私钥生成自签名证书
keySelfSginCrt(){
	openssl genrsa -out server.key 2048
	openssl req -new -key server.key -out server.csr
}

# *** 此时生成的 csr 签名请求文件可提交至 CA进行签发 ***


# 使用 CA 证书及CA密钥 对请求签发的证书进行签发，生成 x509v1证书
CA2crt_x509v1(){
	openssl x509 -req -CA ca.crt -CAkey ca.key -CAcreateserial -days 3650 -in server.csr -out server.crt
}


parse_subjAltname(){
	local tmpfile="$1" c=1 arg tmp

	for arg in "${ARGS[@]}"
	do
		log "${i}: $arg"

		tmp=(${arg/=/ })

		log "${tmp[0]^^}.${c}=${tmp[1]}"
		echo "${tmp[0]^^}.${c}=${tmp[1]}" >> "$tmpfile"

		c=$[c+1]
	done
}

make_extfile(){	
local tmpfile="$1"

echo '[calllivecn]
subjectAltName = @alt_names

[alt_names]' > "$tmpfile"


# DNS.1=*.cc
# DNS.2=*.calllive.cc
# DNS.3=localhost
# IP.4=127.0.0.1' > "$1"

parse_subjAltname "$tmpfile"
}

# 生成 x509v3 证书, 多域名版。
# -extensions section：我们知道一般我们都用X509格式的证书，X509也有几个版本的。如果你在这个选项后面带的那个参数在-extfile文件里有同样名称的key，那么就颁发X509V3证书，否则颁发X509v1证书。
CA2crt_x509(){

	local ca_crt="$1" ca_key="$2" out_csr="$3" out_crt="$4" days="$5"

	EXT_FILE_CNF=$(mktemp)

	log "$EXT_FILE_CNF"

	make_extfile "$EXT_FILE_CNF"

	openssl x509 -req -CA "$ca_crt" -CAkey "$ca_key" -CAcreateserial -extfile "$EXT_FILE_CNF" -extensions calllivecn -days "$days" -in "$out_csr" -out "$out_crt"

	rm -f "$EXT_FILE_CNF"
}

using(){
	echo "Uasge: ${0##*/} --self-ca|--root-ca [-ca ca.crt] [-cakey ca.key] [-days 365]"

	echo "Uasge: ${0##*/} --generate-crt [-ca <ca.crt> ] [-cakey <ca.key>] [-days 365] [-crt ca.crt] [ -key ca.key] -- dns=example.com dns=*.example.com ip=127.0.0.1 ip=10.0.0.1"
}

DEBUG=0

log(){
	if [ "$DEBUG"x = 1x ];then
		echo "$@"
	fi
}

# EXT_FILE_CNF=$(mktemp)
# exit_clear(){
# 	rm -vf "$EXIT_FILE_CNF"
# }
# 
#trap exit_clear EXIT SIGTERM ERR

CA_CRT="ca.crt"
CA_KEY="ca.key"
DAYS=356
OUT_CRT="server.crt"
OUT_KEY="server.key"

ARGS=()
args_count=0

CMD=SelfCA
main(){
	for opt in "$@"
	do

		log "这是当前参数：$opt"

		case "$opt" in
			--debug)
				shift
				DEBUG=1
				;;
			-h|--help)
				using
				break
				;;
			--self-ca|--root-ca)
				shift
				CMD=SelfCA
				;;
			--generate-crt)
				shift
				CMD=generate_x509_crt
				;;
			-ca)
				shift
				CA_CRT="$1"
				;;
			-cakey)
				shift
				CA_KEY="$1"
				;;
			-days)
				shift
				DAYS="$1"
				;;
			-crt)
				shift
				OUT_CRT="$1"
				;;
			-key)
				shift
				OUT_KEY="$1"
				;;
			--)
				shift
				log "当前剩下: $@"
				for args in "$@"
				do
					ARGS[$args_count]="$1"
					args_count=$[args_count+1]
					shift
				done
				log "args_count: $args_count"

				break
				;;

			-*|--*)
				echo "未知选项: $opt"
				shift
				using
				exit 1
				;;

			*)
				log "逃过的参数: $opt"
				shift
				# 这个是跳过 选项参数值的
				;;
		esac

		#log "解析后的\$1: $1"

	done

	if [ "$CMD"x = "SelfCA"x ] || [ "$CMD"x = x ];then
		$CMD "$CA_CRT" "$CA_KEY" "$DAYS"

	elif [ "$CMD"x = "generate_x509_crt"x ];then
		generate2csr "${OUT_CRT%.crt}.csr" "$OUT_KEY"
		CA2crt_x509 "$CA_CRT" "$CA_KEY" "${OUT_CRT%.crt}.csr" "$OUT_CRT" "$DAYS"
	fi
}

main "$@"

