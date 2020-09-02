#!/usr/bin/env python3
# coding=utf-8
# date 2020-05-03 13:51:17
# author calllivecn <c-all@qq.com>


import os
import sys
import ssl
import json
# import socket
import logging
import argparse
from os import path
from urllib import parse, request
from socketserver import ThreadingMixIn
from http.server import (
                        HTTPServer,
                        BaseHTTPRequestHandler,
                        )

def getlogger(level=logging.INFO, logfile=None):

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")

    stream = logging.StreamHandler(sys.stdout)

    stream.setFormatter(fmt)

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(stream)
    return logger

logger = getlogger()


class ThreadHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

    store = None

    def add_store(self, store):
        self.store = store

class Request:

    def __init__(self, path):
        pass


CFG_EXAMPLE="""{
    "<token>": {
        "<protocol>+<host>+[usernam]":{
            "protocol": "http",
            "host": "github.com",
            "username": "<username>",
            "password": "<password>"
        },
        "<protocol>+<host>+[usernam]":{
            "protocol": "http",
            "host": "xxxx.com",
            "username": "<username>",
            "password": "<password>"
        }
    },
    "<token2>":{
        "<protocol>+<host>+[usernam]":{
                "protocol": "<protocol3>",
                "host": "github.com",
                "username": "username",
                "password": "xxxxxx"
            }
    }
}
"""

class Store:

    def __init__(self, cfg=None):

        if cfg is None:
            filename, _ = path.splitext(path.basename(sys.argv[0]))
            filename += ".json"
            self._cfg = path.join(path.expanduser("~"), ".config", filename)
        else:
            self._cfg =  cfg

        logger.debug(f"--cfg: {self._cfg}")
        
        self._store_js = {}

        logger.debug(f"store json: {json.dumps(self._store_js, ensure_ascii=False, indent=4)}")

        if path.exists(self._cfg):
            
            with open(self._cfg) as f:
                try:
                    self._store_js = json.load(f)
                except Exception as e:
                    logger.warning(f"{self._cfg}: 不是一个json文件。")
                    logger.warning(f"{e}")
                    sys.exit(1)
        else:
            with open(self._cfg, "w") as f:
                f.write(CFG_EXAMPLE)
                logger.error(f"请按 {self._cfg} 内容提示配置 。")
            sys.exit(1)

    def get(self, token, protocol, host, username=None):
        """
        protocol: http or https
        host: 是 github.com or github.com:443 这俩种是不同的。 对应你的 git remote -v
        username: 同一个地址的不同用户，（也许有用）

        return: {<info>} or None
        """
        if username is None:
            key = protocol + host
            if key in self._store_js[token]:
                return self._store_js[token][key]
            else:
                return
        else:
            key = protocol + host + username
            if key in self._store_js[token]:
                return self._store_js[token][key]
            else:
                return

    def store(self, token, protocol, host, username, password):
        d = {
            "protocol": protocol,
            "host": host,
            "username": username,
            "password": password,
        }

        key1 = protocol + host
        key2 = protocol + host + username

        if key1 in self._store_js[token]:
            pass
        else:
            self._store_js[token][key1] = d
            self.__save()

        if key2 in self._store_js[token]:
            pass
        else:
            self._store_js[token][key2] = d
            self.__save()
    
    def erase(self, token, protocol, host, username=None):


        if username is None:
            key = protocol + host
            if key in self._store_js[token]:
                self._store_js[token].pop(key)
                self.__save()

        else:
            key = protocol + host + username

            if key in self._store_js[token]:
                self._store_js[token].pop(key)
                self.__save()

    def __save(self):
        with open(self._cfg, "w") as f:
            json.dump(self._store_js , f, ensure_ascii=False, indent=4)


