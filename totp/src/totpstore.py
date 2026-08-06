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
    TOTP 密钥存储。`label`/`description` 明文列（用于 SQL 搜索），
    `secret`/`secret_info` 为 AES-GCM 加密列，搜索时只解密命中条目。
    """

    CHECK_VALUE = b"totp-check"
    ENTRIES_TABLE = "totp_entries"
    META_PREFIX = "totp"
    ENCRYPTED_COLUMNS = ("secret", "secret_info")

    def _init_db(self):
        self._conn.execute(
            f"""CREATE TABLE IF NOT EXISTS {self.ENTRIES_TABLE}(
                id          TEXT PRIMARY KEY,
                label       TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                secret      BLOB NOT NULL,
                secret_info BLOB NOT NULL DEFAULT '',
                created_at  INTEGER NOT NULL,
                updated_at  INTEGER NOT NULL
            )"""
        )

    def _migrate_if_needed(self):
        """把旧版 `data` blob（{label, secret, notes, secret_info}）拆分到新列。
        调用时需已持有 self._lock（由 unlock 调用）。"""
        if not self._has_column("data"):
            return
        for col, ddl in (
            ("label", "TEXT NOT NULL DEFAULT ''"),
            ("description", "TEXT NOT NULL DEFAULT ''"),
            ("secret", "BLOB NOT NULL DEFAULT ''"),
            ("secret_info", "BLOB NOT NULL DEFAULT ''"),
        ):
            if not self._has_column(col):
                self._conn.execute(f"ALTER TABLE {self.ENTRIES_TABLE} ADD COLUMN {col} {ddl}")

        rows = self._conn.execute(
            f"SELECT id, data FROM {self.ENTRIES_TABLE}"
        ).fetchall()
        for eid, data in rows:
            plain = json.loads(self._aesgcm_decrypt(self._kek, data))
            secret_info = plain.get("secret_info", "") or ""
            self._conn.execute(
                f"UPDATE {self.ENTRIES_TABLE} SET label=?, description=?, secret=?, secret_info=? WHERE id=?",
                (
                    plain.get("label", ""),
                    plain.get("notes", "") or plain.get("description", ""),
                    self._aesgcm_encrypt(self._kek, plain.get("secret", "").encode("utf-8")),
                    self._aesgcm_encrypt(self._kek, secret_info.encode("utf-8")) if secret_info else b"",
                    eid,
                ),
            )

        self._conn.execute(f"ALTER TABLE {self.ENTRIES_TABLE} DROP COLUMN data")
        self._conn.commit()

    def _decrypt_row(self, row) -> dict:
        eid, label, description, secret, secret_info, created, updated = row
        entry = {
            "id": eid,
            "label": label,
            "description": description,
            "secret": self._aesgcm_decrypt(self._kek, secret).decode("utf-8"),
            "secret_info": self._aesgcm_decrypt(self._kek, secret_info).decode("utf-8") if secret_info else "",
            "created_at": created,
            "updated_at": updated,
        }
        return entry

    def _select_sql(self, extra: str = "") -> str:
        return (
            f"SELECT id, label, description, secret, secret_info, created_at, updated_at "
            f"FROM {self.ENTRIES_TABLE} {extra}"
        )

    def list_entries(self) -> list[dict]:
        with self._lock:
            if self._kek is None:
                return []
            rows = self._conn.execute(self._select_sql("ORDER BY created_at")).fetchall()
            return [self._decrypt_row(r) for r in rows]

    def search(self, keyword: str) -> list[dict]:
        with self._lock:
            if self._kek is None:
                return []
            like = f"%{keyword}%"
            rows = self._conn.execute(
                self._select_sql("WHERE label LIKE ? OR description LIKE ? ORDER BY created_at"),
                (like, like),
            ).fetchall()
            return [self._decrypt_row(r) for r in rows]

    def get_entry(self, eid: str) -> dict | None:
        with self._lock:
            if self._kek is None:
                raise ValueError("需要登录")
            row = self._conn.execute(
                self._select_sql("WHERE id=?"), (eid,)
            ).fetchone()
            if row is None:
                return None
            return self._decrypt_row(row)

    def add(self, label: str, secret: str, description: str = "", secret_info: str = "") -> str:
        with self._lock:
            if self._kek is None:
                raise ValueError("需要登录")

            eid = uuid.uuid4().hex
            now = int(time.time())
            self._conn.execute(
                f"INSERT INTO {self.ENTRIES_TABLE}(id, label, description, secret, secret_info, created_at, updated_at) "
                "VALUES(?, ?, ?, ?, ?, ?, ?)",
                (
                    eid,
                    label,
                    description,
                    self._aesgcm_encrypt(self._kek, secret.encode("utf-8")),
                    self._aesgcm_encrypt(self._kek, secret_info.encode("utf-8")) if secret_info else b"",
                    now,
                    now,
                ),
            )
            self._conn.commit()
            return eid

    def update(self, eid: str, label: str, secret: str, description: str = "", secret_info: str = "") -> bool:
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
                f"UPDATE {self.ENTRIES_TABLE} SET label=?, description=?, secret=?, secret_info=?, updated_at=? WHERE id=?",
                (
                    label,
                    description,
                    self._aesgcm_encrypt(self._kek, secret.encode("utf-8")),
                    self._aesgcm_encrypt(self._kek, secret_info.encode("utf-8")) if secret_info else b"",
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


def open_store(db_path: Path, password: str) -> TOTPStore:
    store = TOTPStore(db_path)
    if not store.is_initialized():
        store.initialize(password)
    elif not store.unlock(password):
        raise ValueError("密码错误")
    return store
