#!/usr/bin/evn python3
#codnig=utf-8


import sys
from base64 import encodebytes,decodebytes

thunder1 = sys.argv[1]
print('step1:',thunder1)
thunder2 = thunder1.lstrip('thunder://')
print('step2:',thunder2)
decode3 = decodebytes(thunder2.encode()).decode()
print('step3:',decode3)
thunder4 = decode3.lstrip('AA').rstrip('ZZ')

print(thunder4)

