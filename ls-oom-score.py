#!/usr/bin/env python3

import os
import io
import sys

def get_oom_score(proc_dir):
    try:
        with open(os.path.join(proc_dir, "oom_score")) as f:
            return int(f.read().strip())
    except Exception:
        return None

def get_cmdline(proc_dir, number_cmd=64):
    try:
        with open(os.path.join(proc_dir, "cmdline"), "rb") as f:
            cmd = f.read().replace(b'\0', b' ').decode(errors='replace').strip()
            return cmd[:number_cmd]
    except Exception:
        return ""

def main():
    try:
        number = int(sys.argv[1])
    except (IndexError, ValueError):
        number = 20

    try:
        number_cmd = int(sys.argv[2])
    except (IndexError, ValueError):
        number_cmd = 64

    processes = []
    for entry in os.listdir("/proc"):
        if entry.isdigit():
            proc_dir = os.path.join("/proc", entry)
            oom_score = get_oom_score(proc_dir)
            if oom_score is not None:
                cmd = get_cmdline(proc_dir, number_cmd)
                processes.append((oom_score, int(entry), cmd))

    processes.sort(reverse=True)

    print_output = io.StringIO()
    print_output.write("oom_score\tpid\tcmd\n")

    for item in processes[:number]:
        print_output.write(f"{item[0]}\t{item[1]}\t{item[2]}\n")
    
    print(print_output.getvalue(), end="")

if __name__ == "__main__":
    main()