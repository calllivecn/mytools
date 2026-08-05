#!/usr/bin/env python3
# coding=utf-8
# date 2026-08-05
# author calllivecn <calllivecn@outlook.com>


import argparse
import sys

from pathlib import Path

from totpstore import (
    open_store,
)


def getpass_pw(prompt: str = "主密码: ") -> str:
    import getpass
    return getpass.getpass(prompt)


def cmd_list(store):
    for e in store.list_entries():
        notes = e.get("notes") or ""
        print(f"{e['id']}  {e['label']}  {notes}")


def cmd_add(store, label: str, secret: str, notes: str = "", secret_info: str = ""):
    eid = store.add(label, secret, notes, secret_info)
    print(f"已添加: {eid}  {label}")


def cmd_update(store, target: str, label: str, secret: str, notes=None, secret_info=None):
    for e in store.list_entries():
        if e["id"] == target or e["label"] == target:
            if notes is None:
                notes = e.get("notes", "")
            if secret_info is None:
                secret_info = e.get("secret_info", "")
            store.update(e["id"], label, secret, notes, secret_info)
            print(f"已更新: {e['label']} -> {label}")
            return
    print(f"未找到: {target}", file=sys.stderr)
    sys.exit(1)


def cmd_delete(store, target: str):
    for e in store.list_entries():
        if e["id"] == target or e["label"] == target:
            store.delete(e["id"])
            print(f"已删除: {e['label']}")
            return
    print(f"未找到: {target}", file=sys.stderr)
    sys.exit(1)


def main():
    parse = argparse.ArgumentParser(description="TOTP SQLite 管理工具 (add/list/update/delete)")
    parse.add_argument("--db", type=Path, required=True, help="totp 数据库 sqlite 文件(不存在则新建)")
    parse.add_argument("--password", type=str, help="主密码(不指定则交互式输入)")

    sub = parse.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="列出所有条目")

    p_add = sub.add_parser("add", help="添加条目")
    p_add.add_argument("label")
    p_add.add_argument("secret")
    p_add.add_argument("--notes", default="", help="说明文本")
    p_add.add_argument("--secret-info", default="", help="附加信息")

    p_update = sub.add_parser("update", help="按 id 或 label 更新条目")
    p_update.add_argument("target")
    p_update.add_argument("label")
    p_update.add_argument("secret")
    p_update.add_argument("--notes", default=None, help="说明文本(不指定则保持不变)")
    p_update.add_argument("--secret-info", default=None, help="附加信息(不指定则保持不变)")

    p_delete = sub.add_parser("delete", help="按 id 或 label 删除条目")
    p_delete.add_argument("target")

    args = parse.parse_args()

    password = args.password
    if password is None:
        password = getpass_pw()

    try:
        store = open_store(args.db, password)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

    if args.command == "list":
        cmd_list(store)
    elif args.command == "add":
        cmd_add(store, args.label, args.secret, args.notes, args.secret_info)
    elif args.command == "update":
        cmd_update(store, args.target, args.label, args.secret, args.notes, args.secret_info)
    elif args.command == "delete":
        cmd_delete(store, args.target)


if __name__ == "__main__":
    main()
