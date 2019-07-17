#!/usr/bin/env python3
#coding=utf-8
# date 2018-06-13 08:12:03
# author calllivecn <c-all@qq.com>


import os
import re
import sys
import argparse
import hashlib
from functools import partial

parse = argparse.ArgumentParser()

groups = parse.add_mutually_exclusive_group()

groups.add_argument('--md5',action="store_true",help="md5")
groups.add_argument('--sha1',action="store_true",help="sha1")
groups.add_argument('--sha128',action="store_true",help="sha128")
groups.add_argument('--sha224',action="store_true",help="sha224")
groups.add_argument('--sha256',action="store_true",help="sha256 (default)")
groups.add_argument('--sha384',action="store_true",help="sha384")
groups.add_argument('--sha512',action="store_true",help="sha512")

g2 = parse.add_mutually_exclusive_group()

g2.add_argument('-c', "--check", action="store", help="从文件中读取SHA256 的校验值并予以检查")

g2.add_argument('files',nargs="*",default="-",help="files")

args = parse.parse_args()

#print(args);exit(0)

BUF = 1<<14 # 16k

if args.md5:
    s = hashlib.md5()
elif args.sha1:
    s = hashlib.sha1()
elif args.sha128:
    s = hashlib.sha128()
elif args.sha224:
    s = hashlib.sha224()
elif args.sha256:
    s = hashlib.sha256()
elif args.sha384:
    s = hashlib.sha384()
elif args.sha512:
    s = hashlib.sha512()
else:
    s = hashlib.sha256()

resep = re.compile(r"\t| +")

def shafile(filename):
    s_tmp = s.copy()
    with open(filename, 'rb') as f_in:
        for data in iter(partial(f_in.read, BUF), b""):
            s_tmp.update(data)

    return s_tmp.hexdigest()


def readshafile(checksumfile):
    with open(checksumfile) as f:
        c = 0
        for line in iter(partial(f.readline), ""):
            c += 1
            try:
                fvalue, fname = resep.split(line.rstrip("\r\n"), maxsplit=1)
            except Exception as e:
                print("{} line:{} {} 错误".formt(checksumfile, c, line))
                continue

            try:
                value = shafile(fname)
            except FileNotFoundError as e:
                print("{} line:{} 没有文件：{}".format(checksumfile, c, fname))
                continue

            if fvalue == value:
                print(fname, ": ok")
            else:
                print(fname, ": failed")


if args.check:
    readshafile(args.check)

elif args.files == "-" or args.files[0] == "-":
    stdin = sys.stdin.buffer.fileno()
    for data in iter(partial(os.read, stdin, BUF), b""):
        s.update(data)

    print(s.hexdigest(),"-",sep="\t")

else:
    for f in args.files:
        print(shafile(f),f,sep="\t")