class Handler(BaseHTTPRequestHandler):
    """
    method POST: 对应 git credential-store get
    method PUT: 对应 git credential-store store
    method DELETE: 对应 git credential-store erase
    """

    # 关闭自带的 sys.stderr log
    def log_message(self, *args):
        pass

    def do_POST(self):
        self.worker("POST")

    def do_PUT(self):
        self.worker("PUT")

    def do_DELETE(self):
        self.worker("DELETE")

    def worker(self, method):
        if not self.__authorization():
            return

        try:
            client_address = self.headers["X-Real-IP"]
        except Exception:
            client_address = self.client_address[0]

        logger.info(f"client address: {client_address} {method}")

        if method == "POST":
            self.post()
        elif method == "PUT":
            self.put()
        elif method == "DELETE":
            self.delete()

    def post(self):

        js = self.__get_body_js()

        try:
            proto = js["protocol"]
            host = js["host"]
            username = js.get("username")
        except KeyError:
            self.send_response(400)
            self.end_headers()
            return 

        credential = self.server.store.get(self.headers["AUTH"], proto, host, username)

        self.__response(credential)
    

    def put(self):

        js = self.__get_body_js()

        try:
            token = self.headers["AUTH"]
            proto = js["protocol"]
            host = js["host"]
            username = js["username"]
            password = js["password"]
        except KeyError:
            self.send_error(400, "Params Error")
            return 

        self.server.store.store(token, proto, host, username, password)

        self.send_response(200)
        self.end_headers()
    

    def delete(self):
        js = self.__get_body_js()
        try:
            token = self.headers["AUTH"]
            proto = js["protocol"]
            host = js["host"]
            username = js["username"]
        except KeyError:
            self.send_error(400, "Delete Error")
            return
        
        self.server.store.erase(token, proto, host, username)

        self.send_response(200)
        self.end_headers()


    def __response(self, response):

        js = json.dumps(response, ensure_ascii=False, indent=4)

        length = len(js) 

        self.send_response(200)

        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", length)
        self.end_headers()

        self.wfile.write(js.encode("utf-8"))

    def __get_body_js(self):

        length = self.headers.get("Content-Length")

        if length is None:
            return None
        else:
            js = json.loads(self.rfile.read(int(length)))
            return js

    def __authorization(self):
        self.protocol_version = "HTTP/1.1"

        logger.debug(f"request headers:\n{self.headers}")

        auth = self.headers.get("AUTH") 

        logger.debug(f"HTTP header AUTH: {auth}")

        if auth in self.server.store._store_js:
            return True
        else:
            msg = "authorization Error"
            self.send_error(401, msg)
            logger.info(f"{self.client_address[0]} {msg}")
            return False


# client struct
class Client:


    def __init__(self, url, token, unverify=False):

        self.token = token
        self.url = url

        self._unverify = unverify

        # 留着，以后给客户端 添加自定义 证书
        #self._certfile = certfile
        #self._keyfile = keyfile
        #self._ca_cert = ca_cert

    def get(self, protocol, host, username=None):

        js = {
                "protocol": protocol,
                "host": host,
                }

        if username is not None:
            js["userame"] = username

        self.__request(js, "POST")

        #logger.info(f"{self.credential}")
        if self.credential is None:
            pass
        else:
            for k, v in self.credential.items():
                print(f"{k}={v}")
        print()

    def store(self, protocol, host, username, password):
        js = {
                "protocol": protocol,
                "host": host,
                "username": username,
                "password": password,
                }

        self.__request(js, "PUT")

    def erase(self, protocol, host, username=None, password=None):
        js = {
                "protocol": protocol,
                "host": host,
                }
        if username is not None:
            js["username"] = username

        if password is not None:
            js["password"] = password

        self.__request(js, "DELETE")


    def __request(self, js, method):
        js = json.dumps(js, ensure_ascii=False)
        #logger.info(f"请求：{js}")

        req = request.Request(self.url, js.encode("utf-8"), headers={"AUTH": self.token}, method=method)

        if self._unverify:
            ctx = ssl.SSLContext()
            result = request.urlopen(req, context=ctx)
        else:
            result = request.urlopen(req)


        if result.getcode() != 200:
            logger.error("请求服务器出错")
            sys.exit(1)

        if result.headers.get("Content-Length"):
            self.credential = json.loads(result.read())


def server(addr="0.0.0.0", port=11540, cfg=None, certfile=None, keyfile=None, ca_cert=None):

    store = Store(cfg)

    httpd = ThreadHTTPServer((addr, port), Handler)

    httpd.allow_reuse_address = True
    httpd.request_queue_size = 512

    if certfile and keyfile:
        httpd.socket = ssl.wrap_socket(httpd.socket, certfile=certfile, keyfile=keyfile,
                                    server_side=True, ssl_version=ssl.PROTOCOL_TLS_SERVER,
                                    ca_certs=ca_cert)

    httpd.add_store(store)

    try:
        logger.info(f"listen: {addr}:{port}")
        httpd.serve_forever()
    finally:
        httpd.server_close()
        logger.info("Close server.")

