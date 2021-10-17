#!/bin/bash
# date 2021-10-17 20:42:56
# author calllivecn <c-all@qq.com>

# X11 下的
# SELECT_MONITOR: 外接显示器(使用randr, 命令查看), $1: 0 ~ 1 之间的值，亮度。
xrandr --output "$SELECT_MONITOR" --brightness "$1"

