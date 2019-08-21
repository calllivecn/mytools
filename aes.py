#!/usr/bin/env python3
# coding=utf-8
# date 2018-04-08 06:00:42
# author calllivecn <c-all@qq.com>

import os
import sys
import time
import getpass
import logging
import argparse

import glob
import random

from hashlib import sha256
from binascii import b2a_hex
from functools import partial
from os.path import split, join, isfile, isdir, exists, abspath, islink
from struct import Struct, pack, unpack
from threading import Thread

from ctypes import CDLL
from ctypes import c_char_p, c_int, c_long, byref, create_string_buffer, c_void_p
from ctypes.util import find_library

"""
try:
    from Crypto.Cipher import AES
except ModuleNotFoundError:
    print("请运行pip install pycrypto 以安装依赖")
    sys.exit(2)
"""

CIPHER = 1  # 加密
DECIPHER = 0  # 解密

FILE_VERSION = 0x01


def getlogger(level=logging.INFO):
    fmt = logging.Formatter(
        "%(asctime)s %(filename)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    logger = logging.Logger("AES--stdout")
    logger.setLevel(level)
    logger.addHandler(stream)
    return logger


logger = getlogger()


class PromptTooLong(Exception):
    pass


####################################
#
# 加载openssl函数库 begin
#
##################################


# 加密类
class OpenSSLCrypto:
    ciphers = {
        'aes-128-cbc': (16, 16),
        'aes-192-cbc': (24, 16),
        'aes-256-cbc': (32, 16),
        'aes-128-cfb': (16, 16),
        'aes-192-cfb': (24, 16),
        'aes-256-cfb': (32, 16),
        'aes-128-ofb': (16, 16),
        'aes-192-ofb': (24, 16),
        'aes-256-ofb': (32, 16),
        'aes-128-ctr': (16, 16),
        'aes-192-ctr': (24, 16),
        'aes-256-ctr': (32, 16),
        'aes-128-cfb8': (16, 16),
        'aes-192-cfb8': (24, 16),
        'aes-256-cfb8': (32, 16),
        'aes-128-cfb1': (16, 16),
        'aes-192-cfb1': (24, 16),
        'aes-256-cfb1': (32, 16),
        'bf-cfb': (16, 8),
        'camellia-128-cfb': (16, 16),
        'camellia-192-cfb': (24, 16),
        'camellia-256-cfb': (32, 16),
        'cast5-cfb': (16, 8),
        'des-cfb': (8, 8),
        'idea-cfb': (16, 8),
        'rc2-cfb': (16, 8),
        'rc4': (16, 0),
        'seed-cfb': (16, 16),
    }

    def __init__(self, cipher_name, key, iv, op):
        self.libcrypto = None
        self.loaded = False
        self.buF = b''
        self.buf_size = 8192  # 1<<13, 8k size

        self._ctx = None

        if not self.loaded:
            self.__load_openssl()
        cipher = self.libcrypto.EVP_get_cipherbyname(
            cipher_name.encode("utf-8"))
        if not cipher:
            cipher = self.__load_cipher(cipher_name)
        if not cipher:
            raise Exception(
                'cipher {} not found in libcrypto'.format(cipher_name))
        key_ptr = c_char_p(key)
        iv_ptr = c_char_p(iv)
        self._ctx = self.libcrypto.EVP_CIPHER_CTX_new()
        if not self._ctx:
            raise Exception('can not create cipher context')
        r = self.libcrypto.EVP_CipherInit_ex(self._ctx, cipher, None,
                                             key_ptr, iv_ptr, c_int(op))
        if not r:
            self.__clean()
            raise Exception('can not initialize cipher context')

    def update(self, data):

        cipher_out_len = c_long(0)
        l = len(data)
        if self.buf_size < l:
            self.buf_size = l * 2
            self.buf = create_string_buffer(self.buf_size)
        self.libcrypto.EVP_CipherUpdate(self._ctx, byref(self.buf),
                                        byref(cipher_out_len), c_char_p(data), l)
        # self.buf is copied to a str object when we access self.buf.raw
        return self.buf.raw[:cipher_out_len.value]

    def __load_cipher(self, cipher_name):
        func_name = 'EVP_' + cipher_name.replace('-', '_')
        cipher = getattr(self.libcrypto, func_name, None)
        if cipher:
            cipher.restype = c_void_p
            return cipher()
        return None

    def __rand_bytes(self, length):
        if not self.loaded:
            self.__load_openssl()
        self.buf = create_string_buffer(length)
        r = self.libcrypto.RAND_bytes(self.buf, length)
        if r <= 0:
            raise Exception('RAND_bytes return error')
        return self.buf.raw

    def __find_library_nt(self, name):
        # modified from ctypes.util
        # ctypes.util.find_library just returns first result he found
        # but we want to try them all
        # because on Windows, users may have both 32bit and 64bit version installed
        results = []
        for directory in os.environ['PATH'].split(os.pathsep):
            fname = join(directory, name)
            if isfile(fname):
                results.append(fname)
            if fname.lower().endswith(".dll"):
                continue
            fname = fname + ".dll"
            if isfile(fname):
                results.append(fname)
        return results

    def __find_library(self, possible_lib_names, search_symbol, library_name):
        # move to file head.
        #import ctypes.util
        #from ctypes import CDLL

        paths = []

        if type(possible_lib_names) not in (list, tuple):
            possible_lib_names = [possible_lib_names]

        lib_names = []
        for lib_name in possible_lib_names:
            lib_names.append(lib_name)
            lib_names.append('lib' + lib_name)

        for name in lib_names:
            if os.name == "nt":
                paths.extend(self.__find_library_nt(name))
            else:
                path = find_library(name)
                if path:
                    paths.append(path)

        if not paths:
            # We may get here when find_library fails because, for example,
            # the user does not have sufficient privileges to access those
            # tools underlying find_library on linux.

            # move to file head.
            #import glob

            for name in lib_names:
                patterns = [
                    '/usr/local/lib*/lib{}.*'.format(name),
                    '/usr/lib*/lib{}.*'.format(name),
                    'lib{}.*'.format(name),
                    '{}.dll'.format(name)]

                for pat in patterns:
                    files = glob.glob(pat)
                    if files:
                        paths.extend(files)
        for path in paths:
            try:
                lib = CDLL(path)
                if hasattr(lib, search_symbol):
                    logging.info('loading {} from {}'.format(
                        library_name, path))
                    return lib
                else:
                    logging.warn("can't find symbol {} in {}".format(
                        search_symbol, path))
            except Exception as e:
                if path == paths[-1]:
                    raise e
        return None

    def __load_openssl(self):

        self.libcrypto = self.__find_library(('crypto', 'eay32'),
                                             'EVP_get_cipherbyname',
                                             'libcrypto')
        if self.libcrypto is None:
            raise Exception('libcrypto(OpenSSL) not found')

        self.libcrypto.EVP_get_cipherbyname.restype = c_void_p
        self.libcrypto.EVP_CIPHER_CTX_new.restype = c_void_p

        self.libcrypto.EVP_CipherInit_ex.argtypes = (c_void_p, c_void_p, c_char_p,
                                                     c_char_p, c_char_p, c_int)

        self.libcrypto.EVP_CipherUpdate.argtypes = (c_void_p, c_void_p, c_void_p,
                                                    c_char_p, c_int)

        if hasattr(self.libcrypto, "EVP_CIPHER_CTX_cleanup"):
            self.libcrypto.EVP_CIPHER_CTX_cleanup.argtypes = (c_void_p,)
        else:
            self.libcrypto.EVP_CIPHER_CTX_reset.argtypes = (c_void_p,)
        self.libcrypto.EVP_CIPHER_CTX_free.argtypes = (c_void_p,)

        self.libcrypto.RAND_bytes.restype = c_int
        self.libcrypto.RAND_bytes.argtypes = (c_void_p, c_int)

        if hasattr(self.libcrypto, 'OpenSSL_add_all_ciphers'):
            self.libcrypto.OpenSSL_add_all_ciphers()

        self.buf = create_string_buffer(self.buf_size)
        self.loaded = True

    def __del__(self):
        self.__clean()

    def __clean(self):
        if self._ctx:
            if hasattr(self.libcrypto, "EVP_CIPHER_CTX_cleanup"):
                self.libcrypto.EVP_CIPHER_CTX_cleanup(self._ctx)
            else:
                self.libcrypto.EVP_CIPHER_CTX_reset(self._ctx)
            self.libcrypto.EVP_CIPHER_CTX_free(self._ctx)


####################################
#
# 加载openssl函数库 end
#
####################################

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
        # self.long = bytes(8)        # 8byte 加密后数据部分长度
        # self.sha256 = bytes(32)     # 32byte 加密后数据部分校验和
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
        logger.debug("set file header {}".format(fp))
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
        raise argparse.ArgumentTypeError("already file {}".format(filename))
    else:
        return filename


def isstring(key):
    if isinstance(key, str):
        return key
    else:
        raise argparse.ArgumentTypeError("password require is string")


def salt_key(password, salt):
    key = sha256(salt + password.encode("utf-8")).digest()
    return key


def fileinfo(filename):
    header = FileFormat()
    with open(filename, "rb") as fp:
        file_version, prompt_len, iv, salt, prompt = header.getHeader(fp)

    print("File Version: 0x{}".format(
        b2a_hex(pack("!H", file_version)).decode()))

    print("IV: {}".format(b2a_hex(iv).decode()))

    print("Salt: {}".format(b2a_hex(salt).decode()))

    print("Password Prompt: {}".format(prompt))


def main():
    parse = argparse.ArgumentParser(usage="Usage: %(prog)s [-d ] [-p prompt] [-I filename] [-k password] [-v] [-i in_filename|-] [-o out_filename|-]",
                                    description="AES 加密",
                                    )

    groups = parse.add_mutually_exclusive_group()
    groups.add_argument("-d", action="store_false",
                        help="decrypto (default: encrypto)")
    groups.add_argument("-p", action="store", help="password prompt")
    groups.add_argument("-I", action="store",
                        type=isregulerfile, help="AES crypto file")

    parse.add_argument("-k", action="store", type=isstring, help="password")
    parse.add_argument("-v", action="count", help="verbose")

    parse.add_argument("-i", action="store", default="-",
                       type=isregulerfile, help="in file")
    parse.add_argument("-o", action="store", default="-",
                       type=notexists, help="out file")

    args = parse.parse_args()
    # print(args);#sys.exit(0)

    block = 1 << 20  # 1M 读取文件块大小

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
                logger.info("password mismatches.")
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
        #aes = AES.new(key, AES.MODE_CFB, header.iv)
        aes = OpenSSLCrypto("aes-256-cfb", key, header.iv, CIPHER)
        # aes = OpenSSLCrypto("aes-256-cfb1", key, header.iv, CIPHER) # 这个好慢？？？
        #aes = OpenSSLCrypto("aes-256-cfb8", key, header.iv, CIPHER)

        for data in iter(partial(in_stream.read, block), b""):

            #en_data = aes.encrypt(data)
            en_data = aes.update(data)

            out_stream.write(en_data)

        in_stream.close()

        out_stream.close()

    else:
        logger.debug("开始解密...")

        header = FileFormat()

        file_version, prompt_len, iv, salt, prompt = header.getHeader(
            in_stream)

        key = salt_key(password, salt)
        #aes = AES.new(key, AES.MODE_CFB, iv)
        aes = OpenSSLCrypto("aes-256-cfb", key, iv, DECIPHER)
        # aes = OpenSSLCrypto("aes-256-cfb1", key, iv, DECIPHER) # 这个好慢？？？
        #aes = OpenSSLCrypto("aes-256-cfb8", key, iv, DECIPHER)

        for data in iter(partial(in_stream.read, block), b""):
            #de_data = aes.decrypt(data)
            de_data = aes.update(data)
            out_stream.write(de_data)

        in_stream.close()

        out_stream.close()


if __name__ == "__main__":
    main()
