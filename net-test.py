#!/usr/bin/env python3
# coding=utf-8
# date 2020-01-09 00:19:05
# author calllivecn <c-all@qq.com>

import os
import sys
import time
import socket
import threading

import argparse


class Nettest:

    def __init__(self, address, packsize, count, time_, tcp=True):
        self.port = 6789
        self.address = address
        self.packsize = packsize * 1024
        self.count = count
        self._time = time_

        self._data = "-" * self.packsize

        if tcp:
            self._sock = socket.socket()
        else:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        

    def testing(self):

        conn = self._sock.connect((self.address, self.port))

        print("测试发送。。。")
        c = 0 
        for _ in range(self.count):
            start = time.time()
            socke.send((server, SERVER_PORT), self._data)
            end = time.time()
            c += 1
            t = end - start
            if 1 <= t:
                print("发送速度：{}KB/s ".format(c * self.packsize))
                c = 0


        print("测试接收。。。")
        c = 0 
        for _ in range(self.count):
            start = time.time()
            self._sock.readfrom((server, SERVER_PORT), self._data)
            end = time.time()
            c += 1
            t = end - start
            if 1 <= t:
                print("接收速度：{}KB/s ".format(c * self.packsize / 1024))
                c = 0
            else:
                print("接收速度：{}KB/s ".format(c * self.packsize / 1024 / t))
                c = 0


    def server(self, address="0.0.0.0", port=6789):
        
        self._sock.bind((address, port))

        self._sock.listen(5)

        while True:
            client = self._sock.accept()

            if
            while True:
                data = sock._sock.recv(self.packsize)
                self._sock.send(data)

        
    def close(self):

        self._sock.close()


def main():
    parse = argparse.ArgumentParser(usage="Usage: %(prog)s [-tu] [-Tc] [-s <package size>] [host]",
            description="test network",
            epilog="author: calllivecn <https://github.com/calllivecn/mytools>"
            )
    tcp_udp = parse.add_mutually_exclusive_group()
    tcp_udp.add_argument("-t", "--tcp", action="store_true", default=True, help="使用TCP(default)")
    #tcp_udp.add_argument("-u", "--udp", action="store_false", default=False, help="使用UDP")

    time_count = parse.add_mutually_exclusive_group()
    time_count.add_argument("-T", "--time", type=float, default=15.0, help="测试持续时间。(单位：秒，默认15。0: 一直测试。)")
    time_count.add_argument("-c", "--count", type=int, default=1000, help="发送的数据包数量(default: 1000)")

    parse.add_argument("-s", "--size", type=int, default=1, help="发送数据包大小(default: 1K)")

    #parse.add_argument("--recv", action="store_true", help="只接收数据")

    parse.add_argument("host", required=True, help="target address")

    args = parse.args_parse()
    print(args);sys.exit(0)



if __name__ == "__main__":
    main()
