#!/bin/bash
# date 2020-11-27 19:35:12
# author calllivecn <c-all@qq.com>

#  cpu使用率：
#  proc文件：/proc/stat
#  字段解释：只看行首以cpu开头的行，每列字段含义为：
#  name 设备名
#  user 从系统启动开始累计到当前时刻，处于用户态的运行时间，不包含 nice值为负进程。
#  nice 从系统启动开始累计到当前时刻，nice值为负的进程所占用的CPU时间。
#  system 从系统启动开始累计到当前时刻，处于核心态的运行时间。
#  idle 从系统启动开始累计到当前时刻，除IO等待时间以外的其它等待时间。
#  iowait 从系统启动开始累计到当前时刻，IO等待时间。
#  irq 从系统启动开始累计到当前时刻，硬中断时间。
#  softirq 从系统启动开始累计到当前时刻，软中断时间。
#  stealstolen 从系统启动开始累积到当前时刻，在虚拟环境运行时花费在其他操作系统的时间。
#  guest 从系统启动开始累积到当前时刻，在Linux内核控制下的操作系统虚拟cpu花费的时间。
#  guest_nice 从系统启动开始累积到当前时刻，在Linux内核控制下的操作系统虚拟cpu花费在nice进程上的时间。
#  cpu每核时间：
#  第一行name为cpu，描述的是总的cpu时间分配。
#  cpu[0 1 2 3 ...]，指的是cpu单核的时间分配。
#  单位：jiffies
#  jiffies 是内核中的一个全局变量，用来记录系统启动以来产生的节拍数，在 Linux 中，一个节拍大致可以理解为操作系统进程调度的最小时间片，不同的 Linux 系统内核这个值可能不同，通常在 1ms 到 10ms 之间。
#  
#  计算方式：
#  cpu总时间 = user + nice + system + idle + iowait + irq + softirq + stealstolen + guest + guest_nice
#  cpu使用率计算
#  1. 请在一段时间内（推荐：必须大于0s，小于等于1s），获取两次cpu时间分配信息。
#  2. 计算两次的cpu总时间：total_2 - total_1
#  3. 计算两次的cpu剩余时间：idle_2 - idle_1
#  4. 计算两次的cpu使用时间：used = (total_2 - total_1) - (idle_2 - idle_1)
#  5. cpu使用率 = 使用时间 / 总时间 * 100% = used / total * 100%


CPUINFO="/proc/cpuinfo"

STAT="/proc/stat"

cpu_count(){
    grep "cpu MHz" $CPUINFO | wc -l
}

CPUs=$(cpu_count)

row_sum(){
head -n $[CPUs + 1] $STAT | awk '
{
    for(i=2; i<NF; i++){
        total+=$i;
    }

    idle+=$5;
    print total"_"idle;
}'
}

# 初始化一次 cpu 各个部分的使用时间
last_data=()
c=0
for numbers in $(row_sum)
do
    last_data[$c]="$numbers"
    c=$[c+1]
done

sleep 0.01

loop(){
sleep 0.01
c=0
for numbers in $(row_sum)
do
    total_now=$(echo $numbers|cut -d'_' -f1)
    idle_now=$(echo $numbers|cut -d'_' -f2)

    last_total=$(echo ${last_data[$c]}|cut -d'_' -f1)
    last_idle=$(echo ${last_data[$c]}|cut -d'_' -f2)

    last_data[$c]="${total_now}_${idle_now}"
    # (total - last_total) - (idel - last_idle)
    total=$[total_now - last_total]
    used=$[total - idle_now + last_idle]

    # echo "debug: used=$used total=$total"
    usage_rate=$[used * 100 / total]
    # awk '{print $1/$2*100}')

    if [ $c -eq 0 ];then
        echo "CPU 总使用率: ${usage_rate}%"
    else
        p=$[c-1]
        echo "CPU$p 使用率: ${usage_rate}%"
    fi

    c=$[c+1]
done
}

while :
do
    # echo "输出一下 ${last_data[@]}"
    echo -en '\033c'
    loop
    sleep 0.99
done