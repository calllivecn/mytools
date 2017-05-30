#!/usr/bin/env python3
#coding=utf-8

import sys,os,argparse

parse=argparse.ArgumentParser(description='secure file deletion')

parse.add_argument('files',nargs='+',help='security deletion files')

args=parse.parse_args()


def clear_filename(filename):
	char = '0'
	fn_len = len(filename)
	clear_fn = char * fn_len
	while os.path.exists(clear_fn):
		clear_fn += char
		if len(clear_fn) > 128:
			char = '1'
			clear_fn = char * fn_len
	
	os.rename(f,clear_fn)
	os.remove(clear_fn)


l=bytes(4096)

for f in args.files:
	
	file_size = os.stat(f).st_size
	count=file_size//4096+1
	fp = open(f,'r+b')
	
	for tmp in range(count):
		fp.write(l)
		fp.flush()
		
	fp.close()
	
	clear_filename(f)

