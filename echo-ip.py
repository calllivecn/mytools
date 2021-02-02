#!/usr/bin/env python3
# coding=utf-8
# date 2020-10-22 16:00:22
# author calllivecn <c-all@qq.com>

import sys
# import time
import socket
# import asyncio
from datetime import datetime
from threading import Thread

'''
async def echo_ipv4(r, w):
    ip, port = w.get_extra_info("peername")
    # result = w.get_extra_info("peername")
    # print(f"peername --> {result}")
    w.write(ip.encode()+ b"\n")
    w.close()


async def main_ipv4(addr, port=1121):

    server = await asyncio.start_server(echo_ip, addr, port, reuse_address=True)

    async with server:
        await server.serve_forever()

async def main(addr, port=1121):

    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.bind((addr, port))

    server = await asyncio.start_server(echo_ip, sock=sock, reuse_address=True)

    async with server:
        await server.serve_forever()

def start():
    try:
        addr = int(sys.argv[1])
    except Exception:
        addr = "0.0.0.0"
        # addr = "::"

    try:
        port = int(sys.argv[2])
    except Exception:
        port = 1121

    print(f"start listen: {addr} port: {port}")
    
    asyncio.run(main_ipv4(addr, port))


if __name__ == "__main__":
    try:
        start()
    except KeyboardInterrupt:
        print("exit")

'''

def timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H:%M:%S.%f")


def echo_ipv4(addr="0.0.0.0", port=1121):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
    # sock.setsockopt(socket.SOL_SOCKET, socket.TCP_NODELAY, True)
    sock.bind((addr, port))
    sock.listen(512)

    while True:
        client, addr = sock.accept()
        ip, port = client.getpeername()
        client.send(ip.encode() + b"\n")
        print(f"{timestamp()} {ip}")
        client.close()


def echo_ipv6(addr="::", port=1121):
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
    # sock.setsockopt(socket.SOL_SOCKET, socket.TCP_NODELAY, True)
    sock.bind((addr, port))
    sock.listen(512)

    while True:
        client, addr = sock.accept()
        ip, port, notknown, scope = client.getpeername()
        client.send(ip.encode() + b"\n")
        print(f"{timestamp()} {ip}")
        client.close()


def main():

    proc = []
    
    th4 = Thread(target=echo_ipv4, daemon=True)
    th4.start()
    proc.append(th4)

    th6 = Thread(target=echo_ipv6, daemon=True)
    th6.start()
    proc.append(th4)

    for p in proc:
        p.join()


if __name__ == "__main__":
    main()
