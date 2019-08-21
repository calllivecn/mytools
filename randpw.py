#!/usr/bin/env python3
# coding=utf-8
# date 2018-08-22 19:45:55
# author calllivecn <c-all@qq.com>

import random
import argparse


parse = argparse.ArgumentParser(
    description="一个密码生成器", usage="%(prog)s [-l long] [-c complexity]")

parse.add_argument("-l", "--long", type=int, action="store",
                   default=16, help="指密码长度default:16 (可以会降低密码复杂度)")
parse.add_argument("-c", "--complexity", type=int,
                   choices=[1, 2, 3, 4, 5], action="store", default=5, help="指定密码复杂度 (目前没使用)")

args = parse.parse_args()

# print(args)

# define remove password char
remove_chars = [':', "'"]


def remove_char(char_list):

    for char in remove_chars:
        char_list.remove(char)


def password(pwlong):
    available_char = [chr(x) for x in range(ord(' ') + 1, ord('~') + 1)]

    remove_char(available_char)

    pw = ''
    for _ in range(pwlong):
        pw += random.choice(available_char)

    return pw


print(password(args.long))
