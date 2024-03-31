#!/usr/bin/env python3
# coding=utf-8
# date 2022-11-21 20:39:09
# author calllivecn <calllivecn@outlook.com>


import io
import os
import sys
import time
import enum
import shlex
import pickle
import signal
import socket
import argparse
import subprocess
from datetime import datetime

import logging
from logging.handlers import TimedRotatingFileHandler

from threading import (
    Thread,
    Lock,
)
import traceback

from typing import (
    Union,
    List,
)

PROG, _ = os.path.splitext(os.path.basename(sys.argv[0]))

FMT = logging.Formatter("%(asctime)s.%(msecs)d %(lineno)d %(levelname)s %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")

def getlogger(level=logging.INFO):
    logger = logging.getLogger(f"{PROG}")

    # fmt = logging.Formatter("%(asctime)s.%(msecs)d %(filename)s:%(funcName)s:%(lineno)d %(levelname)s %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")

    return logger


logger = getlogger()


def timestamp():
    t = datetime.now()
    return t.strftime("%Y-%m-%d %H:%M:%S")


def infile(f):
    with open(f) as f:
        tmp = f.readlines()

    return [ l.rstrip("\n") for l in tmp ]

BIG_SPLIT = "="*20
SMALL_SPLIT = "-"*20
BIG2_SPLIT = BIG_SPLIT*2

class Task:

    def __init__(self, cmd: Union[str, List[str]], cwd=None, env=None):
        self.cwd = cwd
        self.env = env

        if isinstance(cmd, str):
            self.cmd = shlex.split(cmd)

        elif isinstance(cmd, list):
            self.cmd = cmd
        else:
            raise ValueError(f"给出的命令格式不对")

    def run(self):
        self.start = timestamp()
        p = subprocess.Popen(self.cmd, cwd=self.cwd, env=self.env)
        self.pid = p.pid
        while (recode := p.poll()) is None:
            time.sleep(1)
        self.end = timestamp()
        self.recode = recode
        return self.recode


    def __str__(self):
        s=[]
        if self.env is not None:
            s.append(f"env: {self.env}")

        if hasattr(self, "pid"):
            s.append(f"PID: {self.pid}")

        s.append(f"CWD: {self.cwd}")

        s.append(f"CMD: {self.cmd}")

        if hasattr(self, "recode"):
            s.append(f"RECODE: {self.recode}")
        
        return "\n".join(s)


class Q(List):
    """
    可以调整顺序 任务队列
    """

    def __init__(self, maxlen=1000):
        self.maxlen = maxlen
        self._lock = Lock()
        self._empty_full_lock = Lock().acquire()

    def put(self, item):
        # print("Q put():", item)
        with self._lock:
            self.append(item)
    
    def get(self):
        while len(self) <= 0:
            # print("q.get() wait...")
            time.sleep(1)

        with self._lock:
            return self.pop(0)

    def insert(self, i, item):
        with self._lock:
            super().insert(i, item)
    
    def move(self, i, n):
        with self._lock:
            self[i], self[n] = self[n], self[i]
    
    def remove(self, i):
        with self._lock:
            self.pop(i)


class Status(enum.IntEnum):
    Running =  0x01
    Wait = enum.auto()
    Pause = enum.auto()


