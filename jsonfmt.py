#!/usr/bin/env python3
# coding=utf-8
# date 2019-12-27 14:29:03
# author calllivecn <c-all@qq.com>


import os
import sys
import json

import argparse


def main():
    parse = argparse.ArgumentParser(usage="Usage: %(prog)s [-i] [filename.json]",
            description="格式化输出json文件。",
            epilog="none"
            )

    parse.add_argument("-i", action="store_true", help="直接格式后写回文件")

    parse.add_argument("jsonfile", nargs="?", default="-", help="filename json")

    args = parse.parse_args()
    #print(args);sys.exit(0)

    try:
        if args.jsonfile == "-":
            json_data = json.load(sys.stdin.buffer)
        else:
            if os.path.isfile(args.jsonfile):
                with open(args.jsonfile) as j:
                    json_data = json.load(j)
            else:
                print("需要一个json文件.")
                sys.exit(1)
    except json.decoder.JSONDecodeError:
        print("Json 格式错误。")
        sys.exit(1)

    if args.i:
        os.rename(args.jsonfile, args.jsonfile + "-bak")

        try:
            with open(args.jsonfile, "w") as j:
                json.dump(json_data, j, ensure_ascii=False, indent=4)
        except Exception as e:
            print("写入文件异常:", e)
            os.rename(args.jsonfile + "-bak", args.jsonfile)

        else:
            os.remove(args.jsonfile + "-bak")

    else:
        print(json.dumps(json_data, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    main()
