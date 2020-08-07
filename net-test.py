#!/usr/bin/env python3
# coding=utf-8
# date 2020-01-09 00:19:05
# author calllivecn <c-all@qq.com>

"""
TCP:
    发送测试：
        client --> struct.pack("!HH", typ=TCP_SEND, packsize)
        server --> 一直接收。直到收到typ = EOF时。结束
    
    接收测试：
        情形1（使用 --datasum 时，也是默认选项）：
            client --> struct.pack("!HHI", typ=TCP_SEND, packsize, datasum)
            server --> 在发送完数据后，向client发送EOF结束。

        情形2（使用 --time 时）： 这种。。。。先算了，使用数据总量来跑吧
            client --> struct.pack("!HHI", typ=TCP_SEND_TIME, packsize, time)
            server --> 在时间到后，向client发送EOF结束。
"""

import os
import sys
import time
import socket
import struct
#import signal
import threading
import argparse


BUF=8*(1<<20) # 8K

CMD_PACK = struct.Struct("!HHI")
PROTO_PACK = struct.Struct(">HH")
PROTO_LEN = PROTO_PACK.size
# H 操作类型
# H packsize

# 这里的定义都是相对于client来说的
# typ 字段
TCP_SEND = 0x0001
TCP_RECV = 0x0002

TCP_RECV_TIME = 0x0003
TCP_SEND_TIME = 0x0004

END = 0xffff
# 一个数据包的开头2byte为 0xffff 表示，接收或者发送结束。 0x0000为填充数据
EOF = struct.pack(">HH", 0xffff, 0x0000)

class Nettest:

    def __init__(self, address, port, packsize, datasum, tcp=True, ipv6=False):
        self.port = port
        self.address = address
        self.packsize = packsize

        self.datasum = datasum

        #self.time = time_
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
        self.sock.settimeout(30)

        try:
            self.sock.connect((self.address, self.port))

            # 指令包
            self.sock.send(CMD_PACK.pack(TCP_SEND, self.packsize, self.datasum))

            c = 0 
            datasum = self.datasum
            playload = PROTO_PACK.pack(TCP_SEND, self.packsize) + self._datapack
            start = time.time()
            while datasum > 0:
                self.sock.send(playload)
                end = time.time()
                c += 1
                # 告诉 server 数据发送完～ break
                datasum -= self.packsize
                t = end - start
                if t >= 1:
                    print("发送速度：{} pack/s {}/s 进度：{}%".format(round(c / t), self.__data_unit(c * self.packsize / t), round(datasum / self.datasum * 100)))
                    c = 0
                    start = end

            self.sock.send(EOF)

            # 如果上面在1秒钟内发送完成。这里可以补上。
            t = end - start
            if 0 < t <= 1:
                print("发送速度：{} pack/s {}/s 进度：{}%".format(round(c / t), self.__data_unit(c * self.packsize / t), round(datasum / self.datasum * 100)))

        except socket.timeout:
            print("TCP： 发送测试超时...")

        self.sock.close()
    

    def tcp_recv(self):
        print("测试接收。。。")

        self.__getsock()

        self.sock.settimeout(30)
        try:
            self.sock.connect((self.address, self.port))

            # 告诉server端开始测试接收, 需要参数： typ, packsize, datasum
            self.sock.send(CMD_PACK.pack(TCP_RECV, self.packsize, self.datasum))

            # 接收协议头
            c = 0 
            datasum = self.datasum
            recv_empty = False        
            start = time.time()
            while True:
                # 先接协议头
                proto_head = b""
                lenght = PROTO_PACK.size
                while lenght > 0:
                    d = self.sock.recv(lenght)
                    if not d:
                        print("TCP: 接收测试中断... 接收协议头时")
                        recv_empty = True
                        break
                    lenght -= len(d)
                    proto_head += d

                if recv_empty:
                    break

                if proto_head == EOF:
                    break

                # 接收一个完整的包
                lenght = self.packsize
                while lenght > 0:
                    d = self.sock.recv(lenght)
                    if not d:
                        print("TCP: 接收测试中断... 接收数据时")
                        recv_empty = True
                        break
                    lenght -= len(d)

                datasum -= self.packsize

                end = time.time()
                c += 1
                t = end - start
                if t >= 1:
                    print("接收速度：{} pack/s {}/s 进度：{}%".format(round(c / t), self.__data_unit(c * self.packsize / t), round((1 - (datasum / self.datasum)) * 100)))
                    c = 0
                    start = end

            t = end - start
            if 0 < t:
                print("接收速度：{} pack/s {}/s 进度：{}%".format(round(c / t), self.__data_unit(c * self.packsize / t), round((1 - (datasum / self.datasum)) * 100)))

        except socket.timeout:
            print("TCP: 接收测试超时...")
            
        self.sock.close()


    def tcp_send_time(self, timeout):
        print("测试发送。。。")

        self.__getsock()

        self.sock.settimeout(30)
        
        try: 
            self.sock.connect((self.address, self.port))

            # 指令包
            self.sock.send(CMD_PACK.pack(TCP_SEND, self.packsize, self.datasum))

            c = 0 
            datasum = self.datasum
            playload = PROTO_PACK.pack(TCP_SEND, self.packsize) + self._datapack
            start = time.time()
            start_timeout = start
            while datasum > 0:
                self.sock.send(playload)
                end = time.time()
                c += 1
                # 告诉 server 数据发送完～ break
                datasum -= self.packsize
                t = end - start
                if t >= 1:
                    print("发送速度：{} pack/s {}/s 进度：{}%".format(round(c / t), self.__data_unit(c * self.packsize / t), round(datasum / self.datasum * 100)))
                    c = 0
                    start = end
                 
                if (end - start_timeout) >= timeout:
                    self.sock.send(EOF)
                    break

            # 如果上面在1秒钟内发送完成。这里可以补上。
            t = end - start
            if 0 < t <= 1:
                print("发送速度：{} pack/s {}/s 进度：{}%".format(round(c / t), self.__data_unit(c * self.packsize / t), round(datasum / self.datasum * 100)))

        except socket.timeout:
            print("TCP: 发送测试超时...")

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


