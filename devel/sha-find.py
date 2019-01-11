#!/usr/bin/env python3
#coding=utf-8


import sys
import hashlib

from os.path import isfile,getsize

from argparse import ArgumentParser

parse = ArgumentParser(usage=' %(prog)s <filename|sha512>',description='通过sha值查找文件或通过文件值查找一个sha值',epilog='\n')

parse.add_argument('-f','--file',nargs='+',help='<filename>')

parse.add_argument('-v','--value',nargs='+',help='<sha512>')

args = parse.parse_args()

print(args);#exit(0)

def __sha512(file_):
    sha = hashlib.sha512()
    
    READ_BUF = 1<<20
    size = getsize(file_)
    data_len = 0

    with open(file_,'rb') as f:
        
        data = f.read(READ_BUF)

        while data:
            sha.update(data)
            data = f.read(READ_BUF)
    
    return sha.hexdigest()


def find():
    for f in args.file:
        sha_value = __sha512(f)
        if sha == sha_value:
            print(sha,f,sep='\t')
        else:
            print(f,'not a file')

    
