#!/bin/bash
#
# adjustment display brightness for intel_backlight
# 

case "$1" in
	-h|--help)
	echo "adjustment display brightness for intel_backlight"
	echo
	echo "Usaing: $(basename $0)"
	echo
	echo "'k' or 'u' up adjustment 'j' or ' 'd' down adjustemnt"
	echo "'q' quit"
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

dd if=$TTY bs=1 count=1 2> /dev/null

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


echo "current brightness: $bri_var"

while :
do
	
	ch=$(getch)
	if [ "$ch"x == "j"x -o "$ch"x == "d"x ];then
		bri_var=$[bri_var - step]
		bri_var=$(check_overflow $bri_var)
		ch_bri $bri_var
		echo "current brightness: $bri_var"
	elif [ "$ch"x == "k"x -o "$ch"x == "u"x ];then
		bri_var=$[bri_var + step]
		bri_var=$(check_overflow $bri_var)
		ch_bri $bri_var
		echo "current brightness: $bri_var"
	elif [ "$ch"x == "q"x ];then
		echo 'exit...'
		break
	fi
done
