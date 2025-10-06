#!/usr/bin/env python3
# coding=utf-8
# date 2022-11-21 20:39:09


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
from pathlib import Path
from collections import deque
from datetime import datetime
from dataclasses import dataclass

import logging
from logging.handlers import TimedRotatingFileHandler

from threading import (
    Thread,
    Lock,
    Event,
)
import traceback


from typing import (
    Self,
)


PROG = Path(sys.argv[0]).stem
FMT = logging.Formatter("%(asctime)s.%(msecs)d %(lineno)d %(levelname)s %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")

def getlogger(level=logging.INFO):
    logger = logging.getLogger(f"{PROG}")

    # fmt = logging.Formatter("%(asctime)s.%(msecs)d %(filename)s:%(funcName)s:%(lineno)d %(levelname)s %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")

    return logger


logger = getlogger()


def timestamp():
    t = datetime.now()
    return t.strftime("%Y-%m-%d %H:%M:%S")


PLUS_SPLIT = '+'*20
Q_SPLIT = "#"*20
BIG_SPLIT = "="*20
SMALL_SPLIT = "-"*20
BIG2_SPLIT = BIG_SPLIT*2

SOCK_BUF = 4096

class Task:

    def __init__(self, cmd: str|list[str], cwd=None, env=None):
        self.cwd = cwd
        self.env = env

        if isinstance(cmd, str):
            self.cmd = shlex.split(cmd)

        elif isinstance(cmd, list):
            self.cmd = cmd
        else:
            raise ValueError("给出的命令格式不对")

    def run(self):
        self.start = timestamp()
        p = subprocess.Popen(self.cmd, cwd=self.cwd, env=self.env)
        self.pid = p.pid
        recode = p.wait()
        self.end = timestamp()
        self.recode = recode


    def __str__(self):
        with io.StringIO() as buf:

            if hasattr(self, "start"):
                buf.write(f"START: {self.start}\n")

            if self.env is not None:
                buf.write(f"ENV: {self.env}\n")

            if hasattr(self, "pid"):
                buf.write(f"PID: {self.pid}\n")

            if self.cwd is not None:
                buf.write(f"CWD: {self.cwd}\n")

            buf.write(f"CMD: {self.cmd}\n")

            if hasattr(self, "recode"):
                buf.write(f"RECODE: {self.recode}\n")
        
            return buf.getvalue()


class Q:
    """
    线程安全的可调整顺序任务队列
    """
    def __init__(self, maxlen=1000):
        self._queue = deque(maxlen=maxlen)
        self._lock = Lock()

    def put(self, item: Task):
        with self._lock:
            self._queue.append(item)

    def get(self):
        while True:
            with self._lock:
                if self._queue:
                    return self._queue.popleft()
            time.sleep(1)

    def insert(self, i, item: Task):
        with self._lock:
            self._queue.insert(i, item)

    def move(self, i: int, n: int):
        with self._lock:
            self._queue[i], self._queue[n] = self._queue[n], self._queue[i]

    def remove(self, i: int):
        with self._lock:
            self._queue.remove(self._queue[i])

    def __len__(self):
        with self._lock:
            return len(self._queue)

    def __iter__(self):
        with self._lock:
            return iter(list(self._queue))


class Status(enum.IntEnum):
    Running =  0x01
    Wait = enum.auto()
    Pause = enum.auto()

@dataclass
class OpReturn:
    """
    执行器操作返回值
    """
    success: bool
    message: str = ""


