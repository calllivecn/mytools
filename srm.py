#!/usr/bin/env python3
#coding=utf-8

import sys,os,argparse
from os.path import getsize,join,exists,isdir,isfile,islink,split

parse=argparse.ArgumentParser(description='secure file deletion')

parse.add_argument('files',nargs='+',help='files and dirs')

args=parse.parse_args()
#print(args)

def check_files():
	not_exists_lists=[]
	for f_d in args.files:
		if not exists(f_d):
			not_exists_lists.append(f_d)

	if len(not_exists_lists) > 0:
		for f in not_exists_lists:
			print(f,end=' ')

		print('file not exists')
		exit(1)

check_files()

def clear_filename(filename):
	char_id = 48
	char = chr(char_id)

	path , filename = split(filename)

	fn_len = len(filename)
	clear_fn = char * fn_len

	while exists(join(path,clear_fn)):
		clear_fn += char
		if len(clear_fn) > 128:
			char_id +=1
			char = chr(char_id)
			clear_fn = char * fn_len
	
	os.rename(join(path,filename),join(path,clear_fn))

	if isfile(join(path,clear_fn)):
		os.remove(join(path,clear_fn))
	if isdir(join(path,clear_fn)):
		os.rmdir(join(path,clear_fn))
	if islink(join(path,clear_fn)):
		os.remove(join(path,clear_fn))

l=bytes(4096)
def remove(file__):

	if islink(file__):
		clear_filename(file__)
		return

	file_size = getsize(file__)
	count=file_size//4096+1
	fp = open(file__,'r+b')
	
	for tmp in range(count):
		fp.write(l)
		fp.flush()
		
	fp.close()
	
	clear_filename(file__)


def rm_dir_tree(dir__):
	for r,d,f in os.walk(dir__,topdown=False):
		for f2 in f:
			remove(join(r,f2))

		for dir_ in d:
			clear_filename(join(r,dir_))
	
	clear_filename(dir__.rstrip('/'))


for f in args.files:
	if isfile(f) or islink(f):
		remove(f)
	elif isdir(f):
		rm_dir_tree(f)
	else:
		print(f,'not is dir or normal file,not delete')
