#!/bin/bash
# date 2018-10-29 17:35:20
# author calllivecn <calllivecn@outlook.com>


for snapclean in $(snap list --all |awk '$6~/disable|已禁用/{print $3"#"$1}')
do
	sudo snap remove --revision $(echo "$snapclean" |tr '#' ' ')
done
