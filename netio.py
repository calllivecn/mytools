#!/usr/bin/env python3
#coding=utf-8
# update 2018-05-29 20:29:37
# author calllivecn <c-all@qq.com>



import os
import sys
import time

ifname_dir='/sys/class/net/'

ifname_rx='statistics/rx_bytes'

ifname_tx='statistics/tx_bytes'

ifname_rx_packets='statistics/rx_packets'

ifname_tx_packets='statistics/tx_packets'

class Interface:
    rx_speed = 0
    tx_speed = 0
    rx_packets = 0
    tx_packets = 0

    TB = 1<<40
    GB = 1<<30
    MB = 1<<20
    KB = 1<<10
    def __init__(self,ifname,time=1,unit=KB):
        '''
        time : time interval
        unit : unit in B ,K ,M ,G
        '''
        self.ifname = ifname
        self.ifname_rx = os.path.join(ifname_dir, ifname, ifname_rx)
        self.ifname_tx = os.path.join(ifname_dir, ifname, ifname_tx)
        self.ifname_rx_packets = os.path.join(ifname_dir, ifname, ifname_rx_packets)
        self.ifname_tx_packets = os.path.join(ifname_dir, ifname, ifname_tx_packets)
        
        self.getBytesAndPackets()

        self.time = time
        self.unit = unit

    def getBytesAndPackets(self):
        try:
            f1_rx = open(self.ifname_rx)
            f1_tx = open(self.ifname_tx)
            f2_rx = open(self.ifname_rx_packets)
            f2_tx = open(self.ifname_tx_packets)
            b_rx = f1_rx.read()
            b_tx = f1_tx.read()
            p_rx = f2_rx.read()
            p_tx = f2_tx.read()
        except FileNotFoundError as e:
            raise e

        f1_rx.close()
        f1_tx.close()
        f2_rx.close()
        f2_tx.close()

        self.init_rx = int(b_rx)
        self.init_tx = int(b_tx)
        self.init_p_rx = int(p_rx)
        self.init_p_tx = int(p_tx)

        self.rx_sum = self.init_rx
        self.tx_sum = self.init_tx
        self.p_rx_sum = self.init_p_rx
        self.p_tx_sum = self.init_p_tx
    
    
    def speed(self):
        rx = self.init_rx
        tx = self.init_tx
        p_rx = self.init_p_rx
        p_tx = self.init_p_tx

        self.getBytesAndPackets()
        self.rx_speed = round( self.mod(self.init_rx - rx) / self.time , 2)
        self.tx_speed = round( self.mod(self.init_tx - tx) / self.time , 2)
        
        self.rx_packets = int( (self.init_p_rx - p_rx) / self.time )
        self.tx_packets = int( (self.init_p_tx - p_tx) / self.time )

    def statistics(self):
        pass
        
        
    def __str__(self):
        return '{:<16}{:>12}{:>12}{:>12}{:>12}{:>12}{:>12}'.format(
                self.ifname,
                str(self.rx_packets),
                str(self.tx_packets),
                str(self.rx_speed),
                str(self.tx_speed),
                str(self.statistic_unit(self.rx_sum)),
                str(self.statistic_unit(self.tx_sum))
                )

    def statistic_unit(self,num):
        if num >= self.TB:
            value = round(num/self.TB,2)
            unit = 'TB'
        elif num >= self.GB:
            value = round(num/self.GB,2)
            unit = 'GB'
        elif num >= self.MB:
            value = round(num/self.MB,2)
            unit = 'MB'
        elif num >= self.KB:
            value = round(num/self.KB,2)
            unit = 'KB'
        else:
            value = num
            unit = 'B'

        return str(value) + unit

    def mod(self,s):
        if self.unit == self.KB:
            return round(s/self.unit,2)
        elif self.unit == self.MB:
            return round(s/self.unit,2)
        elif self.unit == self.GB:
            return round(s/self.unit,2)

def getiface():
    ifs = []
    for f in os.listdir(ifname_dir):
        if_ = os.path.join(ifname_dir, f)
        
        if_rx = os.path.join(if_, ifname_rx)
        if_tx = os.path.join(if_, ifname_tx)

        if_rx_packets = os.path.join(if_,ifname_rx_packets)
        if_tx_packets = os.path.join(if_,ifname_tx_packets)

        if os.path.isfile(if_rx) and os.path.isfile(if_tx) and os.path.isfile(if_rx_packets) and os.path.isfile(if_tx_packets):
            ifs.append(f)
    return ifs

def clear():
    CLEAR=0x1b63.to_bytes(2,'big')
    fd=sys.stdout.fileno()
    os.write(fd,CLEAR)

def main():
    import argparse
    parse = argparse.ArgumentParser(usage='Usage: %(prog)s [-t <1>] [ -i <iface> ] [-k|-m|-g] ')
                                #add_help=True)
    parse.add_argument('-i','--ifname',metavar='',nargs='+')
    parse.add_argument('-t',default=1,type=float)
    group = parse.add_mutually_exclusive_group()
    group.add_argument('-k',action="store_true")
    group.add_argument('-m',action="store_true")
    group.add_argument('-g',action="store_true")
    args = parse.parse_args()
    #print(args)
    #exit(0)
    if args.k:
        UNIT='KB'
        unit=1<<10
    elif args.m:
        UNIT='MB'
        unit=1<<20
    elif args.g:
        UNIT='GB'
        unit=1<<30
    else:
        UNIT='KB'
        unit=1<<10

    T=args.t

    if args.ifname is not None:
        ifnames=[]
        for ifs in args.ifname:
            #print(os.path.join(ifname_dir,ifs))
            if os.path.exists(os.path.join(ifname_dir,ifs)):
                ifnames.append(Interface(ifs,time=T,unit=unit))
            else:
                print('interface',ifs,'not found')
                exit(1)

    else:
        ifnames = []
        for ifs in getiface():
            ifnames.append(Interface(ifs,time=T,unit=unit))

    while True:
        clear()
        print('{:<16}{:>12}{:>12}{:>12}{:>12}{:>12}{:>12}'.format('iface','Rxpck/s','Txpck/s','Rx{}/s'.format(UNIT),'Tx{}/s'.format(UNIT),'Rxstatis','Txstatis'))
        for ifs in ifnames:
            try:
                ifs.speed()
            except FileNotFoundError:
                ifnames.remove(ifs)
                continue
            print(ifs)

        time.sleep(T)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass




