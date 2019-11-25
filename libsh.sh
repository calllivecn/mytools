
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

getmemory(){
	grep -E 'MemTotal: +([0-9]+) kB' /proc/meminfo |grep -oE '[0-9]+'
}

selector(){

	# 中文变量名也行
	
	吃饭(){
		echo "执行: one"
	}
	
	two(){
		echo "执行: two"
	}
	
	three(){
		echo "执行: three"
	}
	
	
	selector(){
	
		local var
	
		select var in ${SELECT[@]}
		do
			"$var"
			return 0
		done
	
	}
	
	
	SELECT=(吃饭 two three)
	
	selector ${SELECT[@]}
}

