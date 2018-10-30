#!/bin/bash
# date 2018-10-29 17:35:20
# author calllivecn <c-all@qq.com>


for snapclean in $(snap list --all |awk '$6~/disable/{print $3"#"$1}')
do
	sudo snap remove --revision $(echo "$snapclaen" |tr '#' ' ')
done
