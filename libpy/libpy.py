


import time
import datetime
import sys
import os



## 装饰器
def runtime(func):
	def wapper(*args,**key):
		start = time.time()
		result = func(*args,**key)
		end = time.time()
		print(func.__name__,'运行时间:',end - start)
		return result
	return wapper





def getabspath(f):
	"""getabspath(file) --> (abspath , filename)"""
	p = os.path.abspath(f)
	p = os.path.split(p)
	return p







