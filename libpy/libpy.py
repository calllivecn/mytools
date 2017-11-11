


import datetime
import sys



## 装饰器
import time
def runtime(func):
    def wapper(*args,**key):
        start = time.time()
        result = func(*args,**key)
        end = time.time()
        print(func.__name__,'运行时间:',end - start)
        return result
    return wapper





import os
def getabspath(f):
    """getabspath(file) --> (abspath , filename)"""
    p = os.path.abspath(f)
    p = os.path.split(p)
    return p


import termios,os,copy
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    new_settings = copy.deepcopy(old_settings)
    new_settings[3] &= ~(termios.ICANON | termios.ECHO) # | termios.ISIG)
    #new_settings[6][termios.VMIN] = 1
    #new_settings[6][termios.VTIME] = 0
    termios.tcsetattr(fd,termios.TCSADRAIN,new_settings)
    
    ch = os.read(fd,8)

    termios.tcsetattr(fd,termios.TCSADRAIN,old_settings)

    return ch


