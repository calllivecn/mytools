#!/bin/bash
# date 2017-12-12 17:00:24
# author calllivecn <calllivecn@outlook.com>

# install path /etc/NetworkManager/dispatcher.d/pre-up.d/random-mac.sh
# NetworkManager >= 1.4.1 (Ubuntu 17.04+) 可以自动随机改变MAC。
# 最开始的字节 02 代表这个地址是自行指定的。
# 真实 MAC 地址的前三个字节是由制造商决定的，例如 b4:b6:76 就代表 Intel。

LOG_FILE=/var/log/random-mac.log

echo "$(date): $*" >> ${LOG_FILE}
WIFI_UUIDS=$(nmcli --fields type,uuid connection show |grep 802-11-wireless |awk '{print $2}')
for UUID in ${WIFI_UUIDS}
do
    UUID_DAILY_HASH=$(echo "${UUID}-$(date +%F)" | md5sum)
    RANDOM_MAC="02:$(echo -n ${UUID_DAILY_HASH} | sed 's/^\(..\)\(..\)\(..\)\(..\)\(..\).*$/\1:\2:\3:\4:\5/')"
    CMD="nmcli connection modify ${UUID} 802-11-wireless.cloned-mac-address ${RANDOM_MAC}"
    echo "$CMD" >> ${LOG_FILE}
    $CMD &
done
wait 
