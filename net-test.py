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

PROTO_PACK = struct.Struct(">HHI")
# H 操作类型
# H packsize
# L 要发送的数据包的数量

PROTO_LEN = PROTO_PACK.size

SERVER_RECV = 0x0001
SERVER_SEND = 0x0002
CLIENT_RECV = SERVER_SEND
CLIENT_SEND = SERVER_RECV

EOF = struct.pack(">H", 0xffff)
# UDP 一个数据包的开头2byte为 0xffff 表示，连接结束。

class Nettest:

    def __init__(self, address, port, packsize, packcount, time_, tcp=True, ipv6=False):
        self.port = port
        self.address = address
        self.packsize = packsize
        self.packcount = packcount

        self.datasum = packsize * packcount

        self.time = time_
        self.tcp = tcp
        self.ipv6 = ipv6

        self._datapack = b"-" * self.packsize

    def testing(self, op=1):
        """
        op: 1: CLIENT_SEND, 2: CLIENT_RECV, 3: SEND & RECV
        """

        try:

            if self.tcp:
                if op == 1:
                    self.tcp_send()
                elif op == 2:
                    self.tcp_recv()
                elif op == 3:
                    self.tcp_send()
                    self.tcp_recv()
            else:
                if op == 1:
                    self.udp_send()
                elif op == 2:
                    self.udp_recv()
                elif op == 3:
                    self.udp_send()
                    self.udp_recv()
        except KeyboardInterrupt:
            pass

    def tcp_send(self):
        print("测试发送。。。")

        self.__getsock()

        self.sock.connect((self.address, self.port))

        self.sock.send(PROTO_PACK.pack(CLIENT_SEND, self.packsize, self.packcount))

        c = 0 
        datasum = 0
        start = time.time()
        for _ in range(self.packcount):
            self.sock.send(self._datapack)
            end = time.time()
            c += 1
            datasum += self.packsize
            t = end - start
            if t >= 1:
                print("发送速度：{} pack/s {}/s 进度：{}%".format(round(c / t), self.__data_unit(c * self.packsize / t), round(datasum / self.datasum * 100)))
                c = 0
                start = end

        # 如果上面在1秒钟内发送完成。这里可以补上。
        t = end - start
        if 0 < t <= 1:
            print("发送速度：{} pack/s {}/s 进度：{}%".format(round(c / t), self.__data_unit(c * self.packsize / t), round(datasum / self.datasum * 100)))

        self.sock.close()

    def tcp_recv(self):
        print("测试接收。。。")

        self.__getsock()

        self.sock.connect((self.address, self.port))

        self.sock.send(PROTO_PACK.pack(CLIENT_RECV, self.packsize, self.packcount))

        c = 0 
        datasum = 0
        start = time.time()
        client_reset = False
        for _ in range(self.packcount):

            # 接收一个完整的包
            pack = self.packsize
            while pack > 0:
                data = self.sock.recv(pack)
                pack -= len(data)
                if not data:
                    print("TCP: 接收测试完成...")
                    client_reset = True
                    break
            
            if client_reset:
                break

            datasum += self.packsize
            end = time.time()
            c += 1
            t = end - start
            if t >= 1:
                print("发送速度：{} pack/s {}/s 进度：{}%".format(round(c / t), self.__data_unit(c * self.packsize / t), round(datasum / self.datasum * 100)))
                c = 0
                start = end

        t = end - start
        if 0 < t:
            print("发送速度：{} pack/s {}/s 进度：{}%".format(round(c / t), self.__data_unit(c * self.packsize / t), round(datasum / self.datasum * 100)))


        self.sock.close()

    def udp_send(self):

        self.__getsock()

        self.sock.sendto(PROTO_PACK.pack(CLIENT_SEND, self.packsize, self.packcount), (self.address, self.port))

        c = 0 
        datasum = 0
        start = time.time()
        for _ in range(self.packcount):
            self.sock.sendto(self._datapack, (self.address, self.port))
            end = time.time()
            c += 1
            datasum += self.packsize
            t = end - start
            if t >= 1:
                print("发送速度：{} pack/s {}/s 进度：{}%".format(round(c / t), self.__data_unit(c * self.packsize / t), round(datasum / self.datasum * 100)))
                c = 0
                start = end

        t = end - start
        if 0 < t:
            print("发送速度：{} pack/s {}/s 进度：{}%".format(round(c / t), self.__data_unit(c * self.packsize / t), round(datasum / self.datasum * 100)))

        self.sock.sendto(EOF, (self.address, self.port))

    def udp_recv(self):

        self.__getsock()

        self.sock.sendto(PROTO_PACK.pack(CLIENT_RECV, self.packsize, self.packcount), (self.address, self.port))

        c = 0
        start = time.time()
        datasum = 0
        client_reset = False
        for _ in range(self.packcount):
            # 接收一个完整的包
            pack = self.packsize
            while pack > 0:
                data, addr = self.sock.recvfrom(pack)
                pack -= len(data)
                if not data:
                    print("TCP: 接收测试完成...")
                    client_reset = True
                    break

            if client_reset:
                break

            datasum += self.packsize
            end = time.time()

            c += 1
            t = end - start
            if 1 >= t:
                print("发送速度：{} pack/s {}/s 进度：{}%".format(round(c / t), self.__data_unit(c * self.packsize / t), round(datasum / self.datasum * 100)))
                start = end
                c = 0

        t = end - start
        if 0 < t:
            print("发送速度：{} pack/s {}/s 进度：{}%".format(round(c / t), self.__data_unit(c * self.packsize / t), round(datasum / self.datasum * 100)))


    def close(self):
        if not self.tcp:
            self.sock.close()

    def __getsock(self):
        if self.ipv6:
            if self.tcp:
                self.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            else:
                self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        else:
            if self.tcp:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            else:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    def __data_unit(self, size):
        """
        size: 数据量
        return: 23K or 1M or 1021M or 1.23G
        """
        
        if 0 <= size < 1024: # B
            return "{}B".format(size)
        elif 1024 <= size <= 1048576: # KB
            return "{}KB".format(round(size / 1024, 2))
        elif 1048576<= size < 1073741824: # MB
            return "{}MB".format(round(size / 1048576, 2))
        elif 1048576 <= size: # < 1099511627776: # GB
            return "{}GB".format(round(size / 1073741824, 2))


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
        print(f"Listen TCP: {address}:{port} 等待连接...")
        client, addr = sock.accept()
        print(f"{addr}...已连接")

        cmd = b"" #getpack(client.recv, PROTO_LEN)
        size = PROTO_LEN
        while size > 0:
            c = client.recv(size)
            size -= len(c)
            cmd += c

        type_, packsize, packcount = PROTO_PACK.unpack(cmd)

        client_reset = False

        if type_ == SERVER_RECV:
            print("TCP: 开始测试接收...")
            for i in range(packcount):
                size = packsize
                while size > 0:
                    data = client.recv(size)
                    size -= len(data)
                    if not data:
                        print("TCP: 接收测试完成...")
                        client_reset = True
                        break

                if client_reset:
                    break

            print("TCP: 接收测试完成...")
            client.close()

        elif type_ == SERVER_SEND:
            print("TCP: 开始测试发送...")
            datapack = b"-" * packsize
            for i in range(packcount):
                try:
                    client.send(datapack)
                except BrokenPipeError:
                    break

            print("TCP: 发送测试完成...")
            client.close()
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
        print(f"Listen UDP: {address}:{port} 等待接收...")

        cmd = b""
        size = PROTO_LEN
        while size > 0:
            c, addr = sock.recvfrom(size)
            size -= len(c)
            cmd += c

        print(f"{addr}...")

        type_, packsize, packcount = PROTO_PACK.unpack(cmd)
        client_reset = False
        if type_ == SERVER_RECV:
            print("UDP: 开始测试接收...")
            #for i in range(packcount):
            while True:
                size = packsize
                cmd = b""
                while size > 0:
                    data, addr = sock.recvfrom(size)
                    size -= len(data)
                    cmd += data
                    if not data :
                        print("UDP: Client close()...")
                        client_reset = True
                        break

                if client_reset:
                    break

                if EOF == cmd[0:2]:
                    break

            print("UDP: 接收测试完成...")

        elif type_ == SERVER_SEND:
            print("UDP: 开始测试发送...")
            datapack = b"-" * packsize
            for i in range(packcount):
                sock.sendto(datapack, addr)
            print("UDP: 发送测试完成...")
        else:
            print("未定义的操作类型。", file=sys.stderr)


