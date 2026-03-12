#!/usr/bin/env python3
# coding=utf-8
# date 2024-08-24 20:09:02
# author calllivecn <calllivecn@outlook.com>



import json
import time
import subprocess
import argparse
from pathlib import Path
from threading import (
    Thread,
    Lock,
)


import uvicorn
# from jinja2 import Template
from flask import (
    Flask,
    request,
    Response,
    # redirect,
    Blueprint,
    send_from_directory,
)
from asgiref.wsgi import WsgiToAsgi


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


    bp = Blueprint("prefix", app.name, url_prefix=prefix)

    @bp.errorhandler(404)
    def error404(error):
    #   return '<h1>404</h1>', 404
        print(f"这里是blueprint: {request.path=}")
        return send_from_directory(bp.static_folder, 'index.html')
    
    
    # @bp.get("/assets/<path:path>")
    # def index(path):
    #     return send_from_directory(bp.static_folder, path)

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

    return bp



def main():

    parse = argparse.ArgumentParser()

    parse.add_argument("--addr", action="store", type=str, default="::", help="默认listen 地址(default: [::])")

    parse.add_argument("--port", action="store", type=int, default=12201, help="默认监听端口(default: 12201)")

    parse.add_argument("--prefix", action="store", type=str, default="/", help="默认 nginx 反向代理前缀(default: /)")

    parse.add_argument("--config", type=issecretfile, required=True, help="指定配置文件json")

    args = parse.parse_args()


    app = Flask("totp", static_folder='static', static_url_path='')
    # 或者在较新版本中直接配置 provider
    app.json.ensure_ascii = False

    # @app.get("/")
    # def index():
    #     return send_from_directory(app.static_folder, 'index.html')

    @app.errorhandler(404)
    def handle_global_404(e):
        # 无论哪个蓝图没匹配到，最终都会走到这里
        print(f"这里是app: {request.path=}")
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.get("/favicon.ico")
    def favicon():
        return Response("not found favicon.ico", status=404)

    bp = totp_main(app, LoadFile(args.config, 24 * 3600), args.prefix)
    app.register_blueprint(bp)
    app2 = WsgiToAsgi(app)


    headers = [
        ("server", "nginx")
    ]

    uvicorn.run(app2, host=args.addr, port=args.port, headers=headers, log_level="info")
    # uvicorn.run(app2, host=args.addr, port=args.port, headers=headers, log_level="debug")

if __name__ == "__main__":
    main()
