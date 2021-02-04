#!/usr/bin/env python3
# coding=utf-8
# date 2020-10-22 16:00:22
# author calllivecn <c-all@qq.com>

import sys
# import time
import socket
import asyncio
from datetime import datetime
# from threading import Thread

def timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H:%M:%S.%f")

async def echo_ip(r, w):
    result = w.get_extra_info("peername")
    ip = result[0]
    
    w.write(ip.encode()+ b"\n")
    await w.drain()
    
    print(f"{timestamp()} [{ip}]")
    
    w.close()
    await w.wait_closed()


async def main(addr, port=1121):

    server = await asyncio.start_server(echo_ip, addr, port, reuse_address=True)

    async with server:
        await server.serve_forever()

def start():
    
    print(f"Usage: {sys.argv[0]} [ipv4=0.0.0.0 or ipv6=:: address] [port=1121]")
    
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

    print(f"start listen: [{addr}] port: {port}")
    
    asyncio.run(main(addr, port))


if __name__ == "__main__":
    try:
        start()
    except KeyboardInterrupt:
        print("exit")


'''

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
        ip, port, flowinfo, scope_id = client.getpeername()
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

'''