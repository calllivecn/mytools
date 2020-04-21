#!/usr/bin/env python3
# coding=utf-8
# date 2020-04-20 20:37:09
# author calllivecn <c-all@qq.com>


"""
通过LAN广播的方式，执行指令。
1. 可以执行shell命令。
2. 可以编写py拓展执行。
"""

import os
import sys
import subprocess
import argparse
import logging
import threading
import struct
import socket
import socketserver


def getlogger(level=logging.INFO):
    fmt = logging.Formatter(
        "%(asctime)s %(filename)s:%(lineno)d %(levelname)s %(message)s",
        datefmt="%Y-%m-%d-%H:%M:%S")
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    logger = logging.getLogger("cmd")
    logger.setLevel(level)
    logger.addHandler(stream)
    return logger

logger = getlogger(logging.DEBUG)

def shell(cmd, timeout=5):

    try:
        recode = subprocess.call(cmd.split(), timeout=5, shell=True)
    except Exception:
        return -1

    return recode

class Plugin:
    """
    实现编写插件执行。
    """

    def __init__(self):
        pass

    def run(self):
        pass

bufsize = 2048

PROTOCOL_VERSION = 0x01
PROTOCOL_HEADER = struct.Struct("!HHH")
"""
指令包装:
    version:    2byte,  
    cmd_number:   2byte, number=1 为 shell指令。0 不使用。
    cmd_len:    2byte,  cmd_number 为 1 时，指cmd的长度，否则为0。
    cmd: 
"""

def recv_cmd(sock):

    data, addr = sock.recvfrom(bufsize)

    version, cmd_number, cmd_len = PROTOCOL_HEADER.unpack(data[:6])

    cmd = data[PROTOCOL_HEADER.size:cmd_len].decode()
    
    log = f"{addr} 接收到指令号：{cmd_number} -- "

    if cmd_len != 0:
        log.join(f"指令: {cmd}")
    
    logger.info(log)

    return cmd_number, cmd


def send_cmd(sock, cmd_number, cmd=None):

    if cmd_number == 1 and cmd is not None:
        logger.error(f"指令号为1， 但没有指令shell指令。")
        cmd = cmd.encode()
        cmd_len = len(cmd)
    else:
        cmd = b""
        cmd_len = 0

    data = PROTOCOL_HEADER.pack(PROTOCOL_VERSION, cmd_number, cmd_len)

    sock.sendto(data + cmd, ("<broadcast>",6789))
    
    log = f"发送指令号：{cmd_number} -- "

    if cmd_len != 0:
        log += f"指令: {cmd}"

    logger.info(log)

    return cmd_number, cmd

# client begin

def broadcast_cmd(cmd_number, cmd):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    send_cmd(sock, cmd_number, cmd)
    data, addr = sock.recvfrom(bufsize)
    logger.info(f"confirm: {data.decode()}")

# client end

# server begin

class subcmd(threading.Thread):
    """
    args: (shellcmd,)
    """
    def __init__(self, cmd):
        threading.Thread.__init__(self)
        self.cmd = cmd

    def run(self):
        shell(self.cmd)


class ThreadUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    daemon_threads = True

class UDPHandler(socketserver.DatagramRequestHandler):

    def handle(self):
        logger.info(f"client: {self.client_address}")
        data = self.request[0]
        sock = self.request[1]
        sock.sendto(b"ok", self.client_address)
        versoin, cmd_number, cmd_len = PROTOCOL_HEADER.unpack(data[:6])
        cmd = data[6:].decode()
        if cmd_number == 1:
            logger.info(f"收到的shell指令：{cmd}")
            shell(cmd)
        else:
            logger.info(f"收到指令号：{cmd_number}")



def server():
    with ThreadUDPServer(("", 6789), UDPHandler) as server:
        server.request_queue_size = 128
        server.serve_forever()

# server end

def parse_cli():
    parse = argparse.ArgumentParser()

    parse.add_argument("--server", action="store_true", help="start a server.")

    parse.add_argument("-t", "--type", type=int, default=1, help="1~60000 指令类型:1 为shell 指令")

    parse.add_argument("cmd", nargs="?", help="如果是shell指令的话，必需存在。")

    parse.add_argument("--parse", action="store_true", help="debug argparse parse_args()")

    args = parse.parse_args()

    if args.parse:
        print(args)
        sys.exit(0)

    return args


if __name__ == "__main__":
    
    args = parse_cli()

    if args.server:
        server()
        sys.exit(0)

    broadcast_cmd(args.type, args.cmd)

    
