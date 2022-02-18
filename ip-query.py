#!/usr/bin/env python3
# coding=utf-8
# update: 2022-02-18 12:50

import sys
import json
import argparse
import ipaddress
from urllib.request import urlopen
from socket import gethostbyname_ex

def getselfip():
    url = "https://www.taobao.com/help/getip.php"
    result = urlopen(url).read()
    _, ip, _ = result.decode("utf-8").split('"')
    print(ip)
    return ip
    


def query(ipaddr):
    # 地址
    url = f"https://ip.taobao.com/service/getIpInfo.php?ip={ipaddr}"
    url = f"https://ip.taobao.com/getIpInfo.php?ip={ipaddr}"
    response = urlopen(url)  # post提交数据

    html = response.read()  # 接收返回数据

    tag = json.loads(html.decode("utf-8"))  # ,encoding='utf8') #josh格式转换

    if tag.get("code") == 0 or tag.get("code") == "0":
        #data = tag["data"]
        print(json.dumps(tag["data"], ensure_ascii=False, indent=4))
    else:
        print('返回码非零,查询出错。', ipaddr)
        print(json.dumps(tag, ensure_ascii=False, indent=4))

    # print(data)

    #ip = data["ip"]  # 要查询IP
    #city = data["city"]  # 城市
    #region = data["region"]  # 省
    #area = data["area"]  # 区域
    #isp = data["isp"]  # ISP
    #county = data["county"]  # 市区
    #country = data["country"]  # 国家
    #return "\tIP:{}\n\t运营商：{}\n\t国家:{}\n\t地区城市:{}{}".format(ip, isp, country, region, city)


if __name__ == "__main__":
    parse = argparse.ArgumentParser(
        description='使用淘宝API查询ip地址信息', epilog='calllivecn')

    #parse.add_argument('-a','--address',nargs="*",help="addresss or hostnames")
    parse.add_argument('address', nargs="*", help="IP地址 或者 域名")

    args = parse.parse_args()

    if args.address:

        for ip_or_hostname in args.address:

            try:
                ipaddress.ip_address(ip_or_hostname)
            except ValueError:
                # 不是ip , 当域名查询
                ip_lists = gethostbyname_ex(ip_or_hostname)
                print(ip_lists)
                for ip in ip_lists[2]:
                    print('查询：', ip)
                    query(ip)
                print()
            else:
                print('查询：', ip_or_hostname)
                query(ip_or_hostname)
                print()

    else:
        getselfip()
