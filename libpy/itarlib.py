#!/usr/bin/env python3
#coding=utf-8
# date 2018-04-08 11:29:56
# author calllivecn <c-all@qq.com>



import os
import time
from os.path import split,getsize,getmtime,join,isfile,isdir,exists,abspath
from struct import Struct,pack,unpack
from queue import Queue
from threading import Thread

__all__=["ISDONE","FILEISDONE","ItarComp","ItarDecomp","FileInfo"]

__ITAR_VERSION__ = 1

ITAR_FLAG = b"itar"
ITAR_FLAG_LEN = len(ITAR_FLAG)
ISDONE="is done" # all work is done
FILEISDONE="file is done" # extract a file done

class ItarError(Exception):
    pass

class ItarReadError(ItarError):
    pass

class ItarWriteError(ItarError):
    pass

# I'm tar header
ItarHead = Struct("<BQ") # itar versio byte, create time uint64

# fileinfo
FileInfo = Struct("<HQQQ")
# ["fullname_len",  # 2byte or uint16
# "size",           # 8byte or uint64
# "mtime",          # 8byte or uint64
# "chksum"]         # 8byte or uint64
                    # sum is 26byte

class ItarComp:
    def __init__(self,stream_put):

        self.stream_put = stream_put

        self.version = __ITAR_VERSION__
        self.create_time = int(time.time())

        _HEAD = ItarHead.pack(self.version, # itar version
                            self.create_time) # create time
        
        self.stream_put.put(ITAR_FLAG + _HEAD)


    def __chksum(self):
        """
        check fileinfo for feture
        """
        """
        chksum = FileInfo.pack(name.encode(),
                                    prefix.encode(),
                                    size,
                                    mtime,
                                    bytes(8))
        chksum = chkSum()
        """
        return 0 # fill b'\0'

    def preprocess_file(self,fullname):
        if fullname.startswith('./'):
            fullname_pre = fullname.lstrip('./')
        elif fullname.startswith('/'):
            fullname_pre = fullname.lstrip('/')
        else:
            fullname_pre = fullname
        
        return fullname_pre

    def comp_file(self,fullname,buf=65536): # buff 64k

        if fullname == ISDONE:
            self.stream_put.put(ISDONE)
            return

        size = getsize(fullname)
        mtime = int(getmtime(fullname))

        fullname_itar = self.preprocess_file(fullname)

        fullname_byte = fullname_itar.encode()
        fullname_len = len(fullname_byte)
        data = FileInfo.pack(fullname_len,
                    size,
                    mtime,
                    self.__chksum())

        self.stream_put.put(data + fullname_byte)


        with open(fullname,'rb') as fileobj:
        
            while True:
                data = fileobj.read(buf)
                if not data:
                    break
                self.stream_put.put(data)

        #self.stream_put.task_done()


class ItarDecomp:

    def __init__(self,itarname,stream_put):
        self.itarname = itarname
        self.stream_put = stream_put
        self.itarobj = open(itarname,'rb')

        self.itar_flag = self.itarobj.read(ITAR_FLAG_LEN)

        itar_head = self.itarobj.read(ItarHead.size)
        self.version, self.create_time = ItarHead.unpack(itar_head)


    def __chkSum(self):
        """
        fileinfo checksum for feture
        """
        # self._head
        pass

    def itar_close(self):
        self.itarobj.close()

    def decomp_file(self,buf=65536):

        while True:
            self._filehead = self.itarobj.read(FileInfo.size)

            if self._filehead == b'':
                break

            #print("self._filehead len",len(self._filehead))
            fileinfo = FileInfo.unpack(self._filehead)
    
            fullname_len, size, mtime, chksum = fileinfo

            fullname = self.itarobj.read(fullname_len).decode()

            """
            if not self.__chksum(chksum):
                raise ItarChksumError("{} chksum error.".format(join(prefix,name)))
            """
            self.stream_put.put((fullname, size, mtime, chksum)) # fileinfo is tuple
            
            flag = True
            while flag:
    
                if size <= buf:
                    data = self.itarobj.read(size)
                    flag = False
                else:
                    data = self.itarobj.read(buf)
                    size -= len(data)
                        
                self.stream_put.put(data) # data is byte
    
            self.stream_put.put(FILEISDONE)

        self.stream_put.put(ISDONE)
        self.itar_close()