class Executor:
    """
    可以一个行执行器，只属于一个Q任务队列。
    """
    def __init__(self, queue: Q):
        self.q = queue
        self.e = Event()
        self.status = Status.Wait
    
        self.th = Thread(target=self.__exec, daemon=True)
        self.th.start()

    def done(self) -> OpReturn:
        """
        当前执行，执行完后退出。
        """
        self.e.set()
        return OpReturn(success=True, message="执行器已标记为执行完后退出。")
    
    def kill(self, sig: int) -> OpReturn:

        opreturn = OpReturn(success=True, message="执行器已被kill。")

        if hasattr(self, "task"):
            if hasattr(self.task, "pid"):
                if self.status == Status.Running or self.status == Status.Pause:
                    os.kill(self.task.pid, sig)
            else:
                opreturn.success = False
                opreturn.message = f"task {self.task} 没有运行，标记为退出。"
                logger.info(opreturn.message)
        else:
            opreturn.success = False
            opreturn.message = "当前执行器没有正在执行的任务, 标记为退出。"
            logger.info(opreturn.message)

        self.e.set()

        return opreturn

    def pause(self) -> OpReturn:
        if self.status == Status.Running:
            os.kill(self.task.pid, signal.SIGSTOP)
            self.status = Status.Pause
            return OpReturn(success=True, message="执行器已暂停，请使用 --recover 恢复执行器。")
        else:
            return OpReturn(success=False, message="当前执行器没有正在执行的任务，无法暂停。")

    def recover(self) -> OpReturn:

        if self.status == Status.Pause:
            os.kill(self.task.pid, signal.SIGCONT)
            self.status = Status.Running
            opreturn = OpReturn(success=True, message="执行器已恢复执行。")
        else:
            opreturn = OpReturn(success=True, message="当前执行器没有暂停")
            logger.info(opreturn.message)

        return opreturn

    def __exec(self):
        while True:
            if self.e.is_set():
                # print(f"{self.th.name} 执行完退出")
                return

            # 当前执行器 正在执行的任务
            self.task: Task = self.q.get()

            logger.info(BIG2_SPLIT)
            logger.info(f"↓\n开始时间: {timestamp()}\n{self.task}")
            logger.info(BIG2_SPLIT)

            self.status = Status.Running
            try:
                self.task.run()
            except Exception:
                traceback.print_exc()
                continue

            self.status = Status.Wait

            logger.info(BIG2_SPLIT)
            logger.info(f"↓\n开始时间: {self.task.start}, 结束时间: {self.task.end}\n{self.task}")
            logger.info(BIG2_SPLIT)
    
    def __str__(self) -> str:
        with io.StringIO() as buf:
            buf.write(f"状态: {self.status.name}\n")
            if hasattr(self, "task"):
                buf.write(str(self.task))
                buf.write("\n")
            else:
                buf.write("当前没有任务\n")
            return buf.getvalue()



@dataclass
class QueueExecutor:
    queue: Q
    executor: list[Executor]


