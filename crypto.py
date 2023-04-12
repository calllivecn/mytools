#!/usr/bin/env python3
# coding=utf-8
# date 2018-04-08 06:00:42
# author calllivecn <c-all@qq.com>

import os
import sys
import getpass
import logging
import argparse

from struct import Struct
from pathlib import Path
from binascii import b2a_hex
from os.path import isfile, exists
from hashlib import sha256, pbkdf2_hmac


from cryptography.hazmat.primitives.ciphers import (
    Cipher,
    algorithms,
    modes,
)

__VERSION__ = "v1.4.0"


ENCRYPTO = 1  # 加密
DECRYPTO = 0  # 解密


BLOCK = 1 << 20  # 1M 读取文件块大小


def getlogger(level=logging.INFO):
    fmt = logging.Formatter("%(asctime)s %(filename)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    logger = logging.getLogger("AES")
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

    def __init__(self, file_version=0x0002):
        """
        prompt: `str': 密码提示信息
        out_fp: `fp': 类文件对象
        """

        logger.debug("file header format build")
        self.version = file_version  # 2byte
        self.prompt_len = bytes(2)  # 2bytes 提示信息字节长度
        self.iv = os.urandom(16)     # 16byte
        self.salt = os.urandom(32)   # 32byte
        # self.long = bytes(8)        # 8byte 加密后数据部分长度
        # self.sha256 = bytes(32)     # 32byte 加密后数据部分校验和
        self.prompt = bytes()        # 定长，utf-8编码串, 之后填写，可为空
        # 以上就格式顺序

        self.file_fmt = Struct("!HH")

    def setPrompt(self, prompt=""):
        logger.debug("set prompt info")
        prompt = prompt.encode("utf-8")
        self.prompt_len = len(prompt)

        if self.prompt_len > 65535:
            raise PromptTooLong("你给的密码提示信息太长。(需要 <=65535字节 或 <=21845中文字符)")
        else:
            self.prompt = prompt

    def setHeader(self, fp):
        logger.debug(f"set file header {fp.name}")
        logger.debug(f"\nversion: {self.version}\n prompt_len: {self.prompt_len}\n vi: {self.iv}\n salt: {self.salt}\n prompt: {self.prompt}")
        headers = self.file_fmt.pack(self.version, self.prompt_len)
        self.HEAD = headers + self.iv + self.salt + self.prompt
        return fp.write(self.HEAD)

    def getHeader(self, fp):
        logger.debug("get file header")
        file_version, prompt_len = self.file_fmt.unpack(fp.read(4))
        iv = fp.read(16)
        salt = fp.read(32)
        prompt = fp.read(prompt_len)
        logger.debug(f"\nversion: {file_version}\n prompt_len: {prompt_len}\n vi: {iv}\n salt: {salt}\n prompt: {self.prompt}")
        return file_version, prompt_len, iv, salt, prompt.decode("utf-8")


def isregulerfile(filename):
    if isfile(filename) or filename == "-":
        return Path(filename)
    else:
        raise argparse.ArgumentTypeError("is not a reguler file")


def notexists(filename):
    if exists(filename) and filename != "-":
        raise argparse.ArgumentTypeError(f"already file {filename}")
    else:
        return filename


def isstring(key):
    if isinstance(key, str):
        return key
    else:
        raise argparse.ArgumentTypeError("password require is string")



# v1.0 (version code: 0x01) 的做法，密钥没有派生。
def salt_key(password: bytes, salt: bytes):
    key = sha256(salt + password).digest()
    return key


# 现在 v1.2 (version code: 0x02)使用密钥派生。date: 2021-11-07
def key_deriverd(password: bytes, salt: bytes, count=200000):
    # return pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
    return pbkdf2_hmac("sha256", password, salt, count)


def fileinfo(filename):
    header = FileFormat()
    with open(filename, "rb") as fp:
        file_version, prompt_len, iv, salt, prompt = header.getHeader(fp)

    print("File Version: {}(1byte)".format(hex(file_version)))

    print("IV: {}".format(b2a_hex(iv).decode()))

    print("Salt: {}".format(b2a_hex(salt).decode()))

    print("Password Prompt: {}".format(prompt))


def encrypt(in_stream, out_stream, iv: bytes, key: bytes):

    algorithm = algorithms.AES(key)
    cipher = Cipher(algorithm, mode=modes.CFB(iv))
    aes = cipher.encryptor()

    while (data := in_stream.read(BLOCK)) != b"":
        en_data = aes.update(data)
        out_stream.write(en_data)

    out_stream.write(aes.finalize())

    
def decrypt(in_stream, out_stream, iv: bytes, key: bytes):

    algorithm = algorithms.AES(key)
    cipher = Cipher(algorithm, mode=modes.CFB(iv))
    aes = cipher.decryptor()

    while (data := in_stream.read(BLOCK)) != b"":
        de_data = aes.update(data)
        out_stream.write(de_data)
    
    out_stream.write(aes.finalize())



def main():
    parse = argparse.ArgumentParser(usage="Usage: %(prog)s [-d ] [-p prompt] [-I filename] [-k password] [-v] [-i in_filename|-] [-o out_filename|-]",
                                    description="AES 加密",
                                    epilog="""%(prog)s {}
                                    https://github.com/calllivecn/mytools""".format(__VERSION__)
                                    )

    groups = parse.add_mutually_exclusive_group()
    # groups.add_argument("-d", action="store_false", help="decrypto (default: encrypto)")
    groups.add_argument("-d", action="store_true", help="decrypto (default: encrypto)")
    groups.add_argument("-p", action="store", help="password prompt")
    groups.add_argument("-I", action="store", type=isregulerfile, help="AES crypto file")

    parse.add_argument("-k", action="store", type=isstring, help="password")
    # date: 2023-04-12
    # 提取 keyfile 文件的，从offset 位置开始的1K内容(从offset位置开始必须要有1K的数据, keyfile文件只使用1~3个为好。)
    # 选择keyfile文件时，在有固定头格式的文件时，最好使用offset.
    parse.add_argument("--keyfile", action="store", nargs="+", type=isregulerfile, help=argparse.SUPPRESS)
    parse.add_argument("--offset", action="store", nargs="+", type=int, help=argparse.SUPPRESS)

    parse.add_argument("-v", action="count", help="verbose")

    parse.add_argument("-i", action="store", default="-", type=isregulerfile, help="in file")
    parse.add_argument("-o", action="store", default="-", type=notexists, help="out file")

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    

    args = parse.parse_args()

    if args.parse:
        print(args)
        sys.exit(0)


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

        # 加密
        if args.d is False:
            password = getpass.getpass("Password:")
            password2 = getpass.getpass("Password(again):")
            if password != password2:
                logger.info("password mismatches.")
                sys.exit(2)
            
        else:
            password = getpass.getpass("Password:")

    else:
        password = args.k
    
    # 需要在 key_derived 之前转为 bytes
    password = password.encode("utf8")
    keyfiles = [password]

    if args.keyfile:

        # 使用的offset
        if args.offset:
            if len(args.offset) != len(args.keyfile):
                print(f"If an offset is specified, it must be specified for each keyfile.")
                sys.exit(3)

            for i, file in enumerate(args.keyfile):

                # keyfile 需要大于 1k
                if (file.stat().st_size - args.offset[i]) < 1024:
                    print("keyfile needs to be >=1k after offset.")
                    sys.exit(3)

                with open(file, "rb") as f:
                    f.seek(args.offset[i], os.SEEK_SET)
                    keyfiles.append(f.read(1024))
        
        else:
            for file in args.keyfile:

                # keyfile 需要大于 1k
                if file.stat().st_size < 1024:
                    print("keyfile need >= 1k")
                    sys.exit(3)

                with open(file, "rb") as f:
                    keyfiles.append(f.read(1024))
        
    

    if args.i == "-":
        in_stream = sys.stdin.buffer
    else:
        in_stream = open(args.i, "rb")

    if args.o == "-":
        out_stream = sys.stdout.buffer
    else:
        out_stream = open(args.o, "wb")
    


    # 加密
    if args.d is False:

        header = FileFormat()

        if args.p is None:
            header.setPrompt()
        else:
            header.setPrompt(args.p)

        header.setHeader(out_stream)


        # keyfile 处理成 key
        key = key_deriverd(b"".join(keyfiles), header.salt)


        logger.debug("开始加密...")
        encrypt(in_stream, out_stream, header.iv, key)
        in_stream.close()
        out_stream.close()

    # 解密
    else:

        header = FileFormat()
        file_version, prompt_len, iv, salt, prompt = header.getHeader(in_stream)

        if file_version == 0x02:
            # key = key_deriverd(key, salt)
            key = key_deriverd(b"".join(keyfiles), salt)

        elif file_version == 0x01:
            key = salt_key(password, salt)

        else:
            logger.error(f"不支持的文件版本。")
            sys.exit(2)
    

        logger.debug("开始解密...")

        decrypt(in_stream, out_stream, iv, key)

        in_stream.close()
        out_stream.close()


if __name__ == "__main__":
    main()
