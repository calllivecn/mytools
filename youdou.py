#!/usr/bin/env python3
#coding=utf-8


from urllib import request,parse
from random import randint
from time import time
from hashlib import md5
import sys,json
from pprint import pprint

url='http://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule&sessionFrom='


u = "fanyideskweb"

d = sys.argv[1]

f = int(time() * 1000) + randint(0,10)

c = r"rY0D^0'nM0}g5Mm1z%1G4"

S = u + d + str(f) + c

g = md5(S.encode()).hexdigest()


data={	"i":d,
		"from":"AUTO",
		"to":"AUTO",
		"smartresult":"dict",
		"client":u,
		"salt":f,
		"sign":g,
		"doctype":"json",
		"version":"2.1",
		"keyfrom":"fanyi.web",
		"action":"FY_BY_CLICKBUTTION",
		"typoResult":"true",
		}

header = {	"Accept":"application/json, text/javascript",
			"Host":"fanyi.youdao.com",
			"Origin":"http://fanyi.youdao.com",
			"Referer":"http://fanyi.youdao.com/",
			"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36"
			}


#print(data)
data = parse.urlencode(data).encode()

req = request.Request(url,headers=header,method='POST',data=data)

result = request.urlopen(req).read().decode()

result = json.loads(result)


returncode = result.get("errorCode")
if returncode != 0:
	print('errorCode',returncode)
	exit(1)
else:
	result , smartResult  = result.get("translateResult") , result.get("smartResult")
	result = result[0][0]
	print('原文:',result.get("src"))
	print('翻译:',result.get("tgt"))
	if smartResult != None:
		for i in smartResult.get("entries"):
			if i == "":
				continue
			else:
				print(i.replace('\r\n','\n'))




#{"translateResult":[[{"tgt":"打印","src":"print"}]],"errorCode":0,"type":"en2zh-CHS","smartResult":{"entries":["","n. 印刷业；印花布；印刷字体；印章；印记\r\n","vt. 印刷；打印；刊载；用印刷体写；在...印花样\r\n","vi. 印刷；出版；用印刷体写\r\n"],"type":1}}