class Manager:
    """
    执行器之间是并行关系，每个执行器属于一个执行队列。
    可以多个执行器属于一个执行队列，同队列并行。
    """

    def __init__(self, add_queue: int):
        self.qes: list = []

        self.add_queue(add_queue)
    

    def __check_qe_index(self, qe_index: int) -> OpReturn:
        ll = len(self.qes)
        if 0 <= qe_index <= ll - 1:
            return OpReturn(success=True)
        else:
            return OpReturn(success=False, message=f"没有队列: {qe_index}")


    def __check_executor(self, qe_index: int, executor_index: int) -> OpReturn:
        r = self.__check_qe_index(qe_index)
        if not r.success:
            return r

        e: list[Executor] = self.qes[qe_index].executor

        ll = len(e)
        if 0 <= executor_index <= ll - 1:
            return OpReturn(success=True)
        else:
            return OpReturn(success=False, message=f"没有执行器: {qe_index}")


    def add_queue(self, number: int) -> OpReturn:
        """
        添加<number>个新的任务队列, 默认一个执行器
        """
        l_len = len(self.qes)
        for i in range(number):
            self.qes.append(QueueExecutor(Q(), executor=[]))
            self.add_executor(1, l_len+i)
        
        return OpReturn(success=True)

    def add_executor(self, i: int, qe_index: int = 0) -> OpReturn:
        r = self.__check_qe_index(qe_index)
        if not r.success:
            return r

        qe: QueueExecutor = self.qes[qe_index]
        for _ in range(i):
            qe.executor.append(Executor(qe.queue))
        
        return OpReturn(success=True)

    def done_executor(self, seq: int, qe_index: int = 0) -> OpReturn:

        r = self.__check_executor(qe_index, seq)
        if not r.success:
            return r

        ths: list[Executor] = self.qes[qe_index].executor
        t = ths[seq]
        return t.done()
    
    def add_task(self, task: Task, qe_index: int = 0) -> OpReturn:
        r = self.__check_qe_index(qe_index)
        if not r.success:
            return r

        q: Q = self.qes[qe_index].queue
        q.put(task)
        return OpReturn(success=True)

    def kill(self, seq: int, qe_index: int = 0, sig: int = signal.SIGTERM) -> OpReturn:
        r = self.__check_executor(qe_index, seq)
        if not r.success:
            return r

        qe :QueueExecutor = self.qes[qe_index]
        th = qe.executor.pop(seq)
        return th.kill(sig)

    def pause(self, seq: int, qe_index: int = 0) -> OpReturn:
        r = self.__check_executor(qe_index, seq)
        if not r.success:
            return r

        qe :QueueExecutor = self.qes[qe_index]
        th = qe.executor[seq]
        return th.pause()

    def recover(self, seq: int, qe_index: int = 0) -> OpReturn:
        r = self.__check_executor(qe_index, seq)
        if not r.success:
            return r

        qe :QueueExecutor = self.qes[qe_index]
        th = qe.executor[seq]
        return th.recover()

    def status(self) -> OpReturn:
        buf = io.StringIO()
        buf.write(f"{PLUS_SPLIT}\t队列总数：{len(self.qes)}\t{PLUS_SPLIT}\n")
        for n, qe in enumerate(self.qes):
            buf.write(f"{Q_SPLIT}\t队列编号: {n}\t{Q_SPLIT}\n")
            buf.write(f"\t{BIG_SPLIT}\t执行器(总数: {len(qe.executor)})\t{BIG_SPLIT}\n")

            for i, th in enumerate(qe.executor):
                title = io.StringIO()
                title.write(f"\t\t{SMALL_SPLIT}\t编号:{i} ")

                match th.status:
                    case Status.Running | Status.Pause:

                        if th.status == Status.Running:
                            title.write(" -- 执行中")

                        if th.status == Status.Pause:
                            title.write(" -- 暂停状态(--recover恢复)")

                        if th.e.is_set():
                            qe.executor.pop(i)
                            title.write(" -- 标记: 执行完后退出")

                        title.write(f"\t{SMALL_SPLIT}")
                        buf.write(title.getvalue())
                        buf.write(f"\n{th.task}\n")

                    case Status.Wait:
                        title.write("等待中")
                        title.write(f"\t{SMALL_SPLIT}\n")
                        buf.write(title.getvalue())
                        buf.write("\n")

                    case _:
                        print(f"执行器处理未知状态: {th.status}")

                title.close()

        r = OpReturn(True, buf.getvalue())
        buf.close()
        return r
        
    def list(self) -> OpReturn:
        buf = io.StringIO()

        buf.write(f"{PLUS_SPLIT}\t队列总数：{len(self.qes)}\t{PLUS_SPLIT}\n")
        for n, qe in enumerate(self.qes):

            buf.write(f"\t{Q_SPLIT}\t队列编号: {n}\t{Q_SPLIT}\n")
            buf.write(f"\t{BIG_SPLIT}\t执行器(总数: {len(qe.executor)})\t{BIG_SPLIT}\n")

            buf.write(f"\t\t任务队列(总数: {len(qe.queue)}):\n")
            for i, task in enumerate(qe.queue):
                buf.write(f"\t\t{BIG_SPLIT}\t任务号:{i}\t{BIG_SPLIT}\n")
                buf.write(f"\t\t{str(task)}\n")

        r = OpReturn(True, buf.getvalue())
        buf.close()
        return r

    def insert(self, i: int, task: Task, qe_index: int = 0) -> OpReturn:
        r = self.__check_qe_index(qe_index)
        if not r.success:
            return r

        q: Q = self.qes[qe_index].queue
        q.insert(i, task)
        return OpReturn(success=True)

    def remove(self, i: int, qe_index: int = 0) -> OpReturn:
        r = self.__check_qe_index(qe_index)
        if not r.success:
            return r

        q: Q = self.qes[qe_index].queue
        try:
            q.remove(i)
        except IndexError:
            return OpReturn(success=False, message=f"没有任务: {i}")
        
        return OpReturn(success=True)

    def move(self, i: int, n: int, qe_index: int = 0) -> OpReturn:
        r = self.__check_qe_index(qe_index)
        if not r.success:
            return r

        q: Q = self.qes[qe_index].queue
        try:
            q.move(i, n)
        except IndexError:
            return OpReturn(success=False, message=f"没有任务: {i} or {n}")
        
        return OpReturn(success=True)


