#!/usr/bin/env python3
# coding=utf-8
# date 2026-08-05
# author calllivecn <calllivecn@outlook.com>


import json
import time
import uuid

from pathlib import Path

from secretstore import (
    SecretStore,
)


class TOTPStore(SecretStore):
    """
    TOTP 密钥存储，与密码库共用相同的加密方式（AES-GCM + Argon2id KEK）。
    每条目存 {label, secret}，整体加密后放入 entries.data。
    """

    CHECK_VALUE = b"totp-check"
    ENTRIES_TABLE = "totp_entries"
    META_PREFIX = "totp"

    def _init_db(self):
        self._conn.execute(
            f"""CREATE TABLE IF NOT EXISTS {self.ENTRIES_TABLE}(
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
                f"SELECT id, data, created_at, updated_at FROM {self.ENTRIES_TABLE} ORDER BY created_at"
            ).fetchall()

            result = []
            for eid, data, created, updated in rows:
                plain = json.loads(self._aesgcm_decrypt(self._kek, data))
                entry = {"id": eid, "created_at": created, "updated_at": updated}
                entry.update(plain)
                result.append(entry)
            return result

    def add(self, label: str, secret: str, notes: str = "", secret_info: str = "") -> str:
        with self._lock:
            if self._kek is None:
                raise ValueError("需要登录")

            eid = uuid.uuid4().hex
            now = int(time.time())
            payload = json.dumps(
                {"label": label, "secret": secret, "notes": notes, "secret_info": secret_info},
                ensure_ascii=False,
            ).encode("utf-8")
            blob = self._aesgcm_encrypt(self._kek, payload)
            self._conn.execute(
                f"INSERT INTO {self.ENTRIES_TABLE}(id, data, created_at, updated_at) VALUES(?, ?, ?, ?)",
                (eid, blob, now, now),
            )
            self._conn.commit()
            return eid

    def update(self, eid: str, label: str, secret: str, notes: str = "", secret_info: str = "") -> bool:
        with self._lock:
            if self._kek is None:
                raise ValueError("需要登录")

            row = self._conn.execute(f"SELECT 1 FROM {self.ENTRIES_TABLE} WHERE id=?", (eid,)).fetchone()
            if row is None:
                return False

            now = int(time.time())
            payload = json.dumps(
                {"label": label, "secret": secret, "notes": notes, "secret_info": secret_info},
                ensure_ascii=False,
            ).encode("utf-8")
            blob = self._aesgcm_encrypt(self._kek, payload)
            self._conn.execute(f"UPDATE {self.ENTRIES_TABLE} SET data=?, updated_at=? WHERE id=?", (blob, now, eid))
            self._conn.commit()
            return True

    def get_entry(self, eid: str) -> dict | None:
        with self._lock:
            if self._kek is None:
                raise ValueError("需要登录")

            row = self._conn.execute(
                f"SELECT id, data, created_at, updated_at FROM {self.ENTRIES_TABLE} WHERE id=?", (eid,)
            ).fetchone()
            if row is None:
                return None

            eid_, data, created, updated = row
            plain = json.loads(self._aesgcm_decrypt(self._kek, data))
            entry = {"id": eid_, "created_at": created, "updated_at": updated}
            entry.update(plain)
            return entry

    def delete(self, eid: str) -> bool:
        with self._lock:
            if self._kek is None:
                raise ValueError("需要登录")

            cur = self._conn.execute(f"DELETE FROM {self.ENTRIES_TABLE} WHERE id=?", (eid,))
            self._conn.commit()
            return cur.rowcount > 0


def open_store(db_path: Path, password: str) -> TOTPStore:
    store = TOTPStore(db_path)
    if not store.unlock(password):
        raise ValueError("密码错误")
    return store
