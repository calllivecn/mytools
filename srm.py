#!/usr/bin/env python3
#coding=utf-8

import sys,os,argparse

parse=argparse.ArgumentParser(description='secure file deletion')

parse.add_argument('files',nargs='+',help='security deletion files')

args=parse.parse_args()



l='0'*4096

for f in args.files:
	
	file_size = os.stat(f).st_size
	count=file_size//4096+1
	fp = open(f,'r+')
	
	for tmp in range(count):
		fp.write(l)
		fp.flush()
		
	fp.close()
	
	os.remove(f)