class Executer:
    """
    先只支持一个 执行器吧
    """
    def __init__(self, queue: Q):
        self.q = queue
        self.done_exit = False

        self.status = Status.Wait

        self.add()

    def add(self):
        """
        同队列下，添加一个执行器(并行跑一个任务队列)。
        """
        th = Thread(target=self.__exec, daemon=True)
        th.start()

    def done(self):
        """
        当前执行，执行完后退出。
        """
        self.done_exit = True
    
    def kill(self, sig: signal.signal):
        self.done_exit = True
        if hasattr(self.task, "pid"):
            if self.status == Status.Running or self.status == Status.Pause:
                os.kill(self.task.pid, sig)
        else:
            logger.info(f"task {self.task} 没有运行")

    def pause(self):
        if self.status == Status.Running:
            os.kill(self.task.pid, signal.SIGSTOP)
            self.status = Status.Pause
            return True
        else:
            return "没有任务在执行."

    def recover(self):
        if self.status == Status.Pause:
            os.kill(self.task.pid, signal.SIGCONT)
            self.status = Status.Running
        else:
            logger.info(f"当前执行器没有暂停")

    def __exec(self):
        while True:
            if self.done_exit:
                # print(f"{self.th.name} 执行完退出")
                return

            # 当前执行器 正在执行的任务
            self.task = self.q.get()

            logger.info(f"{BIG2_SPLIT}")
            logger.info(f"↓\n开始时间: {timestamp()}\n{self.task}")
            logger.info(f"{BIG2_SPLIT}")

            self.status = Status.Running
            try:
                self.task.run()
            except Exception as e:
                traceback.print_exc()
                continue

            self.status = Status.Wait

            logger.info(f"{BIG2_SPLIT}")
            logger.info(f"↓\n开始时间: {self.task.start}, 结束时间: {self.task.end}\n{self.task}")
            logger.info(BIG2_SPLIT)


class Manager:
    """
    执行器之间是并行关系，每个执行器属于一个执行队列。
    """

    def __init__(self):
        self.q = Q()
        # {queue-name: TaskQeueu}

        # 执行器s
        self.ths = []
        self.add_executer(1)

    def add_task(self, task: Task):
        self.q.put(task)

    def add_executer(self, i: int):
        for _ in range(i):
            self.ths.append(Executer(self.q))

    def done_executer(self, seq: int):
        l = len(self.ths)
        if 0 <= seq <= l - 1:
            t = self.ths[seq]
            t.done()
    
    def kill(self, seq: int, sig: signal.signal = signal.SIGTERM):
        l = len(self.ths)
        if 0 <= seq <= l - 1:
            th = self.ths.pop(seq)
            th.kill(sig)

    def pause(self, seq: int):
        l = len(self.ths)
        if 0 <= seq <= l - 1:
            th = self.ths[seq]
            return th.pause()

    def recover(self, seq: int):
        l = len(self.ths)
        if 0 <= seq <= l - 1:
            th = self.ths[seq]
            th.recover()

    def status(self):
        buf = []
        buf.append(f"{BIG_SPLIT} 执行器(总数: {len(self.ths)}) {BIG_SPLIT}")
        for i, th in enumerate(self.ths):

            title = f"{SMALL_SPLIT} 编号:{i} "

            if th.status == Status.Running or th.status == Status.Pause:

                if th.status == Status.Running:
                    title += f" -- 执行中"

                if th.status == Status.Pause:
                    title += f" -- 暂停状态(--recover恢复)"

                if th.done_exit:
                    t = self.ths.pop(i)
                    title += f" -- 标记: 执行完后退出"

                title += SMALL_SPLIT
                buf.append(title)

                # buf.append(f"CMD: {th.task.cmd}")
                buf.append(f"{th.task}")

            elif th.status == Status.Wait:

                title += SMALL_SPLIT
                buf.append(title)
                buf.append("等待中")

            else:
                print(f"执行器处理未知状态: {th.status}")

        return "\n".join(buf)
        
    def list(self):
        buf = []
        buf.append(f"任务队列(总数: {len(self.q)}):")
        for i, task in enumerate(self.q):
            s = BIG_SPLIT
            buf.append(f"{s} 任务号:{i} {s}\n{str(task)}")

        return "\n".join(buf)

    def insert(self, i: int, task: Task):
        self.q.insert(i, task)

    def remove(self, i: int):
        try:
            self.q.remove(i)
        except IndexError:
            print(f"没有任务: {i}")

    def move(self, i: int, n: int):
        try:
            self.q.move(i, n)
        except IndexError:
            print(f"没有任务: {i} or {n}")

# 两边传输
class CmdType(enum.IntEnum):
    
    Status = 0x01
    Task = enum.auto()
    List = enum.auto()
    Insert = enum.auto()
    Remove = enum.auto()
    Move = enum.auto()
    Done = enum.auto()

    ADD = enum.auto()
    Kill = enum.auto()
    Pause = enum.auto()
    Recover = enum.auto()

    # 回复client的type
    ReOK = enum.auto()
    ReERR = enum.auto()
    Result = enum.auto()


