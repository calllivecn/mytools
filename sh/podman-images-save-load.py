#!/usr/bin/env python3
import os
import subprocess
import argparse
import glob

def get_images():
    """获取本地所有的 podman 镜像，并按 Image ID 过滤重复镜像"""
    print("正在获取 Podman 镜像列表...")
    # 增加 {{.ID}} 获取镜像的唯一标识符，用管道符 | 分隔
    cmd =["podman", "images", '--format={{.ID}}|{{.Repository}}:{{.Tag}}']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"获取镜像失败: {e.stderr}")
        return []
    
    images_to_export =[]
    seen_ids = set()
    
    # 按行解析输出
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
            
        # 根据 Image ID 去重
        if img_id in seen_ids:
            print(f"   [跳过] 发现重复镜像 (ID: {img_id[:12]}): {img_name}")
            continue
            
        seen_ids.add(img_id)
        images_to_export.append(img_name)
        
    return images_to_export

def escape_filename(image_name):
    """处理镜像名中的特殊字符，将其转换为合法的文件名"""
    # 将 / 和 : 统一替换为下划线 _
    return image_name.replace("/", "_").replace(":", "_")

def save_images(output_dir):
    """将去重后的镜像单独导出为 .zst 压缩包"""
    os.makedirs(output_dir, exist_ok=True)
    images = get_images()
    
    if not images:
        print("未找到任何可导出的镜像。")
        return

    print(f"\n共发现 {len(images)} 个独立镜像准备导出。")
    
    for img in images:
        safe_name = escape_filename(img)
        file_path = os.path.join(output_dir, f"{safe_name}.zst")
        print(f"\n开始导出: {img} -> {file_path}")
        
        # 相当于 shell: podman save "$img" | zstd -T0 - -o "${file_path}"
        p_save = subprocess.Popen(["podman", "save", img], stdout=subprocess.PIPE)
        p_zstd = subprocess.Popen(["zstd", "-T0", "-", "-o", file_path], 
                                  stdin=p_save.stdout, 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE)
        
        # 允许 p_save 接收 SIGPIPE 信号
        p_save.stdout.close()
        
        # 等待 zstd 执行完成
        _, err = p_zstd.communicate()
        
        if p_zstd.returncode == 0:
            print(f"✅ 成功导出: {file_path}")
        else:
            print(f"❌ 导出失败 {img}: {err.decode('utf-8').strip()}")

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
        p_load = subprocess.Popen(["podman", "load"], 
                                  stdin=p_zstd.stdout, 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE)
        
        p_zstd.stdout.close()
        
        out, err = p_load.communicate()
        
        if p_load.returncode == 0:
            print(f"✅ 成功还原: {out.decode('utf-8').strip()}")
        else:
            print(f"❌ 还原失败 {file_path}: {err.decode('utf-8').strip()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Podman 镜像批量 ZSTD 导出/导入工具 (支持去重)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    parser_save = subparsers.add_parser("save", help="导出当前用户的所有 Podman 镜像")
    parser_save.add_argument("-d", "--dir", default=".", help="导出的目标目录 (默认为当前目录)")
    
    parser_load = subparsers.add_parser("load", help="还原目录下的所有 .zst 镜像包")
    parser_load.add_argument("-d", "--dir", default=".", help="读取文件的目录 (默认为当前目录)")
    
    args = parser.parse_args()
    
    if args.command == "save":
        save_images(args.dir)
        print("可以直接使用命令：`ls *.zst | xargs -n 1 podman load -i`批量导入")
    elif args.command == "load":
        load_images(args.dir)
