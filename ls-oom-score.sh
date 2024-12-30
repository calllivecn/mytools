#!/bin/bash

echo -e "oom_score\tpid\tcmd"

for proc in $(find /proc -type d -maxdepth 1 -regex '/proc/[0-9]+'); do
    printf "%d\t%d\t%s\n" \
        "$(cat $proc/oom_score)" \
        "$(basename $proc)" \
        "$(cat $proc/cmdline | tr '\0' ' ' | head -c 50)"

done 2>/dev/null | sort -nr | head -n 20
