# 密码库（Vault）设计文档

> 记录 2026-08 新增「密码管理」功能的规划过程与架构设计。
> 该功能与 TOTP 无关，只是部署在同一个站点内。

## 背景与目标

- 在现有 TOTP Web 服务（`totp/`）中新增一个独立的密码管理器。
- 与 TOTP 功能无关：数据、密码、解锁状态全部独立。
- 目标：完整 CRUD + 搜索 + 客户端密码生成器。
- 多端同步为**未来扩展**，本期只记录设计，不实现。

## 关键决策（已确认）

| 议题 | 决策 |
|---|---|
| 数据存储 | SQLite（与 TOTP 共用同一个数据库文件，各自独立表与主密码），不用加密 JSON 文件 |
| 加密方式 | 字段整体 AES-GCM 加密后存入 SQLite；主密码用 Argon2id 派生 KEK |
| 解锁密码 | 与 TOTP 主密码**完全独立** |
| 前端组织 | 单页多视图（Tab 切换：TOTP / 密码库） |
| 功能范围 | 完整 CRUD + 搜索 + 密码生成器 |
| 多端同步 | 本期不实现，仅在文档中记录未来方案 |

## 架构总览

```
totp/
├── src/
│   ├── secretstore.py         # 加密 SQLite 存储基类 SecretStore（TOTP 与密码库共用）
│   ├── vaultlib.py            # VaultStore 继承 SecretStore + /vault Blueprint
│   ├── totpstore.py           # TOTPStore 继承 SecretStore（相同加密方案）
│   ├── totpv3.py              # create_app()，注册 TOTP 与 /vault 两个 Blueprint
│   ├── manager.py             # 命令行管理工具（totp/vault 两组，各含 add/list/update/delete/password）
│   ├── uvicorn-run.py / flask-run.py  # 入口点，--db 指定共用数据库
│   ├── templates/index.html   # Tab 导航（TOTP / 密码库）
│   └── static/assets/         # index.js / vault.js / request.js
└── docs/vault-design.md      # 本文档
```

- `requirements.txt` 无需改动（`cryptography` 已在依赖中）。
- `Dockerfile` / `build.sh` 不安装（运行时无子进程依赖）。

## 存储与加密（`VaultStore` / `TOTPStore`）

### 数据库

- 唯一数据库由 `--db` 指定（不存在则新建）。TOTP 与密码库共用同一文件，但表与 meta 键按 `META_PREFIX` / `ENTRIES_TABLE` 命名空间隔离：
  - TOTP：表 `totp_entries`，meta 键 `totp:salt` / `totp:check`
  - Vault：表 `vault_entries`，meta 键 `vault:salt` / `vault:check`

### Schema

```sql
CREATE TABLE meta(k TEXT PRIMARY KEY, v BLOB);          -- 各前缀的 argon2id salt / 校验值
CREATE TABLE totp_entries(
  id         TEXT PRIMARY KEY,                          -- uuid4 hex
  data       BLOB NOT NULL,                             -- AES-GCM 加密后的条目 JSON
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE TABLE vault_entries( ... 同上 ... );
```

- `meta.<prefix>:salt`：Argon2id 盐（16B），解锁时派生 KEK。
- `meta.<prefix>:check`：AES-GCM 加密的固定字符串，用于校验密码是否正确（GCM tag 校验失败即密码错误）。
- `entries.data`：`nonce(12) + ciphertext + tag(16)`，明文为 JSON（TOTP：`{"label","secret","notes","secret_info"}`；Vault：`{"site","username","password","notes","category"}`）。
- 元数据列（id、时间戳）明文存储，不含敏感信息。

### 密钥派生与加解密

- 与 `crypto.py` 的 AES-GCM (v0x0003) 使用相同 Argon2id 参数（`iterations=13, lanes=4, memory_cost=64MiB`），通过 `cryptography` 库在进程内实现（不对每个字段起子进程）。
- 解锁后**只在内存保留 KEK（32B）**，不缓存明文，条目按请求按需解密。
- 自动锁定时长：TOTP 默认 24h（`create_app` 传入），Vault 默认 30 分钟（常量可调），后台线程到期清空 KEK。

