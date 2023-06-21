
import os
import sys
import time
import hashlib
import threading


# 看看是不是使用 subprocess 调用 inotifywait 命令工具好点？这样代码简单。
import pyinotify



"""
这个还是不能拿来， 使用在 vboxmanage export <vms> 上。
"""


OVER_FLAG = False

class HanleCloseWrite(pyinotify.ProcessEvent):

    def __init__(self):
        super().__init__()

    def check_flag(self) -> bool:
        return self.OVER_FLAG


    def process_IN_CLOSE_WRITE(self, event):
        global OVER_FLAG
        OVER_FLAG = True
        print("closewrite event:", event)


# start thread
def watchfile(file_path):
    watchmanager = pyinotify.WatchManager()

    notifyer = pyinotify.Notifier(watchmanager, HanleCloseWrite())

    watchmanager.add_watch(file_path, pyinotify.ALL_EVENTS)

    th = threading.Thread(target=notifyer.loop, daemon=True)
    th.start()
    # print("watch thread exit")


BLOCK = 1<<14 # 16k


def tailf_hash(file_path):

    watchfile(file_path)

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file_fd:

        while True:
            data = file_fd.read(BLOCK)
            if data:
                # print(data)
                print(f"file: {file_fd.tell()}.....\r", end="")
                sha256.update(data)
            else:
                # print("empty, f.tell()", file_fd.tell())
                time.sleep(0.1)
        
            if OVER_FLAG and data == b"":
                break
    
    print("sha256:", sha256.hexdigest())


if __name__ == '__main__':
    file_path = sys.argv[1]
    tailf_hash(file_path)

