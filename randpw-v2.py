#!/usr/bin/env python3
# coding=utf-8
# date 2019-02-27 09:58:29
# https://github.com/calllivecn

__all__ = ['randpw']

import random
import string

uppercase = string.ascii_uppercase
lowercase = string.ascii_lowercase
digets = string.digits

# 去除一些特殊符号
punctuation = list(string.punctuation)

remove_chars = ('`', "'", '"')
for char in remove_chars:
    punctuation.remove(char)

punctuation = "".join(punctuation)


password_lenght = 16

Cryptographic_elements = {"upper": uppercase, "lower": lowercase, "digets": digets, "punctuation": punctuation}
CE_KEYS = ("upper","lower", "digets", "punctuation")

password = ""

# 保证每类元素至少有一个字符
CE = Cryptographic_elements.copy()
for key in CE_KEYS:
    chars = CE.pop(key)
    char = random.choice(chars)
    password += char
    password_lenght -= 1


# 生成剩下char
for _ in range(password_lenght):
    key = random.choice(CE_KEYS)
    #print("key:", key)
    chars = Cryptographic_elements.get(key)
    #print("chars:", chars)

    char = random.choice(chars)

    #print("char:", char)

    password += char

PW = list(password)

random.shuffle(PW)

password = "".join(PW)

def randpw():
    return password

if __name__ == "__main__":
    print(password)
