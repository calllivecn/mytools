#!/usr/bin/env python3
# coding=utf-8
# date 2020-08-12 05:55:25
# author calllivecn <c-all@qq.com>


import os
import sys
import json
from urllib import request

"""
文档：https://docs.github.com/cn/rest/reference/repos#list-repositories-for-a-user
"""

# github 默认页大小为：30, MAX: 100
per_page=100


def findnext(link):

    if link is None:
        return None

    for l in link.split(","):
        if l.find("next") != -1:
            url = l.split(";")[0]
            url = url.strip()
            return url.strip("<>")
    
    return None


def get_request(url, headers):
    req = request.Request(url, headers=headers)
    return request.urlopen(req)

def build_request(username_or_token):

    url =f"https://api.github.com/users/{username_or_token}/repos?per_page={per_page}"

    # headers = {"Accept": "application/vnd.github.nebula-preview+json"}
    headers = {"Accept": "application/vnd.github.v3+json"}

    # 是使用的token
    if username_or_token.startswith("ghp_") and len(username_or_token) == 40:
        headers.update({"Authorization": f"Token {username_or_token}"})
        url = f"https://api.github.com/user/repos?per_page={per_page}"

    return url, headers


def get_all_repos(username_or_token):

    link_next, headers = build_request(username_or_token)
    jdata = []
    while True:

        print("link_next:", link_next, file=sys.stderr)
        result = get_request(link_next, headers)

        jdata += json.loads(result.read())

        link = result.getheader("Link")

        # debug
        # print("debug: ", link)

        # 拿到下一页的link
        link_next = findnext(link)
        if link_next is None:
            break

    # output
    for repo in jdata:
        print(repo["clone_url"])


USAGE="""\
Usage: {} <github username|github token>
# 使用 github token 可以查看到私人仓库
""".format(sys.argv[0])

def usage():
    print(USAGE)

if __name__ == "__main__":

    if sys.argv[1] == "-h" or sys.argv[1] == "--help":
        usage()
        sys.exit(0)

    get_all_repos(sys.argv[1])
