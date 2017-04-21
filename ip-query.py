#!/usr/bin/env python3
#coding=utf-8

import json 
from urllib.request import urlopen
from socket import gethostbyname_ex
import sys,argparse


def query(ipaddr):
	url='http://ip.taobao.com/service/getIpInfo.php?ip={}'.format(ipaddr) #地址  
	response = urlopen(url) #post提交数据 
	
	html = response.read()  #接收返回数据 
	
	tag=json.loads(html.decode())#,encoding='utf8') #josh格式转换 
	
	if tag["code"] == 0:
		data=tag["data"]
	else:
		print('返回码非零,查询出错。',ipaddr)
		return 1
	
	#print(data) 
	
	ip=data["ip"]  #要查询IP 
	city=data["city"]#城市 
	region=data["region"]#省
	area=data["area"]#区域 
	isp=data["isp"] #ISP 
	county=data["county"]#市区 
	country=data["country"]#国家 
	return "\tIP:{}\n\t运营商：{}\n\t国家:{}\n\t地区城市:{}{}".format(ip,isp,country,region,city)



if __name__ == "__main__":
	parse = argparse.ArgumentParser(description='query ip information',epilog='this description end.',add_help=True)

	#parse.add_argument('-a','--address',nargs="*",help="addresss or hostnames")
	parse.add_argument('address',nargs="*",help="addresss or hostnames")

	args = parse.parse_args()
	
	for ip_or_hostname in args.address:
		print('查询：',ip_or_hostname)
		ip_lists = gethostbyname_ex(ip_or_hostname)
		for ip in ip_lists[2]:
			print('\n',query(ip),sep='')
		print()
