#!/usr/bin/env python3
#coding=utf-8

import urllib, sys
import ssl
from urllib.request import Request,urlopen
from json import loads,dumps
from pprint import pprint

host = 'https://dm-81.data.aliyun.com'
path = '/rest/160601/ip/getIpInfo.json'
method = 'GET'
appcode = 'c6eec2885f1540caa6b4217119ea7d58'
querys = 'ip={}'.format('210.75.225.254')
bodys = {}
url = host + path + '?' + querys

request = Request(url)
request.add_header('Authorization', 'APPCODE ' + appcode)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
response = urlopen(request, context=ctx)
content = response.read()
if (content):
    pprint(loads(content.decode()))
