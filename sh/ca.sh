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

# 同时生成 RSA私钥和自签名证书, CA:False, x509v3
keySelfCA(){
	openssl req -newkey rsa:2048 -nodes -extensions v3_req -keyout ca.key -x509 -days 5000 -out ca.crt \
	-subj "/C=$C/ST=$ST/O=$O/OU=$OU/CN=$CN"
}


# x509v3， CA:True
keyRootCA(){
	openssl genrsa -out ca.key 2048

	openssl req -new -x509 -key ca.key -days 3650 -in ca.key -out ca.crt
}


# 使用已有私钥生成自签名证书
keySelfSginCrt(){
	openssl req -new -x509 -days 5000 -key rsa_private-1.key -out cert-2.crt
}

# 此后输入密码、server证书信息完成，也可以命令行指定各类参数
key2csr(){
	openssl req -new -key server.key -out server.csr
}



# openssl req -new -key server.key -passin pass:111111 -out server.csr \
# -subj "/C=CN/ST=GD/L=SZ/O=vihoo/OU=dev/CN=vivo.com/emailAddress=yy@vivo.com"
# *** 此时生成的 csr签名请求文件可提交至 CA进行签发 ***


# 使用 CA 证书及CA密钥 对请求签发证书进行签发，生成 x509v1证书
CA2crt_x509v1(){
	openssl x509 -req -CA ca.crt -CAkey ca.key -CAcreateserial -days 3650 -in server.csr -out server.crt
}

# 生成 x509v3 证书
CA2crt_x509v1(){
	local EXT_FILE_CNF=$(mktemp)

	make_extfile "$EXT_FILE_CNF"

	openssl x509 -req -CA ca.crt -CAkey ca.key -CAcreateserial -extfile "$EXT_FILE_CNF" -extensions v3_req -days 365 -in server.csr -out server.crt
	# -extensions section：我们知道一般我们都用X509格式的证书，X509也有几个版本的。如果你在这个选项后面带的那个参数在config文件里有同样名称的key，那么就颁发X509V3证书，否则颁发X509v1证书。

	rm -f "$EXT_FILE_CNF"
}

#keySelfCA
keyRootCA