def server(args):
    host = args.host
    port = args.port

    logger.info(f"启动执行管理器: {host}:{port}")

    m = Manager()

    sock = socket.create_server((host, port), family=socket.AF_INET6, dualstack_ipv6=True)

    while True:
        client, addr = sock.accept()
        data =  client.recv(8192)
        if not data:
            logger.info("peer close()")
            client.close()
            continue

        try:
            proto = pickle.loads(data)
            # print("type:", proto[0])
        except Exception:
            logger.deubg(f"接收客户端数据异常")
            traceback.print_exc()
            continue


        if proto[0] == CmdType.Status:
            data = m.status()
            data = f"{'+'*20} 服务器 [{host}]:{port} {'+'*20}\n" + data
            reply = pickle.dumps((CmdType.Result, data))
        
        elif proto[0] == CmdType.List:
            data = m.list()
            reply = pickle.dumps((CmdType.Result, data))
        
        elif proto[0] == CmdType.Task:
            task = proto[1]
            # print(f"添加任务：{task.cmd}")
            m.add_task(task)

            reply = pickle.dumps((CmdType.ReOK,))

        elif proto[0] == CmdType.Insert:
            number = proto[1]
            task = proto[2]
            m.insert(number, task)

            reply = pickle.dumps((CmdType.ReOK,))
        
        elif proto[0] == CmdType.Remove:
            number = proto[1]
            m.remove(number)

            reply = pickle.dumps((CmdType.ReOK,))

        elif proto[0] == CmdType.Move:
            i, n = proto[1], proto[2]
            try:
                m.move(i, n)
            except IndexError as e:
                reply = pickle.dumps((CmdType.ReERR,))
                traceback.print_exc()
            else: 
                reply = pickle.dumps((CmdType.ReOK,))
        
        elif proto[0] == CmdType.Done:
            i = proto[1]
            m.done_executer(i)

            reply = pickle.dumps((CmdType.ReOK,))

        elif proto[0] == CmdType.Kill:
            i = proto[1]
            m.kill(i)

            reply = pickle.dumps((CmdType.ReOK,))

        elif proto[0] == CmdType.Pause:
            i = proto[1]
            result = m.pause(i)
            # print(f"暂停任务：{i}")

            reply = pickle.dumps((CmdType.ReOK, result))

        elif proto[0] == CmdType.Recover:
            i = proto[1]
            m.recover(i)

            reply = pickle.dumps((CmdType.ReOK,))

        elif proto[0] == CmdType.ADD:
            i = proto[1]
            m.add_executer(i)

            reply = pickle.dumps((CmdType.ReOK,))

        # client.send(reply)
        client.sendall(reply)
        client.close()
    
    sock.close()




def client(args):

    host = args.host
    port = args.port

    cwd = os.getcwd()

    if args.status:
        cmd = pickle.dumps((CmdType.Status,))
    
    elif args.list:
        cmd = pickle.dumps((CmdType.List,))
    
    elif args.insert is not None:
        cmd = pickle.dumps((CmdType.Insert, args.insert, Task(args.taskcmd, cwd)))

    elif args.remove is not None:
        cmd = pickle.dumps((CmdType.Remove, args.remove))

    elif args.move:
        cmd = pickle.dumps((CmdType.Move, int(args.move[0]), int(args.move[1])))
    
    elif args.done is not None:
        cmd = pickle.dumps((CmdType.Done, args.done))

    elif args.add:
        cmd = pickle.dumps((CmdType.ADD, args.add))
    
    elif args.kill is not None:
        cmd = pickle.dumps((CmdType.Kill, args.kill))
    
    elif args.pause is not None:
        cmd = pickle.dumps((CmdType.Pause, args.pause))
    
    elif args.recover is not None:
        cmd = pickle.dumps((CmdType.Recover, args.recover))
    
    elif args.task:
        # 默认选项
        cmd = pickle.dumps((CmdType.Task, Task(args.taskcmd, cwd)))
    else:
        cmd = pickle.dumps((CmdType.Task, Task(args.taskcmd, cwd)))


    sock = socket.create_connection((host, port))

    sock.send(cmd)
    # print(f"指令：{pickle.loads(cmd)}")

    buf = io.BytesIO()
    while (data := sock.recv(8192)) != b"":
        buf.write(data)

    try:
        reply = pickle.loads(buf.getvalue())
    except EOFError:
        reply = (CmdType.ReERR,)

    if reply[0] == CmdType.ReOK:
        recode = 0

    elif reply[0] == CmdType.ReERR:
        print("有什么出错了, 查看服务端日志。")
        recode = 1

    elif reply[0] == CmdType.Result:
        # print(reply[1])
        try:
            print(reply[1], flush=True)
        except BrokenPipeError:
            pass

        recode = 0

    else:
        print("未知返回")
        recode = 1

    sock.close()
    sys.exit(recode)