def stdin_in():
    d = {}
    while True:
        param = sys.stdin.readline()
        # git credential 会以换行符，或NUL字符结束输入
        if param == os.linesep or param == "":
            break
        k, v = param.rsplit(os.linesep)[0].split("=")
        d[k] = v
    return d

def client(operation, url, token, unverify):

    http = Client(url, token, unverify)

    js = stdin_in()

    if operation == "get":
        http.get(**js)
    elif operation == "store":
        http.store(**js)
    elif operation == "erase":
        http.erase(**js)


def check_cfg(filepath):
    if path.exists(filepath):
        return filepath
    else:
        with open(filepath, "w") as f:
            f.write("""{"url": <url>, "token": <token>, "unverify": False}""")
        raise argparse.ArgumentTypeError(f"初始化 {filepath} 配置，请按照提示修改。")

def fileexists(filename):
    if path.exists(filename):
        return filename
    else:
        raise argparse.ArgumentTypeError(f"{filename} 不是一个文件.")

def main():

    parse = argparse.ArgumentParser(
            usage="\n%(prog)s --server --cfg <config path>\n"
            "%(prog)s --url <url>  --token <token> [--unverify]\n"
            "%(prog)s --cfg <config path> [--unverify]",
            epilog="author: calllivecn"
            "<https://github.com/calllivecn/mytools/sh/%(prog)s>"
            )
    #group = parse.add_mutually_exclusive_group()

    parse.add_argument("--server", action="store_true", help="启动 server 模式")

    parse.add_argument("--address", default="0.0.0.0", help="要监听的地址 default: 0.0.0.0")

    parse.add_argument("--port", type=int, default=11540, help="启动server时的 port (default:11540)")

    parse.add_argument("--certfile", type=fileexists, help="证书文件")

    parse.add_argument("--keyfile", type=fileexists, help="私钥文件")

    parse.add_argument("--ca_cert", type=fileexists, help="ca文件")

    parse.add_argument("--unverify", action="store_true", help="不验证https服务器")

    parse.add_argument("--url", help="git credential 服务器地址")

    parse.add_argument("--token", help="git credential 服务器token")

    parse.add_argument("--cfg", type=check_cfg, help="""client 配置文件。例如：{"url": "<https://my-git-credential.com/", "token": "token"}""")

    parse.add_argument("operation", nargs="?", default=None, choices=["get", "store", "erase"], help="client 操作")

    parse.add_argument("--parse", action="store_true", help="debug parse")

    parse.add_argument("--debug", action="store_true", help="debug run")

    args = parse.parse_args()

    if args.parse:
        print(args)
        sys.exit(0)

    if args.debug:
        logger.setLevel(logging.DEBUG)
    #else:
        #logger = getlogger()

    if args.server:

        if args.cfg is None:
            print(f"服务器模式下， --cfg 是必须")
            sys.exit(1)

        if args.ca_cert:
            server(args.address, args.port, args.cfg, certfile=args.certfile, keyfile=args.keyfile, ca_cert=args.ca_cert)
        elif args.certfile and args.keyfile:
            server(args.address, args.port, args.cfg, certfile=args.certfile, keyfile=args.keyfile)
        else:
            server(args.address, args.port, args.cfg)


    if args.operation is None:
        logger.error(f"client模式，必需要有操作指令，choices: get, store, erase")
        sys.exit(2)

    if args.url is not None and args.token is not None:
        client(args.operation, args.url, args.token, args.unverify)

    elif args.cfg:
        with open(args.cfg) as f:
            try:
                cfg = json.load(f)
            except json.decoder.JSONDecodeError:
                logger.error(f"{args.cfg}: 配置错误，请按照 --help 提示修改。")
                sys.exit(1)

        client(args.operation, cfg["url"], cfg["token"], cfg.get("unverify", False))
    else:
        logger.error("什么情况？？？")
        sys.exit(6)

if __name__ == "__main__":
    main()
