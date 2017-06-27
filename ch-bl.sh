#!/bin/bash
#
# adjustment display brightness for intel_backlight
# 

using(){
	echo "'k' or '↑ ' up adjustment 'j' or '↓ ' down adjustemnt"
	echo "'q' or 'ESC' quit"
}

case "$1" in
	-h|--help)
	echo "adjustment display brightness for intel_backlight"
	echo
	echo "Usaing: $(basename $0)"
	echo
	using
	echo
	exit 1
	;;
	*)
	:
	;;
esac


if [ $(id -u) -ne 0 ];then
	echo "need the root user."
	exit 1
fi


SYS_PATH=/sys/class/backlight/intel_backlight/max_brightness

BRI_PATH=/sys/class/backlight/intel_backlight/brightness

MAX_BRI=$(cat $SYS_PATH)

bri_var=$(cat $BRI_PATH)
step=$[(MAX_BRI - 10)/20]


getch(){

TTY=$(tty)

stty -icanon -echo

dd if=$TTY bs=8 count=1 2> /dev/null

stty icanon echo

}

check_overflow(){
local var
var=$1
if [ $var -lt 10 ];then
	var=10
elif [ $var -gt $MAX_BRI ];then
	var=$MAX_BRI
fi
echo $var
}

ch_bri(){
echo $1 > $BRI_PATH
}

using

echo -en "current brightness: $bri_var"

while :
do
	
	ch=$(getch)
	if [ "$ch"x == "j"x -o "$ch"x == "[B"x ];then
		bri_var=$[bri_var - step]
		bri_var=$(check_overflow $bri_var)
		ch_bri $bri_var
		echo -en "\rcurrent brightness:     \b\b\b\b$bri_var"
		#echo -en "\b\b\b\b    \b\b\b\b$bri_var"
	elif [ "$ch"x == "k"x -o "$ch"x == "[A"x ];then
		bri_var=$[bri_var + step]
		bri_var=$(check_overflow $bri_var)
		ch_bri $bri_var
		echo -en "\rcurrent brightness:     \b\b\b\b$bri_var"
		#echo -en "\b\b\b\b    \b\b\b\b$bri_var"
	elif [ "$ch"x == "q"x -o "$ch"x == ""x ];then
		echo  -e '\nexit...'
		break
	fi
done
