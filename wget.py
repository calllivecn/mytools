#!/usr/bin/env python3
# coding=utf-8
# date 2020-09-15 09:32:34
# author calllivecn <c-all@qq.com>

"""
之后可以 加上分段下载（断点续传）
"""


import sys
import time
import hashlib
from urllib import request
from functools import partial
from threading import (
    Thread, 
    Lock,
    )

class Progress:

    def __init__(self):

        self._lock = Lock()
        self._isEnd = False

        self.th = Thread(target=self.__progress, daemon=True)
        #self.th = Thread(target=self.__progress)
        self.th.start()
    
    def over(self):
        with self._lock:
            self._isEnd = True
    
    def __progress(self):

        while not self.__is_end():
            for c in ["-", "\\", "|", "/"]:
                print(c*10, end="\r", file=sys.stderr)
                time.sleep(0.2)
        #print("进度线程是正常结束的~")

    def __is_end(self):
        with self._lock:
            return self._isEnd


class HashAlgError(Exception):
    pass

class Wget:

    HASH = ("md5", "sha1", "sha224", "sha256", "sha384", "sha512", "blake2b")

    def __init__(self, shafunc=set()):
        self.shafuncnames = sorted(shafunc)

        self.shafuncs = []

        # 是否计算hash值
        if len(shafunc) == 0:
            self.sha = False
        else:
            self.sha = True

        # 需要计算的hash函数
        for funcname in self.shafuncnames:
            if funcname in self.HASH:
                self.shafuncs.append(getattr(hashlib, funcname)())
            else:
                raise HashAlgError(f"只支持 {self.HASH} 算法")


    def update(self, data):
        for func in self.shafuncs:
            func.update(data)
    
    def print(self):
        for func in self.shafuncs:
            print(f"{func.name}: {func.hexdigest()}", file=sys.stderr)


    def wget(self, savepath, url):
        block = 1<<14 # 16k

        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"}
        req = request.Request(url, headers=headers)
        response = request.urlopen(req, timeout=15)

        if savepath == "-":
            for data in iter(partial(response.read, block), b""):
                sys.stdout.buffer.write(data)
                if self.sha:
                    self.update(data)
        else:
            with open(savepath, "wb") as f:
                for data in iter(partial(response.read, block), b""):
                    f.write(data)
                    if self.sha:
                        self.update(data)
        self.print()


def main():
    import argparse

    parse = argparse.ArgumentParser(usage="%(prog)s [optional] <url>")

    parse.add_argument("-o", default="-", help="保存文件名")
    parse.add_argument("--md5", action="store_true", help="下载同时计算 md5")
    parse.add_argument("--sha1", action="store_true", help="下载同时计算 sha1")
    parse.add_argument("--sha224", action="store_true", help="下载同时计算 sha224")
    parse.add_argument("--sha256", action="store_true", help="下载同时计算 sha256")
    parse.add_argument("--sha384", action="store_true", help="下载同时计算 sha384")
    parse.add_argument("--sha512", action="store_true", help="下载同时计算 sha512")
    parse.add_argument("--blake2b", action="store_true", help="下载同时计算 blake2b")
    parse.add_argument("--sha-all", action="store_true", help="下载同时计算以上所有值")
    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    parse.add_argument("url", help="下载链接")

    args = parse.parse_args()

    if args.parse:
        print(args)
        sys.exit(0)

    shafuncs = set()

    if args.md5:
        shafuncs |= {"md5"}

    if args.sha1:
        shafuncs |= {"sha1"}

    if args.sha224:
        shafuncs |= {"sha224"}

    if args.sha256:
        shafuncs |= {"sha256"}

    if args.sha384:
        shafuncs |= {"sha384"}

    if args.sha512:
        shafuncs |= {"sha512"}
    
    if args.blake2b:
        shafuncs |= {"blake2b"}
    
    if args.sha_all:
        shafuncs |= set(Wget.HASH)

    w = Wget(shafuncs)

    p = Progress()
    w.wget(args.o, args.url)
    p.over()

if __name__ == "__main__":
    main()
