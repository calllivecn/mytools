#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import shutil
import subprocess
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

try:
    import libvirt
except ModuleNotFoundError:
    print("错误: 未找到 libvirt 模块。")
    print("Debian/Ubuntu: sudo apt install python3-libvirt")
    print("CentOS/RHEL: sudo dnf install python3-libvirt")
    sys.exit(1)

class VMBackup:
    def __init__(self, vm_name, backup_root_path):
        self.vm_name = vm_name
        # 最终备份包存放的路径 (用户指定)
        self.backup_root = Path(backup_root_path).resolve()
        
        self.conn = None
        self.dom = None
        
        self.date_str = datetime.now().strftime('%Y-%m-%d')
        # 临时文件夹名字
        self.staging_dir_name = f"{self.vm_name}-{self.date_str}"
        
        # 临时目录路径将在获取磁盘信息后动态确定
        self.staging_path = None

    def connect(self):
        """连接 libvirt 并获取虚拟机对象"""
        try:
            self.conn = libvirt.open('qemu:///system')
        except libvirt.libvirtError as e:
            print(f"[-] 连接 libvirt 失败: {e}")
            sys.exit(1)

        try:
            self.dom = self.conn.lookupByName(self.vm_name)
        except libvirt.libvirtError:
            print(f"[-] 找不到名为 '{self.vm_name}' 的虚拟机")
            sys.exit(1)

    def check_state(self):
        """检测虚拟机状态"""
        state, _ = self.dom.state()
        if state != libvirt.VIR_DOMAIN_SHUTOFF:
            print(f"[!] 错误: 虚拟机 '{self.vm_name}' 正在运行。")
            print("    为了保证数据一致性及硬链接安全，请先关闭虚拟机。")
            self.conn.close()
            sys.exit(1)

    def get_files(self, xml_desc):
        """解析 XML 获取文件列表"""
        disks = []
        others = [] 
        tree = ET.fromstring(xml_desc)

        # 获取磁盘
        for disk in tree.findall(".//disk"):
            device = disk.get('device')
            if device == 'disk':
                source = disk.find('source')
                if source is not None:
                    file_path = source.get('file')
                    if file_path:
                        disks.append(Path(file_path))

        # 获取 NVRAM
        nvram = tree.find(".//os/nvram")
        if nvram is not None and nvram.text:
            others.append(Path(nvram.text))

        return disks, others

    def handle_nvram_copy(self, src, dest):
        """处理 NVRAM 复制，包含权限不足时的交互逻辑"""
        try:
            shutil.copy2(src, dest)
            print(f"[+] NVRAM 已复制: {src.name}")
        except PermissionError:
            print(f"\n[!] 权限拒绝: 无法读取 NVRAM 文件。")
            print(f"    文件路径: {src}")
            print(f"    通常 NVRAM 文件只有 root 权限可读。")
            print(f"    请在另一个终端执行以下命令来手动复制文件：")
            print("-" * 60)
            # 生成方便用户复制的命令
            print(f"sudo cp -v \"{src}\" \"{dest}\"")
            print(f"sudo chown {os.getenv("USER", "<替换为当前用户名>")} \"{dest}\"")
            print("-" * 60)
            
            while True:
                user_input = input("\n>>> 执行完上述命令后，请输入 'y' 继续 (输入 'n' 退出): ").strip().lower()
                if user_input == 'y':
                    if dest.exists():
                        print(f"[+] 检测到文件已存在，继续备份任务。")
                        # 注意：如果用户用 sudo cp，文件的 owner 是 root。
                        # 后续 tar 打包时如果当前用户有读权限通常没问题（cp默认保留模式，可能600），
                        # 如果 tar 报错，可能需要 sudo 运行此脚本。
                        return
                    else:
                        print("[-] 错误: 目标目录下仍未找到文件，请检查命令是否执行成功。")
                elif user_input == 'n':
                    print("[-] 用户取消操作，脚本退出。")
                    self.cleanup()
                    sys.exit(1)

    def prepare_staging_env(self):
        self.connect()
        self.check_state()

        raw_xml = self.dom.XMLDesc()
        disks, others = self.get_files(raw_xml)

        if not disks:
            print("[-] 错误: 未检测到磁盘文件，无法确定硬链接临时目录位置。")
            sys.exit(1)

        # 1. 确定临时目录位置 (位于第一个磁盘文件的同级目录下)
        first_disk_dir = disks[0].parent
        self.staging_path = first_disk_dir / self.staging_dir_name

        print(f"[*] 磁盘位置: {first_disk_dir}")
        print(f"[*] 临时目录: {self.staging_path}")

        # 创建目录
        if self.staging_path.exists():
            shutil.rmtree(self.staging_path)
        
        try:
            self.staging_path.mkdir(parents=True, exist_ok=True)
        except PermissionError:
             print(f"[-] 错误: 没有权限在 {first_disk_dir} 创建目录。")
             print("    请尝试使用 sudo 运行此脚本。")
             sys.exit(1)

        # 2. 保存 XML
        xml_dest = self.staging_path / f"{self.vm_name}.xml"
        with xml_dest.open('w') as f:
            f.write(raw_xml)
        print(f"[+] XML 配置文件已保存")

        # 3. 复制 NVRAM (带交互式权限处理)
        for src in others:
            if src.exists():
                dest = self.staging_path / src.name
                self.handle_nvram_copy(src, dest)

        # 4. 创建磁盘硬链接 (保留软链接代码备用)
        print("[*] 正在处理磁盘文件...")
        for src in disks:
            if src.exists():
                dest = self.staging_path / src.name
                
                # --- 硬链接逻辑 (优先) ---
                # try:
                #     os.link(src, dest)
                #     print(f"[+] 硬链接创建成功: {dest.name}")
                #     continue # 硬链接成功，跳过当前循环
                # except OSError as e:
                #     # 如果是跨分区错误 (Errno 18) 或其他错误，尝试 fallback 或报错
                #     print(f"[-] 硬链接失败 ({src.name}): {e}")
                
                # --- 软链接逻辑 (作为备选，或者如果你想强制改这里) ---
                # 如果你想完全保留软链接代码，可以在这里解开注释作为 fallback
                print(f"[*] 尝试降级为软链接: {src.name}")
                try:
                    os.symlink(src.resolve(), dest)
                    print(f"[+] 软链接创建成功: {dest.name}")
                except OSError as e:
                    print(f"[-] 软链接也失败了: {e}")

            else:
                print(f"[-] 警告: 源磁盘文件不存在: {src}")

    def run_tar_archive(self):
        """执行打包归档"""
        if not self.staging_path or not self.staging_path.exists():
            print("[-] 错误: 临时目录不存在，无法打包。")
            return False

        archive_filename = f"{self.staging_dir_name}.tar.zst"
        archive_path = self.backup_root / archive_filename
        
        print(f"[*] 开始打包归档...")
        print(f"    输入: {self.staging_path}")
        print(f"    输出: {archive_path}")

        if not self.backup_root.exists():
             self.backup_root.mkdir(parents=True, exist_ok=True)

        cmd = [
            "tar",
            "--dereference", # 追踪软链接(如果混用了软链接), -v: 显示过程
            "--zstd",
            "-cvf",
            str(archive_path),
            str(self.staging_dir_name)
        ]

        try:
            # 这里的 cwd 必须是临时目录的父级
            # 这样 tar 只需要打包目录名，而不是绝对路径
            cwd_path = self.staging_path.parent
            
            subprocess.run(
                cmd,
                cwd=cwd_path, 
                check=True
                # 去掉了 stdout/stderr PIPE，直接输出到屏幕
            )
            print(f"\n[+] 备份成功打包: {archive_path}")
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"\n[-] 打包失败 (Exit Code {e.returncode})")
            return False
        except PermissionError:
             print(f"[-] 权限错误: 无法运行 tar，可能没有权限访问 {cwd_path}")
             return False

    def run_tar_crypt_split(self):
        """执行打包归档+加密+分割"""
        if not self.staging_path or not self.staging_path.exists():
            print("[-] 错误: 临时目录不存在，无法打包。")
            return False

        archive_path = self.backup_root / self.staging_dir_name
        
        print(f"[*] 开始打包归档...")
        print(f"    输入: {self.staging_path}")
        print(f"    输出: {archive_path}")

        if not self.backup_root.exists():
             self.backup_root.mkdir(parents=True, exist_ok=True)

        cmd = [
            "tarpy",
            "--dereference", # 追踪软链接(如果混用了软链接)
            "-ezcv",
            "--split",
            str(archive_path),
            str(self.staging_dir_name),
        ]

        try:
            # 这里的 cwd 必须是临时目录的父级
            # 这样 tar 只需要打包目录名，而不是绝对路径
            cwd_path = self.staging_path.parent
            
            subprocess.run(
                cmd,
                cwd=cwd_path, 
                check=True
                # 去掉了 stdout/stderr PIPE，直接输出到屏幕
            )
            print(f"\n[+] 备份成功打包: {archive_path}")
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"\n[-] 打包失败 (Exit Code {e.returncode})")
            return False
        except PermissionError:
             print(f"[-] 权限错误: 无法运行，可能没有权限访问 {cwd_path}")
             return False

    def check_cmd(self, cmd: str) -> bool:
        try:
            subprocess.run(["type", cmd], shell=True, check=True)
        except subprocess.CalledProcessError:
            return False
        
        return True

    def cleanup(self):
        """清理临时目录"""
        if self.staging_path and self.staging_path.exists():
            print(f"[*] 清理临时目录: {self.staging_path}")
            try:
                shutil.rmtree(self.staging_path)
                print("[+] 清理完成")
            except PermissionError:
                print(f"[-] 清理失败: 权限不足。")
                print(f"    如果刚才使用了 sudo cp，该目录下可能存在 root 拥有的文件。")
                print(f"    请手动执行: sudo rm -rf {self.staging_path}")


    def perform_backup(self):
        print(f"==========================================")
        print(f" 任务: 备份虚拟机 {self.vm_name}")
        print(f" 模式: 硬链接 + 交互式权限处理")
        print(f"==========================================")

        try:
            self.prepare_staging_env()

            if self.check_cmd("tarpy"):
                success = self.run_tar_crypt_split()
            else:
                success = self.run_tar_archive()
            
            if success:
                self.cleanup()
            else:
                print(f"[-] 警告: 任务未完全成功，保留临时目录: {self.staging_path}")

        except Exception as e:
            print(f"\n[-] 发生未预期的错误: {e}")
            # 如果是交互式中断，可能需要清理
            self.cleanup() 
        finally:
            if self.conn:
                self.conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 vm_backup_interactive.py <虚拟机名称> <备份保存根目录>")
        sys.exit(1)

    vm_name_input = sys.argv[1]
    backup_path_input = sys.argv[2]
    
    # 简单的路径检查
    if not os.path.exists(backup_path_input):
         print(f"[-] 警告: 备份目录 {backup_path_input} 不存在，稍后将尝试创建。")

    backup_job = VMBackup(vm_name_input, backup_path_input)
    backup_job.perform_backup()
