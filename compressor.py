#!/usr/bin/env python3
#coding=utf-8
# date 2018-04-08 09:18:05
# author calllivecn <c-all@qq.com>


import gzip
import bz2
import lzma
from struct import Struct

class Itar:
    

class _FileInfo:
    __slots__=["name",      #
                "prefix",   
                "size",
                "mtime",
                "chksum"]


BUF= 8*(1<<20) # buf 8M

def compress():
    with open('data','rb') as fr,open('data.gz','wb') as fw:
        data = fr.read(BUF)
        size = len(data)
        while data:
            comp_data = gzip.compress(data)
            fw.write(comp_data)
            data = fr.read(BUF)
            size += len(data)

        print('read总大小:',size)

def Decompress():
    pass

#compress() 


def bz2comp():
    comp = bz2.BZ2Compressor()
    with open('data','rb') as fr, open('data.bz2','wb') as fw:
        data = fr.read(BUF)
        while data:

            comp_data = comp.compress(data)

            if  comp_data != b'':
                fw.write(comp_data)

            data = fr.read(BUF) 
        
        comp_data = comp.flush()
        fw.write(comp_data)

#bz2comp()


def xzcomp():
    comp = lzma.LZMACompressor()
    with open('data','rb') as fr, open('data.xz','wb') as fw:
        data = fr.read(BUF)
        while data:

            comp_data = comp.compress(data)

            if  comp_data != b'':
                fw.write(comp_data)

            data = fr.read(BUF) 

        comp_data = comp.flush()
        fw.write(comp_data)

#xzcomp()


