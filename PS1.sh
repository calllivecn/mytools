#!/bin/bash
# date 2018-11-30 10:15:40
# author calllivecn <calllivecn@outlook.com>


ps1(){
	local ok_recode='☺ ' err_recode='☹ ' prompt='☘ '
	if [ $1 -eq 0 ];then
		recode="$ok_recode"
	else
		recode="$err_recode"
	fi
	
	echo "$recode"
}

PS1='$(ps1 $?)-\u@\h:\W☘ '
