
import os
import sys
import subprocess
import argparse
import winreg


def validate_python_exe(path):
    """验证 python.exe 路径是否有效。"""
    if not path:
        raise ValueError("python.exe 路径不能为空")
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"找不到文件: {path}")
    if not path.lower().endswith(".exe"):
        raise ValueError(f"python.exe 路径必须以 .exe 结尾: {path}")
    return path


def validate_icon_path(path):
    """验证图标路径，允许 .ico / .exe / .dll。"""
    if not path:
        return None
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"找不到图标文件: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".ico", ".exe", ".dll"):
        raise ValueError(f"图标必须是 .ico、.exe 或 .dll 文件: {path}")
    return path


def find_pythonw(python_exe):
    """在 python.exe 同目录下找 pythonw.exe。"""
    python_dir = os.path.dirname(python_exe)
    candidate = os.path.join(python_dir, "pythonw.exe")
    return candidate if os.path.isfile(candidate) else None


def register_py_file_type(python_exe, pythonw_exe, icon_path):
    """写入注册表：.py 关联、打开命令、默认图标。"""
    prog_id = "Python.File"
    description = "Python Script"

    # .py -> ProgID
    with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, ".py") as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, prog_id)
        winreg.SetValueEx(key, "Content Type", 0, winreg.REG_SZ, "text/plain")

    # ProgID 描述
    with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, prog_id) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, description)

    # 双击打开命令
    open_cmd = f'"{python_exe}" "%1" %*'
    with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, rf"{prog_id}\shell\open\command") as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, open_cmd)

    # 可选：右键 "Run with Python (no console)"
    if pythonw_exe:
        runw_cmd = f'"{pythonw_exe}" "%1" %*'
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, rf"{prog_id}\shell\RunNoConsole\command") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, runw_cmd)
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, rf"{prog_id}\shell\RunNoConsole") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Run with Python (no console)")

    # 默认图标
    if icon_path:
        icon_value = icon_path
        if icon_path.lower().endswith((".exe", ".dll")):
            icon_value = f"{icon_path},0"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, rf"{prog_id}\DefaultIcon") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, icon_value)

    print("注册表写入完成。")


def refresh_icon_cache():
    """通知资源管理器刷新图标缓存。"""
    try:
        subprocess.run(["ie4uinit.exe", "-show"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    try:
        subprocess.run(["taskkill", "/f", "/im", "explorer.exe"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen("explorer.exe")
    except Exception:
        pass


def check_admin():
    """检查是否以管理员身份运行。"""
    try:
        return subprocess.run(
            ["net", "session"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode == 0
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="为 .py 文件注册 Python.File 关联并设置默认图标"
    )
    parser.add_argument(
        "--python-exe",
        required=True,
        help="python.exe 的完整路径，例如 C:\\Python311\\python.exe",
    )
    parser.add_argument(
        "--icon",
        required=True,
        help="图标文件路径，支持 .ico、.exe、.dll",
    )
    args = parser.parse_args()

    if sys.platform != "win32":
        print("此脚本只能在 Windows 上运行。")
        sys.exit(1)

    if not check_admin():
        print("请以管理员身份运行此脚本。")
        print("例如：右键 PowerShell -> 以管理员身份运行 -> python setup_py_icon.py ...")
        sys.exit(1)

    try:
        python_exe = validate_python_exe(args.python_exe)
        icon_path = validate_icon_path(args.icon)
    except (ValueError, FileNotFoundError) as e:
        print(f"参数错误: {e}")
        sys.exit(1)

    pythonw_exe = find_pythonw(python_exe)

    print(f"python.exe  : {python_exe}")
    print(f"pythonw.exe : {pythonw_exe or '未找到'}")
    print(f"图标文件    : {icon_path}")

    register_py_file_type(python_exe, pythonw_exe, icon_path)
    refresh_icon_cache()

    print("完成。如果图标没有立即变化，请重启资源管理器或重新登录。")


if __name__ == "__main__":
    main()
