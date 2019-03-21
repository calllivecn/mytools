#!/usr/bin/env python3
#coding=utf-8

import sys
import os
from os import path
import argparse
import tarfile


parse=argparse.ArgumentParser(
description=r'''GNU %(prog)s saves many files together into a single tape or disk archive,
and can restore individual files from the archive.

Examples:
  tar -cf archive.tar foo bar  # Create archive.tar from files foo and bar.
  tar -tvf archive.tar         # List all files in archive.tar verbosely.
  tar -xf archive.tar          # Extract all files from archive.tar.
''',
usage='%(prog)s [option...] [FILE]...',
epilog="\n",
)


group1 = parse.add_mutually_exclusive_group()

group1.add_argument('-c','--create',action='store_true',help='create a new archive')

group1.add_argument('-x','--extract',action='store_true',help='extract files from an archive')

group1.add_argument('-t','--list',action='store_true',help='list the contents of an archive')

parse.add_argument('-f','--file',action='store',required=True,help='use archive file or device ARCHIVE')

parse.add_argument('-v','--verbose',action='count', default=0,help='verbosely list files processed')

parse.add_argument('files',nargs='*',help='arvchive file or directory')

parse.add_argument('-C','--directory',action='store',default=os.getcwd(),help='change to directory DIR')

groups = parse.add_mutually_exclusive_group()

groups.add_argument('-z','--gzip',action='store_true',help='filter the archive through gzip')

groups.add_argument('-j','--bzip2',action='store_true',help='filter the archive through bzip2')

groups.add_argument('-J','--xz',dest='xz',action='store_true',help='filter the archive through xz')

#parse.add_argument('--exclude',nargs='*',help='exclude files, given as a PATTERN')


args = parse.parse_args()

print(args)

def compress_safe_path(filename):
    # 它会自动去掉路径，/ 和C:\这样的开头。
    realpath = path.realpath(filename)
    _, memberpath = path.split(realpath)
    dirname = path.dirname(realpath)

    return memberpath


def decompress_safe_path(filename):
    realpath = path.realpath(filename)
    return realpath

if args.create or args.extract:
    os.chdir(args.directory)

if args.create and args.files:
    compress='w'

    if args.gzip:
        compress='w:gz'
    elif args.bzip2:
        compress='w:bz2'
    elif args.xz:
        compress='w:xz'

    fp = tarfile.open(args.file, compress, debug=args.verbose)
    for f in args.files:
        memberpath = compress_safe_path(f)
        fp.add(f, memberpath)
        #print("add({}, {})".format(f, memberpath))

    fp.close()         

elif args.extract:
    decompress='r'
    
    if args.gzip:
        decompress='r:gz'
    elif args.bzip2:
        decompress='r:bz2'
    elif args.xz:
        decompress='r:xz'

    fp=tarfile.open(args.file,decompress, debug=args.verbose)

    #fp.extract(f,args.directory)
    safe_path = decompress_safe_path(
    fp.extractall()

    fp.close()

elif args.list:
    decompress='r'
    
    if args.gzip:
        decompress='r:gz'
    elif args.bzip2:
        decompress='r:bz2'
    elif args.xz:
        decompress='r:xz'

    fp=tarfile.open(args.file, decompress, debug=args.verbose)

    fp.list(verbose=args.verbose)

    fp.close()

else:

    sys.exit(1)
