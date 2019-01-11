
getdatetime(){
	date +%Y%m%d%H%M%S
}

# 和 start=$(date +%s) end=$(date +%s)
# 配合使用
#
s_to_date(){
	local tmp s="$1" H=3600 M=60 D=86400 h m d 
	d=$[$s / $D]
	s=$[$s % $D]
	h=$[$s / $H]
	s=$[$s % $H]
	m=$[$s / $M]
	s=$[$s % $M]
	echo "$d-$h:$m:$s"
}

getch(){

local TTY

TTY=$(tty)

stty -icanon -echo

dd if=$TTY bs=8 count=1 2> /dev/null

stty icanon echo

}

selector(){

	local SELECT=$1

	array_len=${#SELECT[@]}
	
	ps3=$PS3
	
	PS3='input number : '
	
	select var in "${SELECT[@]:1:${array_len}}"
	do
	#PS3=$ps3
		case "$var" in
			${SELECT[1]})
				echo your ${SELECT[1]}
				;;
			${SELECT[2]})
				echo your ${SELECT[2]}
				;;
			${SELECT[3]})
				echo your ${SELECT[3]}
				;;
			${SELECT[4]})
				echo exit
				break
				;;
		esac
	
	done
}

