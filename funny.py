#!/usr/bin/env python3
#coding=utf-8


import time,sys
import fileinput
import random
S=' '.join(sys.argv[1:])
#print(S)

def randint(char):
    len_char = len(char.encode())
    if len_char <= 1:
        return random.randint(10,20)/100
    elif 1 < len_char <=2:
        return random.randint(20,30)/100
    else:
        return random.randint(30,50)/100


for char in S:
    time.sleep(randint(char))
    print(char,sep='',end='',flush=True)

print()


