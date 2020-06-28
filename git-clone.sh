#!/bin/bash 
# date 2020-06-28 10:39:54
# author calllivecn <c-all@qq.com>

set -e

PROGRAM=${0##*/}

USAGE="\
Usage: $PROGRAM <github username> <repository>
"

if [ -z "$1" ] || [ -z "$2" ];then
	echo "$USAGE"
	exit 1
fi

GITUSER="$1"

REPO="$2"

BRANCH="$3"

if [ -n "$BRANCH" ];then
	git clone -b "$BRANCH" "https://github.com.cnpmjs.org/${GITUSER}/${REPO}.git"
else
	git clone "https://github.com.cnpmjs.org/${GITUSER}/${REPO}.git"
fi

cd "${REPO}"

git remote set-url origin "https://github.com/${GITUSER}/${REPO}.git"

