#!/usr/bin/env python3
# coding=utf-8
# date 2018-09-14 15:38:09
# author calllivecn <c-all@qq.com>



import os
import sys
import json
import pprint
import argparse
from urllib import request

URL="http://hub.bnq.com.cn"
URL="http://ap01.bnq.in:5000"

headers = {"Context-Type": "application/json"}


def urlmethod(url, method="GET"):
    req = request.Request(url, method=method, headers=headers)
    result = request.urlopen(req).read()

    b = result.rstrip(b"\n")
    return json.loads(b)

def checkapiv2():
    req = request.Request(URL + "/v2/")
    result = request.urlopen(req)
    if result.code == 200:
        return True
    else:
        print("status code:", result.code)
        return False
    
def getimages(url):
    j = urlmethod(url + "/v2/_catalog")
    pprint.pprint(j)


def gettaglist(url, image):
    j = urlmethod(url + "/v2/{}/tags/list".format(image))
    pprint.pprint(j)

def getimageinfo(url, image, tag):
    j = urlmethod(url + "/v2/{}/manifests/{}".format(image, tag))
    pprint.pprint(j)

def deleteimage(url, image, tag):
    j = urlmethod(url + "/v2/{}/manifests/{}".format(image, tag), method="DELETE")
    pprint.pprint(j)


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
    if checkapiv2():
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


#if args.info and args.image and args.tag:
#    getimageinfo(REGISTRY, args.image, args.tag)

if args.delete and args.image and args.tag:
    deleteimage(REGISTRY, args.image, args.tag)

elif args.image and args.tag:
    getimageinfo(REGISTRY, args.image, args.tag)

elif args.image:
    gettaglist(REGISTRY, args.image)

else:
    getimages(REGISTRY)
