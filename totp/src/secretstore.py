#!/usr/bin/env python3
# coding=utf-8
# date 2026-08-05
# author calllivecn <calllivecn@outlook.com>


import os
import sqlite3
import time

from pathlib import Path
from threading import (
    Thread,
    Lock,
)

from cryptography.hazmat.primitives.ciphers import (
    Cipher,
    algorithms,
    modes,
)
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.exceptions import InvalidTag


SALT_LEN = 16
NONCE_LEN = 12
TAG_LEN = 16
KEK_LEN = 32

ARGON2_PARAMS = {
    "iterations": 13,
    "lanes": 4,
    "memory_cost": 64 * 1024,
}


class SecretStore:
    """
    基于主密码的加密 SQLite 存储基类（TOTP 与密码库共用）。

    - meta 表：保存 Argon2id salt 与校验值，用于解锁验证主密码。
    - entries 表：由子类定义；其中 `ENCRYPTED_COLUMNS` 指定的列单独 AES-GCM 加密存入 BLOB，
      其余列（如 label/description）为明文，便于服务端 SQL 搜索。
    - 解锁后只在内存保留 KEK（32B），条目按需解密，超时自动锁定。
    """

    CHECK_VALUE = b"secret-store-check"
    ENTRIES_TABLE = "entries"
    META_PREFIX = ""
    ENCRYPTED_COLUMNS: tuple[str, ...] = ()

    def __init__(self, db_path: Path, time_: float = 30 * 60):
        self.db_path = Path(db_path)
        self.time_ = time_

        self._lock = Lock()
        self._kek: bytes | None = None

        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v BLOB)")
        self._init_db()
        self._conn.commit()

        self.th = Thread(target=self._auto_lock, daemon=True)
        self.th.start()

    def _init_db(self):
        raise NotImplementedError

    def _has_column(self, column: str) -> bool:
        cols = [r[1] for r in self._conn.execute(
            f"PRAGMA table_info({self.ENTRIES_TABLE})"
        ).fetchall()]
        return column in cols

    def _migrate_if_needed(self):
        """
        子类可覆写：解锁后把旧版 `data` blob 迁移到新列。
        默认无操作。
        """
        return

    def _meta_key(self, name: str) -> str:
        if self.META_PREFIX:
            return f"{self.META_PREFIX}:{name}"
        return name

    def _auto_lock(self):
        while True:
            time.sleep(self.time_)
            with self._lock:
                self._kek = None

    @staticmethod
    def _derive_kek(password: str, salt: bytes) -> bytes:
        kdf = Argon2id(salt=salt, length=KEK_LEN, **ARGON2_PARAMS)
        return kdf.derive(password.encode("utf-8"))

    @staticmethod
    def _aesgcm_encrypt(key: bytes, plaintext: bytes) -> bytes:
        nonce = os.urandom(NONCE_LEN)
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
        encryptor = cipher.encryptor()
        ct = encryptor.update(plaintext) + encryptor.finalize()
        return nonce + ct + encryptor.tag

    @staticmethod
    def _aesgcm_decrypt(key: bytes, blob: bytes) -> bytes:
        nonce, ct, tag = blob[:NONCE_LEN], blob[NONCE_LEN:-TAG_LEN], blob[-TAG_LEN:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
        decryptor = cipher.decryptor()
        return decryptor.update(ct) + decryptor.finalize()

    def _verify(self, password: str) -> bytes | None:
        row = self._conn.execute("SELECT v FROM meta WHERE k=?", (self._meta_key("salt"),)).fetchone()
        if row is None:
            return None

        kek = self._derive_kek(password, row[0])
        check = self._conn.execute("SELECT v FROM meta WHERE k=?", (self._meta_key("check"),)).fetchone()
        if check is None:
            return None

        try:
            self._aesgcm_decrypt(kek, check[0])
        except InvalidTag:
            return None

        return kek

    def _init_vault(self, password: str):
        salt = os.urandom(SALT_LEN)
        kek = self._derive_kek(password, salt)
        check = self._aesgcm_encrypt(kek, self.CHECK_VALUE)
        self._conn.execute("INSERT INTO meta(k, v) VALUES(?, ?)", (self._meta_key("salt"), salt))
        self._conn.execute("INSERT INTO meta(k, v) VALUES(?, ?)", (self._meta_key("check"), check))
        self._conn.commit()
        self._kek = kek

    def is_initialized(self) -> bool:
        return self._conn.execute(
            "SELECT 1 FROM meta WHERE k=?", (self._meta_key("salt"),)
        ).fetchone() is not None

    def initialize(self, password: str) -> bool:
        with self._lock:
            if self.is_initialized():
                return False
            self._init_vault(password)
            return True

    def unlock(self, password: str) -> bool:
        with self._lock:
            if not self.is_initialized():
                return False

            kek = self._verify(password)
            if kek is not None:
                self._kek = kek
                self._migrate_if_needed()
                return True
            return False

    def is_unlocked(self) -> bool:
        return self._kek is not None

    def lock(self):
        with self._lock:
            self._kek = None

    def change_password(self, old_password: str, new_password: str) -> bool:
        with self._lock:
            kek = self._verify(old_password)
            if kek is None:
                return False

            new_salt = os.urandom(SALT_LEN)
            new_kek = self._derive_kek(new_password, new_salt)

            cols = self.ENCRYPTED_COLUMNS
            if cols:
                cols_sql = ", ".join(cols)
                rows = self._conn.execute(
                    f"SELECT id, {cols_sql} FROM {self.ENTRIES_TABLE}"
                ).fetchall()
                for row in rows:
                    eid = row[0]
                    new_vals = [self._aesgcm_encrypt(new_kek, self._aesgcm_decrypt(kek, c)) for c in row[1:]]
                    sets = ", ".join(f"{c}=?" for c in cols)
                    self._conn.execute(
                        f"UPDATE {self.ENTRIES_TABLE} SET {sets} WHERE id=?",
                        (*new_vals, eid),
                    )

            check = self._aesgcm_encrypt(new_kek, self.CHECK_VALUE)
            self._conn.execute("INSERT OR REPLACE INTO meta(k, v) VALUES(?, ?)", (self._meta_key("salt"), new_salt))
            self._conn.execute("INSERT OR REPLACE INTO meta(k, v) VALUES(?, ?)", (self._meta_key("check"), check))
            self._conn.commit()
            self._kek = new_kek
            return True
