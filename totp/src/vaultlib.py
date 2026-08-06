#!/usr/bin/env python3
# coding=utf-8
# date 2026-08-05
# author calllivecn <calllivecn@outlook.com>


import json
import time
import uuid

from flask import (
    Flask,
    Blueprint,
    request,
)

from secretstore import (
    SecretStore,
)


class VaultStore(SecretStore):
    """
    密码库存储。`site`/`username`/`notes`/`category` 明文列（用于 SQL 搜索），
    `password` 为 AES-GCM 加密列，按需解密。
    """

    CHECK_VALUE = b"vault-check"
    ENTRIES_TABLE = "vault_entries"
    META_PREFIX = "vault"
    ENCRYPTED_COLUMNS = ("password",)

    def _init_db(self):
        self._conn.execute(
            f"""CREATE TABLE IF NOT EXISTS {self.ENTRIES_TABLE}(
                id         TEXT PRIMARY KEY,
                site       TEXT NOT NULL,
                username   TEXT NOT NULL DEFAULT '',
                password   BLOB NOT NULL,
                notes      TEXT NOT NULL DEFAULT '',
                category   TEXT NOT NULL DEFAULT '',
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )"""
        )

    def _migrate_if_needed(self):
        """把旧版 `data` blob（{site, username, password, notes, category}）拆分到新列。
        调用时需已持有 self._lock（由 unlock 调用）。"""
        if not self._has_column("data"):
            return
        for col, ddl in (
            ("site", "TEXT NOT NULL DEFAULT ''"),
            ("username", "TEXT NOT NULL DEFAULT ''"),
            ("password", "BLOB NOT NULL DEFAULT ''"),
            ("notes", "TEXT NOT NULL DEFAULT ''"),
            ("category", "TEXT NOT NULL DEFAULT ''"),
        ):
            if not self._has_column(col):
                self._conn.execute(f"ALTER TABLE {self.ENTRIES_TABLE} ADD COLUMN {col} {ddl}")

        rows = self._conn.execute(
            f"SELECT id, data FROM {self.ENTRIES_TABLE}"
        ).fetchall()
        for eid, data in rows:
            plain = json.loads(self._aesgcm_decrypt(self._kek, data))
            password = plain.get("password", "") or ""
            self._conn.execute(
                f"UPDATE {self.ENTRIES_TABLE} SET site=?, username=?, password=?, notes=?, category=? WHERE id=?",
                (
                    plain.get("site", ""),
                    plain.get("username", ""),
                    self._aesgcm_encrypt(self._kek, password.encode("utf-8")),
                    plain.get("notes", ""),
                    plain.get("category", ""),
                    eid,
                ),
            )

        self._conn.execute(f"ALTER TABLE {self.ENTRIES_TABLE} DROP COLUMN data")
        self._conn.commit()

    def _row_meta(self, row) -> dict:
        eid, site, username, password, notes, category, created, updated = row
        return {
            "id": eid,
            "site": site,
            "username": username,
            "notes": notes,
            "category": category,
            "has_password": bool(password),
            "created_at": created,
            "updated_at": updated,
        }

    def _row_full(self, row) -> dict:
        meta = self._row_meta(row)
        meta["password"] = self._aesgcm_decrypt(self._kek, row[3]).decode("utf-8") if row[3] else ""
        return meta

    def _select_sql(self, extra: str = "") -> str:
        return (
            f"SELECT id, site, username, password, notes, category, created_at, updated_at "
            f"FROM {self.ENTRIES_TABLE} {extra}"
        )

    def list_metadata(self) -> list[dict]:
        """返回条目元数据（不含解密后的 password），供列表展示。"""
        with self._lock:
            if self._kek is None:
                return []
            rows = self._conn.execute(self._select_sql("ORDER BY created_at")).fetchall()
            return [self._row_meta(r) for r in rows]

    def search(self, keyword: str) -> list[dict]:
        """在 site/username/notes/category 中搜索，返回命中条目的解密密码。"""
        with self._lock:
            if self._kek is None:
                return []
            like = f"%{keyword}%"
            rows = self._conn.execute(
                self._select_sql("WHERE site LIKE ? OR username LIKE ? OR notes LIKE ? OR category LIKE ? ORDER BY created_at"),
                (like, like, like, like),
            ).fetchall()
            return [self._row_full(r) for r in rows]

    def get_entry(self, eid: str) -> dict | None:
        with self._lock:
            if self._kek is None:
                raise ValueError("需要登录")
            row = self._conn.execute(self._select_sql("WHERE id=?"), (eid,)).fetchone()
            if row is None:
                return None
            return self._row_full(row)

    def add(self, entry: dict) -> str:
        with self._lock:
            if self._kek is None:
                raise ValueError("需要登录")

            eid = uuid.uuid4().hex
            now = int(time.time())
            self._conn.execute(
                f"INSERT INTO {self.ENTRIES_TABLE}(id, site, username, password, notes, category, created_at, updated_at) "
                "VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    eid,
                    entry.get("site", ""),
                    entry.get("username", ""),
                    self._aesgcm_encrypt(self._kek, entry.get("password", "").encode("utf-8")),
                    entry.get("notes", ""),
                    entry.get("category", ""),
                    now,
                    now,
                ),
            )
            self._conn.commit()
            return eid

    def update(self, eid: str, entry: dict) -> bool:
        with self._lock:
            if self._kek is None:
                raise ValueError("需要登录")

            row = self._conn.execute(
                f"SELECT 1 FROM {self.ENTRIES_TABLE} WHERE id=?", (eid,)
            ).fetchone()
            if row is None:
                return False

            now = int(time.time())
            self._conn.execute(
                f"UPDATE {self.ENTRIES_TABLE} SET site=?, username=?, password=?, notes=?, category=?, updated_at=? WHERE id=?",
                (
                    entry.get("site", ""),
                    entry.get("username", ""),
                    self._aesgcm_encrypt(self._kek, entry.get("password", "").encode("utf-8")),
                    entry.get("notes", ""),
                    entry.get("category", ""),
                    now,
                    eid,
                ),
            )
            self._conn.commit()
            return True

    def delete(self, eid: str) -> bool:
        with self._lock:
            if self._kek is None:
                raise ValueError("需要登录")

            cur = self._conn.execute(f"DELETE FROM {self.ENTRIES_TABLE} WHERE id=?", (eid,))
            self._conn.commit()
            return cur.rowcount > 0


