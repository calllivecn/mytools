#!/usr/bin/env python3
# coding=utf-8
# date 2018-09-14 15:38:09
# update 2024-07-06 16:53:37
# author calllivecn <calllivecn@outlook.com>



import os
import sys
import json
# import pprint
import argparse
from urllib import request


headers = {"Context-Type": "application/json"}

def urlmethod(url, method="GET", headers=headers):
    req = request.Request(url, method=method, headers=headers)
    result = request.urlopen(req).read()
    return result.decode("utf-8")

def checkapiv2(url):
    req = request.Request(url + "/v2/")
    result = request.urlopen(req)
    if result.code == 200:
        return True
    else:
        print("status code:", result.code)
        return False
    

def getimages(url):
    j = urlmethod(f"{url}/v2/_catalog")
    print(j)


def gettaglist(url, image):
    j = urlmethod(f"{url}/v2/{image}/tags/list")
    print(j)


def getimageinfo(url, image, tag):
    headers = {
        "Accept": "application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json"
    }
    j = urlmethod(f"{url}/v2/{image}/manifests/{tag}", headers=headers)
    print(j)


def query_delete_digest(url, image, tag):
    headers = {
        "Context-Type": "application/json",
        # "Accept": "application/vnd.docker.distribution.manifest.v2+json"
        "Accept": "application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json"
        }

    req = request.Request(f"{url}/v2/{image}/manifests/{tag}", method="GET", headers=headers)

    response = request.urlopen(req)
    result = response.read()

    print(f"{response=}, {dir(response)=}")

    return response.headers["Docker-Content-Digest"]


def deleteimage(url, image, tag):

    digest =  query_delete_digest(url, image, tag)

    req = request.Request(f"{url}/v2/{image}/manifests/{digest}", method="DELETE")

    response = request.urlopen(req)

    result = response.read().decode("utf-8")

    if 200 <= response.status < 300:
        print(f"{result}")
    else:
        print(f"Response code: {response.status}")
        sys.exit(1)



parse = argparse.ArgumentParser(usage="%(prog)s <url> [-2|--apiv2] [-i <image>] [-t <tag>] [-d|--delete]")

parse.add_argument("-2", "--apiv2", action="store_true", help="check API v2")
parse.add_argument("-i", "--image", help="list registry images. (default)")
parse.add_argument("-t", "--tag", help="list images tags")
#parse.add_argument("-I", "--info", action="store_true", help="info image:tag")
parse.add_argument("-d", "--delete", action="store_true", help="delete image:tag")

parse.add_argument("url", nargs="?", default=False, help="registry address or export REGISTRY=http://127.0.0.1:5000")

args = parse.parse_args()
#print(args);sys.exit(0)

if args.apiv2:
    if checkapiv2(args.url):
        print("支持API v2")
    else:
        print("不支持API v2, 还没实现v1。也许不会实现")
    sys.exit(0)


REGISTRY = os.getenv("REGISTRY")
if args.url:
    REGISTRY = args.url
elif not REGISTRY:
    print("需要url参数，或者REGISTRY环境变量", file=sys.stderr)
    sys.exit(1)


if args.delete and args.image and args.tag:
    deleteimage(REGISTRY, args.image, args.tag)
    print(f"如果需要回收硬盘空间，可能还需要在registry 容器里运行：register registry garbage-collect /etc/docker/registry/config.yml")

elif args.image and args.tag:
    getimageinfo(REGISTRY, args.image, args.tag)

elif args.image:
    gettaglist(REGISTRY, args.image)

else:
    getimages(REGISTRY)

