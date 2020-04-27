#!/usr/bin/env python3
# coding=utf-8
# date 2020-04-26 19:40:54
# author calllivecn <c-all@qq.com>

import glob
from os import path
from setuptools import setup

with open("../LICENSE") as f:
    LICENSE = f.read()

# 拿到当前目录下的模块
modules = []
for py in glob.glob("*.py"):
    name, ext = path.splitext(py)
    modules.append(name)


setup(
        name="libpy",
        version="0.0.2",
        description="calllivecn mytools/libpy",
        author="calllivecn",
        author_email="c-all@qq.com",
        url="https://github.com/calllivecn/mytools/libpy/",
        license=LICENSE,
        py_modules=modules,
        platforms=["linux"],
        )