def tcp_server_recv_old(client, type, packsize, datasum):
    client.settimeout(30)
    try:
        recv_empty = False
        while True:
            # 先接收协议头
            proto_head = b""
            lenght = PROTO_PACK.size
            while lenght > 0:
                d = client.recv(lenght)
                if not d:
                    print("TCP: 接收测试中断... 接收协议头时")
                    recv_empty = True
                    break
                lenght -= len(d)
                proto_head += d

            if recv_empty:
                break

            if proto_head == EOF:
                break

            # 接收一个完整的包
            size = packsize
            while size > 0:
                data = client.recv(size)
                if not data:
                    print("TCP: 接收测试中断... 接收数据时")
                    client_reset = True
                    break
                size -= len(data)
    except socket.timeout:
        print("TCP: 接收超时...")

    print("TCP: 接收测试完成...")
    client.close()


def tcp_server_send_old(client, typ, packsize, datasum):
    datapack = PROTO_PACK.pack(TCP_RECV, packsize) + b"-" * packsize
    client.settimeout(30)
    try:
        while datasum > 0:
            client.send(datapack)
            datasum -= packsize
    
        client.send(EOF)
    except BrokenPipeError:
        pass
    except socket.timeout:
        print("TCP: 发送测试超时...")

    print("TCP: 发送测试完成...")
    client.close()


