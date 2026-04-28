#!/usr/bin/env python3
import os
import subprocess
import argparse
import glob

def get_images_grouped_by_id():
    """获取所有镜像，并按 Image ID 将所有相关的镜像名（Tag）进行分组合并"""
    print("正在获取 Podman 镜像列表...")
    cmd =["podman", "images", '--format={{.ID}}|{{.Repository}}:{{.Tag}}']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"获取镜像失败: {e.stderr}")
        return {}
    
    images_by_id = {}
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
            
        parts = line.split('|', 1)
        if len(parts) != 2:
            continue
            
        img_id, img_name = parts
        
        # 过滤掉悬空镜像(dangling images)
        if img_name == "<none>:<none>":
            continue
            
        # 根据 Image ID 将相同底层的镜像名归类到同一个列表中
        if img_id not in images_by_id:
            images_by_id[img_id] = []
        images_by_id[img_id].append(img_name)
        
    return images_by_id

def escape_filename(image_name):
    """处理镜像名中的特殊字符，将其转换为合法的文件名"""
    return image_name.replace("/", "_").replace(":", "_")

def save_images(output_dir):
    """将同 ID 的镜像合并打包导出为单个 .zst"""
    os.makedirs(output_dir, exist_ok=True)
    images_by_id = get_images_grouped_by_id()
    
    if not images_by_id:
        print("未找到任何可导出的镜像。")
        return

    print(f"\n共发现 {len(images_by_id)} 个底层独立镜像(Image IDs) 准备导出。")
    
    for img_id, tags in images_by_id.items():
        # 使用列表中的第一个镜像名作为文件名的主体
        primary_tag = tags[0]
        safe_name = escape_filename(primary_tag)
        
        # 如果同一个镜像有多个 Tag，则在文件名上加个小尾巴以示区分
        if len(tags) > 1:
            file_path = os.path.join(output_dir, f"{safe_name}_and_{len(tags)-1}more.zst")
            print(f"\n开始导出 [多标签聚合包]: {', '.join(tags)}\n  -> {file_path}")
        else:
            file_path = os.path.join(output_dir, f"{safe_name}.zst")
            print(f"\n开始导出: {primary_tag}\n  -> {file_path}")
        
        # 核心逻辑：podman save 后面跟着同一 ID 的所有 Tag，把它们打包进同一个归档里
        cmd_save = ["podman", "save"] + tags
        p_save = subprocess.Popen(cmd_save, stdout=subprocess.PIPE)
        
        # 管道接入 zstd 压缩
        p_zstd = subprocess.Popen(["zstd", "-T0", "-", "-o", file_path], 
                                  stdin=p_save.stdout, 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE)
        
        # 允许 p_save 接收 SIGPIPE 信号
        p_save.stdout.close()
        
        # 等待 zstd 执行完成
        _, err = p_zstd.communicate()
        
        if p_zstd.returncode == 0:
            print(f"✅ 成功导出")
        else:
            print(f"❌ 导出失败: {err.decode('utf-8').strip()}")

def load_images(input_dir):
    """从指定目录还原所有 .zst 镜像包"""
    search_pattern = os.path.join(input_dir, "*.zst")
    zst_files = glob.glob(search_pattern)
    
    if not zst_files:
        print(f"在目录 '{input_dir}' 中未找到任何 .zst 文件。")
        return

    print(f"共发现 {len(zst_files)} 个镜像包准备还原。")
    
    for file_path in zst_files:
        print(f"\n开始还原: {file_path}")
        
        # 相当于 shell: zstd -d -c "${file_path}" | podman load
        p_zstd = subprocess.Popen(["zstd", "-d", "-c", file_path], stdout=subprocess.PIPE)
        
        # 已内置添加 --storage-opt ignore_chown_errors=true 彻底解决由于 SubUID 不足引起的 Rootless 权限报错
        p_load = subprocess.Popen(["podman", "--storage-opt", "ignore_chown_errors=true", "load"], 
                                  stdin=p_zstd.stdout, 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE)
        
        p_zstd.stdout.close()
        out, err = p_load.communicate()
        
        if p_load.returncode == 0:
            load_msg = out.decode('utf-8').strip()
            print(f"✅ 成功还原:\n{load_msg}")
        else:
            print(f"❌ 还原失败 {file_path}: {err.decode('utf-8').strip()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Podman 镜像批量 ZSTD 导出/导入工具 (分组去重完美版)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    parser_save = subparsers.add_parser("save", help="导出当前用户的所有 Podman 镜像")
    parser_save.add_argument("-d", "--dir", default=".", help="导出的目标目录 (默认为当前目录)")
    
    parser_load = subparsers.add_parser("load", help="还原目录下的所有 .zst 镜像包")
    parser_load.add_argument("-d", "--dir", default=".", help="读取文件的目录 (默认为当前目录)")
    
    args = parser.parse_args()
    
    if args.command == "save":
        save_images(args.dir)
        print("可以使用：`ls *.zst |xargs -n 1 podman load -i` 导入")
    elif args.command == "load":
        load_images(args.dir)
