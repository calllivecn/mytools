# 尝试开始使用 容器 跑小服务

## 需要运行在nginx 后面(当前没有通讯加密功能)。

- 默认监听[::]:12201
- 如果在 nginx 中配置了 location /prefix/ {} 路径的， 需要通过 --prefix /prefix 参数指定前缀。
- `--db` 是唯一的 SQLite 数据库文件（不存在则自动新建），TOTP 与密码库共用一个数据库（各自独立表与主密码）。
  TOTP 与密码库都使用 AES-GCM + Argon2id 派生 KEK，在进程内加解密。

```shell
podman run -d --name totp -p 12201:12201 \
  -v /path/to/totp.db:/data/totp.db \
  localhost/totp:latest --db /data/totp.db
```

## 条目管理（命令行 `manager.py`）

TOTP 与密码库的数据都在这一个 SQLite 里，统一用 `src/manager.py` 管理（Web 页面也可增删改查 TOTP 与密码库条目）。

TOTP 条目包含：名称、Base32 密钥、说明（可选）、附加信息（可选，如恢复码，与密钥一起加密保存）。

```shell
# ---- TOTP 管理 ----
# 新建数据库并添加条目
python src/manager.py --db /path/to/totp.db totp add "example.com" "JBSWY3DPEHPK3PXP" --notes "我的账号" --secret-info "恢复码 xxx"

# 列出 / 更新 / 删除（可按 id 或 label 定位）
python src/manager.py --db /path/to/totp.db totp list
python src/manager.py --db /path/to/totp.db totp update "example.com" "example.com" "NEWSECRET" --notes "改一下说明"
python src/manager.py --db /path/to/totp.db totp delete "example.com"

# 修改 TOTP 主密码（--master-password 为旧密码；新密码不传则交互式输入两次确认）
python src/manager.py --db /path/to/totp.db --master-password "旧密码" totp password "新密码"

# ---- 密码库（Vault）管理 ----
# 新增条目
python src/manager.py --db /path/to/totp.db vault add "example.com" --username "u" --password "p" --notes "n" --category "c"

# 列出 / 更新 / 删除（可按 id 或 site 定位；不指定的字段保持不变）
python src/manager.py --db /path/to/totp.db vault list
python src/manager.py --db /path/to/totp.db vault update "example.com" "example.com" --password "newp"
python src/manager.py --db /path/to/totp.db vault delete "example.com"

# 修改密码库主密码
python src/manager.py --db /path/to/totp.db --master-password "旧密码" vault password "新密码"
```

## 在浏览器中使用时

- 解锁后，TOTP 视图显示所有条目的实时动态密码（含倒计时），支持搜索、复制、新增/编辑/删除；「密码库」Tab 为密码管理器。
- 两个视图可通过顶部按钮切换，地址栏 `#totp` / `#vault` 对应各自的视图链接。


## 密码库（Vault）

站点内内置一个与 TOTP 无关的密码管理器（与 TOTP 共用同一 SQLite 数据库、独立主密码）。

- 首次解锁输入的密码即为主密码（初始化），之后每次用同一密码解锁。
- 支持：条目的新增/编辑/删除、搜索、一键复制（15 秒后自动清空剪贴板）、随机密码生成、修改主密码。
- 解锁后密钥仅驻留内存，默认 30 分钟自动锁定。
- 设计细节与未来多端同步方案见 `docs/vault-design.md`。


## 添加上3种启动方式

- flask cli 

```shell
# 需要环境变量TOTP_DB TOTP_PREFIX 传参
flask --app totpv3:flask_run run --reload --debug -p 12201
```

- flask-run.py --help 

- uvicorn.py --help

