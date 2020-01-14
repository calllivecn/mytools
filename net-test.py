#!/usr/bin/env python3
# coding=utf-8
# date 2020-01-09 00:19:05
# author calllivecn <c-all@qq.com>

import os
import sys
import time
import socket
import struct
import threading

import argparse


BUF=8*(1<<20) # 8K

PROTO_PACK = struct.Struct("!HHL")
# H 操作类型
# H packsize
# L 要发送的数据包的数量

PROTO_LEN = PROTO_PACK.size

RECV = 0x0001
SEND = 0x0002

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


def tcp_server(address, port, ipv6):
    """
    ipv6: True or False
    """

    if ipv6:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    sock.bind((address, port))
    sock.listen(5)

    while True:
        print(f"TCP: {address}:{port} 等待连接...")
        client, addr = sock.accept()

        cmd = b"" #getpack(client.recv, PROTO_LEN)
        size = PROTO_LEN
        while size > 0:
            c = client.recv(size)
            size -= len(c)
            cmd += c

        type_, packsize, packcount = PROTO_PACK.unpack(cmd)

        if type_ == RECV:
            print("TCP: 开始测试接收...")
            while True:
                data = client.recv(BUF)
                if not data :
                    print("TCP: 开始接收测试完成...")
                    break
        elif type_ == SEND:
            data = b"-" * packsize
            for i in range(packcount):
                data = client.send(data)
                if not data :
                    break
        else:
            print("未定义的操作类型。", file=sys.stderr)
            client.close()


def udp_server(address, port, ipv6):
    """
    ipv6: True or False
    """

    if ipv6:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.bind((address, port))

    while True:
        print(f"UDP: {address}:{port} 等待接收...")

        cmd = b""
        size = PROTO_LEN
        while size > 0:
            c, addr = sock.recvfrom(size)
            size -= len(c)
            cmd += c

        type_, packsize, packcount = PROTO_PACK.unpack(cmd)

        if type_ == RECV:
            while True:
                data = client.recvfrom(BUF)
                if not data :
                    break
        elif type_ == SEND:
            data = b"-" * packsize
            for i in range(packcount):
                data = client.sendto(data, addr)
                if not data :
                    break
        else:
            print("未定义的操作类型。", file=sys.stderr)
            client.close()


def server(address="", port=6789, ipv6=False):

    if ipv6:
        tcp = threading.Thread(target=tcp_server, args=("", port, ipv6), daemon=True)
        tcp.start()

        udp = threading.Thread(target=udp_server, args=("", port, ipv6), daemon=True)
        udp.start()

        tcp.join()
        udp.join()
    
    else:
        tcp = threading.Thread(target=tcp_server, args=("", port, ipv6), daemon=True)
        tcp.start()

        udp = threading.Thread(target=udp_server, args=("", port, ipv6), daemon=True)
        udp.start()

        tcp.join()
        udp.join()



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

    parse.add_argument("--ipv6", action="store_true", help="使用 ipv6 否则 ipv4 (default: ipv4)")

    parse.add_argument("--port", type=int, help="指定端口")

    parse.add_argument("--server", action="store_true", help="启动测试server。(如果设置这项，就只有ipv46选项有用)")

    parse.add_argument("--recv", action="store_true", help="测试接收数据")

    parse.add_argument("--send", action="store_true", help="测试发送数据")

    parse.add_argument("host", nargs="?", help="target address")

    args = parse.parse_args()
    #print(args);sys.exit(0)

    if args.server:
        if args.ipv6:
            server(port=args.port, ipv6=True)
        else:
            server(port=args.port)

        sys.exit(0)



if __name__ == "__main__":
    main()