class CmdType(enum.IntEnum):
    
    Status = 0x01
    Task = enum.auto()
    List = enum.auto()
    Insert = enum.auto()
    Remove = enum.auto()
    Move = enum.auto()
    Done = enum.auto()
    Queue = enum.auto()

    ADD = enum.auto()
    Kill = enum.auto()
    Pause = enum.auto()
    Recover = enum.auto()

    # 回复client的type
    ReOK = enum.auto()
    ReERR = enum.auto()
    Result = enum.auto()


@dataclass
class CmdProtocol:
    CmdType: CmdType
    reply: str = ""
    qe_number: int = 0
    task: Task|None = None
    task_number: int|None = None
    move_i: int|None = None
    move_n: int|None = None

    def dumps(self) -> bytes:
        return pickle.dumps(self)

    @classmethod
    def loads(cls, data) -> Self:
        """
        try:
            proto = pickle.loads(data)
        except Exception as e:
            logger.error(f"加载协议异常: {e}")
            traceback.print_exc()
            return None

        if isinstance(proto, cls):
            return proto
        else:
            logger.error("加载协议失败，类型不匹配")
            return None
        """
        return pickle.loads(data)


def server(args: argparse.Namespace):
    host = args.host
    port = args.port

    logger.info(f"启动执行管理器: {host}:{port}")

    if args.add_queue == 0:
        m = Manager(1)
    else:
        m = Manager(args.add_queue)

    with socket.create_server((host, port), family=socket.AF_INET6, dualstack_ipv6=True) as sock:

        while True:
            data_buf = io.BytesIO()
            client, addr = sock.accept()
            client.settimeout(60)

            try:
                while (data := client.recv(SOCK_BUF)) != b"":
                    data_buf.write(data)
            except socket.timeout:
                logger.error("接收客户端数据超时")
                client.close()
                data_buf.close()
                continue

            # if not data:
            if data_buf.tell() == 0:
                logger.info("peer close()")
                client.close()
                data_buf.close()
                continue

            try:
                proto = CmdProtocol.loads(data_buf.getvalue())
            except Exception:
                logger.error("接收客户端数据异常")
                traceback.print_exc()
                continue

            finally:
                data_buf.close()


            match proto.CmdType:
                case CmdType.ReOK | CmdType.ReERR | CmdType.Result:
                    logger.error(f"客户端发送了错误的指令: {proto.CmdType}")
                    continue

                case CmdType.Status:
                    r = m.status()

                case CmdType.List:
                    r = m.list()

                case CmdType.Task:
                    if proto.task is None:
                        r = OpReturn(False, "没有任务数据")
                    else:
                        r = m.add_task(proto.task, qe_index=proto.qe_number)


                case CmdType.Insert:
                    if proto.task is None or proto.task_number is None:
                        r = OpReturn(False, "没有任务数据或任务编号")
                    else:
                        r = m.insert(proto.task_number, proto.task, qe_index=proto.qe_number)


                case CmdType.Remove:
                    if proto.task_number is None:
                        r = OpReturn(False, "没有任务编号")
                    else:
                        r = m.remove(proto.task_number, qe_index=proto.qe_number)


                case CmdType.Move:
                    if proto.move_i is None or proto.move_n is None:
                        r = OpReturn(False, "没有任务编号")
                    else:
                        r = m.move(proto.move_i, proto.move_n, qe_index=proto.qe_number)


                case CmdType.Done:
                    if proto.task_number is None:
                        r = OpReturn(False, "没有任务编号")
                    else:
                        r = m.done_executor(proto.task_number, qe_index=proto.qe_number)


                case CmdType.Kill:
                    if proto.task_number is None:
                        r = OpReturn(False, "没有任务编号")
                    else:
                        r = m.kill(proto.task_number, qe_index=proto.qe_number)


                case CmdType.Pause:
                    if proto.task_number is None:
                        r = OpReturn(False, "没有任务编号")
                    else:
                        r = m.pause(proto.task_number, qe_index=proto.qe_number)


                case CmdType.Recover:
                    if proto.task_number is None:
                        r = OpReturn(False, "没有任务编号")
                    else:
                        r = m.recover(proto.task_number, qe_index=proto.qe_number)


                case CmdType.ADD:
                    if proto.task_number is None:
                        r = OpReturn(False, "没有任务编号")
                    else:
                        r = m.add_executor(proto.task_number, qe_index=proto.qe_number)

                
                case CmdType.Queue:
                    if proto.qe_number is None:
                        r = OpReturn(False, "没有队列编号")
                    else:
                        r =  m.add_queue(proto.qe_number)


                case _:
                    r = OpReturn(False, f"未知指令: {proto.CmdType}")


            if r.success:
                reply = CmdProtocol(CmdType=CmdType.ReOK, reply=r.message).dumps()
            else:
                logger.error(r.message)
                reply = CmdProtocol(CmdType=CmdType.ReERR, reply=r.message).dumps()

            client.sendall(reply)
            client.close()


