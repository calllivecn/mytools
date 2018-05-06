#!/bin/bash
# date 2018-05-07 04:04:48
# author calllivecn <c-all@qq.com>

set -e

###########
#
# 1. 创建证书和私钥 
# 第一步是创建一个证书/私有RSA密钥对，稍后将用于对内核模块进行签名。
# 请注意由于私钥用于签署模块，病毒和恶意软件可能会使用私钥对模块进行签名并危及操作系统。要确保私钥安全。
# 使用openssl命令，创建一个私钥和DER编码的证书。
# 记住将公用名称（CN）字段（YOUR_NAME）设置为对访客有意义的文字。
# 此例中我们使用kvaser.com作为公用名称。
#
############

YOUR_NAME='calllivecn'

MOD_DER=module-sign.der
MOD_PRIV=module-sign.priv

mk_sert(){
openssl req -new -x509 -newkey rsa:2048 -keyout $MOD_DER -outform DER -out $MOD_DER -nodes -days 36500 -subj "/CN=$YOUR_NAME/"
}

##########
#
# 2. 将公钥导入并注册到系统
# 下一步使用mokutil4命令导入公钥，让其可以被系统信任。这个过程需要两步，
# 其中首先导入密钥，然后在下次启动机器时必须进行注册。
# 简单的密码即可，因为只是临时使用。
#
#########

import_key(){
sudo mokutil --import $MOD_DER
}


# 我们现在可以验证是否已导入正确的证书。 在这里我们也注意到上面使用的公用名称（CN）是kvaser.com。
show_key(){
sudo mokutil --list-new
}

# 现在重新启动机器。引导加载程序启动时，MOK管理器EFI实用程序应自动启动。
# 在我的机器屏幕上出现浅蓝色背景的白色文字，提示要“点击任意键执行MOK管理”和“10秒后启动”
# 5 YMMV。选择“注册MOK”，选择密钥，并注册密钥。在上述导入步骤中我们会被要求输入设置密码。
# 完成注册步骤，然后继续启动。Linux内核将记录加载的密钥，我们可以使用dmesg命令查看我们自己的密钥。



# 我们现在还可以使用mokutil命令测试我们的证书是否已注册。
mok_key_test(){
sudo mokutil --test-key $MOD_DER
}

########################################
#
# 构建，签名和安装模块
#
#########################################

sign_vbox(){

local kernel_version=$(uname -r)

for f in $(dirname $(modinfo -n vboxdrv))/vbox*.ko
do
	echo "signatrue ${f}"
	sudo /lib/modules/${kernel_version}/build/scripts/sign-file sha256 $MOD_PRIV $MOD_DER ${f}
done

}

sign_vbox
