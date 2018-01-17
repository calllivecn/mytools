#!/usr/bin/env python3
#codnig=utf-8


import sys
from base64 import encodebytes,decodebytes

thunder1 = sys.argv[1]
print()
print('step1:',thunder1)
print()
thunder2 = thunder1.lstrip('thunder://')
print('step2:',thunder2)
print()
decode3 = decodebytes(thunder2.encode())
try:
    decode4 = decode3.decode()
except UnicodeError:
    decode4 = decode3.decode('gb18030')

print('step3:',decode4)
print()
thunder4 = decode4.lstrip('AA').rstrip('ZZ')

print(thunder4)

