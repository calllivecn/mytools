#!/bin/bash -x
# date 2018-07-18 15:08:07
# author calllivecn <c-all@qq.com>

C=zh
ST=hubei
O=calllive
OU=calllive.cc
CN=localhost
EMAIL=c-all@qq.com


# 同时生成 RSA私钥和自签名证书, （root CA）
keySelfCA(){
	openssl req -newkey rsa:2048 -nodes -keyout ca.key -x509 -days 5000 -out ca.crt \
	-subj "/C=$C/ST=$ST/O=$O/OU=$OU/CN=$CN/emailAddress=$EMAIL"
}



# 使用已有私钥生成自签名证书
key2crt(){
	openssl req -new -x509 -days 5000 -key rsa_private-1.key -out cert-2.crt
}

# 使用 RSA私钥生成 CSR 签名请求
KeyRSA(){
	openssl genrsa -aes256 -passout pass:111111 -out server.key 2048
}

# 此后输入密码、server证书信息完成，也可以命令行指定各类参数
key2csr(){
	openssl req -new -key server.key -out server.csr
}



# openssl req -new -key server.key -passin pass:111111 -out server.csr \
# -subj "/C=CN/ST=GD/L=SZ/O=vihoo/OU=dev/CN=vivo.com/emailAddress=yy@vivo.com"
# *** 此时生成的 csr签名请求文件可提交至 CA进行签发 ***


# 使用 CA 证书及CA密钥 对请求签发证书进行签发，生成 x509证书

# openssl x509 -req -days 3650 -in server.csr -CA ca.crt -CAkey ca.key -passin pass:111111 -CAcreateserial -out server.crt



keySelfCA
