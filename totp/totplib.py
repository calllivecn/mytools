#!/usr/bin/env python3
# coding=utf-8
# date 2023-09-06 17:02:12
# author calllivecn <c-all@qq.com>

import time
import hmac
import hashlib
import base64
import argparse
from pathlib import Path

from typing import (
    Any,
    Optional,
)

"""
有一个开源模块: pip install pyotp
"""

class TOTP:

    def __init__(self, secret: str, time_step=30, digits=6):
        self.secret = secret
        self.time_step = time_step
        self.digits = digits

        self.time_left = 0

    def generate_totp(self, current_time: Optional[int] = None) -> str:
        # 获取当前时间戳，单位为秒
        if current_time is None:
            current_time = int(time.time())

        # 计算时间步数
        time_step_count = current_time // self.time_step
        self.time_left = self.time_step - (current_time % self.time_step)

        # 将时间步数转换为字节数组（big-endian）
        time_bytes = time_step_count.to_bytes(8, "big")

        # 使用HMAC-SHA1算法计算哈希值
        hmac_result = hmac.new(self.byte_secret(), time_bytes, hashlib.sha1).digest()

        # 获取哈希值的最后一个字节的低4位
        offset = hmac_result[-1] & 0x0F

        # 从哈希值中截取4个字节
        truncated_hash = hmac_result[offset:offset + 4]

        # 将截取的4个字节转换为整数
        otp_value = int.from_bytes(truncated_hash, byteorder='big') & 0x7FFFFFFF

        # 计算模数，以获得指定位数的OTP值
        mod_value = 10 ** self.digits
        otp = otp_value % mod_value

        # 将OTP值转换为固定位数的字符串
        otp_str = str(otp).zfill(self.digits)

        return otp_str
    

    def verify(self, opt: str, for_time: Optional[int] = None, valid_window: int = 0) -> bool:

        if for_time is None:
            for_time = int(time.time())
        
        if valid_window:
            for i in range(-valid_window, valid_window+1):
                if opt == self.generate_totp(for_time+i):
                    return True
            
            return False
        
        return opt == self.generate_totp(for_time)


    def byte_secret(self) -> bytes:
        """
        进来的是个base32格式的secret...
        """

        self.__preprocess()

        secret = self.secret
        missing_padding = len(secret) % 8 
        if missing_padding != 0:
            secret += "=" * (8 - missing_padding)

        return base64.b32decode(secret, casefold=True)
    

    def __preprocess(self):
        # 去掉太长 key 中间的空格
        secret = self.secret

        if secret.endswith("\n"):
            secret = secret.strip("\n")

        self.secret = "".join(secret.split(" "))

        # print(f"预处理过后：{self.secret=}")
    


def test(secret):

	# 用于生成TOTP的秘密密钥（通常由服务提供商和用户共享）
    # secret = "xxxxxxxxxxxxxxx"

    totp = TOTP(secret)

    # 生成TOTP：6位字串数字
    pw = totp.generate_totp()

    print(f"TOTP：{pw}, 剩余时间：{totp.time_left}")
    print("verify:", totp.verify(pw))



def issecretfile(filename):
    p = Path(filename)
    if p.name == "-":
        return "-"

    elif p.exists():
        return p
    else:
        raise argparse.ArgumentTypeError("必须是一个包含secret的文本文件")


def main():

    parse = argparse.ArgumentParser()

    parse.add_argument("--secret-file", type=issecretfile, help="指定secret文件")

    parse.add_argument("--html", action="store_true", help="输出为html格式")

    args = parse.parse_args()

    with open(args.secret_file) as f:
        secret = f.read()

    
    totp = TOTP(secret)
    pw = totp.generate_totp()

    if args.html:
        print(f"<h1>TOTP</h1><p>一次性密码：{pw}</p><p>剩余时间：{totp.time_left} 秒</p>")
    else:
        print(f"TOTP：{pw} 剩余时间：{totp.time_left} 秒")




if __name__ == "__main__":
	# test()
    main()

