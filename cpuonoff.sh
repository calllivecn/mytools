#!/bin/bash
# date 2018-05-22 02:20:50
# author calllivecn <calllivecn@outlook.com>


CPU_PREFIX='/sys/devices/system/cpu/cpu'
CPU_SUFFIX='online'

CPUn=0
for c in "${CPU_PREFIX}"[0-9]*;
do
	CPUn=$[CPUn+1]
done
unset c

# choice:{nmu,range}
CHECK_NMU=''

check_cpun(){

	local tmp
	
	#nmu=$(echo "$1" |sed -r -e 's/^,+//g' -e 's/,+/,/g' -e 's/$,+//g' )
	
	if echo "$1" |grep -qE '^[0-9]+\-[0-9]+$';then
	
		CHECK_result_1=$(echo "$1" |cut -d'-' -f 1)
		CHECK_result_2=$(echo "$1" |cut -d'-' -f 2)
	
		if [ $CHECK_result_1 -lt 0 ] || [ $CHECK_result_1 -gt $CPUn ];then
			echo "$1 : should be 0-$CPUn"
			exit 2
		elif [ $CHECK_result_2 -lt 0 ] || [ $CHECK_result_2 -gt $CPUn ];then
			echo "$1 : should be 0-$CPUn"
			exit 2
		fi
	
		if [ $CHECK_result_1 -gt $CHECK_result_2 ];then
			tmp=$CHECK_result_1
			CHECK_result_1=$CHECK_result_2
			CHECK_result_2=$tmp
		fi
	
		CHECK_NMU=range
	
	elif echo "$1" |grep -qE '^[0-9]+(,[0-9]+)*$';then
	
		CHECK_result=$(echo "$1" |tr ',' '\n' |sort -n |uniq)
		for tmp in $CHECK_result;
		do
			if [ $tmp -lt 0 ] || [ $tmp -gt $CPUn ];then
				echo "$1 : should be 0-$CPUn"
				exit 2
			fi
		done
	
		CHECK_NMU=nmu
	
	else
		return 1
	fi
}

example(){
	EXA="Example: 
	${0##*/} -n 2,3,4
	or
	${0##*/} -f 2-4"
	echo $EXA
	exit 2
}

cpu_core_info(){
	local i state
	
	echo "CPUs: ${CPUn}"
	echo "CPU0 always on"
	for i in $(seq 1 $[CPUn - 1]);
	do
		state=$(cat "${CPU_PREFIX}${i}/${CPU_SUFFIX}")
		if [ "$state"x = "1"x ];then
			echo "CPU${i} on"
		elif [ "$state"x = "0"x ];then
			echo "CPU${i} off"
		else
			echo "CPU${i} unknown state"
		fi
	done
}

cpu_on(){

	local i
	
	check_cpun "$1"
	
	if [ "$CHECK_NMU"x = "nmu"x ];then
		for i in $CHECK_result;
		do
			if [ -f ${CPU_PREFIX}${i}/${CPU_SUFFIX} ];then
				echo 1 > ${CPU_PREFIX}${i}/${CPU_SUFFIX}
			else
				echo "not found: ${CPU_PREFIX}${i}/${CPU_SUFFIX}"
			fi
		done
	elif [ "$CHECK_NMU"x = "range"x ];then
		for i in $(seq ${CHECK_result_1} ${CHECK_result_2})
		do
			if [ -f ${CPU_PREFIX}${i}/${CPU_SUFFIX} ];then
				echo 1 > ${CPU_PREFIX}${i}/${CPU_SUFFIX}
			else
				echo "not found: ${CPU_PREFIX}${i}/${CPU_SUFFIX}"
			fi
		done
	else
		example
	fi
	
	cpu_core_info

}

cpu_off(){

	local i
	check_cpun "$1"
	
	if [ "$CHECK_NMU"x = "nmu"x ];then
		for i in $CHECK_result;
		do
			if [ -f ${CPU_PREFIX}${i}/${CPU_SUFFIX} ];then
				echo 0 > ${CPU_PREFIX}${i}/${CPU_SUFFIX}
			else
				echo "not found: ${CPU_PREFIX}${i}/${CPU_SUFFIX}"
			fi
		done
	elif [ "$CHECK_NMU"x = "range"x ];then
		for i in $(seq ${CHECK_result_1} ${CHECK_result_2})
		do
			if [ -f ${CPU_PREFIX}${i}/${CPU_SUFFIX} ];then
				echo 0 > ${CPU_PREFIX}${i}/${CPU_SUFFIX}
			else
				echo "not found: ${CPU_PREFIX}${i}/${CPU_SUFFIX}"
			fi
		done
	else
		example
	fi
	
	cpu_core_info

}

usage(){

	USING="Usage: ${0##*/}
	
	Usage: ${0##*/} [-h] [-nf <CPUn>]
	
	-n		on core nmuber.
	-f		off cpu core nmber.
	-h		help
	"
	echo "$USING"
	example
	exit 0
}


####################
# main()
###################

if [ $# -eq 0 ];then
	cpu_core_info
fi

while getopts ":hn:f:" args;
do
	case "$args" in
		n)
			#echo cpu_on "$OPTARG"
			cpu_on "$OPTARG"
			;;
		f)
			#echo cpu_off "$OPTARG"
			cpu_off "$OPTARG"
			;;
		h)
			usage
			;;
		\:)
			echo "-${OPTARG} need a parameter!"
			example
			exit 2
			;;
		\?)
			echo "Unknown parameter."
			exit 2
	esac
done

shift $[OPTIND - 1]

