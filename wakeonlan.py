#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-19 14:33:29
# author calllivecn <calllivecn@outlook.com>


"""
wakeOnLAN工作原理：
    0. 前提：现在绝大多数的主板和网卡都是直接支持的。
    1. 在BIOS里设置wake on LAN 开启(的有主板还可以设置一个4或6字节的密码)。
    2. 接电源，插网线。（如果：工作了，网卡的指示灯一般会亮起。也有可以网卡没有指示灯。。。）


Wake On LAN 协议实现：
    0. 魔法数据包（Magic Packet）是一个广播性的帧（frame），透过端口7或端口9进行发送，且可以用无连接（Connectionless protocol）的通信协议（如UDP、IPX）来传递，不过一般而言多是用UDP。
    1. 在魔法数据包内，每次都会先有连续6个"FF"（十六进制，换算成二进制即：11111111）的数据，即：FF FF FF FF FF FF，在连续6个"FF"后则开始带出MAC地址信息，有时还会带出4字节或6字节的密码，一旦经由网卡侦测、解读、研判（广播）魔法数据包的内容，内容中的MAC地址、密码若与计算机自身的地址、密码吻合，就会引导唤醒、引导的程序。

IPv6 ff02::1组播：
    0. ipv6 组播地址
"""

import sys
import socket
import argparse
from struct import pack


BROADCAST_IPv4 = '255.255.255.255'
LOCAL_LINK_IPv6 = 'fe80::1'
LOCAL_LINK_IPv6 = 'ff02::1'

DEFAULT_PORT = 9  # 9 or 7


def magic_packet(mac):

    if len(mac) == 12:
        pass
    elif len(mac) == 17:
        sep = mac[2]
        mac = mac.replace(sep, '')
    else:
        raise ValueError('Incorrect MAC address format')

    # Pad the synchronization stream
    data = b'FFFFFFFFFFFF' + (mac * 16).encode()
    send_data = b''

    # Split up the hex values in pack
    for i in range(0, len(data), ):
        send_data += pack(b'B', int(data[i: i + 2], 16))
    return send_data


def get_all_ipv6_ifname(port):
    multicast_addrs = []
    for index, ifname in socket.if_nameindex():
        addr = socket.getaddrinfo(LOCAL_LINK_IPv6 + "%" + ifname, port, socket.AF_INET6,socket.SOCK_DGRAM, socket.SOL_UDP)[0][4]
        multicast_addrs.append((ifname, addr))
    return multicast_addrs


def send_packet(macs, ipv6, port, ifname=None):

    if ipv6:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    for mac in macs:
        packet = magic_packet(mac)
        #print(packet)
        if ipv6:

            if ifname:
                multicast_addr = socket.getaddrinfo(LOCAL_LINK_IPv6 + "%" + ifname, port, socket.AF_INET6,socket.SOCK_DGRAM, socket.SOL_UDP)[0][4]
                sock.sendto(packet, multicast_addr)
            else:
                for if_, multicast_addr in get_all_ipv6_ifname(port):
                    try:
                        sock.sendto(packet, multicast_addr)
                        print(f"{if_} -- ok.")
                    except Exception as e:
                        print(f"{if_} -- error: {e}")


        else:
            sock.sendto(packet, (BROADCAST_IPv4, port))

    sock.close()


def main():

    parse = argparse.ArgumentParser(
        description='Wake one or more computers using the wake on lan protocol.')

    parse.add_argument('--ipv6', action="store_true", default=False, help="ipv6 default: ipv4")

    parse.add_argument('--ifname', help="使用ipv6时，指定接口。(默认向所有ipv6接口发送)")

    parse.add_argument('-p', '--port',  metavar='port', type=int, choices=(7, 9), default=DEFAULT_PORT,
                        help='The port of the host to send the magic packet to 7 or 9(default 9)')

    parse.add_argument('macs', metavar='mac address', nargs='+',
                        help='The mac addresses or of the computers you are trying to wake.')

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    args = parse.parse_args()

    if args.parse:
        print(args)
        sys.exit(0)

    """
    if args.ipv6:
        if not args.ifname:
            print("使用ipv6时，必须指定接口")
            sys.exit(1)
    """

    send_packet(args.macs, args.ipv6, args.port, args.ifname)


if __name__ == '__main__':
    main()
