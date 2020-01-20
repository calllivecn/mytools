#!/bin/bash -x
# date 2018-07-18 15:08:07
# author calllivecn <c-all@qq.com>

C=cn
ST=hubei
O=calllive
OU=calllive.cc
CN=localhost

##########################
#
# define functions begin
#
##########################

make_extfile(){	

echo '[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1=*.cc
DNS.2=*.calllive.cc
DNS.3=localhost
DNS.4=127.0.0.1' > "$1"

}


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

# 一步完成。
# 同时生成 RSA私钥和自签名证书, CA:True, x509v3
keySelfCA(){
	local ca_key="$1" ca_crt="$2"
	openssl req  -newkey rsa:2048 -x509 -nodes -keyout "$ca_key" -days 5000 -out "$ca_crt" #\
	#-subj "/C=$C/ST=$ST/O=$O/OU=$OU/CN=$CN"
}


# 二步完成。
# x509v3， CA:True , 
keyRootCA(){
	openssl genrsa -out ca.key 2048

	openssl req -new -x509 -key ca.key -days 3650 -in ca.key -out ca.crt
}



# 一步，生成csr。
# 此后输入密码、server证书信息完成，也可以命令行指定各类参数
gen2csr(){
	openssl req -newkey rsa:2048 -nodes -keyout server.key -out server.csr
}

# 二步，生成csr
# 使用已有私钥生成自签名证书
keySelfSginCrt(){
	openssl genrsa -out server.key 2048
	openssl req -new -key server.key -out server.csr
}

# *** 此时生成的 csr 签名请求文件可提交至 CA进行签发 ***


# 使用 CA 证书及CA密钥 对请求签发证书进行签发，生成 x509v1证书
CA2crt_x509v1(){
	openssl x509 -req -CA ca.crt -CAkey ca.key -CAcreateserial -days 3650 -in server.csr -out server.crt
}

# 生成 x509v3 证书, 多域名版。
CA2crt_x509(){
	local EXT_FILE_CNF=$(mktemp)

	make_extfile "$EXT_FILE_CNF"

	openssl x509 -req -CA ca.crt -CAkey ca.key -CAcreateserial -extfile "$EXT_FILE_CNF" -extensions v3_req -days 365 -in server.csr -out server.crt
	# -extensions section：我们知道一般我们都用X509格式的证书，X509也有几个版本的。如果你在这个选项后面带的那个参数在config文件里有同样名称的key，那么就颁发X509V3证书，否则颁发X509v1证书。

	rm -f "$EXT_FILE_CNF"
}


using(){
	echo "Uasge: ${0##*/} -c certificate.crt -k certificate.key"
}


while getopts ":hc:k:" opt
do
	case "$opt" in
		h)
			using
			exit 0
			;;
		c)
			cert="$OPTARG"
			;;
		k)
			key="$OPTARG"
			;;
		?)
			echo "Error option."
			using
			exit 0
			;;
	esac
done

shift $OPTIND

keySelfCA "$key" "$cert"
echo "$cert $key"
#keyRootCA
