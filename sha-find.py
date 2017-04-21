#!/usr/bin/env python3
#coding=utf-8


import hashlib,sys


def __sha512(file_):
	#print('|'*60,'__sha512() {}'.format(file_))	
	sha = sha512()
	
	READ_BUF = 2**20*4
	size = getsize(file_) # os.stat(file_).st_size
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



if len(sys.argv) < 2:
	print('Using: {} <sha value> [file ... ]')
	exit(-1)

sha = sys.argv[1]


for f in sys.argv[2:]:
	if isfile(f):
		sha_value = __sha512(f)
		if sha == sha_value:
			print(sha,f,sep='\t')
	else:
		print(f,'not a file')

	

