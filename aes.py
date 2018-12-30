#!/usr/bin/env python3
#coding=utf-8
# date 2018-04-08 06:00:42
# author calllivecn <c-all@qq.com>

import argparse
from hashlib import sha256
import os
import sys
import time
from os.path import split,join,isfile,isdir,exists,abspath,islink
from struct import pack, unpack
from threading import Thread

try:
    from Crypto.Cipher import AES
except ModuleNotFoundError:
    print("请运行pip install pycrypto 以安装依赖")
    exit(2)

PROGRAM = sys.argv[0]

FORMAT_VERSION = 1

class PromptTooLong(Exception):
    pass

class StoreFormat:
    """
    写入到文件的文件格式
    """
    
    def __init__(self, prompt, out_fp):
        """
        prompt: `str': 密码提示信息
        out_fp: `fp': 类文件对象
        """

        self.version = FORMAT_VERSION  # 2byte
        self.iv = os.urandom(32)     # 32byte
        self.salt = os.urandom(30)   # 30byte
        self.prompt = bytes(4096)   # 定长，utf-8编码串, 之后填写，可为空
        self.header_len = 2 + 30 + 32 + 8 + 32 + 4096
        # 以上就格式顺序

        self.fill = 0                # 1byte , 放在数据流的最后的

        prompt = prompt.encode("utf-8")
        if len(prompt) > 4096:
            raise PromptTooLong("你给的密码提示信息太长。(utf8编码后>4096字节)")
        else:
            self.prompt = prompt

        FORMAT="!HH"
        headers = pack(FORMAT, 1, slef.prompt_len)

        self.HEAD = headers + self.iv + self.salt + self.prompt

    def overwrite(self):
        pass
    

class AES256:
    """mehtod:
    encrypto() --> block data
    decrypto() --> block data
    
    attribute:
    self.key
    self.key_salt 
    self.iv
    """

    def __init__(self, key, iv):
        """
        key 洒
        """
        self.key = key
        self.iv = iv 
        slef.mode = AES.MODE_CBC

        self.fill = 0

        self.cryptor = AES.new(self.key, self.mode, self.iv)
        
    def encrypt(self, data):
        """
        data: `byte': 由于AES 256加密块为32字节
            当数据结尾加密块不足32字节时，
            填充空字节。
        return: `byte': 加密字节
        """
        data_len = len(data)

        blocks, rema = divmod(data_len, 32)

        if rema == 0:
            return self.cryptor.crypt(data)

        else:
            fill = 32 - rema
            self.fill = fill
            return self.cryptor.encrypt(data + bytes(fill))

    def decrypt(self, data, fill=0):
        """
        data: `byte': 需解密数据
        fill: `int': 0~31 number
        return: `byte':
        """

        # if fill != 0 说明这是最后一块，且有填充字节。
        if fill != 0:
            return self.cryptor.decrypt(data)
        else:
            data = self.cryptor.decrypt(data)
            return data[0:-fill]


    def finish(self):
        pass


    def encode_header(self):
        pass


    def decode_header(self):
        pass

class 