def client(args: argparse.Namespace):

    host = args.host
    port = args.port

    if args.list:
        cmd = CmdProtocol(CmdType=CmdType.List).dumps()
    
    elif args.insert is not None:
        cmd = CmdProtocol(CmdType=CmdType.Insert, task_number=args.insert, qe_number=args.queue_number, task=Task(args.taskcmd, args.cwd)).dumps()

    elif args.remove is not None:
        cmd = CmdProtocol(CmdType=CmdType.Remove, task_number=args.remove, qe_number=args.queue_number).dumps()

    elif args.move:
        cmd = CmdProtocol(CmdType=CmdType.Move, move_i=int(args.move[0]), move_n=int(args.move[1]), qe_number=args.queue_number).dumps()
    
    elif args.done is not None:
        cmd = CmdProtocol(CmdType=CmdType.Done, task_number=args.done, qe_number=args.queue_number).dumps()

    elif args.add:
        cmd = CmdProtocol(CmdType=CmdType.ADD, task_number=args.add, qe_number=args.queue_number).dumps()
    
    elif args.kill is not None:
        cmd = CmdProtocol(CmdType=CmdType.Kill, task_number=args.kill, qe_number=args.queue_number).dumps()
    
    elif args.pause is not None:
        cmd = CmdProtocol(CmdType=CmdType.Pause, task_number=args.pause, qe_number=args.queue_number).dumps()
    
    elif args.recover is not None:
        cmd = CmdProtocol(CmdType=CmdType.Recover, task_number=args.recover, qe_number=args.queue_number).dumps()
    
    elif args.add_queue:
        cmd = CmdProtocol(CmdType=CmdType.Queue, qe_number=args.add_queue).dumps()

    elif args.task:
        cmd = CmdProtocol(CmdType=CmdType.Task, task=Task(args.taskcmd, args.cwd), qe_number=args.queue_number).dumps()

    elif args.status:
        cmd = CmdProtocol(CmdType=CmdType.Status, qe_number=args.queue_number).dumps()
    else:
        # 默认选项
        cmd = CmdProtocol(CmdType=CmdType.Status).dumps()


    with socket.create_connection((host, port)) as sock:

        sock.send(cmd)
        sock.shutdown(socket.SHUT_WR)

        buf = io.BytesIO()
        while (data := sock.recv(SOCK_BUF)) != b"":
            buf.write(data)

        try:
            proto = CmdProtocol.loads(buf.getvalue())
        except EOFError:
            print("接收数据异常，可能是服务端异常退出了。")
            return

        match proto.CmdType:
            case CmdType.ReOK|CmdType.Result:
                recode = 0
                print(proto.reply, flush=True)

            case CmdType.ReERR:
                recode = 1
                print(proto.reply, flush=True)

            case _:
                print("未知返回")
                recode = 1

    return recode


