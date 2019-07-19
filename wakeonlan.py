#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-19 14:33:29
# author calllivecn <c-all@qq.com>


"""
wakeOnLAN工作原理：
    0. 前提：现在绝大多数的主板和网卡都是直接支持的。
    1. 在BIOS里设置wake on LAN 开启(的有主板还可以设置一个4或6字节的密码)。
    2. 接电源，插网线。（如果：工作了，网卡的指示灯一般会亮起。也有可以网卡没有指示灯。。。）


Wake On LAN 协议实现：
    0. 魔法数据包（Magic Packet）是一个广播性的帧（frame），透过端口7或端口9进行发送，且可以用无连接（Connectionless protocol）的通信协议（如UDP、IPX）来传递，不过一般而言多是用UDP。
    1. 在魔法数据包内，每次都会先有连续6个"FF"（十六进制，换算成二进制即：11111111）的数据，即：FF FF FF FF FF FF，在连续6个"FF"后则开始带出MAC地址信息，有时还会带出4字节或6字节的密码，一旦经由网卡侦测、解读、研判（广播）魔法数据包的内容，内容中的MAC地址、密码若与计算机自身的地址、密码吻合，就会引导唤醒、引导的程序。

"""

import socket
import argparse
from struct import pack


BROADCAST_IP = '255.255.255.255'
DEFAULT_PORT = 9 # 9 or 7


def magic_packet(macaddress):

    if len(macaddress) == 12:
        pass
    elif len(macaddress) == 17:
        sep = macaddress[2]
        macaddress = macaddress.replace(sep, '')
    else:
        raise ValueError('Incorrect MAC address format')

    # Pad the synchronization stream
    data = b'FFFFFFFFFFFF' + (macaddress * 16).encode()
    send_data = b''

    # Split up the hex values in pack
    for i in range(0, len(data), 2):
        send_data += pack(b'B', int(data[i: i + 2], 16))
    return send_data


def send_packet(*macs, **kwargs):

    packets = []
    ip = kwargs.pop('ip_address', BROADCAST_IP)
    port = kwargs.pop('port', DEFAULT_PORT)
    for k in kwargs:
        raise TypeError('send_magic_packet() got an unexpected keyword '
                        'argument {!r}'.format(k))

    for mac in macs:
        packet = magic_packet(mac)
        packets.append(packet)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.connect((ip, port))
    for packet in packets:
        sock.send(packet)
    sock.close()


def main():

    parser = argparse.ArgumentParser(description='Wake one or more computers using the wake on lan protocol.')
    parser.add_argument('-i', metavar='ip', default=BROADCAST_IP, help='The ip address of the host to send the magic packet to.(default {})'.format(BROADCAST_IP))
    parser.add_argument('-p', metavar='port', type=int, default=DEFAULT_PORT, help='The port of the host to send the magic packet to (default 9)')

    parser.add_argument('macs', metavar='mac address', nargs='+', help='The mac addresses or of the computers you are trying to wake.')

    args = parser.parse_args()

    send_packet(*args.macs, ip_address=args.i, port=args.p)


if __name__ == '__main__':
    main()
