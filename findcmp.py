#!/usr/bin/env python3
# coding=utf-8
# update 2022-08-03 05:03:07
# author calllivecn <c-all@qq.com>


import os
import re
import sys
import sqlite3 as sql
# from functools import partial
from threading import Thread
from hashlib import sha512
from tempfile import mktemp
from argparse import ArgumentParser
from os import (
    kill,
    remove,
)
from multiprocessing import (
    Process,
    Queue,
)
from os.path import (
    abspath,
    isdir,
    join,
    isfile,
    islink,
    getsize,
    basename,
)

SIGTERM = 15  # from signal import SIGTERM

CPU_COUNT = os.cpu_count()

argparse = ArgumentParser(
    description='通过文件名，文件大小和sha512值检测多个目录下有无相同文件.', add_help=True)

argparse.add_argument('-d', dest='delete',
                      action="store_true", help='相同文件直接删除')
argparse.add_argument('-i', dest='ask', action="store_true",
                      default=True, help='询问是否删除相同文件(默认)')
argparse.add_argument('-p', dest='out', action="store_true", help='输出相同文件(默认)')
argparse.add_argument('-P', dest='process', type=int,
                      metavar='CPU', default=CPU_COUNT - 1, help='使用几个CPU核心')
argparse.add_argument('dirs', nargs='*', action="store", help='目录')

args = argparse.parse_args()


def checkDirs(lists):
    '''check dirs 是否全是目录'''
    flag = False
    not_dir = []
    for d in lists:
        if not isdir(d):
            flag = True
            not_dir.append(d)
    if flag:
        print('不是目录:')
        for d in not_dir:
            print(d, '', end='')
        print()
        sys.exit(1)

    if args.process > CPU_COUNT and args.process <= 0:
        print('CPU MAX : {} your {}'.format(CPU_COUNT, args.process))
        sys.exit(1)


checkDirs(args.dirs)

# print(args);sys.exit(0)

task_put = Queue(128)
task_end_flag = 0


class Sql3():
    def __init__(self, db_filename=False):

        if db_filename:
            self.sql_file = db_filename
            self.db = sql.connect(self.sql_file)
            fetch = self.db.execute(
                'select tbl_name from sha where type="table" and tbl_name="sha";')

            if fetch.fetchall() == []:
                self.db.execute(
                    'create table sha512(filename text,filepath text,filesize int,sha512 int);')

        else:

            self.sql_file = mktemp()
            self.db = sql.connect(self.sql_file)
            self.db.execute(
                'create table sha512(filename text,filepath text,filesize int,sha512 int);')
        self.db.commit()

    def add(self, db_lists):
        self.db.executemany(
            'insert into sha512(filename,filepath,filesize,sha512) values(?,?,?,?)', db_lists)
        self.db.commit()

    def __update_sha(self, db_lists):
        self.db.executemany(
            'update sha512 set sha512=? where filepath=?;', db_lists)
        self.db.commit()

    def sha_sum(self):
        '''比较相同名的文件'''
        multi_file = self.db.execute(
            'select filename from sha512 group by filename having count(*)>1;')
        multi_file = multi_file.fetchall()

        for f in multi_file:
            f = f[0]
            fetch = self.db.execute(
                'select * from sha512 where filename=? and filesize in (select filesize from (select filename from sha512 where filename=?) group by filename having count(*)>1);', (f, f))  # 找出文件名相同，大小相同的文件

            sha__ = []

            for filename, filepath, size, sha in fetch.fetchall():
                sha_value = self.__sha512(filepath)
                sha__.append((sha_value, filepath))

            self.__update_sha(sha__)

    # '''
        # 比较相同大小的文件
        multi_file = self.db.execute(
            'select filesize from sha512 group by filesize having count(*)>1;')
        multi_file = multi_file.fetchall()

        # print('比较相同大小的文件',multi_file)

        for f in multi_file:  # .fetchall():
            fetch = self.db.execute(
                'select * from sha512 where filesize=?;', f)

            sha__ = []

            for filename, filepath, size, sha in fetch.fetchall():
                sha_value = self.__sha512(filepath)
                sha__.append((sha_value, filepath))

            self.__update_sha(sha__)
    # '''

    def __delete(self, del_lists):
        self.db.executemany(
            'delete from sha512 where filename=? and filepath=? and filesize=? and sha512=?', del_lists)
        self.db.commit()
        for filename, filepath, filesize, sha512 in del_lists:
            remove(filepath)

    def close(self):
        self.db.close()
        os.remove(self.sql_file)

    def check_diff(self):
        sha_value_lists = self.db.execute(
            'select sha512 from (select * from sha512 where sha512 is not null) group by sha512 having count(*)>1;')

        for sha_value in sha_value_lists.fetchall():  # sha_value_lists.fetchall():

            if sha_value != ('',):
                fetch = self.db.execute(
                    'select * from sha512 where sha512=?', sha_value)
                file_sha = fetch.fetchall()
                file_sha_len = len(file_sha)

                print('重复文件：')
                for i in range(file_sha_len):
                    print(i, file_sha[i][0], file_sha[i][1], sep='\t')

                if args.delete:
                    save_or_del = 's'
                    number_list = [0]
                else:
                    save_or_del, number_list = self.__rule_input(file_sha_len)

                if save_or_del == 'n' and save_or_del == 'N':
                    continue

                del_list = []

                if save_or_del == 's' or save_or_del == 'S':
                    for i in range(file_sha_len):
                        if not i in number_list:
                            del_list.append(file_sha[i])
                elif save_or_del == 'd' or save_or_del == 'D':
                    for i in range(file_sha_len):
                        if i in number_list:
                            del_list.append(file_sha[i])

                self.__delete(del_list)

    def __rule_input(self, len_file):
        while True:
            try:
                input_str = input(r'<s[ave]|d[el]|N[o]|[0-9]+ > ')
            except EOFError:
                print()
                continue

            if input_str == '':
                return 'No'

            input_number = re.findall(r'[0-9]+', input_str)
            input_str = input_str.split()
            s_or_d = input_str[0]

            if s_or_d == 's' or s_or_d == 'S' or s_or_d == 'd' or s_or_d == 'D':
                pass
            elif s_or_d == 'n' or s_or_d == 'N':
                return 'No'
            else:
                print('input wrong')
                continue

            if input_number == []:
                print('input number is null')
                continue

            input_number.sort(reverse=True)
            for i in range(len(input_number)):
                input_number[i] = int(input_number[i])

            max_len = input_number[0]
            # print('len_file',len_file,'max_len',max_len)
            if max_len > len_file:
                print('number error')
                continue

            return s_or_d, input_number

    def __sha512(self, file_):
        sha = sha512()
        READ_BUF = 1<<20
        with open(file_, 'rb') as f:
            # for data in iter(partial(f.read, READ_BUF), b""): # 这是py3.8以前的写法
            while (data := f.read(READ_BUF)) != b"":
                sha.update(data)
        # return sha.hexdigest()
        return sha.digest()


def taskPut(PATH_list):

    for PATH in PATH_list:
        PATH = abspath(PATH)
        for root, directory, files in os.walk(PATH):
            for f in files:
                abs_path = join(root, f)
                if isfile(abs_path) and not islink(abs_path):
                    # print('文件：',abs_path)
                    file_size = getsize(abs_path)
                    filename = basename(abs_path)
                    task_put.put((filename, abs_path, file_size, ''))

    task_put.put(task_end_flag)


def exitProgram(mp_pids):
    for pid in mp_pids:
        kill(pid, SIGTERM)


def main():
    sql_instance = Sql3()

    while True:
        add_sql_list = []

        for i in range(128):
            result = task_put.get()
            if result == 0:
                break
            add_sql_list.append(result)

        sql_instance.add(add_sql_list)

        if result == 0:
            break

    sql_instance.sha_sum()

    sql_instance.check_diff()

    sql_instance.close()


th = Thread(target=taskPut, args=(args.dirs,), daemon=True)
th.start()

try:
    main()
except (KeyboardInterrupt, EOFError) as e:
    pass
