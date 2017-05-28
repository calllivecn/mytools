#!/usr/bin/env python3
#coding=utf-8

import hashlib,argparse

parse=argparse.ArgumentParser()

parse.add_argument('-md5',action="store_true",help="md5")
parse.add_argument('-sha1',action="store_true",help="sha1")
parse.add_argument('-sha128',action="store_true",help="sha128")
parse.add_argument('-sha224',action="store_true",help="sha224")
parse.add_argument('-sha256',action="store_true",help="sha256")
parse.add_argument('-sha384',action="store_true",help="sha384")
parse.add_argument('-sha512',action="store_true",help="sha512")

parse.add_argument('files',nargs="+",help="input files")

args=parse.parse_args()

#print(args)

if args.md5:
	s=hashlib.md5()
elif args.sha1:
	s=hashlib.sha1()
elif args.sha128:
	s=hashlib.sha128()
elif args.sha224:
	s=hashlib.sha224()
elif args.sha256:
	s=hashlib.sha256()
elif args.sha384:
	s=hashlib.sha384()
elif args.sha512:
	s=hashlib.sha512()
else:
	s=hashlib.md5()

for f in args.files:
	s_tmp=s.copy()
	f_in=open(f,'rb')
	data=1
	while data:
		data=f_in.read(4096)
		s_tmp.update(data)
	print(s_tmp.hexdigest(),f,sep="\t")
	f_in.close()
