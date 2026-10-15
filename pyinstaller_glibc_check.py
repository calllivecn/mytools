#!/usr/bin/bash


# 检测当前虚拟环境下所有的动态库需要的最低级glibc版本

find .venv/lib/python3.12/site-packages/ -type f \( -name "*.so" -o -name "*.so.*" -o -perm -u+x \) -print0   | xargs -0 -I{} sh -c '
      v=$(strings "{}" 2>/dev/null | grep -oP "GLIBC_\d+\.\d+" | sort -V | tail -1)
      [ -n "$v" ] && echo "$v  {}"
    ' | sort -V | tail -20

