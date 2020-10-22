#!/usr/bin/env python3
# coding=utf-8
# date 2020-10-22 16:00:22
# author calllivecn <c-all@qq.com>

import sys
import asyncio


async def echo_ip(r, w):
    ip, port = w.get_extra_info("peername")
    w.write(ip.encode()+ b"\n")
    w.close()


async def main(addr, port=1121):

    server = await asyncio.start_server(echo_ip, addr, port, reuse_address=True)

    async with server:
        await server.serve_forever()


def start():
    try:
        addr = int(sys.argv[1])
    except Exception:
        addr = "0.0.0.0"

    try:
        port = int(sys.argv[2])
    except Exception:
        port = 1121

    print(f"start listen: {addr} port: {port}")
    
    asyncio.run(main(addr, port))


if __name__ == "__main__":
    try:
        start()
    except KeyboardInterrupt:
        print("exit")
