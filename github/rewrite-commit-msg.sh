#!/bin/bash
# date 2024-01-19 11:14:18
# author calllivecn <c-all@qq.com>


git filter-branch --env-filter '
if [ "$GIT_AUTHOR_EMAIL" = "old_email_address@example.com" ]
then
    export GIT_AUTHOR_EMAIL="new_email_address@example.com"
fi
if [ "$GIT_COMMITTER_EMAIL" = "old_email_address@example.com" ]
then
    export GIT_COMMITTER_EMAIL="new_email_address@example.com"
fi
' --tag-name-filter cat -- --branches --tags
t filter-branch --env-filter '
if [ "$GIT_AUTHOR_EMAIL" = "old_email_address@example.com" ]
then
    export GIT_AUTHOR_EMAIL="new_email_address@example.com"
fi
if [ "$GIT_COMMITTER_EMAIL" = "old_email_address@example.com" ]
then
    export GIT_COMMITTER_EMAIL="new_email_address@example.com"
fi
' --tag-name-filter cat -- --branches --tags


