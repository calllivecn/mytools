#!/usr/bin/env python3
# coding=utf-8
# date 2017-10-12 08:19:53
# https://github.com/calllivecn

import sys
import os
import argparse
import logging
from pprint import pprint,pformat
from os.path import getsize,join,exists,isdir,isfile,islink,split

parse = argparse.ArgumentParser(description='secure file deletion')

parse.add_argument('files',nargs='+',help='files and dirs')
parse.add_argument('-v','--verbose',action="store_true", help='DEBUG mode')
parse.add_argument('-f','--force',action="store_true", help='try force delete')

args=parse.parse_args()
#print(args)

logger = logging.getLogger()
stream = logging.StreamHandler(sys.stdout)
fmt = logging.Formatter("%(asctime)s %(filename)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
stream.setFormatter(fmt)
logger.addHandler(stream)

if args.verbose:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


def check_files():
    not_exists_lists=[]
    for f_d in args.files:
        logger.debug(f"check : {f_d}")
        if not exists(f_d):
            not_exists_lists.append(f_d)

    if len(not_exists_lists) > 0:
        for f in not_exists_lists:
            logger.info(f"{f} file not exists")

        sys.exit(1)

check_files()

def clear_filename(filename):
    char_id = 48
    char = chr(char_id)

    path , filename = split(filename)

    fn_len = len(filename)
    clear_fn = char * fn_len

    while exists(join(path,clear_fn)):
        clear_fn += char
        if len(clear_fn) > 128:
            char_id +=1
            char = chr(char_id)
            clear_fn = char * fn_len
    
    logger.debug("{} --> ".format(join(path,filename)) + join(path,clear_fn))

    os.rename(join(path,filename),join(path,clear_fn))

    logger.debug("remove: " + join(path,clear_fn))

    if isfile(join(path,clear_fn)):
        os.remove(join(path,clear_fn))
    if isdir(join(path,clear_fn)):
        try:
            os.rmdir(join(path,clear_fn))
        except OSError:
            logger.info("cannot delete Directory not empty: " + join(path,clear_fn))

    if islink(join(path,clear_fn)):
        os.remove(join(path,clear_fn))


l=bytes(4096)
def remove(file__):

    if islink(file__):
        clear_filename(file__)
        return

    file_size = getsize(file__)

    count, c = divmod(file_size, 4096)
    if c > 0:
        count += 1


    if not os.access(file__, os.R_OK | os.W_OK):
        mode = os.stat(file__).st_mode
        try:
            os.chmod(file__, mode | 0o600)
        except PermissionError:
            logger.info("cannot delete {}: ".format(file__) + "not permission")
            return

    fp = open(file__,'r+b')
    
    for tmp in range(count):
        fp.write(l)
        fp.flush()
        
    fp.close()
    
    clear_filename(file__)


def rm_dir_tree(dir__):
    for r,d,f in os.walk(dir__,topdown=False):
        for f2 in f:
            remove(join(r,f2))

        for dir_ in d:
            clear_filename(join(r,dir_))

    clear_filename(r)
    

for f in args.files:
    f = f.rstrip('/')
    if isfile(f) or islink(f):
        remove(f)
    elif isdir(f):
        rm_dir_tree(f)
    else:
        logger.info(f + 'not is dir or normal file,not delete')
