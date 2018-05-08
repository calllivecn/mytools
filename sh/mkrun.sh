#!/bin/bash

if [ ! -f "$1" -o -f "$2" ];then
	echo "using: $0 file"
	exit -1
fi


tar_package="$1"

run_file="$2"

shell=$(mktemp)

trap "rm $shell" EXIT

file_size=$(du -b "$tar_package" |awk '{print $1}' )

file_md5sum=$(md5sum "$tar_package" |awk '{print $1}' )

shell_text='IyEvYmluL2Jhc2gKCnRtcF9maWxlPSQobWt0ZW1wKQoKc2l6ZT1maWxlX3NpemUKCm1kNXN1bT1maWxlX21kNXN1bQoKaWYgWyAtbiAiJDEiIF07dGhlbgogICAgICAgIG91dF9wYXRoPSIkMSIKZWxzZQogICAgICAgIG91dF9wYXRoPSIuLyIKZmkKCnRhaWwgLWMgJHNpemUgJDAgPiAkdG1wX2ZpbGUKCm1kNT0kKG1kNXN1bSAkdG1wX2ZpbGUgfGF3ayAne3ByaW50ICQxfScpCgppZiBbICIkbWQ1InggPT0gIiRtZDVzdW0ieCBdO3RoZW4KICAgICAgICB0YXIgLXhmICR0bXBfZmlsZSAtQyAiJG91dF9wYXRoIgplbHNlCiAgICAgICAgZWNobyBmaWxlIG1kNXN1bSBlcnJvci4KICAgICAgICBleGl0IC0xMjcKZmkKZXhpdCAwCiMtLS0tLS0tLS0tLS0K'

echo -n ${shell_text} | base64 -w 0 -d > $shell

sed -i -e "s/file_size/${file_size}/" -e "s/file_md5sum/${file_md5sum}/" $shell

cat "$shell" "$tar_package" > "$run_file"