def tcp_server_recv(client, typ, packsize, datasum):

    if typ == TCP_RECV_TIME:
        time_ = True
        total_time = datasum * 1.2
    else:
        time_ = False

    client.settimeout(30)
    start = time.time()
    try:
        recv_empty = False
        while True:
            # 先接收协议头
            proto_head = b""
            lenght = PROTO_PACK.size
            while lenght > 0:
                d = client.recv(lenght)
                if not d:
                    print("TCP: 接收测试中断... 接收协议头时")
                    recv_empty = True
                    break
                lenght -= len(d)
                proto_head += d

            if recv_empty:
                break

            if proto_head == EOF:
                break

            # 接收一个完整的包
            size = packsize

            while size > 0:
                data = client.recv(size)
                if not data:
                    print("TCP: 接收测试中断... 接收数据时")
                    client_reset = True
                    break
                size -= len(data)

            end = time.time()
            if time_ and (end - start) >= total_time:
                break

    except socket.timeout:
        print("TCP: 接收超时...")

    print("TCP: 接收测试完成...")
    client.close()


def tcp_server_send(client, typ, packsize, datasum):
    datapack = PROTO_PACK.pack(TCP_RECV, packsize) + b"-" * packsize

    if typ == TCP_SEND_TIME:
        time_ = True
        if datasum <= 0:
            total_time = 15
        else:
            total_time = datasum
    else:
        time_ = False

    client.settimeout(30)

    try:
        start = time.time()
        while datasum > 0:
            client.send(datapack)

            if not time_:
                datasum -= packsize

            end = time.time()

            if time_ and (end - start) >= total_time:
                break
    
        client.send(EOF)

    except BrokenPipeError:
        pass
    except socket.timeout:
        print("TCP: 发送测试超时...")

    print("TCP: 发送测试完成...")
    client.close()


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

        recv_empty = False
        # 接收指令类型头
        cmd = b""
        size = CMD_PACK.size
        while size > 0:
            d = client.recv(size)

            if not d:
                recv_empty = True
                break

            size -= len(d)
            cmd += d

        if recv_empty:
            client.close()
            continue

        typ, packsize, datasum = CMD_PACK.unpack(cmd)

        # typ 是相对于client来说的。
        if typ == TCP_SEND:
            print("TCP: 开始测试接收...")
            th = threading.Thread(target=tcp_server_recv, args=(client, typ, packsize, datasum), daemon=True)
            th.start()

        elif typ == TCP_RECV:
            print("TCP: 开始测试发送...")
            th = threading.Thread(target=tcp_server_send, args=(client, typ, packsize, datasum), daemon=True)
            th.start()

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

def countdown():
    sys.exit(0)

def integer(number):
    i = int(number)
    if 1 <= i <= 4294967295:
        return i
    else:
        raise argparse.ArgumentTypeError("值的有效范围：1 <= number <= 4294967295")


def main():
    parse = argparse.ArgumentParser(usage="%(prog)s [-tucs] [-T <time>] [-d <data sum>] [-s <package size>] [host]",
            description="test network",
            epilog="author: calllivecn <https://github.com/calllivecn/mytools>"
            )
    tcp_udp = parse.add_mutually_exclusive_group()
    tcp_udp.add_argument("-t", "--tcp", action="store_true", help="使用TCP(default)")
    tcp_udp.add_argument("-u", "--udp", action="store_true", help="使用UDP")

    time_count = parse.add_mutually_exclusive_group()
    #time_count.add_argument("--time", type=int, default=15, help="测试持续时间。(单位：秒，默认15，0: 一直测试。)")
    #time_count.add_argument("-c", "--count", type=integer, default=10000, help="发送的数据包数量1 ~ 4294967295 (default: 10000)")

    time_count.add_argument("-d", "--datasum", type=integer, default=64, help="发送的数据量1 ~ 4095 (defulat: 64M) 单位：M")

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
        print(args)
        sys.exit(0)
    
    #if args.time > 0:
    #    signal.signal(signal.SIGALRM, countdown)
    #    signal.alarm(args.time)
    #    print(f"{args.time} 秒钟后退出")

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

    net = Nettest(args.address, args.port, args.size, args.datasum * (1<<20),  proto, args.ipv6)

    # 交换了 args.send args.recv
    net.testing(op) 
    net.close()
    

if __name__ == "__main__":
    main()
