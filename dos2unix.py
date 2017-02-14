#!/usr/bin/env python3
#coding=utf-8


import fileinput,sys

for line in fileinput.input(inplace=True):
	if line[-2:] == '\r\n':
		line = line + '\n'
	print(line)


