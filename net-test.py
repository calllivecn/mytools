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

import io
import sys
import time
import socket
import struct
# import signal
import threading
import argparse
from functools import partial


CMD_PACK = struct.Struct("!HIQ")
# H 指令类型
# I 数据包大小
# Q 数据总量B 或 总的时间s

# 这里的定义都是相对于client来说的
# typ 字段
TCP_SEND_DATASUM = 0x0001
TCP_RECV_DATASUM = 0x0002

TCP_RECV_TIME = 0x0003
TCP_SEND_TIME = 0x0004

UDP_SEND = 0x0005
UDP_RECV = 0x0006


# functions define begin

class Speed:

    def __init__(self, packsize, total, recvsend=True, time_=True):
        self.packsize = packsize
        self.total = total
        self.time = time_
        self.recvsend = recvsend

        self.datasum = 0
        self.timecount = 0
        self.packcount = 0
        self.curdata = 0
        self.timestamp = time.time()

        self.end = False
    
        # show speed 
        self.lock = threading.Lock()

        if self.time:
            self.thread = threading.Thread(target=self.__showtime, daemon=True) 
            self.thread.start()
        else:
            self.thread = threading.Thread(target=self.__showdata, daemon=True) 
            self.thread.start()
    
    def add_pack(self):
        with self.lock:
            self.packcount += 1
            self.datasum += self.packsize
            self.curdata += self.packsize

    def __showdata(self):
        while True:
            time.sleep(1)
            with self.lock:
                self.timestamp = time.time()
                self.__print(round(self.packcount), self.__data_unit(self.curdata), round(self.datasum / self.total * 100))
                self.packcount = 0
                self.curdata = 0

    def __showtime(self):
        while True:
            time.sleep(1)
            with self.lock:
                t = time.time() - self.timestamp
                self.__print(round(self.packcount), self.__data_unit(self.curdata), round(t / self.total * 100))
                self.packcount = 0
                self.curdata = 0

    def endshowdata(self):
        self.lock.acquire()
        t = time.time() - self.timestamp
        if t < 1:
            self.__print(round(self.packcount / t), self.__data_unit(self.curdata / t), round(self.datasum / self.total * 100))
    
    def endshowtime(self):
        self.lock.acquire()
        t = time.time() - self.timestamp
        if t < 1:
            self.__print(round(self.packcount / t), self.__data_unit(self.curdata / t), round(t / self.total * 100))

    def __print(self, pack, cur, progress):
        if self.recvsend:
            print("接收速度：{} pack/s {}/s 进度：{}%".format(pack, cur, progress), flush=True)
        else:
            print("发送速度：{} pack/s {}/s 进度：{}%".format(pack, cur, progress), flush=True)
 
    def __data_unit(self, size):
        """
        size: 数据量
        return: 23K or 1M or 1021M or 1.23G
        """

        if 0 <= size < 1024: # B
            return "{}B".format(size)
        elif 1024 <= size <= 1048576: # KB
            return "{}KB".format(round(size / 1024, 1))
        elif 1048576<= size < 1073741824: # MB
            return "{}MB".format(round(size / 1048576, 1))
        elif 1048576 <= size: # < 1099511627776: # GB
            return "{}GB".format(round(size / 1073741824, 1))


def get_size_pack(sock, size):
    data = b""
    while 0 < size:
        d = sock.recv(size)

        if not d:
            return b""

        size -= len(d)
        data += d
    
    return data


# 看看这样能不能，避免GC。（不可以。。。)
# BUFVIEW = io.BytesIO(bytearray(4096)).getbuffer()

class Buffer:

    def __init__(self, sock, bufsize=64*(1<<10)):
        """
        sock: client sock
        bufsize: int: default 96k unit: k
        """
        self.bufsize = bufsize 
        self.buf = io.BytesIO(bytearray(self.bufsize)).getbuffer() # 64K buf
        self.sock = sock

    def recvsize(self, size):
        cur = 0
        while cur < size:
            n = self.sock.recv_into(self.buf[cur:size])
            # 不能这样， socke.recv_into(), 是写入到self.buf[cur:]的大小的。导致实际接收了很多，但没计算进去。
            # n = self.sock.recv_into(self.buf[cur:]) 
            if n == 0:
                return self.buf[:0]
            cur += n
        
        return self.buf[:cur]

    def oldrecvsize(self, size):
        data = b""
        while 0 < size:
            d = self.sock.recv(size)
            if not d:
                return b""
            size -= len(d)
            data += d

        return data
    
    def sendpack(self, pack):
        view = memoryview(pack)
        while len(view):
           n = self.sock.send(view) 
           view = view[n:]
    
    def close(self):
        self.sock.close()



