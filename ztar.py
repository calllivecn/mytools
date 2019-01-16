#!/usr/bin/env python3
#coding=utf-8


import tarfile,sys,os,argparse

parse=argparse.ArgumentParser(
description=r'''GNU %(prog)s saves many files together into a single tape or disk archive,
and can restore individual files from the archive.

Examples:
  tar -cf archive.tar foo bar  # Create archive.tar from files foo and bar.
  tar -tvf archive.tar         # List all files in archive.tar verbosely.
  tar -xf archive.tar          # Extract all files from archive.tar.
''',usage='%(prog)s [option...] [FILE]...'
)


parse.add_argument('-c','--create',action='store_true',help='create a new archive')

parse.add_argument('-x','--extract',action='store_true',help='extract files from an archive')

parse.add_argument('-t','--list',action='store_true',help='list the contents of an archive')

parse.add_argument('-f','--file',action='store',required=True,help='use archive file or device ARCHIVE')

parse.add_argument('-v','--verbose',action='count',help='verbosely list files processed')

parse.add_argument('files',nargs='*',help='arvchive file or directory')

parse.add_argument('-C','--directory',action='store',default=os.getcwd(),help='change to directory DIR')

groups = parse.add_mutually_exclusive_group()

groups.add_argument('-z','--gzip',action='store_true',help='filter the archive through gzip')

groups.add_argument('-j','--bzip2',action='store_true',help='filter the archive through bzip2')

groups.add_argument('-J','--xz',dest='xz',action='store_true',help='filter the archive through xz')

#parse.add_argument('--exclude',nargs='*',help='exclude files, given as a PATTERN')


args=parse.parse_args()

#print(args)

if args.create and args.files :
    compress='w'
    
    if args.gzip:
        compress='w:gz'
    elif args.bzip2:
        compress='w:bz2'
    elif args.xz:
        compress='w:xz'

    fp=tarfile.open(args.file,compress)
    for f in args.files:
        if os.path.isfile(f):
            if args.verbose: print(f)
            fp.add(f)
        elif os.path.isdir(f):
            for root,dirs,files in os.walk(f):
                for file2 in files:
                    if args.verbose: print(os.path.join(root,file2))
                    fp.add(os.path.join(root,file2))
        else:
                print(f,': is not file or directory')
                continue
    fp.close()            
            

elif args.extract :
    decompress='r'
    
    if args.gzip:
        decompress='r:gz'
    elif args.bzip2:
        decompress='r:bz2'
    elif args.xz:
        decompress='r:xz'

    fp=tarfile.open(args.file,decompress)
    for f in fp.getnames():
        if os.path.isdir(args.directory):
            if args.verbose:
                print(f)
            fp.extract(f,args.directory)
        elif args.directory==None :
            if args.verbose:
                print(f)
            fp.extract(f,'.')
        else:
            print(args.directory,'not a directory, exited')
            sys.exit(2)
    fp.close()

elif args.list :
    decompress='r'
    
    if args.gzip:
        decompress='r:gz'
    elif args.bzip2:
        decompress='r:bz2'
    elif args.xz:
        decompress='r:xz'

    fp=tarfile.open(args.file,decompress)

    fp.list(verbose=args.verbose)

    fp.close()

else:

    sys.exit(1)
