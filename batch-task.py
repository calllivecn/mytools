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
from pathlib import Path
from collections import deque
from datetime import datetime
from dataclasses import dataclass

import logging
# from logging.handlers import TimedRotatingFileHandler

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


Q_SPLIT = "#"*20
BIG_SPLIT = "="*20
SMALL_SPLIT = "-"*20
BIG2_SPLIT = BIG_SPLIT*2

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
            self.task = self.q.get()

            logger.info(f"{BIG2_SPLIT}")
            logger.info(f"↓\n开始时间: {timestamp()}\n{self.task}")
            logger.info(f"{BIG2_SPLIT}")

            self.status = Status.Running
            try:
                self.task.run()
            except Exception:
                traceback.print_exc()
                continue

            self.status = Status.Wait

            logger.info(f"{BIG2_SPLIT}")
            logger.info(f"↓\n开始时间: {self.task.start}, 结束时间: {self.task.end}\n{self.task}")
            logger.info(BIG2_SPLIT)


@dataclass
class QueueExecutor:
    queue: Q
    executor: list[Executor]


class Manager:
    """
    执行器之间是并行关系，每个执行器属于一个执行队列。
    可以多个执行器属于一个执行队列，同队列并行。
    """

    def __init__(self):
        self.qes: list = [QueueExecutor(Q(), executor=[])]
        # self.q = Q()
        # self.ths: list[Executor] = []
        self.add_executor(1)

    def add_queue(self):
        """
        添加一个新的任务队列, 默认一个执行器
        """
        self.qes.append(QueueExecutor(Q(), executor=[]))
        self.add_executor(1, len(self.qes)-1)


    def add_executor(self, i: int, qe_index: int = 0):
        qe: QueueExecutor = self.qes[qe_index]
        for _ in range(i):
            qe.executor.append(Executor(qe.queue))

    def done_executor(self, seq: int, qe_index: int = 0) -> OpReturn:
        ths: list[Executor] = self.qes[qe_index].executor
        ll = len(ths)
        if 0 <= seq <= ll - 1:
            t = ths[seq]
            opr = t.done()
        else:
            opr = OpReturn(success=False, message=f"没有执行器: {seq}")

        return opr
    
    def add_task(self, task: Task, qe_index: int = 0):
        q: Q = self.qes[qe_index].queue
        q.put(task)

    def kill(self, seq: int, qe_index: int = 0, sig: int = signal.SIGTERM) -> OpReturn:
        qe :QueueExecutor = self.qes[qe_index]

        ll = len(qe.executor)
        if 0 <= seq <= ll - 1:
            th = qe.executor.pop(seq)
            opr = th.kill(sig)
        else:
            opr = OpReturn(success=False, message=f"没有执行器: {seq}") 

        return opr

    def pause(self, seq: int, qe_index: int = 0) -> OpReturn:
        qe :QueueExecutor = self.qes[qe_index]

        ll = len(qe.executor)
        if 0 <= seq <= ll - 1:
            th = qe.executor[seq]
            opr = th.pause()
        else:
            opr = OpReturn(success=False, message=f"没有执行器: {seq}")

        return opr

    def recover(self, seq: int, qe_index: int = 0) -> OpReturn:
        qe :QueueExecutor = self.qes[qe_index]
        ll = len(qe.executor)
        if 0 <= seq <= ll - 1:
            th = qe.executor[seq]
            opr = th.recover()
        else:
            opr = OpReturn(success=False, message=f"没有执行器: {seq}")

        return opr

    def status(self) -> str:
        buf = io.StringIO()
        buf.write(f"{Q_SPLIT} 队列数：{len(self.qes)} {Q_SPLIT}\n")
        for n, qe in enumerate(self.qes):
            buf.write(f"{Q_SPLIT} 队列编号: {n} {Q_SPLIT}\n")
            buf.write(f"{BIG_SPLIT} 执行器(总数: {len(qe.exector)}) {BIG_SPLIT}\n")

            for i, th in enumerate(qe.executor):
                title = io.StringIO()
                title.write(f"{SMALL_SPLIT} 编号:{i}")

                match th.status:
                    case Status.Running | Status.Pause:

                        if th.status == Status.Running:
                            title.write(" -- 执行中")

                        if th.status == Status.Pause:
                            title.write(" -- 暂停状态(--recover恢复)")

                        if th.e.is_set():
                            qe.executor.pop(i)
                            title.write(" -- 标记: 执行完后退出")

                        title.write(f"{SMALL_SPLIT}")
                        buf.write(title.getvalue())
                        buf.write(f"\n{th.task}\n")

                    case Status.Wait:
                        title.write(f"{SMALL_SPLIT}")
                        buf.write(title.getvalue())
                        buf.write("等待中\n")

                    case _:
                        print(f"执行器处理未知状态: {th.status}")

        return buf.getvalue()
        
    def list(self) -> str:
        buf = io.StringIO()

        buf.write(f"{Q_SPLIT} 队列数：{len(self.qes)} {Q_SPLIT}\n")

        for n, qe in enumerate(self.qes):
            buf.write(f"{Q_SPLIT} 队列编号: {n} {Q_SPLIT}\n")
            buf.write(f"{BIG_SPLIT} 执行器(总数: {len(qe.exector)}) {BIG_SPLIT}\n")

            buf.write(f"任务队列(总数: {len(qe.executor)}):\n")
            for i, task in enumerate(qe.executor):
                s = BIG_SPLIT
                buf.write(f"{s} 任务号:{i} {s}\n{str(task)}\n")

        return buf.getvalue()

    def insert(self, i: int, task: Task, qe_index: int = 0):
        q: Q = self.qes[qe_index].queue
        q.insert(i, task)

    def remove(self, i: int, qe_index: int = 0):
        q: Q = self.qes[qe_index].queue
        try:
            q.remove(i)
        except IndexError:
            print(f"没有任务: {i}")

    def move(self, i: int, n: int, qe_index: int = 0):
        q: Q = self.qes[qe_index].queue
        try:
            q.move(i, n)
        except IndexError:
            print(f"没有任务: {i} or {n}")


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


