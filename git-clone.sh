#!/bin/bash 
# date 2020-06-28 10:39:54
# author calllivecn <c-all@qq.com>

set -e

PROGRAM=${0##*/}

USAGE="\
Usage: $PROGRAM <github repository> [branch]
"

if [ -z "$1" ];then
	echo "$USAGE"
	exit 1
fi

GIT="$1"

BRANCH="$2"

eval $(python3 -c "from urllib import parse;p=parse.urlparse(\"$GIT\");print(f'scheme={p.scheme} host={p.netloc} path={p.path}')")

tmp_str=${path%.git}
REPO=$(basename "$tmp_str")

if [ -n "$BRANCH" ];then
	git clone -b "$BRANCH" "https://github.com.cnpmjs.org${path}"
else
	git clone "https://github.com.cnpmjs.org${path}"
fi

cd "${REPO}"

git remote set-url origin "https://github.com${path}"

