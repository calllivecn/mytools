#!/usr/bin/env python3
#codnig=utf-8


import sys
from base64 import encodebytes,decodebytes
from argparse import ArgumentParser

def thunder(thunder1):
    thunder2 = thunder1.lstrip('thunder://')
    decode3 = decodebytes(thunder2.encode())
    try:
        decode4 = decode3.decode()
    except UnicodeError:
        decode4 = decode3.decode('gb18030')

    thunder4 = decode4.lstrip('AA').rstrip('ZZ')

    print(thunder4)


parse = ArgumentParser(usage="Using: %(prog)s <thunder ...>",description="解析thunder下载地址",add_help=True,)

parse.add_argument("thunder",nargs="+",help="迅雷专用下载链接")

args = parse.parse_args()


for th in args.thunder:
    thunder(th)


