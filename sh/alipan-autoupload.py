

import sys
import argparse
import subprocess
import threading
import queue

from pathlib import Path


from aligo import Aligo

# 上传到阿里云盘
def upload_to_alipan(net_path: Path, file_path: Path):
    ali = Aligo("calllivecn")
    remote_folder = ali.get_folder_by_path(net_path.parent.as_posix())

    if remote_folder is None:
        print(f"远程目录不存在: {net_path.parent}, 现在创建")
        remote_folder = ali.create_folder(net_path.parent.as_posix())

    ali.upload_file(file_path, remote_folder.file_id)


def monitor_dir(dir_path: Path, file_queue: queue.Queue):
    cmd = [
        "inotifywait", "-mrq",
        "--format", r"%w%f",
        "-e", "move,close_write",
        dir_path
    ]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True) as proc:
        while True:
            if proc.stdout is None:
                break
            line = proc.stdout.readline().strip()
            file_path = Path(line)
            file_queue.put(file_path)
            print(f"监控到新文件: {file_path}")



def clear_empty_dirs(root_dir: Path):
    empty_found = True
    while empty_found:
        empty_found = False
        for dirpath, dirnames, filenames in root_dir.walk(top_down=False):
            if not dirnames and not filenames:
                try:
                    if root_dir != dirpath:
                        dirpath.rmdir()
                        empty_found = True
                        print(f"删除空目录: {dirpath}")
                except OSError as e:
                    print(f"无法删除目录 {dirpath}: {e}")

def main():

    parse = argparse.ArgumentParser(description="监控目录中的新文件")
    parse.add_argument("dir", type=Path, help="要监控的目录")
    args = parse.parse_args()
    if args.dir.exists() and args.dir.is_dir():
        watch_dir = args.dir
    else:
        print(f"{args.dir} 必需是一个存在的目录")
        sys.exit(1)
    
    file_queue: queue.Queue[Path] = queue.Queue(100000)

    t = threading.Thread(target=monitor_dir, args=(watch_dir, file_queue), daemon=True)
    t.start()

    # 示例：主线程处理队列中的文件
    while True:
        try:
            file_path = file_queue.get(timeout=60)
        except queue.Empty:
            clear_empty_dirs(watch_dir)
            continue

        print(f"处理文件: {file_path}")

        # 在这里添加你的处理逻辑
        net_path = file_path.relative_to(watch_dir)

        if file_path.is_file():
            upload_to_alipan(net_path, file_path)
            file_path.unlink(missing_ok=True)
            print(f"上传完成，已删除本地文件: {file_path}")
        else:
            print(f"本地文件不存在: {file_path}")
        file_queue.task_done()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass