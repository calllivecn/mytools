#!/bin/bash
# date 2022-03-14 06:08:33
# author calllivecn <c-all@qq.com>

set -e

PORT=${2-1121}

exec 9<>/dev/tcp/$1/$PORT

cat <&9

# close socket
exec &9<&-
exec &9>&-
