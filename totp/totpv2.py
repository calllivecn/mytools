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
from jinja2 import Template
from flask import (
    Flask,
    request,
    Response,
    redirect,
    url_for,
    Blueprint,
)
from asgiref.wsgi import WsgiToAsgi


from totplib import (
    TOTP,
    issecretfile,
)



from typing import (
    List,
    Dict,
)



# 使用外部命令解密
class LoadFile:
    
    def __init__(self, secretfile: Path, time_: float):

        self.sf = secretfile

        self._decrypt = False

        self.time_ = time_

        self._lock = Lock()

        self.th = Thread(target=self.re_dectypt, daemon=True)
        self.th.start()

    def decrypt(self, pw: str) -> Dict:

        with self._lock:

            p = subprocess.run(["crypto.py", "-d", "-k", pw, "-i", self.sf, "-o", "-"], stdout=subprocess.PIPE)
            p.check_returncode()
            try:
                conf = json.loads(p.stdout)
            except json.JSONDecodeError:
                raise ValueError("密码错误")

            self._decrypt = True

        return conf


    def is_decrypt(self) -> bool:
        return self._decrypt


    def re_dectypt(self):

        while True:
            time.sleep(self.time_)

            with self._lock:
                self._decrypt = False



def query_label(conf: List[Dict], label: str, comment: str = None):

    for info in conf:
        if label in info["label"]:
            if comment is not None:
                if comment in info["comment"]:
                    return info
                else:
                    continue

            return info

    return None



head_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
     <meta name="viewport" content="width=device-width, initial-scale=1.0">
     <style>
        .container {
            display: flex;
            justify-content: center;
            /* align-items: center; */
            align-items: flex-start;
            height: 100vh; /* 使用视口单位让容器填满整个高度 */
        }

        .centered-element {
            /* background-color: #f0f0f0; */
            padding: 20px;
            border: 1px solid #ccc;
            text-align: center;
        }
    </style>
    <title>TOTP</title>
</head>
"""

end_html = """
</body>
</html>
"""

totp_password_html = """
<body>
    <div class="container">
        <div class="centered-element">

    {% if pw_is_wrong %}
        <h1>密码错误, 请重新输入。</h1>
    {% endif %}

    <form action="{{ url_prefix }}" method="post">
    <label for="password">密码：</label>
    <input type="password" name="password" id="password" required>
    <input type="submit" value="提交">
    </form>
        </div>
    </div>
"""

totp_result_html = """
<body>
    <div class="container">
        <div class="centered-element">

    <h1>TOTP(基于时间的一致性密码)</h1>
    {% for item in items %}
    <br><label> {{ item.label }} 动态密码：{{ item.pw }} 剩下时间：{{ item.time_left }} </label></br>
    {% endfor %}

        </div>
    </div>
"""

label_not_found_html = """
<body>
    <div class="container">
        <div class="centered-element">
        <h3>在URL输入 {{ url_prefix }}?label=xxx 查询对应TOTP</h3>
        <a href="{{ url_prefix }}">查询全部</a>
        </div>
    </div>
"""



def totp_main(app: Flask, secret: LoadFile, prefix: str):


    bp = Blueprint("prefix", app.name, url_prefix=prefix)
    
    global conf

    @bp.get('/')
    def get_totp():

        label = request.args.get("label")
        comment = request.args.get("comment")

        if secret.is_decrypt():

            totps = []
            if label is None:
                for info in conf:
                    label = info["label"]
                    totp = TOTP(info["secret"])
                    pw = totp.generate_totp()

                    totps.append({"label": label, "pw": pw, "time_left": totp.time_left})

                temp = Template("".join([head_html, totp_result_html, end_html]))
                return Response(temp.render(items=totps))

            else:

                info = query_label(conf, label, comment)
                if info is None:
                
                    temp = Template("".join([head_html, label_not_found_html, end_html]))
                    return Response(temp.render(url_prefix=url_for(".get_totp")))

                else:

                    lable = info["label"]
                    totp = TOTP(info["secret"])
                    pw = totp.generate_totp()

                    temp = Template("".join([head_html, totp_result_html, end_html]))
                    return Response(temp.render(items=[{"label": lable, "pw": pw, "time_left": totp.time_left}]))
        else:

            # return redirect(url_for(".login", next=request.full_path))
            return redirect(url_for(".login"))


    @bp.get("/login")
    def login():

        # print(f"{request.path=}\n{request.full_path=}\n{request=}")
        # print(f"{request.args=}\n{request.form=}")

        temp = Template("".join([head_html, totp_password_html, end_html]))
        return Response(temp.render(url_prefix=url_for(".post_login"), pw_is_wrong=False))


    @bp.post("/login")
    def post_login():

        global conf

        pw = request.form.get("password")
        try:
            conf = secret.decrypt(pw)
        except ValueError:
            temp = Template("".join([head_html, totp_password_html, end_html]))
            return Response(temp.render(url_prefix=url_for(".login"), pw_is_wrong=True))
        
        # return redirect(request.args.get("next") or url_for(".get_totp"))
        return redirect(url_for(".get_totp"))


    return bp



def main():

    parse = argparse.ArgumentParser()

    parse.add_argument("--addr", action="store", type=str, default="::", help="默认listen 地址(default: [::])")

    parse.add_argument("--port", action="store", type=int, default=12201, help="默认监听端口(default: 12201)")

    parse.add_argument("--prefix", action="store", type=str, default="/", help="默认 nginx 反向代理前缀(default: /)")

    parse.add_argument("--config", type=issecretfile, required=True, help="指定配置文件json")

    args = parse.parse_args()


    app = Flask("totp")
    bp = totp_main(app, LoadFile(args.config, 24 * 3600), args.prefix)
    app.register_blueprint(bp)
    app2 = WsgiToAsgi(app)


    headers = [
        ("server", "nginx")
    ]

    uvicorn.run(app2, host=args.addr, port=args.port, headers=headers, log_level="info")


if __name__ == "__main__":
    main()