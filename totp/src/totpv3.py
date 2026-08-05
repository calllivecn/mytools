#!/usr/bin/env python3
# coding=utf-8
# date 2024-08-24 20:09:02
# author calllivecn <calllivecn@outlook.com>


from pathlib import Path

from flask import (
    Flask,
    request,
    render_template,
    Blueprint,
    send_from_directory,
)

from totplib import (
    TOTP,
)

from totpstore import (
    TOTPStore,
)

from vaultlib import (
    VaultStore,
    vault_main,
)


def query_label(conf: list[dict], label: str) -> list:

    result = []
    for info in conf:
        if label in info["label"]:
            result.append(info)

    return result


def totp_main(app: Flask, store: TOTPStore, prefix: str):
    print(f"{prefix=}")

    bp = Blueprint("prefix", app.name, url_prefix=prefix)

    @bp.get("/")
    def index():
        print(f"这是 @bp.get()  {request.path=}")
        return render_template("index.html", base_url=prefix)

    @bp.get('/totpall')
    def get_totp():
        if store.is_unlocked():

            totps = []
            for info in store.list_entries():
                label = info["label"]
                totp = TOTP(info["secret"])
                pw = totp.generate_totp()

                totps.append({
                    "id": info["id"],
                    "label": label,
                    "pw": pw,
                    "time_left": totp.time_left,
                    "notes": info.get("notes", ""),
                    "has_info": bool(info.get("secret_info")),
                })

            return {"code": 0, "msg": "查询全部", "data": totps}

        else:
            return {"code": -1, "msg": "需要登录", "data": []}

    @bp.post('/totp/add')
    def totp_add():
        if not store.is_unlocked():
            return {"code": -1, "msg": "需要登录"}

        js = request.get_json(silent=True) or {}
        label = js.get("label", "")
        secret = js.get("secret", "")
        if not label or not secret:
            return {"code": -1, "msg": "名称和密钥不能为空"}

        eid = store.add(label, secret, js.get("notes", ""), js.get("secret_info", ""))
        return {"code": 0, "msg": "添加成功", "data": {"id": eid}}

    @bp.get('/totp/get')
    def totp_get():
        if not store.is_unlocked():
            return {"code": -1, "msg": "需要登录"}

        eid = request.args.get("id")
        entry = store.get_entry(eid)
        if entry is None:
            return {"code": -1, "msg": "条目不存在"}
        return {"code": 0, "msg": "查询结果", "data": entry}

    @bp.put('/totp/update')
    def totp_update():
        if not store.is_unlocked():
            return {"code": -1, "msg": "需要登录"}

        js = request.get_json(silent=True) or {}
        eid = js.get("id")
        label = js.get("label", "")
        secret = js.get("secret", "")

        entries = {e["id"]: e for e in store.list_entries()}
        if eid not in entries:
            return {"code": -1, "msg": "条目不存在"}

        if not secret:
            secret = entries[eid]["secret"]

        store.update(eid, label, secret, js.get("notes", ""), js.get("secret_info", ""))
        return {"code": 0, "msg": "修改成功"}

    @bp.post('/totp/delete')
    def totp_delete():
        if not store.is_unlocked():
            return {"code": -1, "msg": "需要登录"}

        js = request.get_json(silent=True) or {}
        eid = js.get("id")
        if store.delete(eid):
            return {"code": 0, "msg": "删除成功"}
        return {"code": -1, "msg": "条目不存在"}

    @bp.post('/totp')
    def post_totp():

        js = request.get_json()

        label = js.get("label")

        totps = []
        if store.is_unlocked():

            if not label:
                return {"code": -1, "msg": "需要查询的名称", "data": []}

            infos = query_label(store.list_entries(), label)

            if infos:
                for info in infos:
                    lable = info["label"]
                    totp = TOTP(info["secret"])
                    pw = totp.generate_totp()

                    totps.append({"label": lable, "pw": pw, "time_left": totp.time_left})

                return {"code": 0, "msg": "查询结果", "data": totps}

            else:
                return {"code": 0, "msg": "没有查询", "data": []}
        else:
            return {"code": -1, "msg": "需要登录"}

    @bp.get("/login")
    def login():
        """
        检查是否已经解密
        """
        if store.is_unlocked():
            return {"code": 0, "msg": "登录成功"}
        else:
            return {"code": -1, "msg": "需要登录"}

    @bp.post("/logout")
    def logout():
        store.lock()
        return {"code": 0, "msg": "已锁定"}

    @bp.post("/login")
    def post_login():

        js = request.get_json()
        pw = js.get("password", "not found pw")

        if store.unlock(pw):
            return {"code": 0, "msg": "登录成功"}

        return {"code": -1, "msg": "密码错误"}

    @bp.errorhandler(404)
    def error404(error):
        order_path = request.path.removeprefix(prefix)
        print(f"这里是blueprint: {request.path=} {prefix=} {order_path=}")
        if order_path and order_path != "/":
            # print("send_from_directory()")
            return send_from_directory(app.static_folder, order_path)
        else:
            # print("render_template(index.html)")
            return render_template("index.html", base_url=prefix)

    return bp


def create_app(db: Path, prefix: str):

    if not prefix.endswith("/"):
        prefix = prefix + "/"

    app = Flask("totp", static_url_path=prefix, static_folder='static')
    # 或者在较新版本中直接配置 provider
    app.json.ensure_ascii = False

    @app.errorhandler(404)
    def handle_global_404(e):
        # 无论哪个蓝图没匹配到，最终都会走到这里
        print(f"这里是 global_404(): {request.path=} {prefix=}")
        return "<h1>404</h1>", 404

    # TOTP 与密码库共用同一个 SQLite 数据库（各自独立表与主密码）
    store = TOTPStore(db, 24 * 3600)
    bp = totp_main(app, store, prefix)
    app.register_blueprint(bp)

    vstore = VaultStore(db)
    vbp = vault_main(app, vstore, prefix)
    app.register_blueprint(vbp)

    return app


def flask_run():
    # 这是直接使用flask run 时使用的。
    # flask --app totpv3:flask_run run --reload --debug -p 12201
    import os
    import sys
    try:
        db: Path = Path(os.environ["TOTP_DB"])
        prefix: str = os.environ["TOTP_PREFIX"]
    except ValueError:
        print("开发环境中需要配置环境变量：TOTP_DB TOTP_PREFIX")
        sys.exit(1)

    return create_app(db, prefix)