@dataclass
class CmdProtocol:
    CmdType: CmdType
    qe_number: int|None = 0
    task: Task|None = None
    task_number: int|None = None
    reply: str|None = None
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


def server(args):
    host = args.host
    port = args.port

    logger.info(f"启动执行管理器: {host}:{port}")

    m = Manager()

    with socket.create_server((host, port), family=socket.AF_INET6, dualstack_ipv6=True) as sock:

        while True:
            client, addr = sock.accept()
            data =  client.recv(8192)
            if not data:
                logger.info("peer close()")
                client.close()
                continue

            try:
                # proto = pickle.loads(data)
                proto = CmdProtocol.loads(data)
            except Exception:
                logger.error("接收客户端数据异常")
                traceback.print_exc()
                continue

            match proto.CmdType:
                case CmdType.ReOK | CmdType.ReERR | CmdType.Result:
                    logger.error(f"客户端发送了错误的指令: {proto.CmdType}")
                    continue

                case CmdType.Status:
                    data = m.status()
                    data = f"{'+'*20} 服务器 [{host}]:{port} {'+'*20}\n" + data
                    reply = CmdProtocol(CmdType=CmdType.Result, reply=data).dumps()

                case CmdType.List:
                    data = m.list()
                    reply = CmdProtocol(CmdType=CmdType.Result, reply=data).dumps()

                case CmdType.Task:
                    # print(f"添加任务：{task.cmd}")
                    if proto.task is None:
                        logger.error("没有任务数据")
                        reply = CmdProtocol(CmdType=CmdType.ReERR).dumps()
                    else:
                        m.add_task(proto.task)

                    reply = CmdProtocol(CmdType=CmdType.ReOK).dumps()

                case CmdType.Insert:
                    if proto.task is None or proto.task_number is None:
                        logger.error("没有任务数据或任务编号")
                        reply = CmdProtocol(CmdType=CmdType.ReERR).dumps()
                    else:
                        m.insert(proto.task_number, proto.task)
                        reply = pickle.dumps((CmdType.ReOK,))

                case CmdType.Remove:
                    if proto.task_number is None:
                        logger.error("没有任务编号")
                        reply = CmdProtocol(CmdType=CmdType.ReERR).dumps()
                    else:
                        m.remove(proto.task_number)
                        reply = CmdProtocol(CmdType=CmdType.ReOK).dumps()

                case CmdType.Move:
                    if proto.move_i is None or proto.move_n is None:
                        logger.error("没有任务编号")
                        reply = CmdProtocol(CmdType=CmdType.ReERR).dumps()
                    else:
                        try:
                            m.move(proto.move_i, proto.move_n)
                        except IndexError:
                            reply = CmdProtocol(CmdType=CmdType.ReERR).dumps()
                            traceback.print_exc()
                        else:
                            reply = CmdProtocol(CmdType=CmdType.ReOK).dumps()

                case CmdType.Done:
                    if proto.task_number is None:
                        logger.error("没有任务编号")
                        reply = CmdProtocol(CmdType=CmdType.ReERR).dumps()
                    else:
                        m.done_executor(proto.task_number)
                        reply = CmdProtocol(CmdType=CmdType.ReOK).dumps()

                case CmdType.Kill:
                    if proto.task_number is None:
                        logger.error("没有任务编号")
                        reply = CmdProtocol(CmdType=CmdType.ReERR).dumps()
                    else:
                        m.kill(proto.task_number)
                        reply = CmdProtocol(CmdType=CmdType.ReOK).dumps()

                case CmdType.Pause:
                    if proto.task_number is None:
                        logger.error("没有任务编号")
                        reply = CmdProtocol(CmdType=CmdType.ReERR).dumps()
                    else:
                        opr = m.pause(proto.task_number)
                        if opr.success:
                            reply = CmdProtocol(CmdType=CmdType.ReOK).dumps()
                        else:
                            logger.error(opr.message)
                            reply = CmdProtocol(CmdType=CmdType.ReERR).dumps()

                case CmdType.Recover:
                    if proto.task_number is None:
                        logger.error("没有任务编号")
                        reply = CmdProtocol(CmdType=CmdType.ReERR).dumps()
                    else:
                        m.recover(proto.task_number)
                        reply = CmdProtocol(CmdType=CmdType.ReOK).dumps()

                case CmdType.ADD:
                    if proto.task_number is None:
                        logger.error("没有任务编号")
                        reply = CmdProtocol(CmdType=CmdType.ReERR).dumps()
                    else:
                        m.add_executor(proto.task_number)
                        reply = CmdProtocol(CmdType=CmdType.ReOK).dumps()

                case _:
                    logger.error(f"未知指令: {proto.CmdType}")
                    reply = CmdProtocol(CmdType=CmdType.ReERR).dumps()

            client.sendall(reply)
            client.close()


