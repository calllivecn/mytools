# mytools 一些小工具和bash、py函数

### randpw.py:
* 生成高强度的随机密码
* tr -cd ' -~' < /dev/urandom |head -c 16;生成随机密码的命令
* tr -cd ' -~' < /dev/urandom |tr -d " \"\'\`" |head -c 16;排除一些特殊符号。

### randpw-v2.py:
* 生成符合MySQL MEDIUM 密码强度的随机密码

### cpuonoff.sh:
* 开启或关闭CPU core来省电(几次测试，貌似并不会省电。只在x86架构下有效)

### cpumonitor.sh
* CPU使用率监控，shell原理版。

### io.sh:
* 测试硬盘读写速度

### libsh.sh:
* 库

### netio.py:
* linux网速查看工具。

### adjbacklight.py:
* 调整显示器亮度

### adjbacklight-ext.sh(使用ddcutil工具):
* 调整外接显示器亮度

### youtube-dl.sh:
* youtube-dl外壳。

### ztar.py:
* py版tar。

### ssl-crypto.sh:
* 文件加密脚本，openssl 加密文件格式会随着版本发生变化，导致无法解密。(弃用，改用aes.py)

### aes.py or crypto.py:
* 加密小工具

 - aes.py 使用ctypes 链接的openssl、libcrypto.so 库
 - crypto.py 使用的 cryptography 库
 - 兼容的

### hash.py:
* 计算md5,sha1,sha128,sha224,sha256,sha384,sha512,blake2b。

### jsonfmt.py:
* 提取json里的指定字段值，（类拟jq命令)

### srm.py(有对应的命令工具shred):
* 安全删除文件。(好像SSD不需要这玩意儿)

### dos2unix.py:
* 简化版dos2unix。

### ip-query.py:
* 用阿里提供的API。
* 查询ip或域名的运营商、所在国家的地区。
* 还可以直接这么获取(curl https://ip.cn)。

### findcmp.py:
* 通过sha512值检测多个目录下有无相同文件。（升级版）

### smail.py:
* 安全邮件发送。（用法--help)

### wakeonlan.py(支持ipv4,ipv6):
* wake on LAN

### mygzip.py:
* 写个gzip练练手。（用法--help)
