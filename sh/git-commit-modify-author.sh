#!/bin/bash
# date 2020-04-30 17:40:01
# update 2024-01-19 11:14:18
# author calllivecn <calllivecn@outlook.com>

export FILTER_BRANCH_SQUELCH_WARNING=1

git filter-branch -f --env-filter '
OLD_NAME=""
OLD_EMAIL=""

NEW_NAME=""
NEW_EMAIL=""

#if [ "$GIT_AUTHOR_EMAIL" != "$OLD_EMAIL" ] || [ "$GIT_COMMITER_EMAIL" != "$OLD_EMAIL" ];then
if [ "$GIT_COMMITTER_EMAIL" != "$OLD_EMAIL" ];then
	echo "找到目标， 进行替换"
    export GIT_AUTHOR_NAME="$NEW_NAME"
    export GIT_AUTHOR_EMAIL="$NEW_EMAIL"

    export GIT_COMMITER_NAME="$NEW_NAME"
    export GIT_COMMITER_EMAIL="$NEW_EMAIL"
	env |grep "^GIT_"
else
	echo "没有找到目标， 不进行替换"
fi
' --tag-name-filter cat -- --branches --tags

# 强制推送： 执行以下命令来强制推送修改后的历史：
# git push --force --tags origin 'refs/heads/*'



# git filter-branch --env-filter '
# if [ "$GIT_AUTHOR_EMAIL" = "old@mail.com" ]
# then
#     export GIT_AUTHOR_EMAIL="new@mail.com"
# 	echo "修改作者"
# fi
# if [ "$GIT_COMMITTER_EMAIL" = "" ]
# then
#     export GIT_COMMITTER_EMAIL="calllivecn@outlook.com"
# 	echo "修改提交者"
# fi
# ' --tag-name-filter cat -- --branches --tags



# 这种是新方式。 需要安装 apt install git-filter-repo
#git filter-repo --email-callback '
#if commit.author.email == b"old_email_address@example.com":
#commit.author.email = b"new_email_address@example.com"' --force

