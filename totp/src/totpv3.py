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


def totp_main(app: Flask, store: TOTPStore, prefix: str, vault_enabled: bool = False):
    print(f"{prefix=}")

    bp = Blueprint("prefix", app.name, url_prefix=prefix)

    @bp.get("/")
    def index():
        print(f"这是 @bp.get()  {request.path=}")
        return render_template("index.html", base_url=prefix, vault_enabled=vault_enabled)

    @bp.get('/totpall')
    def get_totp():
        if store.is_unlocked():

            totps = []
            for info in store.list_entries():
                label = info["label"]
                totp = TOTP(info["secret"])
                pw = totp.generate_totp()

                totps.append({"label": label, "pw": pw, "time_left": totp.time_left})

            return {"code": 0, "msg": "查询全部", "data": totps}

        else:
            return {"code": 0, "msg": "请输入查询名"}

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
            return render_template("index.html", base_url=prefix, vault_enabled=vault_enabled)

    return bp


def create_app(config: Path, prefix: str, vault: Path | None = None):

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

    vault_enabled = vault is not None

    store = TOTPStore(config, 24 * 3600)
    bp = totp_main(app, store, prefix, vault_enabled)
    app.register_blueprint(bp)

    if vault is not None:
        vstore = VaultStore(vault)
        vbp = vault_main(app, vstore, prefix)
        app.register_blueprint(vbp)

    return app


def flask_run():
    # 这是直接使用flask run 时使用的。
    # flask --app totpv3:flask_run run --reload --debug -p 12201
    import os
    import sys
    try:
        config: Path = Path(os.environ["TOTP_CONFIG"])
        prefix: str = os.environ["TOTP_PREFIX"]
    except ValueError:
        print("开发环境中需要配置环境变量：TOTP_CONFIG TOTP_PREFIX")
        sys.exit(1)

    vault: Path | None = None
    if os.environ.get("TOTP_VAULT"):
        vault = Path(os.environ["TOTP_VAULT"])

    return create_app(config, prefix, vault)
