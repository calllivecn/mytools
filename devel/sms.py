#!/usr/bin/env python3
#coding=utf-8

import sys
from json import loads,dumps
from urllib.request import Request,urlopen
from urllib.parse import quote

host = 'http://sms.market.alicloudapi.com'
path = '/singleSendSms'
method = 'GET'
appcode = '' # 我的appcode
querys = 'ParamString=%7B%22no%22%3A%22123456%22%7D&RecNum=RecNum&SignName=SignName&TemplateCode=TemplateCode'
querys = 'ParamString={}&RecNum={}&SignName={}&TemplateCode={}'.format(quote(dumps({"text":"text"})),
                                                                        quote('18107298655'),
                                                                        quote('SIGN'),
                                                                        quote('test${text}'))
bodys = {}
url = host + path + '?' + querys
print(url)
#'http://sms.market.alicloudapi.com/singleSendSms?ParamString=%7B%22no%22%3A%22123456%22%7D&RecNum=RecNum&SignName=SignName&TemplateCode=TemplateCode'
#header = {'Authorization':'APPCODE ' + appcode}

request = Request(url)
request.add_header('Authorization', 'APPCODE ' + appcode)

#print(request.full_url);exit(1)

response = urlopen(request)
content = response.read()
if (content):
    print(content.decode())
