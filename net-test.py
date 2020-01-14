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
        self.packsize = packsize
        self.count = count
        self.time = time_
        self.tcp = tcp

        self._datapack = b"-" * self.packsize

        self._recv = b"recv"
        self._send = b"send"

        if tcp:
            self._sock = socket.socket()
            self._recv = self._sock.recv
            self._send = self._sock.send
        else:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._recv = self._sock.recvfrom
            self._send = lambda x: self._sock.sendto((self.address, self.port), x)
        

    def testing(self):

        conn = self._sock.connect((self.address, self.port))

    def server(self):
        

    def __server_tcp(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind((self.address, self.port))
        self._sock.listen(5)

        while True:
            print("TCP: {self.address}:{self.port} 等待连接...")
            client, addr = self._sock.accept()
            print(f"conn: {addr}")
            self.__select_rs(client)

    def __server_udp(self):

        while True:
            print("UDP: {self.address}:{self.port} 等待连接...")
            self.__select_rs(self._sock)

    def __send(self):

        print("测试发送。。。")
        c = 0 
        for _ in range(self.count):
            start = time.time()
            self._send(self._datapack)
            end = time.time()
            c += 1
            t = end - start
            if 1 <= t:
                print("接收速度：{} pack/s {} KB/s ".format(c, c * self.packsize))
                c = 0
            else:
                print("接收速度：{} pack/s {} KB/s ".format(c, c * self.packsize / t))
                c = 0

    def __recv(self):

        print("测试接收。。。")
        c = 0 
        for _ in range(self.count):
            start = time.time()
            self._recv(self.packsize)
            end = time.time()
            c += 1
            t = end - start
            if 1 <= t:
                print("接收速度：{} pack/s {} KB/s ".format(c, c * self.packsize))
                c = 0
            else:
                print("接收速度：{} pack/s {} KB/s ".format(c, c * self.packsize / t))
                c = 0

    def __select_rs(self, conn):

        data = conn.read(4)

        if self._recv == data:
            self.recv()
        elif self._send == data:
            self.send()
        else:
            print(f"错误的标识头：{data}，关闭连接。")
            client.close()

    def close(self):
        self._sock.close()


def main():
    parse = argparse.ArgumentParser(usage="Usage: %(prog)s [-tu] [-Tc] [-s <package size>] [host]",
            description="test network",
            epilog="author: calllivecn <https://github.com/calllivecn/mytools>"
            )
    tcp_udp = parse.add_mutually_exclusive_group()
    tcp_udp.add_argument("-t", "--tcp", action="store_true", default=True, help="使用TCP(default)")
    tcp_udp.add_argument("-u", "--udp", action="store_false", default=False, help="使用UDP")

    time_count = parse.add_mutually_exclusive_group()
    time_count.add_argument("--time", type=float, default=15.0, help="测试持续时间。(单位：秒，默认15，0: 一直测试。)")
    time_count.add_argument("-c", "--count", type=int, default=1000, help="发送的数据包数量(default: 1000)")

    parse.add_argument("-s", "--size", type=int, default=1024, help="发送数据包大小(default: 1024 byte)")

    parse.add_argument("--server", action="store_true", help="启动测试server。")

    parse.add_argument("--recv", action="store_true", help="测试接收数据")

    parse.add_argument("--send", action="store_true", help="测试发送数据")

    parse.add_argument("host", required=True, help="target address")

    args = parse.args_parse()
    print(args);sys.exit(0)



if __name__ == "__main__":
    main()
