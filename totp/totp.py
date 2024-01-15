#!/usr/bin/env python3
# coding=utf-8
# date 2023-09-08 11:09:02
# author calllivecn <c-all@qq.com>

from typing import (
    List,
    Dict,
)


import io
import json
import subprocess
import argparse
from pathlib import Path
from urllib import parse
from http.server import (
                        # HTTPServer,
                        ThreadingHTTPServer, # 3.7 版本新功能。
                        BaseHTTPRequestHandler,
                        # SimpleHTTPRequestHandler
                        )


from totplib import (
    TOTP,
    issecretfile,
)

global URL_PREFIX

# 使用外部命令解密
class LoadFile:
    
    def __init__(self, secretfile: Path):

        self.sf = secretfile

        self._decrypt = False

    def decrypt(self, pw: str) -> Dict:

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



def respose_headers(buf: io.BytesIO):
    buf.write()

def respose_headers_end():
    pass


def query_label(label: str, comment: str = None):

    for info in CONF:
        if label in info["label"]:
            if comment is not None:
                if comment in info["comment"]:
                    return info
                else:
                    continue

            return info
    
    return None

def wrap_server_header(func):
    def wrap(*args, **kwargs):
        s = args[0]

        # self.server_version = "server/0.1 ca/1.0"
        s.server_version = "server"
        s.sys_version = ""
        # 返回http协议版本
        s.protocol_version = "HTTP/1.1"

        return func(*args, **kwargs)
    
    return wrap


class Handler(BaseHTTPRequestHandler):

    def urlparse(self):
        # parse 参数
        self.pr = parse.urlparse(self.path)

        # print(f"urlparse: {self.pr}")
        querys = parse.parse_qs(self.pr.query)
        # print(f"参数: {querys}")

        l = querys.get("label")
        c = querys.get("comment")

        if l:
            if c:
                return l[0], c[0]
            else:
                return l[0], None

        else:
            return None, None


    @wrap_server_header
    def do_GET(self):
        if self.path == "/favicon.ico":
            self.send_response(404)
            self.end_headers()
            return

        if not SECRET.is_decrypt():

            SECRET_HTML=f"""\
            <!DOCTYPE html>
            <html>
            <meta charset="UTF-8">
            <title>需要输入密码:</title>
            <body>
                <form action="{URL_PREFIX}" method="post">
                <label for="password">密码：</label>
                <input type="password" name="password" id="password" required>
                <input type="submit" value="提交">
                </form>
            </body>
            </html>
            """

            self.urlparse()
            # 解密文件
            html_buf = io.BytesIO()
            html_buf.write(SECRET_HTML.encode("utf-8"))
            content_length = html_buf.tell()

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", content_length)
            self.end_headers()

            self.wfile.write(html_buf.getvalue())
            html_buf.close()

            return


        label, comment = self.urlparse()

        # 就是说返回全部的TOTP
        totps = []
        if label is None:
            for info in CONF:
                label = info["label"]
                totp = TOTP(info["secret"])
                pw = totp.generate_totp()
                totp.time_left

                totps.append(f"<br><label> {label} 动态密码：{pw} 剩下时间：{totp.time_left} </label></br>".encode("utf-8"))
        else:
            info = query_label(label, comment)
            # print(f"debug: {info=}")
            label = info["label"]
            totp = TOTP(info["secret"])
            pw = totp.generate_totp()
            totp.time_left

            totps.append(f"<br><label> {label} 动态密码：{pw} 剩下时间：{totp.time_left} </label></br>".encode("utf-8"))
        
        # print(f"{totps=}")

        html_buf = io.BytesIO()

        html_buf.write("""<html><meta charset="UTF-8">""".encode("utf-8"))
        html_buf.write("""<title>TOTP(基于时间的一性密码)</title>""".encode("utf-8"))

        html_buf.write("<body>".encode())

        html_buf.write("<h1>TOTP</h1>".encode())

        # html_buf.write(f"<label> {label} 动态密码：{totp} 剩下时间：{t} </label>".encode("utf-8"))
        html_buf.write(b"".join(totps))

        html_buf.write("</body></html>".encode())

        content_length = html_buf.tell()

        self.send_response(200)

        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", content_length)
        self.end_headers()

        # print(f"最后的HTML:")
        # print(html_buf.getvalue())
        self.wfile.write(html_buf.getvalue())
        html_buf.close()


    @wrap_server_header
    def do_POST(self):
        # 处理从表单收到的密码


        # headers
        #print(f"headers: {self.headers}")

        # read() body 没有Content-Length 头，就是没有body
        length = self.headers.get("Content-Length")
        if length is None:
            # length = 0, not body
            body = b""
        else:
            body = self.rfile.read(int(length))
            #print(f"read json data: {json.loads(body)}")

        # 从body里拿密码
        _, pw = body.decode().split("=")

        self.urlparse()

        global CONF
        # 解密
        with io.BytesIO() as buf:
            try:
                CONF = SECRET.decrypt(pw)
            except ValueError:
                msg=f"""\
                <!DOCTYPE>
                <html>
                <meta charset="UTF-8">
                <h1>密码错误。</h1>
                <a href="{URL_PREFIX}">重新输入</a>
                </html>
                """
                buf.write(msg.encode("utf-8"))
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", buf.tell())
                self.end_headers()
                self.wfile.write(buf.getvalue())
                return


            # 成功了，跳转到totp
            msg=f"""\
            <!DOCTYPE>
            <html>
            <meta charset="UTF-8">
            <h3>在URL输入 {URL_PREFIX}?label=xxx 查询对应TOTP</h3>
            <a href="{URL_PREFIX}">查询全部</a>
            </html>
            """
            buf.write(msg.encode("utf-8"))
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", buf.tell())
            self.end_headers()
            self.wfile.write(buf.getvalue())


    def log_message(self, *args):
        pass


def httpserver(addr, port):
    addr = (addr, port)
    print(f"listening: {addr}")

    #httpd = HTTPServer(addr, Handler)

    httpd = ThreadingHTTPServer(addr, Handler, bind_and_activate=False)
    httpd.allow_reuse_address = True
    httpd.request_queue_size = 128

    #httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    # httpd.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

    httpd.server_bind()
    httpd.server_activate()


    # TCP 心跳
    #httpd.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 5) # 75 -> 5
    #httpd.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20) # 7200 -> 200
    #httpd.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 3) # 9 -> 3

    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
        print(f"Close server")


def main():
    parse = argparse.ArgumentParser()

    # http.server 这玩意儿不支持ipv6 ...
    # parse.add_argument("--addr", action="store", type=str, default="::1", help="默认listen 地址(default: ::1)")
    parse.add_argument("--addr", action="store", type=str, default="127.0.0.1", help="默认listen 地址(default: 127.0.0.1)")

    parse.add_argument("--port", action="store", type=int, default=12201, help="默认监听端口(default: 12201)")

    parse.add_argument("--prefix", action="store", type=str, default="/", help="默认 nginx 反向代理前缀(default: /)")

    parse.add_argument("--config", type=issecretfile, help="指定配置文件json")

    args = parse.parse_args()

    global URL_PREFIX
    URL_PREFIX = args.prefix

    global CONF
    """
    with open(args.config) as f:
        CONF = json.load(f)
    """

    global SECRET
    SECRET = LoadFile(args.config)
    
    # print(f"{CONF=}")

    httpserver(args.addr, args.port)


if __name__ == "__main__":
    main()