#!/usr/bin/env python3
# coding=utf-8
# updated 2025-05-30 16:00:00
# author calllivecn <calllivecn@outlook.com>

import os
import sys
import json
import httpx

"""
文档：https://docs.github.com/cn/rest/reference/repos#list-repositories-for-a-user
"""

# GitHub 每页最多返回 100 个仓库
PER_PAGE = 100


def find_next_link(link_header):
    if not link_header:
        return None

    for part in link_header.split(','):
        if 'rel="next"' in part:
            url_part = part.split(';')[0].strip()
            return url_part.strip('<>')
    return None


def build_request_params(username_or_token):
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }

    # 判断是否为 classic token (ghp_xxx)
    if username_or_token.startswith("ghp_") and len(username_or_token) == 40:
        headers["Authorization"] = f"token {username_or_token}"
        url = f"https://api.github.com/user/repos?per_page={PER_PAGE}"
        return url, headers

    # 判断是否为 fine-grained token (github_pat_xxx)
    elif username_or_token.startswith("github_pat_"):
        headers["Authorization"] = f"Bearer {username_or_token}"
        url = f"https://api.github.com/user/repos?per_page={PER_PAGE}"
        return url, headers

    # 默认情况：当作用户名处理
    else:
        url = f"https://api.github.com/users/{username_or_token}/repos?per_page={PER_PAGE}"
        return url, headers


def get_all_repos(username_or_token):
    url, headers = build_request_params(username_or_token)

    jdata = []
    while True:
        print(f"Fetching: {url}", file=sys.stderr)
        with httpx.Client(http2=True) as client:
            response = client.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            sys.exit(1)

        jdata.extend(response.json())

        next_url = find_next_link(response.headers.get("Link"))
        if not next_url:
            break
        url = next_url

    # 输出所有仓库的 clone 地址
    for repo in jdata:
        print(repo["clone_url"])


USAGE = """\
Usage: {} <github username|classic_token(ghp_xxx)|fine_grained_token(github_pat_xxx)>
注意：
- 使用 ghp_xxx token 可以查看自己的私有仓库（需要 repo 权限）
- 使用 github_pat_xxx 需要确保 token 有 repository contents 的 read 权限
""".format(sys.argv[0])


def usage():
    print(USAGE)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        usage()
        sys.exit(0)

    get_all_repos(sys.argv[1])
