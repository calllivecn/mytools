#!/usr/bin/env python3
# coding=utf-8
# date 2021-01-10 23:23:37
# author calllivecn <calllivecn@outlook.com>


# 改用bash

from systemd import journal

j = journal.Reader()

j.add_match(_COMM="systemd-logind")

for l in j:
    pass
