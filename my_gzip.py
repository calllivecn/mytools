#!/usr/bin/env python3
#coding=utf-8

import gzip,sys,os,argparse

parse=argparse.ArgumentParser(description='Gzip compress and decompress',usage='Usage: [Option]... [File]...',epilog='end')

parse.add_argument('-c','--stdout',action='store_true',help='write on standard output, keep original files unchanged')

parse.add_argument('-d', '--decompress',action='store_true', help='decompress')

parse.add_argument('-k','--keep',action='store_false',help='keep (don\'t delete) input files')

parse.add_argument('-v', '--verbose',action='store_true',help='verbose mode')

parse.add_argument('-1','--fast',action='store_true',help='compress fast')

parse.add_argument('-9','--best',action='store_true',help='compress best')

parse.add_argument('files',nargs='*',help='compress files')


args=parse.parse_args()


#print(args.decompress)

class Stdout():
	def write(self,data):
		return sys.stdout.write(str(data))
	def close(self):
		pass

if args.decompress:

		for	f in args.files:
			
			f_d=gzip.open(f,'rb')
	
			if args.stdout:
				out=Stdout()
			else:
				out=open(f.rstrip('.gz'),'wb')
			
			f_s=f_d.read(4096)
	
			while f_s:
				out.write(f_s)
				f_s=f_d.read(4096)
		
			f_d.close()
			out.close()
			
			if args.keep and not args.stdout:
				os.remove(f)

else:

		for f in args.files:
			
			f_s=open(f,'rb')
			
			if args.stdout:
				out=Stdout()
			else:
				out=f+'.gz'
			
			f_d=gzip.open(out,'wb')

			d=f_s.read(4096)
				
			while d:
				f_d.write(d)
				d=f_s.read(4096)
			f_d.close()

			if args.keep and not args.stdout:
				os.remove(f)

