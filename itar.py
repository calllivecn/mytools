#!/usr/bin/env python3
#coding=utf-8
# date 2018-04-09 13:46:24
# author calllivecn <c-all@qq.com>


import os
import sys
import time
import argparse
from os.path import split,join,isfile,isdir,exists,abspath,islink
from queue import Queue
from threading import Thread

#from itarlib import ItarComp,ItarDecomp
from libpy.itarlib import *

PROGRAM = sys.argv[0]


def check_member_names(member):
    for name in member:
        if name.startswith('/'):
            print("Removing leading `/' from member names")

def create_itar(args):

    def preprocess(fullname):
        if fullname == args.itar:
            print("{}: {} is archive file skip".format(PROGRAM,fullname))
            return
        
        if islink(fullname):
           print("{}: is a symbolic link ... skip".format(fullname)) 
           return

        if args.verbose:
            print(fullname)

        itar.comp_file(fullname) 

    stream_put = Queue(100)

    itar = ItarComp(stream_put)

    def addfile_itar():

        check_member_names(args.files)

        for f1 in args.files:
           #print("com_file({})".format(f1))
           if isfile(f1):
               preprocess(f1)
           else:
               for root,dirs,files in os.walk(f1):
                   for f2 in files:
                       #print("com_file({})".format(join(root,f2)))
                       preprocess(join(root,f2))
        # is done
        stream_put.put(ISDONE)

    def getfile_stream():
        
        with open(args.itar,'wb') as fw:
            while True:
                data = stream_put.get()
                if data == ISDONE:
                    return
                fw.write(data)

    th = Thread(target=addfile_itar,daemon=True)
    th.start()

    getfile_stream() 

    # ------------------------------------------------------


def extract_itar(args):

    stream_put = Queue(100)

    def create_file(fullname, mtime):
        if args.verbose:
            print(fullname)
        prefix, _ = split(fullname)
        if not exists(prefix):
            os.makedirs(prefix)

        fp = open(fullname,'wb')
        # change fp file mtime
        #
        #
        return fp

    itar = ItarDecomp(args.itar,stream_put)

    th = Thread(target=itar.decomp_file,daemon=True)
    th.start()

    while True:
        data = stream_put.get()
        if isinstance(data,tuple):
            fileobj = create_file(data[0],data[3])
        elif isinstance(data,bytes):
            fileobj.write(data)
        elif data == FILEISDONE:
            #print(join(prefix,name))
            fileobj.close()
        elif data == ISDONE:
            break


def chk_fullname(fullname):
    if ( isfile(fullname) or isdir(fullname) ) and not islink(fullname):
        return fullname
    else:
        raise argparse.ArgumentTypeError("is not a reguler file")

def itar(itarname):
    if not exists(itarname):
        raise argparse.ArgumentTypeError(itarname + " not exists")
    else:
        return abspath(itarname)

parse = argparse.ArgumentParser(usage=\
" Using : %(prog)s <options> [file|directory]...")

groups = parse.add_mutually_exclusive_group(required=True)

groups.add_argument("-c",dest="create",action="store_true",
        help="create a itar file")

groups.add_argument("-x",dest="extract",action="store_true",
        help="extract itar file")

parse.add_argument("-C",dest="chdir",default=".",help="change work directory")

parse.add_argument("-f",dest="itar",required=True,help="itar filename suffix is *.itar")

parse.add_argument("-v",dest="verbose",action="count",help="print verbose info")

parse.add_argument("files",nargs="*",type=chk_fullname,help="file or dirs ...")

args = parse.parse_args()

#print(args)

# ----------------------------------------------------------


args.itar = abspath(args.itar)

os.chdir(args.chdir)

if args.create:
    create_itar(args)
elif args.extract:
    extract_itar(args)
