#!/bin/bash
# date 2019-10-14 10:13:40
# author calllivecn <c-all@qq.com>


PROGRAM=${0##*/}

usage(){

	echo "Usage: $PROGRAM [目录]"
	echo "默认执行：${PROGRAM} $HOME/git-backup"
	echo "$HOM/git-backup 放入在备份的仓库"
}



case "$1" in
	-h|--help)
		usage
		exit 0
		;;
esac

if [ -n "$1" ];then
	GIT="$1"
else
	GIT="$HOME/git-backup"
	echo "创建 $GIT"
fi



if [ -d "$GIT" ];then
	:
else
	echo "$GIT 不存在，请创建 $GIT"
	echo "并将要备份的仓库放入${GIT}目录"
	exit 1
fi

for gitdir in $(echo "$GIT/*");
do
	if [ -d "$gitdir/.git" ];then
		pushd "$gitdir"
		git fetch 
		popd
	fi
done

