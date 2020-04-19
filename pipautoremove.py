#!/usr/bin/env python3
# coding=utf-8
# date 2020-03-27 02:23:41
# author calllivecn <c-all@qq.com>

import sys
import subprocess
import pkg_resources


WHITE_LIST = ("pip", "setuptools","wheel")


def pipcmd(cmd):
    cmd = cmd.split()
    subprocess.check_call([sys.executable, "-m", "pip"] + cmd)


def pipuninstall(name):
    pipcmd("uninstall {}".format(name))

def confirm():
    return input("uninstall [y/N]?") == "y"

def get_all_pkg():
    all_pkg = set()
    for d in pkg_resources.working_set:
            all_pkg.add(d)
    return all_pkg


def find_depends_graph(all_pkg):
    depends = set()

    for d in all_pkg:
        for depend in d.requires():
            depends.add(depend)

    return  depends


def get_all_pkg_sub_names(all_pkg, names):
    return all_pkg - set(names)


# 所有用户安装的包，和没有被删除的依赖包
# 也就是在依赖树顶端的包。
# 也是pip list --not-required 列出来的包
def find_not_requireds(all_pkg, depends_graph):
    return all_pkg - depends_graph


# 用户删除的包只能是 not-required 里的，
# 否则会破坏依赖。
def check_names(not_requireds, names):
    not_names = []
    for n in names:
        if n not in not_requrieds:
            not_names.append(n)
    
    if len(not_names) != 0:
        for n in not_names:
            print("删除{n}包会破坏依赖关系")
        sys.exit(2)



# 找到需要移除的names包的全部依赖
def find_names_depend_graph(all_pkg_sub_names, names=()):
    """
    all_pkg: 系统、和当前用户空间的所有包集合
    names: 是一个要删除的包元组
    """
    depends_set = set()
    for d in all_pkg_sub_names:
        for depend in d.requires():
            depends_set.add(d)

    return depends_set


# 找出除names包的其他包的所有依赖。记为dependIndepend集合。
# 然后用names_depends_graph 集合减去 dependIndepend.
# 得到可删除依赖图。
def depend_in_depend_graph(all_pkg_sub_names):

    dependindepend = set()
    for d in all_pkg_sub_names:
        for depend in d.requires():
            dependindepend.add(depend)

    return dependindepend


# 可以删除依赖graph 排除白名单。
def remove_graph(names_depend_graph, depend_in_depend_graph):

    removes = names_depend_graph - depend_in_depend_graph

    for white in WHITELIST:
        removes.remove(pkg_resources.get_distribution(white))

    return removes


# print pip list --not-required
def pip_not_required(not_required):
    for n in sorted(not_required, key=lambda x: x.project_name.lower()):
        print("{}=={}".format(n.project_name,n.version))


def main():
    import argparse

    parse = argparse.ArgumentParser(usage="%(prog)s [optin] <name ...>")

    parse.add_argument("names", nargs="*", action="append", help="需要移除的包")

    parse.add_argument("-l", "--list", action="store_true", help="例出同 pip list --not-required")

    parse.add_argument("-y", "--yes", action="store_true", help="直接删除，不确认。")

    parse.add_argument("--parse", action="store_true", help="debug args.parse_args()")

    args = parse.parse_args()

    if args.parse:
        print(args)
        sys.exit(0)

    all_pkg = get_all_pkg()
    
    not_required = find_not_requireds(all_pkg, find_depends_graph(all_pkg))
    
    if args.list:
        pip_not_required(not_required)
        sys.exit(0)
    

if __name__ == "__main__":
    main()
