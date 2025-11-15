#!/usr/bin/env python3
# coding=utf-8
# date 2018-04-08 06:00:42
# date 2025-11-14
# author calllivecn <calllivecn@outlook.com>

import os
import sys
import getpass
import logging
import argparse

from struct import Struct
from pathlib import Path
from binascii import b2a_hex
from hashlib import sha256, pbkdf2_hmac
from contextlib import contextmanager

from typing import (
    cast,
    Protocol,
)

from cryptography.hazmat.primitives.kdf import (
    pbkdf2,
    argon2,
)
from cryptography.hazmat.primitives.ciphers import (
    Cipher,
    algorithms,
    modes,
)



VERSION = "v1.5.0"

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


class ReadWrite(Protocol):
    def read(self, size: int) -> bytes: ...
    def write(self, data: bytes) -> int: ...
    def close(self) -> None: ...

@contextmanager
def open_stream(path: str, mode: str):
    """
    通用打开流：path 为 "-" 时返回标准输入/输出的 buffer，否则打开文件。
    只在实际打开文件时负责关闭流；标准流不关闭。
    """
    if path == "-":
        if "r" in mode:
            yield cast(ReadWrite, sys.stdin.buffer)
        elif "w" in mode:
            yield cast(ReadWrite, sys.stdout.buffer)
        else:
            raise ValueError("unsupported mode for std stream")
    else:
        f = open(path, mode)
        try:
            yield cast(ReadWrite, f)
        finally:
            f.close()

class FileFormat:
    """
    文件格式类，支持流式数据的编码和解码。
    """

    HEADER_STRUCT = Struct("!HH16s32s")  # version, prompt_len, iv, salt

    def __init__(self, file_version=0x0002):
        self.version = file_version
        self.prompt_len = 0
        self.iv = os.urandom(16)
        self.salt = os.urandom(32)
        self.prompt = b""

    def set_prompt(self, prompt=""):
        """
        设置密码提示信息。
        """
        prompt = prompt.encode("utf-8")
        if len(prompt) > 65535:
            raise PromptTooLong("你给的密码提示信息太长。(需要 <=65535字节 或 <=21845中文字符)")
        self.prompt = prompt
        self.prompt_len = len(prompt)

    def encode(self):
        """
        将文件头编码为二进制数据。
        """
        header = self.HEADER_STRUCT.pack(
            self.version,
            self.prompt_len,
            self.iv,
            self.salt
        )
        return header + self.prompt

    @classmethod
    def decode(cls, data):
        """
        从二进制数据解码为 FileFormat 实例。
        """
        header_size = cls.HEADER_STRUCT.size
        header_data = data[:header_size]
        prompt_data = data[header_size:]

        version, prompt_len, iv, salt = cls.HEADER_STRUCT.unpack(header_data)
        prompt = prompt_data[:prompt_len].decode("utf-8")

        instance = cls(file_version=version)
        instance.iv = iv
        instance.salt = salt
        instance.prompt = prompt.encode("utf-8")
        instance.prompt_len = prompt_len

        return instance

    def write_to_stream(self, stream: ReadWrite):
        """
        将文件头写入流中。
        """
        header = self.HEADER_STRUCT.pack(
            self.version,
            self.prompt_len,
            self.iv,
            self.salt
        )
        stream.write(header)
        stream.write(self.prompt)

    @classmethod
    def read_from_stream(cls, stream: ReadWrite):
        """
        从流中读取文件头并返回 FileFormat 实例。
        """
        header_size = cls.HEADER_STRUCT.size
        header_data = stream.read(header_size)
        if len(header_data) < header_size:
            raise ValueError("文件头数据不足，无法解析。")

        version, prompt_len, iv, salt = cls.HEADER_STRUCT.unpack(header_data)
        prompt = stream.read(prompt_len)
        if len(prompt) < prompt_len:
            raise ValueError("密码提示信息数据不足，无法解析。")

        instance = cls(file_version=version)
        instance.iv = iv
        instance.salt = salt
        instance.prompt = prompt
        instance.prompt_len = prompt_len

        return instance

    def __repr__(self):
        return (
            f"FileFormat(version={self.version}, prompt_len={self.prompt_len}, "
            f"iv={self.iv.hex()}, salt={self.salt.hex()}, prompt={self.prompt.decode('utf-8')})"
        )
    
    def __str__(self):
        return self.__repr__()


