#!/usr/bin/env python3
# coding=utf-8
# date 2018-09-14 15:38:09
# author calllivecn <c-all@qq.com>

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

def deletetag(url, image, tag):
    j = urlmethod(url + "/v2/{}/manifests/{}".format(image, tag), method="DELETE")
    pprint.pprint(j)


parse = argparse.ArgumentParser(usage="%(prog)s <url> [-2|--apiv2] [-i <image>] [-t <tag>] [-I|--info]")

parse.add_argument("-2", "--apiv2", help="check API v2")
parse.add_argument("-i", "--image", help="list registry images. (default)")
parse.add_argument("-t", "--tag", help="list images tags")
parse.add_argument("-I", "--info", action="store_true", help="info image:tag")

parse.add_argument("url", help="registry address")

args = parse.parse_args()
#print(args);sys.exit(0)

if args.apiv2:
    if checkapiv2():
        print("支持API v2")
    else:
        print("不支持API v2, 还没实现v1。也许不会实现")
    sys.exit(0)


if args.info and args.image and args.tag:
    getimageinfo(args.url)

elif args.image and args.tag:
    getimageinfo(args.url, args.image, args.tag)

elif args.image:
    gettaglist(args.url, args.image)

else:
    getimages(args.url)
