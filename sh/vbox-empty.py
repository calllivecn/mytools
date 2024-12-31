
import os
import sys
from pathlib import Path

BUF = bytes((1<<20))
BUF_size = 1<<20

GB = 1<<30

def usage():
    """
    Usage: vbox-empty.py <盘符, 比如 C:/ , D:/> <写入的大小单位:GB>
    """
    print(usage.__doc__)
    sys.exit(0)

disk_fd = Path(sys.argv[1])
print(f"{disk_fd=}")
try:
    write_size = int(sys.argv[2])
except ValueError:
    usage()


if not disk_fd.is_dir():
    usage()


open_file = disk_fd / "empty"
print(f"{open_file=}")
try:
    with open(open_file, "ab") as f:
        f.seek(0, os.SEEK_END)

        count, c = divmod(write_size * GB, BUF_size)
        if c > 0:
            count += 1
        write_size = 0
        for i in range(count):
            f.write(BUF)
            f.flush()
            write_size += 1
            G, v = divmod(write_size, 1024)
            if v == 0:
                print(f"已写入{G}GB")

except OSError:
    print("磁盘已满。")
    #os.remove("empty")


print(f"可以删除：{open_file}，然后导出虚拟机了。")

         