def tcp_recv(client, packsize, datasum, time_):
    client.settimeout(30)

    speed = Speed(packsize, datasum, True, time_=time_)
    buf = Buffer(client, packsize)
    try:

        for data in iter(partial(buf.recvsize, packsize), b""):
            # 接收一个完整的包
            speed.add_pack()

    except socket.timeout:
        print("TCP: 接收超时...")
    finally:
        # 正常结束
        if time_:
            speed.endshowtime()
        else:
            speed.endshowdata()
        print("TCP: 接收测试完成...")
        client.close()


def tcp_send(client, packsize, datasum, time_):
    datapack = b"-" * packsize
    client.settimeout(30)

    speed = Speed(packsize, datasum, recvsend=False, time_=time_)
    buf = Buffer(client, packsize)
    try:

        while True:
            buf.sendpack(datapack)
            speed.add_pack()

    except BrokenPipeError:
        print("TCP: BrokenPipe...")
    except socket.timeout:
        print("TCP: 发送测试超时...")
    except ConnectionResetError:
        #print("TCP: Peer Connection Reset...")
        pass
    finally:
        if time_:
            speed.endshowtime()
        else:
            speed.endshowdata()
        print("TCP: 发送测试完成...")
        client.close()


# 下面是server 函数

class Sleep:

    def __init__(self, t):
        self.end = False
        self.time = t
        self.lock = threading.Lock()
        self.th = threading.Thread(target=self.__sleep, daemon=True)
        self.th.start()

        self.end = False
    
    def isEnd(self):
        with self.lock:
            return self.end

    def __sleep(self):
        time.sleep(self.time)
        with self.lock:
            self.end = True

def tcp_server_recv_datasum(client, packsize, datasum):
    client.settimeout(30)

    buf = Buffer(client, packsize)
    data = 0

    try:
        for d in iter(partial(buf.recvsize, packsize), b""):
            data += len(d)
            if data >= datasum:
                break
        print("TCP: 接收测试完成...")
    except socket.timeout:
        print("TCP： 接收超时...")
    finally:
        buf.close()

def tcp_server_send_datasum(client, packsize, datasum):
    client.settimeout(30)

    buf = Buffer(client, packsize)
    pack = memoryview(bytearray(packsize))
    data = 0
    try:
        while data < datasum:
            buf.sendpack(pack)
            data += packsize

    except BrokenPipeError:
        print("TCP: BrokenPipe...")
    except socket.timeout:
        print("TCP: 发送测试超时...")
    except ConnectionResetError:
        print("TCP: 发送测试完成...")
    finally:
        buf.close()


def tcp_server_recv_time(client, packsize, time_):
    client.settimeout(30)

    buf = Buffer(client, packsize)
    t = Sleep(time_)

    try:
        for _ in iter(partial(buf.recvsize, packsize), b""):
            if t.isEnd():
                break

        print("TCP: 接收测试完成...")
    except socket.timeout:
        print("TCP: 接收测试超时...")
    finally:
        buf.close()

def tcp_server_send_time(client, packsize, time_):
    client.settimeout(30)

    buf = Buffer(client, packsize)
    pack = bytearray(packsize)
    t = Sleep(time_)
    try:
        while not t.isEnd():
            buf.sendpack(pack)
    except BrokenPipeError:
        print("TCP: BrokenPipe...")
    except socket.timeout:
        print("TCP: 发送测试超时...")
    except ConnectionResetError:
        print("TCP: 发送测试完成...")
    finally:
        buf.close()

# functions define end