def isregulerfile(filename: str) -> Path|str:
    if filename == "-":
        return "-"

    f = Path(filename)
    if f.is_file():
        return f
    else:
        raise argparse.ArgumentTypeError("is not a reguler file")


def notexists(filename: str) -> Path|str:
    if filename == "-":
        return "-"
    
    f = Path(filename)
    
    if f.exists():
        raise argparse.ArgumentTypeError(f"already file {filename}")
    else:
        return f


def isstring(key: str) -> str:
    if isinstance(key, str):
        return key
    else:
        raise argparse.ArgumentTypeError("password require is string")


def fileinfo(filename):
    """
    读取并打印文件的头部信息。
    """
    try:
        with open(filename, "rb") as fp:
            # 使用 FileFormat 类解析文件头
            header = FileFormat.read_from_stream(cast(ReadWrite,fp))

        # 打印文件头信息
        print(f"File Version: {hex(header.version)}")
        print(f"IV: {b2a_hex(header.iv).decode()}")
        print(f"Salt: {b2a_hex(header.salt).decode()}")
        print(f"Password Prompt: {header.prompt.decode('utf-8')}")

    except ValueError as e:
        logger.error(f"无法解析文件头：{e}")
        raise e
    except FileNotFoundError as e:
        logger.error(f"文件未找到：{filename}")
        raise e
    except Exception as e:
        logger.error(f"读取文件信息时发生错误：{e}")
        raise e


def key_Argon2id(self, salt: bytes, iterations=13, memory_cost=65536, lanes=4):
    """
    v1.3 (version code: 0x0003) date: 2025-11-14
    memory_cost: KB 65536KB = 64 MB
    leans: 并行度(使用几个线程)
    参考: https://cryptography.io/en/latest/hazmat/primitives/kdf/
    """
    kdf = argon2.Argon2id(salt=salt, length=32, iterations=iterations, memory_cost=memory_cost, lanes=lanes)
    return kdf.derive(self.password)


class AESCrypto:
    """
    AES 加密/解密类，支持流式数据处理。
    """

    def __init__(self, password: bytes):

        self.password = password

    def _derive_key(self, salt: bytes) -> bytes:
        """
        现在 v1.2 (version code: 0x02)使用密钥派生。date: 2021-11-07
        使用 PBKDF2 派生密钥。修改时间：2025-04-24
        """
        return pbkdf2_hmac("sha256", self.password, salt, 200000)

    def _legacy_key(self, salt: bytes) -> bytes:
        """
        旧版本的密钥派生方式。
        现在 v1.0 (version code: 0x01)使用密钥派生。
        """
        return sha256(salt + self.password).digest()

    def encrypt(self, in_stream: ReadWrite, out_stream: ReadWrite, prompt=None):
        """
        加密数据流。
        """
        # 创建文件头
        header = FileFormat()
        header.set_prompt(prompt or "")
        header.write_to_stream(out_stream)

        # 派生密钥
        key = self._derive_key(header.salt)

        # 初始化 AES 加密器
        cipher = Cipher(algorithms.AES(key), modes.CFB(header.iv))
        aes = cipher.encryptor()

        # 加密数据块
        while (data := in_stream.read(BLOCK)) != b"":
            out_stream.write(aes.update(data))
        out_stream.write(aes.finalize())

    def decrypt(self, in_stream: ReadWrite, out_stream: ReadWrite):
        """
        解密数据流。
        """
        # 读取文件头
        header = FileFormat.read_from_stream(in_stream)

        # 根据文件版本派生密钥
        if header.version == 0x02:
            key = self._derive_key(header.salt)
        elif header.version == 0x01:
            key = self._legacy_key(header.salt)
        else:
            logger.error(f"不支持的文件版本：{header.version}")
            sys.exit(2)

        # 初始化 AES 解密器
        cipher = Cipher(algorithms.AES(key), modes.CFB(header.iv))
        aes = cipher.decryptor()

        # 解密数据块
        while (data := in_stream.read(BLOCK)) != b"":
            out_stream.write(aes.update(data))
        out_stream.write(aes.finalize())


