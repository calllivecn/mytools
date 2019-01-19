#!/usr/bin/env python3
#coding=utf-8
# date 2018-06-13 08:12:03
# author calllivecn <c-all@qq.com>


import hashlib
import argparse
import sys
import os

parse=argparse.ArgumentParser()

groups = parse.add_mutually_exclusive_group()

groups.add_argument('--md5',action="store_true",help="md5")
groups.add_argument('--sha1',action="store_true",help="sha1")
groups.add_argument('--sha128',action="store_true",help="sha128")
groups.add_argument('--sha224',action="store_true",help="sha224")
groups.add_argument('--sha256',action="store_true",help="sha256")
groups.add_argument('--sha384',action="store_true",help="sha384")
groups.add_argument('--sha512',action="store_true",help="sha512")

parse.add_argument('files',nargs="*",default="-",help="files")

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

BUF = 4*(1<<20)

if args.files == "-" or args.files[0] == "-":
    stdin = sys.stdin.buffer
    data=True
    while data:
        data = stdin.read(BUF)
        data = data
        s.update(data)
    print(s.hexdigest(),"-",sep="  ")

else:
    for f in args.files:
        s_tmp=s.copy()
        with open(f, 'rb') as f_in:
            data=True
            while data:
                data=f_in.read(BUF)
                s_tmp.update(data)
            print(s_tmp.hexdigest(),f,sep="  ")