### 首次使用

- 数据库某前缀不存在 salt 时视为首次初始化：以当前输入的密码作为主密码，写入该前缀的 salt 与 check。

## 后端 API（Blueprint，前缀 `{prefix}vault`）

| 方法/路径 | 说明 |
|---|---|
| `GET  /status`  | 返回是否已解锁 |
| `POST /login`   | 用独立密码解锁（首次登录即初始化主密码） |
| `POST /logout`  | 锁库（清空内存 KEK） |
| `GET  /list`    | 返回全部解密条目（搜索在前端做） |
| `POST /add`     | 新增条目 |
| `PUT  /update`  | 修改条目（body 带 `id`） |
| `POST /delete`  | 删除条目（用 POST 而非 DELETE，兼容 `request.js` 将 DELETE 参数放入 query 的行为） |
| `POST /password`| 修改主密码（重派生 KEK 并重加密全部条目） |

统一返回 `{"code": 0|-1, "msg": "...", "data": ...}`。

线程安全：`VaultStore` 用 `Lock` 保护解锁/写操作；SQLite 连接 `check_same_thread=False`。

## 前端（单页多视图）

- `index.html`：顶部 Tab（TOTP / 密码库）+ 两个视图容器，各自独立登录表单。
- `index.js`：Tab 路由器 + 原有 TOTP 逻辑（含 `?all=1`）。URL 改为从 `<base>` 取前缀并拼接绝对路径，替换原 `configure({baseURL})` 全局配置方式，使 TOTP 与 Vault 两组 API 可共存。
- `vault.js`（新，复用 `request.js`）：
  - 解锁表单 / 锁定按钮；
  - 条目表格：站点、用户名、密码（默认掩码，可切换显示）、分类、操作（复制/编辑/删除）；
  - 搜索框：客户端过滤（站点/用户名/备注/分类）；
  - 新增/编辑弹窗；
  - 一键复制：写入剪贴板，15 秒后自动清除；
  - 密码生成器：`crypto.getRandomValues`，可配长度（默认 16）与字符集。

## 安全说明

- KEK 仅内存驻留，超时自动锁定；磁盘上无明文密码；主密码不落日志、不入库。
- 密码库与 TOTP 完全隔离：不同文件、不同密码、不同解锁状态。
- 传输层由 nginx 提供 HTTPS（既有部署假设）。

## 共享存储基类（TOTP 复用）

密码库的方案也复用于 TOTP：`SecretStore`（`src/secretstore.py`）提供主密码派生 KEK、AES-GCM 加密、`meta` 表校验、解锁/锁定/超时自动锁定与改主密码；`VaultStore` 与 `TOTPStore` 各自继承并定义自己的 `ENTRIES_TABLE` / `META_PREFIX` 与业务方法。

- TOTP 与密码库共用 `--db` 指定的 SQLite 数据库，条目整体加密；Web 端 TOTP 视图支持实时动态密码与增删改查。
- TOTP 主密码独立（默认 24h 自动锁定），Vault 主密码独立（默认 30min 自动锁定）。
- 不再支持旧版 `crypto.py` 加密的 `totp.a` 文件，TOTP 与密码库均不依赖 `crypto.py`。

## 未来：多端同步（本期不实现）

为使将来能平滑加入同步/合并，当前 schema 已按以下方向预留：

- 条目用 UUID（`id`）标识，已含 `updated_at`。
- 未来需扩展：
  1. 软删除（`deleted` 墓碑 + `deleted_at`），避免删除在合并时复活；
  2. 字段级 `updated_at`（site/username/password/notes/category 各自的时间戳），实现字段级 LWW 合并；
  3. 同步游标 / Lamport 时钟或服务器自增序号，用于增量拉取与全局排序；
  4. 每设备本地加密副本（离线优先，WebCrypto）或服务器权威 + 增量推送两种模式可选。

推荐协议：设备拉取自上次游标以来的变更 → 逐条按字段 LWW 合并 → 推送本地变更 → 服务器为权威源合并写入。合并以解密后的明文为准，因此当前"条目整体加密"不构成障碍。