def main():
    parse = argparse.ArgumentParser(usage="Usage: %(prog)s [-d ] [-p prompt] [-I filename] [-k password] [-v] [-i in_filename|-] [-o out_filename|-]",
                                    description="AES系列算法加密",
                                    epilog=f"""%(prog)s {VERSION} https://github.com/calllivecn/mytools"""
                                    )

    groups = parse.add_mutually_exclusive_group()
    groups.add_argument("-d", action="store_true", help="加密/解密(不指定则为加密)")
    groups.add_argument("-p", action="store", help="提示信息(需要 <=65535字节 或 <=21845中文字符)")
    groups.add_argument("-I", action="store", type=isregulerfile, help="查看文件信息")

    parse.add_argument("-k", action="store", type=isstring, help="密码字符串(如果没有指定本参数，则交互式输入密码)")
    parse.add_argument("--key-count", action="count", help="交互式输入密码次数(默认1次)，使用多密码时起用。")
    # date: 2023-04-12
    # 提取 keyfile 文件的，从offset 位置开始的1K内容(从offset位置开始必须要有1K的数据, keyfile文件只使用1~3个为好。)
    # 选择keyfile文件时，在有固定头格式的文件时，最好使用offset.
    # 多个 keyfile 时，offset 也需要指定多个。按顺序对应
    parse.add_argument("--keyfile", action="store", nargs="+", type=isregulerfile, help=argparse.SUPPRESS)
    parse.add_argument("--offset", action="store", nargs="+", type=int, default=[0], help=argparse.SUPPRESS)
    parse.add_argument("--keysize", action="store", type=int, default=1024, help=argparse.SUPPRESS)

    parse.add_argument("-v", action="count", help="增加日志输出详细级别，可以使用多个 -v 参数")

    parse.add_argument("-i", action="store", default="-", type=isregulerfile, help="输入文件")
    parse.add_argument("-o", action="store", default="-", type=notexists, help="输出文件")

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

    """
    使用密码或者 keyfile 进行加密/解密。
    keyfile 可以指定多个，每个 keyfile 读取指定offset 之后的 1K 内容作为密钥的一部分。
    """
    if args.k is None and not args.keyfile:

        if args.d is True:
            password = getpass.getpass("Password:")
        else:
            password = getpass.getpass("Password:")
            password2 = getpass.getpass("Password(again):")
            if password != password2:
                logger.info("password mismatches.")
                sys.exit(2)
            
        key = password.encode("utf-8")
    
    elif args.k is not None:
        key = args.k.encode("utf-8")

    elif args.keyfile:

        # keyfile， offset, keysize 参数必须是一样多
        if len(args.keyfile or []) != len(args.offset or []):
            print("keyfile, offset 参数必须是一样多")
            sys.exit(3) 

        keyfiles = []
        file: Path
        for i, file in enumerate(args.keyfile):
            # keyfile 需要大于 1k
            if (file.stat().st_size - args.offset[i]) < args.keysize:
                print("密钥文件 (keyfile) 在偏移量 (offset) 之后需要大于或等于 keysize 大小")
                sys.exit(3)

            with open(file, "rb") as f:
                f.seek(args.offset[i], os.SEEK_SET)
                keyfiles.append(f.read(args.keysize))
        
        key = b"".join(keyfiles)
    
    else:
        logger.error("无法获取加密/解密密钥。")
        sys.exit(2)


    with open_stream(args.i, "rb") as in_stream, open_stream(args.o, "wb") as out_stream:

        crypto = AESCrypto(key)

        if args.d:
            logger.debug("开始解密...")
            crypto.decrypt(in_stream, out_stream)
        else:
            logger.debug("开始加密...")
            crypto.encrypt(in_stream, out_stream, args.p)


if __name__ == "__main__":
    main()
