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
                print(c*10, end="\r")
                time.sleep(0.2)
        #print("进度线程是正常结束的~")

    def __is_end(self):
        with self._lock:
            return self._isEnd


def wget(savepath, url):
    block = 1<<14 # 16k

    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"}
    req = request.Request(url, headers=headers)
    response = request.urlopen(req, timeout=15)

    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    sha384 = hashlib.sha384()
    sha512 = hashlib.sha512()
    
    progress = Progress()

    with open(savepath, "wb") as f:
        for data in iter(partial(response.read, block), b""):
            f.write(data)
            md5.update(data)
            sha256.update(data)
            sha384.update(data)
            sha512.update(data)
    
    progress.over()

    print("md5: ", md5.hexdigest())
    print("sh256: ", sha256.hexdigest())
    print("sh384: ", sha384.hexdigest())
    print("sh512: ", sha512.hexdigest())
    
USAGE="""\
Usage: {} <文件保存路径> <url>
""".format(sys.argv[0])

def main():
    if len(sys.argv) != 3:
        print(USAGE)
        sys.exit(1)
    

    wget(sys.argv[1], sys.argv[2])



if __name__ == "__main__":
    main()
