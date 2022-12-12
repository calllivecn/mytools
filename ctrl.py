#!/usr/bin/env python3
# coding=utf-8
# date 2020-04-20 20:37:09
# author calllivecn <c-all@qq.com>


"""
通过LAN广播的方式，执行指令。
1. 可以执行shell命令。
2. 可以编写py拓展执行。
3. termux-tts-speak 文字转语音
"""

import os
import sys
import time
import shlex
import struct
import socket
import logging
import argparse
import threading
import subprocess
from multiprocessing import (
    Process,
    ProcessError,
)


from cryptography import exceptions
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

__all__ = (
    "Plugin",
)

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


class subcmd(threading.Thread):
    """
    args: (shellcmd,)
    """
    def __init__(self, cmd, timeout=30):
        super().__init__()
        self.cmd = cmd
        self.timeout = timeout

    def run(self):
        logger.debug(f"执行shell(cmd): {self.cmd}")
        try:
            # 安全处理下命令
            cmd = shlex.split(self.cmd)
            com = subprocess.run(cmd, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            logger.warning(f'执行: "{cmd}" 超时。')
            return -1
        except Exception:
            logger.error(f'执行: "{cmd}" 异常。')
            return -1

        logger.info(f'执行: "{cmd}" recode: {com.returncode}')

        return com.returncode


class Plugin(Process):
    """
    实现编写插件执行。
    """

    def __init__(self):
        pass

    def run(self):
        pass


BUFSIZE = 2048

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

    data, addr = sock.recvfrom(BUFSIZE)

    version, cmd_number, cmd_len = PROTOCOL_HEADER.unpack(data[:PROTOCOL_HEADER.size])

    cmd = data[PROTOCOL_HEADER.size:cmd_len].decode()
    
    log = f"{addr} 接收到指令号：{cmd_number}"

    if cmd_number == 1:
        log += f"指令: {cmd}"
    
    logger.info(log)

    return cmd_number, cmd

# client begin

def broadcast_cmd(port, cmd_number, cmd):

    # sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(1)
    #send_cmd(sock, port, cmd_number, cmd)

    if cmd_number == 1 and cmd is not None:
        cmd_byte = cmd.encode()
        cmd_len = len(cmd_byte)
    elif cmd_number == 1 and cmd is None:
        logger.error(f"指令号为1， 但没有指令shell指令。")
        sys.exit(1)
    else:
        cmd_byte = b""
        cmd_len = 0

    data = PROTOCOL_HEADER.pack(PROTOCOL_VERSION, cmd_number, cmd_len)
    
    log = f"发送指令号：{cmd_number} -- "

    if cmd_len != 0:
        log += f"指令: {cmd}"

    logger.info(log)

    broadcast = ("<broadcast>", port)

    # retry 3 次
    for i in range(1, 4):
        sock.sendto(data + cmd_byte, broadcast)
        try:
            data, addr = sock.recvfrom(BUFSIZE)
        except socket.timeout:
            logger.info(f"超时重试: {i}/3")
            time.sleep(1)
            continue

        logger.info(f"server: {addr} -- confirm: {data.decode()}")
        break
    
    #logger.error(f"指定可能发送失败。")

    return cmd_number, cmd

# client end

# server begin

# 这里是 server 部分
def server(address, port):
    # sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.bind((address, port))

    logger.info(f"接收端口: {port}")

    try:
        while True:
            data, addr = sock.recvfrom(BUFSIZE)
            logger.debug(f"收到UDP包：{addr} -- {data}")
            # reply ok
            sock.sendto(b"ok", addr)

            versoin, cmd_number, cmd_len = PROTOCOL_HEADER.unpack(data[:6])
            cmd = data[6:]
            cmd = cmd.decode("utf8")
            if cmd_number == 1:
                logger.info(f"收到的shell指令：{cmd}")
                th = subcmd(cmd)
                th.start()
            else:
                logger.info(f"收到指令号：{cmd_number}")
    except Exception as e:
        logger.error(f"异常：", e)
    finally:
        sock.close()


# server end

def parse_cli():
    parse = argparse.ArgumentParser()

    parse.add_argument("--server", action="store_true", help="start a server.")

    parse.add_argument("--address", action="store", default="", help="listen 地址")

    parse.add_argument("--port", action="store", type=int, default=11234, help="listen port")

    parse.add_argument("-t", "--type", type=int, default=1, help="1~60000 指令类型:1 为shell 指令")

    parse.add_argument("cmd", nargs="?", help="如果是shell指令的话，必需存在。")

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    parse.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)

    args = parse.parse_args()

    if args.parse:
        print(args)
        sys.exit(0)

    if args.debug:
        logger.setLevel(logging.DEBUG)

    return args


if __name__ == "__main__":
    
    args = parse_cli()

    if args.server:
        try:
            server(args.address, args.port)
        except KeyboardInterrupt:
            sys.exit(0)
    else:
        broadcast_cmd(args.port, args.type, args.cmd)

    


