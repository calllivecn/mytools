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
import logging
import struct
import socket
import socketserver


def getlogger(level=logging.INFO):
    fmt = logging.Formatter(
        "%(asctime)s %(filename)s:%(lineno)d %(message)s",
        datefmt="%Y-%m-%d-%H:%M:%S")
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    logger = logging.getLogger("cmd")
    logger.setLevel(level)
    logger.addHandler(stream)
    return logger

logger = getlogger()

def shell(cmd, timeout=5):

    try:
        recode = subprocess.call(cmd.split(), timeout=5)
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

bufsize = 1024

PROTOCOL_VERSION = 0x01
PROTCOL_HEADER = struct.Struct("!HHH")
"""
指令包装:
    version:    2byte,  
    cmd_number:   2byte, number=1 为 shell指令。0 不使用。
    cmd_len:    2byte,  cmd_number 为 1 时，指cmd的长度，否则为0。
    cmd: 
"""

def recv_cmd(sock):

    data, addr = sock.recvfrom(PROTCOL_HEADER.size)

    version, cmd_number, cmd_len = PROTCOL_HEADER.unpack(data)

    cmd = sock.recvfrom(bufsize)
    
    log = f"{addr} 接收到指令号：{cmd_number} -- "

    if cmd_len != 0:
        log.join(f"指令: {cmd}")
    
    logger.info(log)

    return cmd_number, cmd


def send_cmd(sock, cmd_number, cmd):

    cmd = cmd.encode()
    cmd_len = len(cmd)

    data = PROTCOL_HEADER.pack(PROTOCOL_VERSION, cmd_number, cmd_len)

    sock.sendto(PROTCOL_HEADER.pack())
    
    log = f"发送指令号：{cmd_number} -- "

    if cmd_len != 0:
        log.join(f"指令: {cmd}")

    logger.info(log)

    return cmd_number, cmd
