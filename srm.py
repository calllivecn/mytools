#!/usr/bin/env python3
# coding=utf-8
# date 2017-10-12 08:19:53
# update 2019-06-06-12:55:07
# https://github.com/calllivecn

import os
import sys
import mmap
import argparse
import logging
from os.path import getsize, join, exists, isdir, isfile, islink, split

parse = argparse.ArgumentParser(description='secure file deletion')

parse.add_argument('files',nargs='+',help='files and dirs')
parse.add_argument('-v','--verbose',action="store_true", help='DEBUG mode')
parse.add_argument('-f','--force',action="store_true", help='try force delete')

args=parse.parse_args()
#print(args)

logger = logging.Logger(sys.argv[0])
stream = logging.StreamHandler(sys.stdout)
fmt = logging.Formatter("%(filename)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
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

    fn_len = len(filename.encode("utf-8"))
    clear_fn = char * fn_len

    while exists(join(path,clear_fn)):
        clear_fn += char
        if len(clear_fn) > 128:
            char_id +=1
            char = chr(char_id)
            clear_fn = char * fn_len
    
    logger.debug("rename: {} --> {}".format(join(path,filename), join(path,clear_fn)))

    os.rename(join(path,filename),join(path,clear_fn))

    if isfile(join(path,clear_fn)):
        os.remove(join(path,clear_fn))
    if isdir(join(path,clear_fn)):
        try:
            os.rmdir(join(path,clear_fn))
        except OSError:
            logger.warning("cannot delete Directory not empty: " + join(path,clear_fn))

    if islink(join(path,clear_fn)):
        logger.debug("remove link file: {}".format(join(path,clear_fn)))
        os.remove(join(path,clear_fn))


# blksize is 1M
def memory_alingment(blksize=1048576):
    m = mmap.mmap(-1, blksize)
    m.write(bytes(blksize))
    mv = memoryview(m)
    return mv


def getfsblksize(filename):

    if hasattr(os, "statvfs"):
        fs_blksize = os.statvfs(filename).f_bsize
    else:
        fs_blksize = 4096

    return fs_blksize

def fswrite(fp, blksize):
    os.write(fp, BUF[0:blksize])

def remove(file__):

    global BUF

    logger.debug("remove: " + file__)

    if islink(file__):
        clear_filename(file__)
        return

    file_size = getsize(file__)

    if not os.access(file__, os.R_OK | os.W_OK):
        mode = os.stat(file__).st_mode
        try:
            os.chmod(file__, mode | 0o600)
        except PermissionError:
            logger.warning("cannot delete {}: ".format(file__) + "not permission")
            return

    try:
        if hasattr(os, "O_DIRECT"):
            fp = os.open(file__, os.O_RDWR | os.O_DIRECT)
        else:
            fp = os.open(file__, os.O_RDWR)
    except Exception as e:
        logger.error(e)
        return 

    if file_size <= len(BUF):

        fsblksize = getfsblksize(file__)

        count, c = divmod(file_size, fsblksize)

        if count == 0:
            os.write(fp, BUF[0:fsblksize])
        elif c > 0:
            count += 1
            os.write(fp, BUF[0:fsblksize*count])
        
    else:

        count, c = divmod(file_size, len(BUF))

        if c > 0:
            count += 1

        for tmp in range(count):
            os.write(fp, BUF)

    os.fsync(fp)

    os.close(fp)
    
    clear_filename(file__)


def rm_dir_tree(dir__):
    for r,d,f in os.walk(dir__,topdown=False):
        for f2 in f:
            remove(join(r,f2))

        for dir_ in d:
            clear_filename(join(r,dir_))

    clear_filename(r)
    

BUF = memory_alingment()

for f in args.files:
    f = f.rstrip('/')
    if isfile(f) or islink(f):
        remove(f)
    elif isdir(f):
        rm_dir_tree(f)
    else:
        logger.warning(f + 'not is dir or normal file,not delete')

