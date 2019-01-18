#!/usr/bin/env python3
#coding=utf-8
# date 2018-04-08 06:00:42
# author calllivecn <c-all@qq.com>

import os
import sys
import time
import getpass
import logging
import argparse
from hashlib import sha256
from os.path import split,join,isfile,isdir,exists,abspath,islink
from struct import Struct, pack, unpack
from threading import Thread

__all__ = ["AES256", "FileFormat"]

try:
    from Crypto.Cipher import AES
except ModuleNotFoundError:
    print("请运行pip install pycrypto 以安装依赖")
    sys.exit(2)

FILE_VERSION = 1

def getlogger(level=logging.INFO):
    fmt = logging.Formatter("%(asctime)s %(filename)s:%(lineno)d %(message)s",datefmt="%Y-%m-%d-%H:%M:%S")
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    logger = logging.getLogger("AES--stdout")
    logger.setLevel(level)
    logger.addHandler(stream)
    return logger

logger = getlogger()
class PromptTooLong(Exception): pass

class FileFormat:
    """
    写入到文件的文件格式
    """
    
    def __init__(self):
        """
        prompt: `str': 密码提示信息
        out_fp: `fp': 类文件对象
        """

        logger.debug("files format build")
        self.version = FILE_VERSION  # 2byte
        self.prompt_len = bytes(2)   # 2bytes 提示信息字节长度
        self.iv = os.urandom(16)     # 16byte
        self.salt = os.urandom(32)   # 32byte
        #self.long = bytes(8)        # 8byte 加密后数据部分长度
        #self.sha256 = bytes(32)     # 32byte 加密后数据部分校验和
        self.prompt = bytes()        # 定长，utf-8编码串, 之后填写，可为空
        # 以上就格式顺序
        self.fill = 0                # 1byte , (最后一块的填充字节数)放在数据流的最后

        self.file_fmt = Struct("!HH")

    def setPrompt(self, prompt=""):
        logger.debug("set prompt info")
        prompt = prompt.encode("utf-8")
        self.prompt_len = len(prompt)

        if self.prompt_len > 65536:
            raise PromptTooLong("你给的密码提示信息太长。(需要<=21845中文字符)")
        else:
            self.prompt = prompt

    def setHeader(self, fp):
        logger.debug(f"set file header {fp}")
        headers = self.file_fmt.pack(self.version, self.prompt_len)
        self.HEAD = headers + self.iv + self.salt + self.prompt
        return os.write(fp, self.HEAD)

    def getHeader(self, fp):
        logger.debug("get file header")
        file_version, prompt_len = self.file_fmt.unpack(os.read(fp,4))
        iv = os.read(fp, 16)
        salt = os.read(fp, 32)
        prompt = os.read(fp, prompt_len)
        return file_version, prompt_len, iv, salt, prompt

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
        self.mode = AES.MODE_CBC

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


def isregulerfile(filename):
    if isfile(filename) or filename == "-":
        return filename
    else:
        raise argparse.ArgumentTypeError("is not a reguler file")

def notexists(filename):
    if exists(filename) and filename != "-":
        raise argparse.ArgumentTypeError(f"already file {filename}")
    else:
        return filename

def isstring(key):
    if isinstance(key,str):
        return key
    else:
        raise argparse.ArgumentTypeError("password require is string")


def salt_key(password, salt):
    key = sha256(salt + password.encode("utf-8")).digest()
    return key

def main():
    parse = argparse.ArgumentParser(usage="Usage: %(prog)s [-i in_filename|-] [-o out_filename|-] [-I filenme] [-dc]",
                                   description="AES 加密",
                                   )
    parse.add_argument("-i", action="store", default="-", type=isregulerfile, help="in file")
    parse.add_argument("-o",action="store", default="-", type=notexists, help="out file")
    
    groups = parse.add_mutually_exclusive_group()
    groups.add_argument("-p",action="store", help="password prompt")
    groups.add_argument("-d",action="store_false",help="decrypto (default: encrypto)")

    parse.add_argument("-I",action="store", type=isregulerfile, help="AES crypto file")

    parse.add_argument("-k",action="store", type=isstring, help="password")
    parse.add_argument("-v",action="count", help="verbose")

    args = parse.parse_args()
    print(args);#sys.exit(0)

    block = 1<<16 # 64k 块大小

    if args.v == 1:
        logger.setLevel(logging.INFO)
    elif args.v == 2:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if args.k is None:
        password = getpass.getpass()
    else:
        password = args.k

    if args.i == "-":
        in_stream = sys.stdin.fileno()
    else:
        in_stream = open(args.i, "rb").fileno()

    if args.o == "-":
        out_stream = sys.stdout.fileno()
    else:
        out_stream = open(args.o, "wb").fileno()


    if args.d:

        header = FileFormat()

        if args.p is None:
            header.setPrompt()
        else:
            header.setPrompt(args.p)

        header.setHeader(out_stream)

        key = salt_key(password, header.salt)
        aes = AES256(key, header.iv)

        #data = True
        data = os.read(in_stream, block)

        while data:

            en_data = aes.encrypt(data)

            os.write(out_stream, en_data)

            data = os.read(in_stream, block)

        
        os.write(out_stream, pack("!B", aes.fill))

        os.close(in_stream)

        os.close(out_stream)

    else:

        header = FileFormat()
        file_version, prompt_len, iv, salt, prompt = header.getHeader(in_stream)

        prompt = os.read(in_stream, prompt)

        aes = AES256(key, iv)

        #data = True
        data = os.read(in_stream, block)

        while data:

            data_len, fill = divmod(len(data),32)

            en_data = aes.decrypt(data, fill)

            out_stream.write(en_data)

            data = in_stream.read(block)

        
        os.write(out_stream, pack("!B",fill))

        os.close(in_stream)

        os.close(out_stream)
        

if __name__ == "__main__":
    main()