def server(address, port=6789, ipv6=False):

    if ipv6:
        tcp = threading.Thread(target=tcp_server, args=(address, port, ipv6), daemon=True)
        tcp.start()

        udp = threading.Thread(target=udp_server, args=(address, port, ipv6), daemon=True)
        udp.start()

        tcp.join()
        udp.join()
    
    else:
        tcp = threading.Thread(target=tcp_server, args=(address, port, ipv6), daemon=True)
        tcp.start()

        udp = threading.Thread(target=udp_server, args=(address, port, ipv6), daemon=True)
        udp.start()

        tcp.join()
        udp.join()


def integer(number):
    i = int(number)
    if 1 <= i <= 4294967295:
        return i
    else:
        raise argparse.ArgumentTypeError("值的有效范围：1 <= number <= 4294967295")

def main():
    parse = argparse.ArgumentParser(usage="%(prog)s [-tucs] [-T <time>] [-c <count>] [-s <package size>] [host]",
            description="test network",
            epilog="author: calllivecn <https://github.com/calllivecn/mytools>"
            )
    tcp_udp = parse.add_mutually_exclusive_group()
    tcp_udp.add_argument("-t", "--tcp", action="store_true", help="使用TCP(default)")
    tcp_udp.add_argument("-u", "--udp", action="store_true", help="使用UDP")

    time_count = parse.add_mutually_exclusive_group()
    time_count.add_argument("--time", type=int, default=15, help="测试持续时间。(单位：秒，默认15，0: 一直测试。)")
    time_count.add_argument("-c", "--count", type=integer, default=10000, help="发送的数据包数量1 ~ 4294967295 (default: 10000)")

    parse.add_argument("-s", "--size", type=int, default=1024, help="发送数据包大小1 ~ 65535(default: 1024 byte)")

    parse.add_argument("--ipv6", action="store_true", help="使用 ipv6 否则 ipv4 (default: ipv4)")

    parse.add_argument("--port", type=int, default=6789, help="指定端口(default: 6789)")

    parse.add_argument("--server", action="store_true", help="启动测试server。(如果设置这项，就只有ipv46选项有用)")

    parse.add_argument("--recv", action="store_false", help="测试接收数据(default: 测试收和发)")

    parse.add_argument("--send", action="store_false", help="测试发送数据(default: 测试收和发)")

    parse.add_argument("address", nargs="?", default="", help="target address")

    parse.add_argument("--parse", action="store_true", help="debug parse_args()")

    if len(sys.argv) == 1:
        parse.print_usage()
        sys.exit(0)

    args = parse.parse_args()

    if args.parse:
        print(args);sys.exit(0)

    if args.server:
        try:
            if args.ipv6:
                server(args.address, port=args.port, ipv6=True)
            else:
                server(args.address, port=args.port)
        except KeyboardInterrupt:
            pass
        sys.exit(0)

    
    if args.udp:
        proto = False
        print("""UDP 还不好做测量指标。目前还有问题。退出。""")
        sys.exit(0)
    else:
        proto = True

    if args.send is True and args.recv is True:
        op = 3
    elif args.send is True and args.recv is False :
        op = 2
    elif args.send is False and args.recv is True:
        op = 1
    else:
        op = 3

    net = Nettest(args.address, args.port, args.size, args.count, args.time, proto, args.ipv6)

    # 交换了 args.send args.recv
    net.testing(op) 
    net.close()
    

if __name__ == "__main__":
    main()
