#!/usr/bin/env python3
#coding=utf-8



import sys
import ssl
from urllib.request import Request,urlopen

host = 'https://dm-81.data.aliyun.com'
path = '/rest/160601/ip/getIpInfo.json'
method = 'GET'
appcode = '你自己的AppCode'
querys = 'ip=0.0.0.0'
bodys = {}
url = host + path + '?' + querys

request = Request(url)
request.add_header('Authorization', 'APPCODE ' + appcode)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
response = urlopen(request)# context=ctx)
content = response.read()
if (content):
    print(content)
