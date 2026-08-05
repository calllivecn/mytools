# AGENTS.md

本仓库是 Python 和 Bash 工具的个人集合。主要维护的子项目是 `totp/`。

## totp/ — TOTP Web 服务

一个基于 Flask + uvicorn 的 Web 服务，在浏览器中提供 TOTP 码，设计用于在 podman 容器中配合 nginx 运行。

### 架构

- `src/secretstore.py` — 加密 SQLite 存储基类 `SecretStore`（TOTP 与密码库共用）：主密码 Argon2id 派生 KEK（内存驻留，超时自动锁定）、AES-GCM 整体加密条目、`meta` 表存 salt/校验值。
- `src/totpv3.py` — Flask 应用工厂 (`create_app()`)，Blueprint 支持可配置的 URL 前缀；TOTP 配置解密的密钥在 24 小时后自动过期。
- `src/totplib.py` — 独立的 TOTP 实现（RFC 6238，HMAC-SHA1），也可作为 CLI 工具使用。
- `src/totpstore.py` — TOTP 密钥存储：SQLite + 与密码库相同的加密方式（`TOTPStore` 继承 `SecretStore`），`--config` 指向该数据库文件。
- `src/vaultlib.py` — 密码库（Vault）：SQLite 存储 + 独立主密码（`VaultStore` 继承 `SecretStore`），含 `/vault` Blueprint。仅在 `create_app()` 传入 `vault` 参数（入口点 `--vault`）时启用。
- `src/totp-manage.py` — TOTP 条目管理 CLI（`add/list/update/delete`）。Web 端 TOTP 视图也提供条目的增删改查。
- `src/flask-run.py` — 使用 Flask 内置开发服务器的入口点。
- `src/uvicorn-run.py` — 生产环境入口点，使用 uvicorn（Flask 通过 `asgiref.wsgi.WsgiToAsgi` 包装）。
- `src/static/` / `src/templates/` — 前端资源（JS 模块，单个 HTML 页面，Tab 切换 TOTP/密码库）。
- 默认端口：`12201`，监听 `[::]`。

前端 URL 拼接：`index.js`/`vault.js` 从 `<base>` 元素读取前缀并传绝对路径给 `request.js`（不依赖其全局 `baseURL`）。Vault API 前缀为 `{prefix}vault`。

### 配置文件

- `--config` 是 TOTP 的 **SQLite 数据库文件**（不存在则新建），不再是加密 JSON。
- TOTP 与密码库都在进程内用 `cryptography` 加解密（AES-GCM + Argon2id），**不依赖 `crypto.py`**。

### 构建（容器）

```bash
cd totp
./build.sh
```

`build.sh` 运行 `podman build`。容器镜像不再安装 `crypto.py`。

### 依赖文件

pip 的依赖文件为 `requirements.txt`。`Dockerfile` 和源代码都引用这个文件名。

### 运行（本地开发）

使用 Flask CLI 入口点时需要两个环境变量：

```
TOTP_CONFIG=/path/to/totp.db TOTP_PREFIX=/ flask --app totpv3:flask_run run --reload --debug -p 12201
# 可选：TOTP_VAULT=/path/to/vault.db 启用密码库
```

或直接使用 CLI 入口点：

```bash
python src/uvicorn-run.py --config /path/to/totp.db --prefix /totp [--vault /path/to/vault.db] [--addr 0.0.0.0 --port 12201]
python src/flask-run.py   --config /path/to/totp.db --prefix /totp [--vault /path/to/vault.db] [--addr 0.0.0.0 --port 12201]
```

- `--config` 为 TOTP SQLite 数据库（不存在则新建），条目可在 Web 端或 `totp-manage.py` 管理。
- `--vault` 可选：指定密码库 SQLite 文件；省略则密码库功能禁用（前端隐藏「密码库」Tab）。
- 密码库设计文档：`docs/vault-design.md`（含未来多端同步方案）。

### 运行（容器）

```bash
podman run -d --name totp -p 12201:12201 \
  -v /path/to/totp.db:/data/totp.db \
  localhost/totp:latest --prefix /totp --config /data/totp.db
```

### 约定

- `--prefix` 必须以 `/` 结尾（运行时会强制执行）。
- 使用 `podman`，而非 Docker。
- 没有测试套件或 CI。
