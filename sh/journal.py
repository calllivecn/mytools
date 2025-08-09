#!/usr/bin/env python3
# coding=utf-8
# date 2023-03-28 21:00:56
# author calllivecn <calllivecn@outlook.com>

import time
# apt install python3-systemd 一般都有安装
from systemd import journal


# 创建一个 JournalReader 实例
j = journal.Reader()

#j.add_match(_COMM="systemd-logind")

# 将读取位置设置到日志的末尾，这样我们只会看到新的日志。
j.seek_tail()


# 在 seek_tail() 之后，我们希望跳过当前的最新日志，
# 只关注从现在开始生成的新日志。
j.get_previous()

print("开始实时监控日志 (类似于 journalctl -f) ...")
print("按 Ctrl+C 退出。")

try:
    while True:
        # 使用 wait() 方法阻塞程序，直到有新日志写入。
        # 此方法会返回新日志的数量，或在超时时返回 0。
        # 如果没有指定超时，它会一直等待。
        # 将返回常量：如果没有变化，则返回 NOP；如果日志末尾添加了新条目，则返回 APPEND；如果日志文件已添加或删除，则返回 INVALIDATE。
        event = j.wait()

        # 一旦 wait() 返回，说明有新日志可用，我们就可以遍历它们。
        for entry in j:
            # 打印日志的 MESSAGE 字段。
            # 这里也做了一些优化，以避免额外的嵌套循环。
            print(f"{entry=} --> 日志: {entry.get('MESSAGE', 'N/A')}")
        
        # 增加一个短暂的休眠，以避免在某些情况下 CPU 占用过高。
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n程序已终止。")
except Exception as e:
    print(f"\n发生错误: {e}")

finally:
    j.close()