def main():

    parse = argparse.ArgumentParser()

    option = parse.add_argument_group(title="通用参数")
    option.add_argument("--server", action="store_true", help="启动server端")
    option.add_argument("--host", default="::1", help="默认地址(server: '::', or client: '::1'， 如果有BATCH_TASK_HOST环境变量优先使用)")
    option.add_argument("--port", type=int, default=1122, help="server 地址(default: 1122，如果有BATCH_TASK_PORT环境变量优先使用)")
    option.add_argument("--log", help=f"指定日志输出文件(default: {PROG}.log)")

    c = parse.add_argument_group(title="client 参数")
    group = c.add_mutually_exclusive_group()
    group.add_argument("--add-executer", dest="add", type=int, metavar="number", help="添加一个并行执行器")
    group.add_argument("--done-executer", dest="done", type=int, metavar="number", help="指定一个执行器，本次执行完后退出。(减少一个并行执行)")
    group.add_argument("--kill", type=int, metavar="number", help="kill一个执行器(减少一个并行执行)")
    group.add_argument("--pause", type=int, metavar="number", help="暂停一个正在的执行器")
    group.add_argument("--recover", type=int, metavar="number", help="恢复一个正在的执行器")

    c.add_argument("--task", action="store_true", help="添加任务(默认选项)")

    group.add_argument("--status", action="store_true", help="查看状态")
    group.add_argument("--list", action="store_true", help="查看队列")
    group.add_argument("--insert", type=int, metavar="number", help="在队列指定位置插入新任务")
    group.add_argument("--remove", type=int, metavar="number", help="删除队列指定位置任务")
    group.add_argument("--move", action="store", nargs=2, metavar="number", help="调整任务顺序")
    group.add_argument("--not-stdout", dest="not_stdout", action="store_true", help="只输出到日志文件")

    parse.add_argument("taskcmd", nargs="*", help="需要执行的命令行")

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    args = parse.parse_args()

    if not args.not_stdout:
        stream = logging.StreamHandler(sys.stdout)
        stream.setFormatter(FMT)
        logger.addHandler(stream)

    if args.parse:
        print(args)
        # parse.print_help()
        sys.exit(0)

    ENV_HOST = os.environ.get("BATCH_TASK_HOST")
    ENV_PORT = os.environ.get("BATCH_TASK_PORT")

    if args.server:
        if ENV_HOST:
            args.host = ENV_HOST

        args.port = int(ENV_PORT) if ENV_PORT else args.port

        fp = logging.FileHandler(f"{PROG}.logs")
        # fp = TimedRotatingFileHandler(f"{prog}.logs", when="D", interval=1, backupCount=7)
        fp.setFormatter(FMT)
        logger.setLevel(logging.INFO)
        logger.addHandler(fp)

        try:
            server(args)
        except KeyboardInterrupt:
            pass

        sys.exit(0)
    
    if ENV_PORT:
        args.port = int(ENV_PORT)

    client(args)


if __name__ == "__main__":
    main()
