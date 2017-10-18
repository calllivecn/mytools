


import time,datetime





## 装饰器
def runtime(func):
	def wapper(*args,**key):
		start = time.time()
		result = func(*args,**key)
		end = time.time()
		print(func.__name__,'运行时间:',end - start)
		return result
	return wapper













