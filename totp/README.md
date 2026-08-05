# 尝试开始使用 容器 跑小服务

## 需要运行在nginx 后面，没有加密的。

- 默认监听[::]:12201
- 如果在 nginx 中配置了 location /prefix/ {} 路径的， 需要通过 --prefix /prefix 参数指定前缀。
- `--config` 是 TOTP 的 SQLite 数据库文件（不存在则自动新建，首次登录输入的密码即主密码）。
  TOTP 与密码库都使用 AES-GCM + Argon2id 派生 KEK，在进程内加解密，不再依赖 `crypto.py`。

```shell
podman run -d --name totp -p 12201:12201 \
  -v /path/to/totp.db:/data/totp.db \
  localhost/totp:latest --prefix /totp --config /data/totp.db
```

## TOTP 条目管理

TOTP 数据存在 SQLite 中。Web 页面解锁后可直接新增/编辑/删除条目，也可用命令行工具管理：

```shell
# 新建数据库并添加条目
python src/totp-manage.py --db /path/to/totp.db add "example.com" "JBSWY3DPEHPK3PXP"

# 列出 / 更新 / 删除（可按 id 或 label 定位）
python src/totp-manage.py --db /path/to/totp.db list
python src/totp-manage.py --db /path/to/totp.db update "example.com" "example.com" "NEWSECRET"
python src/totp-manage.py --db /path/to/totp.db delete "example.com"
```

## 在浏览器中使用时

- 解锁后，TOTP 视图显示所有条目的实时动态密码（含倒计时），支持搜索、复制、新增/编辑/删除；「密码库」Tab 为密码管理器。
- 两个视图可通过顶部按钮切换，地址栏 `#totp` / `#vault` 对应各自的视图链接。


## 密码库（Vault）

站点内可同时部署一个与 TOTP 无关的密码管理器（SQLite + AES-GCM 加密，独立主密码）。

- 需要给 `--vault <path>` 指定 SQLite 数据库文件（如 `/data/vault.db`），未指定时密码库功能禁用，页面隐藏「密码库」Tab。
- 首次解锁输入的密码即为主密码（初始化），之后每次用同一密码解锁。
- 支持：条目的新增/编辑/删除、搜索、一键复制（15 秒后自动清空剪贴板）、随机密码生成、修改主密码。
- 解锁后密钥仅驻留内存，默认 30 分钟自动锁定。
- 设计细节与未来多端同步方案见 `docs/vault-design.md`。

```shell
podman run -d --name totp -p 12201:12201 \
  -v /path/to/totp.db:/data/totp.db \
  -v /path/to/vault.db:/data/vault.db \
  localhost/totp:latest --prefix /totp --config /data/totp.db --vault /data/vault.db
```


## 添加上3种启动方式

- flask cli 

```shell
# 需要环境变量TOTP_CONFIG TOTP_PREFIX 传参
flask --app totpv3:flask_run run --reload --debug -p 12201
```

- flask-run.py --help 

- uvicorn.py --help

