#!/bin/sh

echo "附近wifi信道统计："

sudo iw dev wlp2s0 scan  | grep -i "primary channel" |sort -t ':' -k 2 -nr  |uniq -c | sort -k 1 -nr


