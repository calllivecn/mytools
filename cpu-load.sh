#!/bin/bash
# date 2022-12-12 14:08:18
# author calllivecn <c-all@qq.com>

# 这个是腾,讯-云. 机器在负载过低的时候，会被关机，
# 所以需要在机器没有负载的时候搞点负载,
# 但是在负载高到一个阈值时，需要停止这个负载。
# so... 有了这个脚本

# 可配置： cpulimit 负载阈值 0~100
CPU_THRESHOLD=40


# 变量声明
PIDS=()
CPULIMIT_PID=

STAT="/proc/stat"

run(){
    pv -ab /dev/urandom | gzip -c > /dev/null
}

non(){
    while :
    do
        :
    done
    # pv -ab /dev/urandom > /dev/null
}

CPUs=$(nproc)

# 比较 两个数的大小, 返回 1, 0.
cmp(){
    local op="$1" # 有 lt:< , le: <=, eq: == gt: >, ge: >=

    if [ "$op"x = ltx ];then
        result=$(awk -v arg1=$2 -v arg2=$3 'BEGIN{if(arg1<arg2) {print 1;} else {print 0;}}')

    elif [ "$op"x = lex ];then
        result=$(awk -v arg1=$2 -v arg2=$3 'BEGIN{if(arg1<=arg2) {print 1;} else {print 0;}}')

    elif [ "$op"x = eqx ];then
        result=$(awk -v arg1=$2 -v arg2=$3 'BEGIN{if(arg1==arg2) {print 1;} else {print 0;}}')

    elif [ "$op"x = gtx ];then
        result=$(awk -v arg1=$2 -v arg2=$3 'BEGIN{if(arg1>arg2) {print 1;} else {print 0;}}')

    elif [ "$op"x = gex ];then
        result=$(awk -v arg1=$2 -v arg2=$3 'BEGIN{if(arg1>=arg2) {print 1;} else {print 0;}}')

    fi
    
    return $result
}

cpu_load(){
    awk 'NR==1{
        for(i=2; i<NF; i++){
            total+=$i;
        }
    
        idle+=$5;
        print total,idle;
    }' $STAT
}


# 返回 0~100 cpu 占用率
getcpuload(){

    local load1
    local load2
    load1=($(cpu_load))
    sleep 0.1
    load2=($(cpu_load))

    # 这样不行
    # awk -v total1=${load1[0]} -v idle1=${load1[1]} -v total2=${load2[0]} -v idle2=${load2[1]} 'BEING{
    # total=total2 - total1;
    # idle=idle2 - idle1;
    # used=total - idle;
    # print total,idle,used;
    # printf("%0.f", (used/total*100));
    # }'
    #echo "没结束？"

    echo "${load1[@]} ${load2[@]}" |awk '
    {
    total1=$1;
    idle1=$2;
    total2=$3;
    idle2=$4;
    }
    END{
    total=total2 - total1;
    idle=idle2 - idle1;
    used=total - idle;
    #print "这是先前输出：",total,used,total1,total2,idle1,idle2;
    printf("%0.f", used/total*100);
    }'
}


pause(){
    local non_pid=$1 
    kill -s STOP $CPULIMIT_PID
    kill -s STOP $non_pid
}

recover(){
    local non_pid=$1
    kill -s CONT $CPULIMIT_PID
    kill -s CONT $non_pid
}

safe_exit(){
    local pid
    for pid in ${PIDS[@]}
    do
        kill $pid > /dev/null 2>&1
    done
}

trap safe_exit SIGTERM EXIT

main(){

    non &
    load_pid=$!
    PIDS[0]=$load_pid
    
    renice -n 19 -p $load_pid
    
    cpulimit -f -p $load_pid -l $CPU_THRESHOLD &
    CPULIMIT_PID=$!
    PIDS[1]=$CPULIMIT_PID

    echo "pids: ${PIDS[@]}"

    # 查询cpu 负载
    stat=1
    while :;
    do
        load=$(getcpuload)
        echo "CPU load: $load"
        if [ $load -ge 20 ];then
            if [ $stat == 1 ];then
                pause $load_pid
                echo "Pause CPU load."
                stat=0
            fi
        else
            if [ $stat == 0 ];then
                recover $load_pid
                echo "Recover CPU load."
                stat=1
            fi
        fi

        sleep 5
    done
}

main
