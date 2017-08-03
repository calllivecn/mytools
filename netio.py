#!/usr/bin/env python3
#coding=utf-8


import os,time

ifname_dir='/sys/class/net/'

ifname_rx='/statistics/rx_bytes'

ifname_tx='/statistics/tx_bytes'


class Interface:
	rx_speed = 0
	tx_speed = 0
	def __init__(self,ifname):
		self.ifname = ifname
		self.ifname_rx = ifname_dir + ifname + ifname_rx
		self.ifname_tx = ifname_dir + ifname + ifname_tx
		
		self.getBytes()

		self.TB = 1<<40
		self.GB = 1<<30
		self.MB = 1<<20
		self.KB = 1<<10

		self.unit = None

		self.rx_unit = None
		self.tx_unit = None

		self.rx_sum_unit = None
		self.tx_sum_unit = None
	
	def getBytes(self):
		with open(self.ifname_rx) as f_rx, open(self.ifname_tx) as f_tx:
			b_rx = f_rx.read()
			b_tx = f_tx.read()
		self.init_rx = int(b_rx)
		self.init_tx = int(b_tx)

		self.rx_sum = self.init_rx
		self.tx_sum = self.init_tx
	
	
	def num(self):
		rx = self.init_rx
		tx = self.init_tx
		self.getBytes()
		self.rx_speed = self.mod(self.init_rx - rx)
		self.rx_unit = self.unit
		self.tx_speed = self.mod(self.init_tx - tx)
		self.tx_unit = self.unit
		
		self.rx_sum = self.mod(self.rx_sum)
		self.rx_sum_unit = self.unit
		self.tx_sum = self.mod(self.tx_sum)
		self.tx_sum_unit = self.unit
	
	def mod(self,s):
		if s > self.TB:
			self.unit = 'TB/s'
			return round(s/self.TB,2)
		elif s > self.GB:
			self.unit = 'GB/s'
			return round(s/self.GB,2)
		elif s > self.MB:
			self.unit = 'MB/s'
			return round(s/self.MB,2)
		elif s > self.KB:
			self.unit = 'KB/s'
			return round(s/self.KB,2)
		else:
			self.unit = 'B/s'
			return round(s,2)
		
	def __str__(self):
		return '{:<16}{:>12}{:>12}{:>12}{:>12}'.format(
				self.ifname,
				str(self.rx_speed) + self.rx_unit,
				str(self.tx_speed) + self.tx_unit,
				str(self.rx_sum) + self.rx_sum_unit[:-2],
				str(self.tx_sum) + self.tx_sum_unit[:-2]
				)
		
	

def getiface():
	ifs = []
	for f in os.listdir(ifname_dir):
		if_rx = ifname_dir + f + ifname_rx
		if_tx = ifname_dir + f + ifname_tx
		if os.path.isfile(if_rx) and os.path.isfile(if_tx):
			ifs.append(f)
	return ifs


def main():

	ifnames = []
	
	for ifs in getiface():
		ifnames.append(Interface(ifs))
	

	if len(ifnames) != 0:

		while True:
			print()
			print('{:<16}{:>12}{:>12}{:>12}{:>12}'.format('iface','recv','send','RX_sum','TX_sum'))
			for ifs in ifnames:
				try:
					ifs.num()
				except FileNotFoundError:
					ifnames.remove(ifs)
					continue
				print(ifs)
			time.sleep(1)


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		pass




