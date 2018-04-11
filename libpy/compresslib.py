#!/usr/bin/env python3
#coding=utf-8
# date 2018-04-09 14:28:18
# author calllivecn <c-all@qq.com>

import gzip
import bz2
import lzma
from struct import Struct,pack,unpack

ISDONE="is done"

CompressHeader = Struct("<BI")
# B is compress flag
# I is block size

CompressFlag = {"none":0, "gzip":1, "bz2":2, "xz":3}


BLOCK = 1<<20 # 1M

class ReturnBlock:
    """
    从流中返回BLOCK大小的数据
    """
    def __init__(self, stream, block=BLOCK):
        self.stream = stream
        self.block = block
    
    def getblock(self):

        size = 0
        while True:
            data = self.stream.get()
            size += len(data)
            if size < self.block:
                continue
            elif size > self.block:
                
            if size == self.block:
                return data
                

        

def compress(stream_task,stream_result):
    with open('data','rb') as fr,open('data.gz','wb') as fw:
        data = stream_task.get()
        if data == DONE:
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


