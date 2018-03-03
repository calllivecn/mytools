#!/usr/bin/env python3
#coding=utf-8


import sys
from argparse import ArgumentParser,REMAINDER
#from fileinput import FileInput

parse = ArgumentParser(description='dos to unix in test or unix to dos',
                        usage='%(prog)s [option] -o outfile files'
                        )

parse.add_argument('-c','--conversion',action='store_false',help='default DOS to UINX else UINX to DOS.')

parse.add_argument('-f','--inencoding',metavar='',default='gb18030',help='input encode default: %(default)s')

parse.add_argument('-t','--outencoding',metavar='',default='utf-8',help='output encode default: %(default)s')

parse.add_argument('-o','--outfile',metavar='',required=True,help='output filename')

parse.add_argument('files',metavar='files',help='filename') #nargs=REMAINDER)

args = parse.parse_args()

#print(args)

def conversion(conver_type=args.conversion):

    if conver_type:
        r_encoding = args.inencoding
        w_encoding = args.outencoding
        CRLF=('\r\n','\n')
    else:
        w_encoding = args.inencoding
        r_encoding = args.outencoding
        CRLF=('\n','\r\n')

    with open(args.files,encoding=r_encoding) as fd,open(args.outfile,'w+',encoding=w_encoding) as fdout:
        for line in fd:
            data = line.replace(*CRLF)
            fdout.write(data)

try:
    conversion()
except UnicodeDecodeError:
    print('input file encode error',args.inencoding)