class Nettest:

    def __init__(self, address, port, packsize, total, time_=True, tcp=True, ipv6=False):
        self.port = port
        self.address = address
        self.packsize = packsize

        self.total = total
        self.time = time_

        self.tcp = tcp
        self.ipv6 = ipv6

    def testing(self, op=1):
        """
        op: 1: CLIENT_SEND, 3: CLIENT_RECV, 3: SEND & RECV
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
            if self.time:
                self.sock.send(CMD_PACK.pack(TCP_SEND_TIME, self.packsize, self.total))
            else:
                self.sock.send(CMD_PACK.pack(TCP_SEND_DATASUM, self.packsize, self.total))

            tcp_send(self.sock, self.packsize, self.total, self.time)

        except socket.timeout:
            print("TCP: connect 超时...")
        
        self.sock.close()
    

    def tcp_recv(self):
        print("测试接收。。。")

        self.__getsock()

        self.sock.settimeout(30)
        try:
            self.sock.connect((self.address, self.port))

            # 告诉server端开始测试接收, 需要参数： typ, packsize, datasum
            if self.time:
                self.sock.send(CMD_PACK.pack(TCP_RECV_TIME, self.packsize, self.total))
            else:
                self.sock.send(CMD_PACK.pack(TCP_RECV_DATASUM, self.packsize, self.total))

            tcp_recv(self.sock, self.packsize, self.total, self.time)

        except socket.timeout:
            print("TCP: connect 超时...")
            
        self.sock.close()


    def udp_send(self):
        pass

    def udp_recv(self):
        pass

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
        print(f"Listen TCP: {address}:{port} 等待连接... ")
        client, addr = sock.accept()
        print(f"{addr} ...已连接")

        # 接收指令类型头
        cmd = get_size_pack(client, CMD_PACK.size)
        if not cmd:
            print("接收指令类型错误...")
            client.close()
            continue

        typ, packsize, total = CMD_PACK.unpack(cmd)

        # typ 是相对于client来说的。
        if typ == TCP_SEND_DATASUM:
            print("TCP: 开始测试接收...")
            th = threading.Thread(target=tcp_server_recv_datasum, args=(client, packsize, total), daemon=True)
            th.start()

        elif typ == TCP_RECV_DATASUM:
            print("TCP: 开始测试发送...")
            th = threading.Thread(target=tcp_server_send_datasum, args=(client, packsize, total), daemon=True)
            th.start()

        elif typ == TCP_RECV_TIME:
            print("TCP: 开始测试发送...")
            th = threading.Thread(target=tcp_server_send_time, args=(client, packsize, total), daemon=True)
            th.start()

        elif typ == TCP_SEND_TIME:
            print("TCP: 开始测试接收...")
            th = threading.Thread(target=tcp_server_recv_time, args=(client, packsize, total), daemon=True)
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
        addr = ""
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

                if EOF == cmd[0:3]:
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


def tcpserver(address, port=6789, ipv6=False):

    if ipv6:
        tcp = threading.Thread(target=tcp_server, args=(address, port, ipv6), daemon=True)
        tcp.start()
        tcp.join()
    else:
        tcp = threading.Thread(target=tcp_server, args=(address, port, ipv6), daemon=True)
        tcp.start()
        tcp.join()

def udpserver(address, port=6789, ipv6=False):

    if ipv6:
        udp = threading.Thread(target=udp_server, args=(address, port, ipv6), daemon=True)
        udp.start()
        udp.join()
    else:
        udp = threading.Thread(target=udp_server, args=(address, port, ipv6), daemon=True)
        udp.start()
        udp.join()




def biginteger(number):
    i = int(number)
    # (1<<63) - 1
    if 1 <= i <= 9223372036854775807:
        return i
    else:
        raise argparse.ArgumentTypeError("值的有效范围：1 <= number <= 9223372036854775807")

def integer(number):
    i = int(number)
    # if 1 <= i <= 4294967295:
    if 1 <= i <= 10485760:
        return i
    else:
        raise argparse.ArgumentTypeError("值的有效范围：1 <= number <= 10485760")


def main():
    parse = argparse.ArgumentParser(usage="%(prog)s [-tus] [-T <time>] [-d <data sum>] [-s <package size>] [host]",
            description="test network tcp udp speed",
            epilog="author: calllivecn <https://github.com/calllivecn/mytools>"
            )
    tcp_udp = parse.add_mutually_exclusive_group()
    tcp_udp.add_argument("-t", "--tcp", action="store_true", default=True, help="使用TCP(default)")
    tcp_udp.add_argument("-u", "--udp", action="store_true", help="使用UDP")

    time_count = parse.add_mutually_exclusive_group()

    time_count.add_argument("-T", "--time", type=int, help="测试持续时间。(单位：秒，默认: 7)")
    #time_count.add_argument("-c", "--count", type=integer, default=10000, help="发送的数据包数量1 ~ 4294967295 (default: 10000)")

    time_count.add_argument("-d", "--datasum", type=biginteger, help="发送的数据量1 ~ 8796093022208 (defulat: 64M) 单位：M")

    parse.add_argument("-s", "--size", type=integer, default=1024, help="发送数据包大小1B ~ 10485760B(10M) (default: 1024 byte)")

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
    
    if args.server:
        try:
            if args.ipv6:
                if args.tcp:
                    tcpserver(args.address, port=args.port, ipv6=True)
                else:
                    udpserver(args.address, port=args.port, ipv6=True)
            else:
                if args.tcp:
                    tcpserver(args.address, port=args.port)
                else:
                    udpserver(args.address, port=args.port)
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

    if args.time:
        net = Nettest(args.address, args.port, args.size, args.time, True, proto, args.ipv6)
    elif args.datasum:
        net = Nettest(args.address, args.port, args.size, args.datasum * (1<<20), False, proto, args.ipv6)
    else:
        net = Nettest(args.address, args.port, args.size, 7, True, proto, args.ipv6)

    # 交换了 args.send args.recv
    net.testing(op) 
    net.close()
    

if __name__ == "__main__":
    main()
