#!/usr/bin/env python3
#coding=utf-8



import sqlite3,os
from argparse import ArgumentParser
from os.path import abspath,isdir,join,isfile,getsize
SGITERM = 15 # from signal import SIGTERM
from os import kill
from hashlib import sha512
from multiprocessing import Process,Queue
from threading import Thread

CPU_COUNT = os.cpu_count()

argparse = ArgumentParser(description='通过sha512值检测多个目录下有无相同文件.',add_help=True)

argparse.add_argument('-d',dest='delete',action="store_true",help='相同文件直接删除')
argparse.add_argument('-i',dest='ask',action="store_true",default=True,help='询问是否删除相同文件(default)')
argparse.add_argument('-p',dest='out',action="store_true",help='输出相同文件')
argparse.add_argument('-P',dest='process',type=int,metavar='CPU',default=CPU_COUNT - 1,help='使用几个CPU核心')
argparse.add_argument('dirs',nargs='*',action="store",help='目录')

args = argparse.parse_args()

# check dirs 是否全是目录

def checkDirs(lists):
    flag=False
    not_dir=[]
    for d in lists:
        if not isdir(d):
            flag=True
            not_dir.append(d)
    if flag:
        print('不是目录:')
        for d in not_dir:
            print(d,'',end='')
        print()
        sys.exit(1)
    
    if args.process > CPU_COUNT:
        print('CPU MAX : {}'.format(CPU_COUTN))
        sys.exit(1)

checkDirs(args.dirs)

#print(args);sys.exit(0)

task_put = Queue(128)
task_get = Queue(128)
task_end_flag = (0,0)

FILE_SHA_VALUES={}


def __sha512(file_):
    sha = sha512()
    READ_BUF = 4*1<<20
    with open(file_,'rb') as f:
        data = True
        while data:
            data = f.read(READ_BUF)
            sha.update(data)
    return sha.hexdigest()

def taskPut(PATH_list):
    
    for PATH in PATH_list:
        PATH = abspath(PATH)
        for root,directory,files in os.walk(PATH):
            for f in files:
                abs_path = join(root,f)
                if isfile(abs_path):
                    task_put.put(abs_path)
    
    task_put.put(task_end_flag)

def taskSha512():
    while True:
        file_path = task_put.get() # 从 task_put 拿任务
        if file_path == task_end_flag:
            task_put.put(task_end_flag)
            task_get.put(task_end_flag)
            #print('任务结束')
            return
        
        #print('拿到文件{}'.format(file_path))
        try:
            sha = __sha512(file_path)
        except FileNotFoundError:
            print('没有找到文件{}'.format(file_path))

        task_get.put((file_path,sha))



def file_exists(value,file1,file2):
    print('存在相同文件:')
    print('[1]',file1)
    print('[2]',file2)

    if args.out:
        return 1

    if args.delete:
        os.remove(file1)
        print('删除',file1)
        return 1

    in_flag=False
    while not in_flag:
        
        y = input('删除那个<1,2,N>? ')
        
        if y == '':
            y='n'

        if y == '1':
            
            try:
                os.remove(file1)
            except FileNotFoundError:
                print('删除文件没找到{}'.format(file1))
            return file2

            in_flag = True
        elif y == '2':
            try:
                os.remove(file2)
            except FileNotFoundError:
                print('删除文件没找到{}'.format(file2))
            return file1

            in_flag = True
        elif y == 'n' or y == 'N':
            in_flag = True


def valueCmp():
    
    exit_process=0

    while True:
        
        f , value = task_get.get()
        if f == 0:
            exit_process+=1
            if exit_process == args.process:
                return
        else:
            if value in FILE_SHA_VALUES:
                f = file_exists(value,f,FILE_SHA_VALUES[value])
                if f == 1:
                    pass
                else:
                    FILE_SHA_VALUES[value] = f
            else:
                FILE_SHA_VALUES[value] = f



def exitProgram(mp_pids):
    for pid in mp_pids:
        kill(pid,SIGTERM)


# main 

mp_pid_list=[]
for p in range(args.process):
    mp = Process(target=taskSha512)
    mp.start()
    mp_pid_list.append(mp.pid)


th = Thread(target=taskPut,args=(args.dirs,),daemon=True)
th.start()


try:
    valueCmp()
except KeyboardInterrupt:
    exitProgram(mp_pid_list)
    
