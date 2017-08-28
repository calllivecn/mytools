#!/usr/bin/env python3
#coding=utf-8



import sys,json,pprint,os

isfile = os.path.isfile


files=sys.argv[1:]

for f in files:
	if isfile(f):
		with open(f,'r') as fp:
			jn = json.load(fp)
			pprint.pprint(jn)
	else:
		print('{}不是一个文件'.format(f))
