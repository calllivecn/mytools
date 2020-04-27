#!/usr/bin/env python3
#coding=utf-8
# date 2018-04-09 14:28:18
# author calllivecn <c-all@qq.com>

import gzip
import bz2
import lzma
import os
from struct import Struct,pack,unpack
import multiprocessing as mp

Header = Struct("<HH")
# B is compress flag
# I is block size 64k

CompressFlag = {"none":0, "gzip":1, "bz2":2, "xz":3}

NONE = 0
GZIP = 1
BZ2 = 2
XZ = 3

COMP = 1
DECOMP = 2

BLOCK = 1<<16 # 64k

class ReturnBlock:
    """
    从流中返回BLOCK大小的数据
    """
    def __init__(self, stream, block=1):
        self.stream = stream
        self.block = block * BLOCK
    
    def getblock(self):

        size = 0
        while True:
            data = self.stream.get()
            self.stream.task_done()
            size += len(data)
            if size < self.block:
                continue
            elif size >= self.block:
                data, self.last = data[:self.block], data[self.block:]
                return data
            #elif size == self.block:
            #    return data

def none_comp(block):
    return block

def gzipcomp(block):
    return gzip.compress(data)

def gzipdecomp(block):
    return gzip.decompress(block)

#compress() 

def bz2comp(block):
    return bz2.compress(block)

#bz2comp()

def bz2decomp(block):
    return bz2.decompress(block)

def xzcomp(block):
    return lzma.compress(block)

#xzcomp()

def xzdecomp(block):
    return lzma.decompress(block)


class Algorithm:
    
    def __init__(self,alg,choice):
        if alg == NONE:
            self.algorithm = none_comp

        elif alg == GZIP:
            if choice == COMP:
                self.algorithm = gzipcomp
            else:
                self.algorithm = gzipdecomp
        elif alg == BZ2:
            if choice == COMP:
                self.algorithm = bz2comp
            else:
                self.algorithm = bz2decomp
        elif alg == XZ:
            if choice == COMP:
                self.algorithm = xzcomp
            else:
                self.algorithm = xzdecomp

    def alg(self,data_block):
        return self.algorithm(data_block)



class Com:
    
    def __init__(self, task, result, alg=NONE,choice=COMP, block=1):
        #from queue import Queue
        #if not ( isinstance(task,Queue) and isinstance(result,Queue) ):
        #    raise TypeError("task and result must be is Queue")

        self.getblock = ReturnBlock(task,block = BLOCK * block)
        self.alg = Algorithm(alg, choice)

        self.task = task
        self.result = result

        self.header = Header.pack(fmt, self.block)

        self.result.put(self.header)

    def com_result(self):
        while True:
            data = self.getblock()
            data_alg = self.alg(data)
            self.result.put(data_alg)
