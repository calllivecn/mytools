#!/usr/bin/env python3
#coding=utf-8


import hashlib,sys

from argparse import ArgumentParser

parse = ArgumentParser(usage=' %(prog)s <filename|sha512>',description='',epilog='\n')

parse.add_argument('file',nargs='+',help='filename|sha512')


args = parse.parse_args()

print(args);exit(0)

def __sha512(file_):
	sha = sha512()
	
	READ_BUF = 4*1<<20
	size = getsize(file_)
	data_len = 0

	with open(file_,'rb') as f:
		
		data = f.read(READ_BUF)
		
		sha.update(data)

		data_len = len(data)

		while data_len < size :
			sha.update(data)
			data = f.read(READ_BUF)
			data_len += len(data)
	
	return sha.hexdigest()


for f in args.file:
	if isfile(f):
		sha_value = __sha512(f)
		if sha == sha_value:
			print(sha,f,sep='\t')
	else:
		print(f,'not a file')

	

