#!/usr/bin/env python3
# coding=utf-8
# date 2023-03-28 21:00:56
# author calllivecn <c-all@qq.com>

from systemd import journal


j = journal.Reader()

#j.add_match(_COMM="systemd-logind")

j.seek_tail()
#j.get_previous()


while True:
    event = j.wait() # 返回NOP（无更改）、APPEND（新条目已添加到 日志结束）或INVALIDATE（已添加日志文件或 移除）
    if event == journal.APPEND:
        #l = j.get_next()
        #print("line:", l)
        for l in j:
            print("line:", l["MESSAGE"])
    else:
        print("其他事件", event)