def client(args: argparse.Namespace):

    host = args.host
    port = args.port

    if args.status:
        cmd = CmdProtocol(CmdType=CmdType.Status).dumps()
    
    elif args.list:
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
    
    elif args.task:
        cmd = CmdProtocol(CmdType=CmdType.Task, task=Task(args.taskcmd, args.cwd), qe_number=args.queue_number).dumps()

    else:
        # 默认选项
        cmd = CmdProtocol(CmdType=CmdType.Status).dumps()


    with socket.create_connection((host, port)) as sock:

        sock.send(cmd)

        buf = io.BytesIO()
        while (data := sock.recv(8192)) != b"":
            buf.write(data)

        try:
            proto = CmdProtocol.loads(buf.getvalue())
        except EOFError:
            print("接收数据异常，可能是服务端异常退出了。")
            return

        match proto.CmdType:
            case CmdType.ReOK:
                recode = 0

            case CmdType.ReERR:
                print("有什么出错了, 查看服务端日志。")
                recode = 1

            case CmdType.Result:
                try:
                    print(proto.reply, flush=True)
                except BrokenPipeError:
                    pass
                recode = 0
            case _:
                print("未知返回")
                recode = 1

    sys.exit(recode)


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
    group = c.add_mutually_exclusive_group()
    group.add_argument("--add-queue", dest="queue", type=int, metavar="number", default=1, help="添加<number>个新的执行队列，并在这个队列上添加一个默认执行器")
    group.add_argument("--queue-number", dest="queue_number", type=int, metavar="number", default=0, help="在指定的队列上添加任务，默认0号队列")
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

    if ENV_HOST:
        args.host = ENV_HOST

    client(args)


if __name__ == "__main__":
    main()
