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
from hashlib import sha256
from binascii import b2a_hex
from functools import partial
from threading import Thread

from os.path import (
                    split, 
                    join, 
                    isfile, 
                    isdir, 
                    exists, 
                    abspath, 
                    islink
                )

from struct import (
                    Struct, 
                    pack, 
                    unpack
                )

from ctypes import CDLL
from ctypes.util import find_library
from ctypes import (
                    c_char_p, 
                    c_int, 
                    c_long, 
                    byref, 
                    create_string_buffer, 
                    c_void_p
                )

"""
# 这玩意的加密速度太慢了。
# 改用openssl，libctypro.so C库，速度提升到230M/s。
try:
    from Crypto.Cipher import AES
except ModuleNotFoundError:
    print("请运行pip install pycrypto 以安装依赖")
    sys.exit(2)
"""

ENCRYPTO = 1  # 加密
DECRYPTO = 0  # 解密

FILE_VERSION = 0x01

version = "v1.1.0"


def getlogger(level=logging.INFO):
    fmt = logging.Formatter(
        "%(asctime)s %(filename)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    logger = logging.getLogger("AES")
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
    """
    对称加密和解密的流程类似，一般有以下几个步骤：

    1. 生成一个记录加密（解密）上下文信息的EVP_CIPHER_CTX对象
    2. 初始化加密（解密）算法，在这一步指定算法和密钥
    3. 加密（解密）数据
    4. 处理尾部数据，结束加密（解密）
    5. 清空并释放加密（解密）上下文对象，清空其他敏感信息
    其中使用的函数以及其他一些相关函数如下：

    1. 创建新加密上下文EVP_CIPHER_CTX对象, 并将其作为返回值返回:
        EVP_CIPHER_CTX *EVP_CIPHER_CTX_new(void)
    
    2. 清除并释放加密上下文对象(防止数据泄露)，参数为需要释放的EVP_CIPHER_CTX对象，在所有加密操作结束后调用该函数:
        void EVP_CIPHER_CTX_free(EVP_CIPHER_CTX *ctx)

    3. 目前不是很清楚具体作用，可能是重置一个EVP_CIPHER_CTX对象从而可以循环利用避免不必要的内存释放和分配吧:
        int EVP_CIPHER_CTX_reset(EVP_CIPHER_CTX *ctx)

    4. 加解密初始化操作

        4.1. 执行加密初始化
        int EVP_EncryptInit_ex(EVP_CIPHER_CTX *ctx, const EVP_CIPHER *type, ENGINE *impl, const unsigned char *key, const unsigned char *iv)
        返回值为1表示成功，0表示失败，可以使用上述错误处理中的函数打印错误信息

        参数	描述
        ctx	    加密上下文对象
        type	加密算法类型，在openssl/evp.h中定义了许多以算法命名的函数, 这些函数的返回值作为此参数使用，比如EVP_aes_256_cbc()
        impl	利用硬件加密的接口，本文不讨论，设置为NULL
        key	    用于加密的密钥
        iv	    某些加密模式如cbc需要使用的初始化向量，如果加密模式不需要可以设置为NULL

        4.2. 执行解密初始化
        int EVP_DecryptInit_ex(EVP_CIPHER_CTX *ctx, const EVP_CIPHER *type, ENGINE *impl, const unsigned char *key, const unsigned char *iv)
        该函数对解密操作进行初始化，参数与返回值上述加密初始化函数描述相同

    5. 执行加解密操作
        注意, 输出缓冲区的长度需要比输入缓冲区大一个加密块，否则会出现错误。
        注意，如果出现overlap错误，请检查输入和输出缓冲区是否分离，以及是否其长度是否满足第一个注意事项

        5.1. 加密
        int EVP_DecryptUpdate(EVP_CIPHER_CTX *ctx, unsigned char *out, int *outl, const unsigned char *in, int inl)
        返回值为1表示成功，返回值为0表示失败

        参数	描述
        ctx	    加密上下文对象
        out	    保存输出结果（密文）的缓冲区
        outl	接收输出结果长度的指针
        in	    包含输入数据（明文）的缓冲区
        inl	    输入数据的长度

        5.2. 解密
        int EVP_DecryptUpdate(EVP_CIPHER_CTX *ctx, unsigned char *out, int *outl, const unsigned char *in, int inl)
        执行解密的函数，参数和返回值和上述加密函数类似，只需要注意输入和输出不要混淆


    6. 加解密尾部数据处理

        6.1. 加密
        int EVP_EncryptFinal_ex(EVP_CIPHER_CTX *ctx, unsigned char *out, int *outl)
        返回值为1表示成功，0表示失败。

        该函数处理加密结果的尾部数据（比如填充段块），还可能输出一些密文数据，参数描述如下：
        参数	描述
        ctx	    加密上下文对象
        out	    保存输出结果（密文）的缓冲区（注意这个指针要指向之前已经保存的加密数据的尾部）
        outl	接收输出结果长度的指针

        6.2. 解密
        int EVP_DecryptFinal_ex(EVP_CIPHER_CTX *ctx, unsigned char *outm, int *outl)
        该函数处理解密结果的尾部数据，还可能输出一些明文数据，参数和返回值同上述加密尾部数据处理的函数类似，注意这个函数输出的是明文即可

    7. 资源释放
        在加解密操作完成后，对可能的密码缓冲区的清空，以及释放上下文对象，一般使用上下文处理中的
        void EVP_CIPHER_CTX_free(EVP_CIPHER_CTX *ctx)
        
    8. 口令生成密钥(key derivation)
        有时候我们需要使用口令来生成加密密钥，openssl推荐使用PBKDF2算法来进行这个操作，使用到的函数如下。

        int PKCS5_PBKDF2_HMAC(const char *pass, int passlen,
                   const unsigned char *salt, int saltlen, int iter,
                   const EVP_MD *digest,
                   int keylen, unsigned char *out);
        返回值为1表示成功，0表示失败。

        该函数使用PKKDF2算法利用口令生成指定长度的密钥，其参数描述如下：
            参数	描述
            pass	用于生成密钥的口令
            passlen	口令的长度
            salt	用于生成密钥的盐值(建议4字节以上)，当然也可以设置为NULL表示不使用
            saltlen	盐值的长度，如果不使用则为0
            iter	迭代次数（openssl建议设置到1000以上，用于增加暴力破解的难度）
            digest	单向hash函数，在openssl/evp.h中定义了许多以算法命名的函数, 这些函数的返回值作为此参数使用，比如EVP_sha256()
            keylen	输出的密钥的长度
            out	    保存输出的密钥的缓冲区

    """

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

    #def __rand_bytes(self, length):
    #    if not self.loaded:
    #        self.__load_openssl()
    #    self.buf = create_string_buffer(length)
    #    r = self.libcrypto.RAND_bytes(self.buf, length)
    #    if r <= 0:
    #        raise Exception('RAND_bytes return error')
    #    return self.buf.raw

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
                    logging.warning("can't find symbol {} in {}".format(
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
        logger.debug("set file header {}".format(fp.name))
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
                                    epilog="""%(prog)s {}
                                    https://github.com/calllivecn/mytools""".format(version)
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
        aes = OpenSSLCrypto("aes-256-cfb", key, header.iv, ENCRYPTO)
        # aes = OpenSSLCrypto("aes-256-cfb1", key, header.iv, ENCRYPTO) # 这个好慢？？？
        #aes = OpenSSLCrypto("aes-256-cfb8", key, header.iv, ENCRYPTO)

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
        aes = OpenSSLCrypto("aes-256-cfb", key, iv, DECRYPTO)
        # aes = OpenSSLCrypto("aes-256-cfb1", key, iv, DECRYPTO) # 这个好慢？？？
        #aes = OpenSSLCrypto("aes-256-cfb8", key, iv, DECRYPTO)

        for data in iter(partial(in_stream.read, block), b""):
            #de_data = aes.decrypt(data)
            de_data = aes.update(data)
            out_stream.write(de_data)

        in_stream.close()

        out_stream.close()


if __name__ == "__main__":
    main()
