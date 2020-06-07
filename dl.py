#!/usr/bin/env python3
# coding=utf-8
# date 2020-05-16 21:47:23
# author calllivecn <c-all@qq.com>

import enum
from urllib import request

class Adjust(enu.Enum):
    UP = 1
    KEEP = 2
    DOWN = 3

class DL:

    Speed = 0
    thread_count = 2
    adjust = Adjust.KEEP

    def __init__(self, url):

        self._url = url


    def __httpdown(self, offset, size):
        req = request.Request(self._url)

        Range = "bytes = "

        req.add_header("Range", )


