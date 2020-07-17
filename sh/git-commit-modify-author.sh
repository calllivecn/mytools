#!/bin/bash
# date 2020-04-30 17:40:01
# author calllivecn <c-all@qq.com>

export FILTER_BRANCH_SQUELCH_WARNING=1

git filter-branch --env-filter '
OLD_NAME="your old name"
OLD_EMAIL="your ola email"

NEW_NAME="your name"
NEW_EMAIL="your email"

if [ "$GIT_COMMITTER_NAME" = "$OLD_NAME" ] && [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ];then
	echo "找到目标， 进行替换"
    export GIT_AUTHOR_NAME="$NEW_NAME"
    export GIT_AUTHOR_EMAIL="$NEW_EMAIL"
else
	echo "没有找到目标， 不进行替换"
fi
' --tag-name-filter cat -- --branches --tags
