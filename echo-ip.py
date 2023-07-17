#!/usr/bin/env python3
# coding=utf-8
# date 2020-10-22 16:00:22
# author calllivecn <c-all@qq.com>

import sys
import asyncio
import logging
from datetime import datetime

def timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H:%M:%S.%f")

def getlogger(level=logging.INFO):
    logger = logging.getLogger("echo-ip")
    # formatter = logging.Formatter("%(asctime)s %(levelname)s %(filename)s:%(funcName)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
    formatter = logging.Formatter("%(levelname)s %(filename)s:%(funcName)s:%(lineno)d %(message)s")
    consoleHandler = logging.StreamHandler(stream=sys.stdout)
    #logger.setLevel(logging.DEBUG)

    consoleHandler.setFormatter(formatter)

    # consoleHandler.setLevel(logging.DEBUG)
    logger.addHandler(consoleHandler)
    logger.setLevel(level)
    return logger

logger = getlogger()


async def echo_ip(r, w):
    result = w.get_extra_info("peername")
    ip = result[0]
    
    w.write(ip.encode()+ b"\n")
    try:
        await w.drain()
    except ConnectionResetError:
        logger.info(f"{ip} ConnectReset...")
    
    logger.info(f"[{ip}]")
    
    w.close()
    await w.wait_closed()


async def main(addr, port=1121):

    server = await asyncio.start_server(echo_ip, addr, port, reuse_address=True)

    async with server:
        await server.serve_forever()

def start():
    
    logger.info(f"Usage: echo-ip.py [ipv4=0.0.0.0 or ipv6=:: address] [port=1121]")
    
    try:
        addr = sys.argv[1]
    except Exception:
        # addr = "0.0.0.0" # ipv4
        # addr = "::" # ipv6
        addr = "*" # 双栈...

    try:
        port = int(sys.argv[2])
    except Exception:
        port = 1121

    logger.info(f"start listen: [{addr}] port: {port}")
    
    asyncio.run(main(addr, port))


if __name__ == "__main__":
    try:
        start()
    except KeyboardInterrupt:
        logger.info("exit")