Usage = f"""
用法: {PROG} [options] [--] [taskcmd]
如果没有指定taskcmd，则默认执行 --status
启动服务器：
    {PROG} --server [options]

启动客户端：
    {PROG} [options] [--] [taskcmd]

一些小技巧：
    0. 在当前任务队列最后增加一个等待pid进程退出:
        {PROG} --task -- tail -f /dev/null --pid <pid>

    1. 在PID执行完成后，发送邮件通知。
        {PROG} --task -- mail -s '任务完成'
      或者桌面通知。
        {PROG} --task -- notify-send '任务完成'

"""

def main():
    parse = argparse.ArgumentParser(epilog=Usage, formatter_class=argparse.RawDescriptionHelpFormatter)

    option = parse.add_argument_group(title="通用参数", description="通用参数，server和client都可以使用的参数")
    option.add_argument("--server", action="store_true", help="启动server端")
    option.add_argument("--host", default="::1", help="默认地址(server: '::', or client: '::1'， 如果有BATCH_TASK_HOST环境变量优先使用)")
    option.add_argument("--port", type=int, default=1122, help="server 端口(default: 1122，如果有BATCH_TASK_PORT环境变量优先使用)")
    option.add_argument("--log", help=f"指定日志输出文件(default: {PROG}.log)")


    c = parse.add_argument_group(title="client 参数")
    c.add_argument("--add-queue", dest="add_queue", action="store", type=int, metavar="number", default=0, help="添加<number>个新的执行队列，并在这个队列上添加一个默认执行器")
    c.add_argument("--queue-number", dest="queue_number", type=int, metavar="number", default=0, help="添加，移动，删除，等等... 任务时指定队列号，默认0号队列")
    group = c.add_mutually_exclusive_group()
    group.add_argument("--add-executor", dest="add", type=int, metavar="number", help="添加一个并行执行器")
    group.add_argument("--done-executor", dest="done", type=int, metavar="number", help="指定一个执行器，本次执行完后退出。(减少一个并行执行)")
    group.add_argument("--kill", type=int, metavar="number", help="kill一个执行器(减少一个并行执行)")
    group.add_argument("--pause", type=int, metavar="number", help="暂停一个正在的执行器")
    group.add_argument("--recover", type=int, metavar="number", help="恢复一个正在的执行器")

    c.add_argument("--task", action="store_true", help="添加任务")
    c.add_argument("--task-workdir", dest="cwd", action="store", help="执行任务目录")

    group.add_argument("--status", action="store_true", help="查看状态(默认选项)")
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
        return 0

    ENV_HOST = os.environ.get("BATCH_TASK_HOST")
    ENV_PORT = os.environ.get("BATCH_TASK_PORT")

    if args.server:
        if ENV_HOST:
            args.host = ENV_HOST

        args.port = int(ENV_PORT) if ENV_PORT else args.port

        # fp = logging.FileHandler(f"{PROG}.log")
        fp = TimedRotatingFileHandler(f"{PROG}.log", when="D", interval=1, backupCount=7)
        fp.setFormatter(FMT)
        logger.setLevel(logging.INFO)
        logger.addHandler(fp)

        try:
            server(args)
        except KeyboardInterrupt:
            pass
        
        return 0
    
    if ENV_PORT:
        args.port = int(ENV_PORT)

    if ENV_HOST:
        args.host = ENV_HOST

    return client(args)


if __name__ == "__main__":
    sys.exit(main())
