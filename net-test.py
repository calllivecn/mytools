#!/usr/bin/env python3
# coding=utf-8
# date 2020-01-09 00:19:05
# author calllivecn <c-all@qq.com>

import sys
import time
import socket
import threading

import argparse


C=sk.socket(sk.AF_INET,sk.SOCK_DGRAM)

try:
    while True:
        b=input('enter : ')
        if b=='quit':
            break
        print('sendto :',b)
        b=b.encode('utf-8')
        C.sendto(b,('0.0.0.0',6789))
        C.settimeout(15)    
        data,address=C.recvfrom(1024)
        data=data.decode('utf-8')
        print('recvfrom :',data)
    
except:
    print('有接收异常。')
    raise
finally:
        C.close()

print('Client exit.')


import socket as st
import time

BIND=('0.0.0.0',6789)

try:

    S=st.socket(st.AF_INET,st.SOCK_DGRAM)

    S.bind(BIND)

except:
    print('初始化异常！')
    raise

try:
    while True:

        #S.settimeout(5)
        data, address = S.recvfrom(128)
        #data2 = data.decode('utf-8')
        #if data2 == 'quit':
        #    break
        #if data2.split(' ').[0] == 'address :':
        # data2.
        data = 'recv: ' + data.decode('utf-8')
        print('address : ', address, data)
        S.sendto('OK!'.encode('utf-8'), address)
        print('sendto : OK done.')

except KeyboardInterrupt:
    pass

finally:
    S.close()


def main():
    parse = argparse.ArgumentParser(usage="Usage: %(prog)s [-tu] [-Tc] [-s <package size>] [host]",
            description="test network",
            epilog="author: calllivecn <https://github.com/calllivecn/mytools>"
            )
    tcp_udp = parse.add_mutually_exclusive_group()
    tcp_udp.add_argument("-t", "--tcp", action="store_true", default=True, help="使用TCP(default)")
    tcp_udp.add_argument("-u", "--udp", action="store_false", default=False, help="使用UDP")

    time_count = parse.add_mutually_exclusive_group()
    time_count.add_argument("-T", "--time", type=float, default=10.0, help="测试持续时间。(单位：秒)")
    time_count.add_argument("-c", "--count", type=int, default=1000, help="发送的数据包数量(default: 1000)")

    parse.add_argument("-s", "--size", type=int, default=1024, help="发送数据包大小(default: 1024 byte)")

    parse.add_argument("host", help="target address")

    args = parse.args_parse()
    print(args);sys.exit(0)
