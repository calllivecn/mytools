#!/bin/bash

install_lists='adjbacklight.py
cpuonoff.sh
dos2unix.py
findcmp.py
hash.py
io.sh
ip-query.py
libsh.sh
netio.py
randpw.py
srm.py
ztar.py
aes.py
jsonfmt.py
unmount.sh
git-backup.sh
'
HOME_BIN='youtube-dl.sh
'

install_libs='libpy
sh'

if [ "$EUID"x != "0"x ];then
	echo "need root user execoute."
	exit 2
fi

prefix_dir='/usr/local/stow/calllivecn'

bin="$prefix_dir/bin"

mkdir -p "$bin"

for f in $install_lists
do
	install -m755 "$f" "$bin/$f"
done
for d in $install_libs
do
	cp -av "$d" "$bin"
done