def _entry_from_js(js: dict) -> dict:
    return {
        "site": js.get("site", ""),
        "username": js.get("username", ""),
        "password": js.get("password", ""),
        "notes": js.get("notes", ""),
        "category": js.get("category", ""),
    }


def vault_main(app: Flask, store: VaultStore, prefix: str):
    bp = Blueprint("vault", app.name, url_prefix=prefix + "vault")

    @bp.get("/status")
    def status():
        return {
            "code": 0,
            "unlocked": store.is_unlocked(),
            "initialized": store.is_initialized(),
        }

    @bp.post("/init")
    def init():
        js = request.get_json(silent=True) or {}
        pw = js.get("password", "")
        if not pw:
            return {"code": -1, "msg": "密码不能为空"}
        if not store.initialize(pw):
            return {"code": -1, "msg": "已初始化，请直接解锁"}
        return {"code": 0, "msg": "主密码已创建"}

    @bp.post("/login")
    def login():
        js = request.get_json(silent=True) or {}
        pw = js.get("password", "")

        if not store.is_initialized():
            return {"code": -1, "msg": "首次使用请先设置主密码"}

        if store.unlock(pw):
            return {"code": 0, "msg": "解锁成功"}
        return {"code": -1, "msg": "密码错误"}

    @bp.post("/logout")
    def logout():
        store.lock()
        return {"code": 0, "msg": "已锁定"}

    @bp.get("/list")
    def get_list():
        if not store.is_unlocked():
            return {"code": -1, "msg": "需要登录", "data": []}
        return {"code": 0, "msg": "查询结果", "data": store.list_metadata()}

    @bp.get("/search")
    def get_search():
        if not store.is_unlocked():
            return {"code": -1, "msg": "需要登录", "data": []}
        q = (request.args.get("q") or "").strip()
        if not q:
            return {"code": -1, "msg": "缺少搜索关键字", "data": []}
        return {"code": 0, "msg": "查询结果", "data": store.search(q)}

    @bp.get("/get")
    def get_entry():
        if not store.is_unlocked():
            return {"code": -1, "msg": "需要登录"}
        eid = request.args.get("id")
        entry = store.get_entry(eid)
        if entry is None:
            return {"code": -1, "msg": "条目不存在"}
        return {"code": 0, "msg": "查询结果", "data": entry}

    @bp.post("/add")
    def add():
        if not store.is_unlocked():
            return {"code": -1, "msg": "需要登录"}
        js = request.get_json(silent=True) or {}
        eid = store.add(_entry_from_js(js))
        return {"code": 0, "msg": "添加成功", "data": {"id": eid}}

    @bp.put("/update")
    def update():
        if not store.is_unlocked():
            return {"code": -1, "msg": "需要登录"}
        js = request.get_json(silent=True) or {}
        eid = js.get("id")
        if store.update(eid, _entry_from_js(js)):
            return {"code": 0, "msg": "修改成功"}
        return {"code": -1, "msg": "条目不存在"}

    @bp.post("/delete")
    def delete():
        if not store.is_unlocked():
            return {"code": -1, "msg": "需要登录"}
        js = request.get_json(silent=True) or {}
        eid = js.get("id")
        if store.delete(eid):
            return {"code": 0, "msg": "删除成功"}
        return {"code": -1, "msg": "条目不存在"}

    @bp.post("/password")
    def change_password():
        if not store.is_unlocked():
            return {"code": -1, "msg": "需要登录"}
        js = request.get_json(silent=True) or {}
        old = js.get("old_password", "")
        new = js.get("new_password", "")
        if not new:
            return {"code": -1, "msg": "新密码不能为空"}
        if store.change_password(old, new):
            return {"code": 0, "msg": "修改成功"}
        return {"code": -1, "msg": "旧密码错误"}

    return bp
