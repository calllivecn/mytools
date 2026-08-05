#!/usr/bin/env python3
# coding=utf-8
# date 2026-08-05
# author calllivecn <calllivecn@outlook.com>


import argparse
import sys

from pathlib import Path

from totpstore import (
    TOTPStore,
)

from vaultlib import (
    VaultStore,
)


def getpass_pw(prompt: str = "主密码: ") -> str:
    import getpass
    return getpass.getpass(prompt)


def open_store(store_cls, db_path: Path, password: str):
    store = store_cls(db_path)
    if not store.is_initialized():
        store.initialize(password)
    elif not store.unlock(password):
        raise ValueError("密码错误")
    return store


def change_password(store, old_password: str, new_password=None):
    if new_password is None:
        pw1 = getpass_pw("新主密码: ")
        pw2 = getpass_pw("再次输入新主密码: ")
        if pw1 != pw2:
            print("两次输入的新密码不一致", file=sys.stderr)
            sys.exit(1)
        new_password = pw1

    if not new_password:
        print("新密码不能为空", file=sys.stderr)
        sys.exit(1)

    if store.change_password(old_password, new_password):
        print("主密码已修改")
    else:
        print("旧密码错误", file=sys.stderr)
        sys.exit(1)


# ---------- TOTP ----------

def cmd_totp_list(store):
    for e in store.list_entries():
        notes = e.get("notes") or ""
        print(f"{e['id']}  {e['label']}  {notes}")


def cmd_totp_add(store, label: str, secret: str, notes: str = "", secret_info: str = ""):
    eid = store.add(label, secret, notes, secret_info)
    print(f"已添加: {eid}  {label}")


def cmd_totp_update(store, target: str, label: str, secret: str, notes=None, secret_info=None):
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


def cmd_totp_delete(store, target: str):
    for e in store.list_entries():
        if e["id"] == target or e["label"] == target:
            store.delete(e["id"])
            print(f"已删除: {e['label']}")
            return
    print(f"未找到: {target}", file=sys.stderr)
    sys.exit(1)


# ---------- Vault ----------

def cmd_vault_list(store):
    for e in store.list_entries():
        print(f"{e['id']}  {e.get('site', '')}  {e.get('username', '')}  {e.get('category', '')}")


def cmd_vault_add(store, site: str, username: str = "", password: str = "", notes: str = "", category: str = ""):
    entry = {
        "site": site,
        "username": username,
        "password": password,
        "notes": notes,
        "category": category,
    }
    eid = store.add(entry)
    print(f"已添加: {eid}  {site}")


def cmd_vault_update(store, target: str, site: str, username=None, password=None, notes=None, category=None):
    for e in store.list_entries():
        if e["id"] == target or e.get("site") == target:
            entry = {
                "site": site,
                "username": e.get("username", "") if username is None else username,
                "password": e.get("password", "") if password is None else password,
                "notes": e.get("notes", "") if notes is None else notes,
                "category": e.get("category", "") if category is None else category,
            }
            store.update(e["id"], entry)
            print(f"已更新: {e.get('site')} -> {site}")
            return
    print(f"未找到: {target}", file=sys.stderr)
    sys.exit(1)


def cmd_vault_delete(store, target: str):
    for e in store.list_entries():
        if e["id"] == target or e.get("site") == target:
            store.delete(e["id"])
            print(f"已删除: {e.get('site')}")
            return
    print(f"未找到: {target}", file=sys.stderr)
    sys.exit(1)


def main():
    parse = argparse.ArgumentParser(description="管理工具: totp/vault 的 add/list/update/delete/password")
    parse.add_argument("--db", type=Path, required=True, help="sqlite 数据库文件(不存在则新建, TOTP 与密码库共用)")
    parse.add_argument("--master-password", type=str, help="当前组的主密码(不指定则交互式输入)")

    sub = parse.add_subparsers(dest="group", required=True)

    # ---- TOTP 组 ----
    p_totp = sub.add_parser("totp", help="TOTP 管理")
    totp_sub = p_totp.add_subparsers(dest="cmd", required=True)
    totp_sub.add_parser("list", help="列出所有条目")

    p_add = totp_sub.add_parser("add", help="添加条目")
    p_add.add_argument("label")
    p_add.add_argument("secret")
    p_add.add_argument("--notes", default="", help="说明文本")
    p_add.add_argument("--secret-info", default="", help="附加信息")

    p_upd = totp_sub.add_parser("update", help="按 id 或 label 更新条目")
    p_upd.add_argument("target")
    p_upd.add_argument("label")
    p_upd.add_argument("secret")
    p_upd.add_argument("--notes", default=None, help="说明文本(不指定则保持不变)")
    p_upd.add_argument("--secret-info", default=None, help="附加信息(不指定则保持不变)")

    p_del = totp_sub.add_parser("delete", help="按 id 或 label 删除条目")
    p_del.add_argument("target")

    p_pw = totp_sub.add_parser("password", help="修改 TOTP 主密码")
    p_pw.add_argument("new_password", nargs="?", help="新主密码(不指定则交互式输入两次)")

    # ---- Vault 组 ----
    p_vault = sub.add_parser("vault", help="密码库管理")
    vault_sub = p_vault.add_subparsers(dest="cmd", required=True)
    vault_sub.add_parser("list", help="列出所有条目")

    p_vadd = vault_sub.add_parser("add", help="添加条目")
    p_vadd.add_argument("site")
    p_vadd.add_argument("--username", default="")
    p_vadd.add_argument("--password", default="", help="站点密码")
    p_vadd.add_argument("--notes", default="")
    p_vadd.add_argument("--category", default="")

    p_vupd = vault_sub.add_parser("update", help="按 id 或 site 更新条目")
    p_vupd.add_argument("target")
    p_vupd.add_argument("site")
    p_vupd.add_argument("--username", default=None)
    p_vupd.add_argument("--password", default=None, help="站点密码(不指定则保持不变)")
    p_vupd.add_argument("--notes", default=None)
    p_vupd.add_argument("--category", default=None)

    p_vdel = vault_sub.add_parser("delete", help="按 id 或 site 删除条目")
    p_vdel.add_argument("target")

    p_vpw = vault_sub.add_parser("password", help="修改密码库主密码")
    p_vpw.add_argument("new_password", nargs="?", help="新主密码(不指定则交互式输入两次)")

    args = parse.parse_args()

    master = args.master_password
    if master is None:
        master = getpass_pw()

    try:
        if args.group == "totp":
            store = open_store(TOTPStore, args.db, master)
            if args.cmd == "list":
                cmd_totp_list(store)
            elif args.cmd == "add":
                cmd_totp_add(store, args.label, args.secret, args.notes, args.secret_info)
            elif args.cmd == "update":
                cmd_totp_update(store, args.target, args.label, args.secret, args.notes, args.secret_info)
            elif args.cmd == "delete":
                cmd_totp_delete(store, args.target)
            elif args.cmd == "password":
                change_password(store, master, args.new_password)
        else:
            store = open_store(VaultStore, args.db, master)
            if args.cmd == "list":
                cmd_vault_list(store)
            elif args.cmd == "add":
                cmd_vault_add(store, args.site, args.username, args.password, args.notes, args.category)
            elif args.cmd == "update":
                cmd_vault_update(store, args.target, args.site, args.username, args.password, args.notes, args.category)
            elif args.cmd == "delete":
                cmd_vault_delete(store, args.target)
            elif args.cmd == "password":
                change_password(store, master, args.new_password)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
