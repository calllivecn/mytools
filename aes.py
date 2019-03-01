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
from binascii import b2a_hex
from os.path import split,join,isfile,isdir,exists,abspath,islink
from struct import Struct, pack, unpack
from threading import Thread


try:
    from Crypto.Cipher import AES
except ModuleNotFoundError:
    print("请运行pip install pycrypto 以安装依赖")
    sys.exit(2)

FILE_VERSION = 0x01

def getlogger(level=logging.INFO):
    fmt = logging.Formatter("%(asctime)s %(filename)s:%(lineno)d %(message)s",datefmt="%Y-%m-%d-%H:%M:%S")
    stream = logging.StreamHandler(sys.stderr)
    stream.setFormatter(fmt)
    logger = logging.getLogger("AES--stdout")
    logger.setLevel(level)
    logger.addHandler(stream)
    return logger

logger = getlogger()

class PromptTooLong(Exception):
    pass

class FileFormat:
    """
    写入到文件的文件格式
    """
    
    def __init__(self):
        """
        prompt: `str': 密码提示信息
        out_fp: `fp': 类文件对象
        """

        logger.debug("file header format build")
        self.version = FILE_VERSION  # 2byte
        self.prompt_len = bytes(2)   # 2bytes 提示信息字节长度
        self.iv = os.urandom(16)     # 16byte
        self.salt = os.urandom(32)   # 32byte
        #self.long = bytes(8)        # 8byte 加密后数据部分长度
        #self.sha256 = bytes(32)     # 32byte 加密后数据部分校验和
        self.prompt = bytes()        # 定长，utf-8编码串, 之后填写，可为空
        # 以上就格式顺序

        self.file_fmt = Struct("!HH")

    def setPrompt(self, prompt=""):
        logger.debug("set prompt info")
        prompt = prompt.encode("utf-8")
        self.prompt_len = len(prompt)

        if self.prompt_len > 65536:
            raise PromptTooLong("你给的密码提示信息太长。(需要 <=65536字节 或 <=21845中文字符)")
        else:
            self.prompt = prompt

    def setHeader(self, fp):
        logger.debug(f"set file header {fp}")
        headers = self.file_fmt.pack(self.version, self.prompt_len)
        self.HEAD = headers + self.iv + self.salt + self.prompt
        return fp.write(self.HEAD)

    def getHeader(self, fp):
        logger.debug("get file header")
        file_version, prompt_len = self.file_fmt.unpack(fp.read(4))
        iv = fp.read(16)
        salt = fp.read(32)
        prompt = fp.read(prompt_len)
        return file_version, prompt_len, iv, salt, prompt.decode("utf-8")


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

def fileinfo(filename):
    header = FileFormat()
    with open(filename,"rb") as fp:
        file_version, prompt_len, iv, salt, prompt = header.getHeader(fp)
    
    print("File Version: 0x{}".format(b2a_hex(pack("!H",file_version)).decode()))

    print("IV: {}".format(b2a_hex(iv).decode()))

    print("Salt: {}".format(b2a_hex(salt).decode()))

    print("Password Prompt: {}".format(prompt))


def main():
    parse = argparse.ArgumentParser(usage="Usage: %(prog)s [-d ] [-p prompt] [-I filename] [-k password] [-v] [-i in_filename|-] [-o out_filename|-]",
                                   description="AES 加密",
                                   )
    
    groups = parse.add_mutually_exclusive_group()
    groups.add_argument("-d",action="store_false",help="decrypto (default: encrypto)")
    groups.add_argument("-p",action="store", help="password prompt")
    groups.add_argument("-I",action="store", type=isregulerfile, help="AES crypto file")

    parse.add_argument("-k",action="store", type=isstring, help="password")
    parse.add_argument("-v",action="count", help="verbose")

    parse.add_argument("-i", action="store", default="-", type=isregulerfile, help="in file")
    parse.add_argument("-o",action="store", default="-", type=notexists, help="out file")


    args = parse.parse_args()
    #print(args);#sys.exit(0)

    block = 1<<20 # 1M 读取文件块大小

    if args.I:
        fileinfo(args.I)
        sys.exit(0)

    if args.v == 1:
        logger.setLevel(logging.INFO)
    elif args.v == 2:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if args.k is None:
        if args.d:
            password = getpass.getpass("Password:")
            password2 = getpass.getpass("Password(again):")
            if password != password2:
                print("password mismatches.",file=sys.stderr)
                sys.exit(2)
        else:
            password = getpass.getpass("Password:")
            
    else:
        password = args.k

    if args.i == "-":
        in_stream = sys.stdin.buffer
    else:
        in_stream = open(args.i, "rb")

    if args.o == "-":
        out_stream = sys.stdout.buffer
    else:
        out_stream = open(args.o, "wb")


    if args.d:

        logger.debug("开始加密...")

        header = FileFormat()

        if args.p is None:
            header.setPrompt()
        else:
            header.setPrompt(args.p)

        header.setHeader(out_stream)

        key = salt_key(password, header.salt)
        aes = AES.new(key, AES.MODE_CFB, header.iv)

        data = True
        while data:

            data = in_stream.read(block)

            en_data = aes.encrypt(data)

            out_stream.write(en_data)


        in_stream.close()

        out_stream.close()

    else:
        logger.debug("开始解密...")

        header = FileFormat()

        file_version, prompt_len, iv, salt, prompt = header.getHeader(in_stream)

        key = salt_key(password, salt)
        aes = AES.new(key, AES.MODE_CFB, iv)

        data = True
        while data:

            data = in_stream.read(block)
            de_data = aes.decrypt(data)
            out_stream.write(de_data)
        

        in_stream.close()

        out_stream.close()
        

if __name__ == "__main__":
    main()
