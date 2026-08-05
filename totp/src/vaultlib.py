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

    CHECK_VALUE = b"vault-check"

    def _init_db(self):
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS entries(
                id         TEXT PRIMARY KEY,
                data       BLOB NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )"""
        )

    def list_entries(self) -> list[dict]:
        with self._lock:
            if self._kek is None:
                return []

            rows = self._conn.execute(
                "SELECT id, data, created_at, updated_at FROM entries ORDER BY created_at"
            ).fetchall()

            result = []
            for eid, data, created, updated in rows:
                plain = json.loads(self._aesgcm_decrypt(self._kek, data))
                entry = {"id": eid, "created_at": created, "updated_at": updated}
                entry.update(plain)
                result.append(entry)
            return result

    def add(self, entry: dict) -> str:
        with self._lock:
            if self._kek is None:
                raise ValueError("需要登录")

            eid = uuid.uuid4().hex
            now = int(time.time())
            payload = json.dumps(entry, ensure_ascii=False).encode("utf-8")
            blob = self._aesgcm_encrypt(self._kek, payload)
            self._conn.execute(
                "INSERT INTO entries(id, data, created_at, updated_at) VALUES(?, ?, ?, ?)",
                (eid, blob, now, now),
            )
            self._conn.commit()
            return eid

    def update(self, eid: str, entry: dict) -> bool:
        with self._lock:
            if self._kek is None:
                raise ValueError("需要登录")

            row = self._conn.execute("SELECT 1 FROM entries WHERE id=?", (eid,)).fetchone()
            if row is None:
                return False

            now = int(time.time())
            payload = json.dumps(entry, ensure_ascii=False).encode("utf-8")
            blob = self._aesgcm_encrypt(self._kek, payload)
            self._conn.execute("UPDATE entries SET data=?, updated_at=? WHERE id=?", (blob, now, eid))
            self._conn.commit()
            return True

    def delete(self, eid: str) -> bool:
        with self._lock:
            if self._kek is None:
                raise ValueError("需要登录")

            cur = self._conn.execute("DELETE FROM entries WHERE id=?", (eid,))
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
        return {"code": 0, "unlocked": store.is_unlocked()}

    @bp.post("/login")
    def login():
        js = request.get_json(silent=True) or {}
        pw = js.get("password", "")
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
        return {"code": 0, "msg": "查询结果", "data": store.list_entries()}

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
