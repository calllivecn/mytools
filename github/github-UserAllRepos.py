#!/usr/bin/env python3
# coding=utf-8
# date 2020-08-12 05:55:25
# author calllivecn <c-all@qq.com>


import sys
import json
from urllib import request




GITHUB_USER_REPOS="https://api.github.com/users/{}/repos"


def get_all_repos(username):
    
    url = GITHUB_USER_REPOS.format(username)
    req = request.Request(url, headers={"Accept": "application/vnd.github.nebula-preview+json"})
    data = request.urlopen(req).read()

    for repo in json.loads(data):
        print(repo["clone_url"])


USAGE="""\
Usage: {} <github username>
""".format(sys.argv[0])

def usage():
    print(USAGE)

if __name__ == "__main__":

    if sys.argv[1] == "-h" or sys.argv[1] == "--help":
        usage()
        sys.exit(0)

    get_all_repos(sys.argv[1])
