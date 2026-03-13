#!/usr/bin/env python3
# coding=utf-8
# date 2024-08-24 20:09:02
# author calllivecn <calllivecn@outlook.com>



import json
import time
import subprocess

from pathlib import Path
from threading import (
    Thread,
    Lock,
)


# from jinja2 import Template
from flask import (
    Flask,
    request,
    render_template,
    # Response,
    # redirect,
    Blueprint,
    send_from_directory,
)


from totplib import (
    TOTP,
    issecretfile,
)


# 使用外部命令解密
class LoadFile:
    
    def __init__(self, secretfile: Path, time_: float):

        self.sf = secretfile

        self._decrypt = False

        self.time_ = time_

        self._lock = Lock()
        # 解密结果
        self.conf: list[dict] = []

        self.th = Thread(target=self.re_dectypt, daemon=True)
        self.th.start()

    def decrypt(self, pw: str):

        with self._lock:

            p = subprocess.run(["crypto.py", "-d", "-k", pw, "-i", self.sf, "-o", "-"], stdout=subprocess.PIPE)
            
            try:
                p.check_returncode()
                self.conf = json.loads(p.stdout)
            except (json.JSONDecodeError, subprocess.CalledProcessError):
                raise ValueError("密码错误")

            self._decrypt = True


    def is_decrypt(self) -> bool:
        return self._decrypt


    def re_dectypt(self):

        while True:
            time.sleep(self.time_)

            with self._lock:
                self._decrypt = False
                self.conf = []



def query_label(conf: list[dict], label: str) -> list:

    result = []
    for info in conf:
        if label in info["label"]:
            result.append(info)

    return result



def totp_main(app: Flask, secret: LoadFile, prefix: str):
    print(f"{prefix=}")

    bp = Blueprint("prefix", app.name, url_prefix=prefix)
    
    @bp.get("/")
    def index():
        print(f"这是 @bp.get()  {request.path=}")
        return render_template("index.html", base_url=prefix)


    @bp.get('/totpall')
    def get_totp():
        if secret.is_decrypt():

            totps = []
            for info in secret.conf:
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
        if secret.is_decrypt():

            if not label:
                return {"code": -1, "msg": "需要查询的名称", "data": []}

            infos = query_label(secret.conf, label)

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
            print("是执行到跳转了吗？")
            # return redirect("/")
            return {"code": -1, "msg": "需要登录"}


    @bp.get("/login")
    def login():
        """
        检查是否已经解密
        """
        if secret.is_decrypt():
            return {"code": 0, "msg": "登录成功"}
        else:
            return {"code": -1, "msg": "需要登录"}
        

    @bp.post("/login")
    def post_login():

        global conf

        js = request.get_json()
        pw = js.get("password", "not found pw")
        try:
            conf = secret.decrypt(pw)
        except ValueError:
            return {"code": -1, "msg": "密码错误"}
        
        return {"code": 0, "msg": "登录成功"}

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


def create_app(config: Path, prefix: str):

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
    
    bp = totp_main(app, LoadFile(config, 24 * 3600), prefix)
    app.register_blueprint(bp)

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
        
    return create_app(config, prefix)

