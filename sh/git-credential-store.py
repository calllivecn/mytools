#!/usr/bin/env python3
# coding=utf-8
# date 2020-05-03 13:51:17
# author calllivecn <c-all@qq.com>


import sys
import logging
from os import path
from urllib import parse
from socketserver import ThreadingMixIn
from http.server import (
                        HTTPServer,
                        BaseHTTPRequestHander,
                        )

def getlogger(level=logging.INFO):
    fmt = logging.Formatter(
        "%(asctime)s %(filename)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    logger = logging.getLogger("AES")
    logger.setLevel(level)
    logger.addHandler(stream)
    return logger

logger = getlogger()


class ThreadHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class Request:

    def __init__(self, path):
        pass

class Store:
    """
    credential:
    {
        "<token>":[
            {
                "protocol": "http", # or https
                "host": "github.com", # gihtub.com:443, 不同。
                "username": "<username>",
                "password": "<password>"
            },
                {
                "protocol": "http", # or https
                "host": "xxxx.com", # gihtub.com:443, 不同。
                "username": "<username>",
                "password": "<password>"
            },
        ]},
        "<token2>":[
            {
                "protocol": "<protocol3>"
                ....
            }
        ]
    ]}
    """

    def __init__(self, cfg=None):

        if cfg is None:
            filename, ext = path.splitext(filename)
            filename += ".json"
            self._cfg = path.join(path.expanduser("~"), ".config", filename)
        else:
            self._cfg =  cfg
        
        self._store_js = {}

        if path.exists(self._cfg):
            
            with open(self._cfg) as f:
                try:
                    self._store_js = json.load(f)
                except Exception:
                    logger.warning(f"{self._cfg}: 不是一个json文件。")
                    sys.exit(1)
        else:
            logger.error(f"请配置 {self._cfg} 配置文件")
            sys.exit(1)

    def get(self, token, protocol, host, username=None):
        """
        protocol: http or https
        host: 是 github.com or github.com:443 这俩种是不同的。 对应你的 git remote -v
        username: 同一个地址的不同用户，（也许有用）

        return: index, credential
        """
        if username is None:
            for index, credential in enumerate(self._store_js[token]):
                if protocol == credential["protocol"] and host == credential["host"]:
                    return index, credential
        else:
            for index, credential in self._store_js[token]:
                if protocol == credential["protocol"] and host == credential["host"] and username == credential["username"]:
                    return index, credential

    def store(self, token, protocol, host, username, password):
        d = {
            "protocol": protocol,
            "host": host,
            "username": username,
            "password": password,
        }

        self._store_js[token].append(d)
    
    def erase(self, token, protocol, host, username):
        index, _ self.get(token, protocol, host, username)
        self._store_js.pop(index)
        self.__save()

    def __save(self):
        with open(self._cfg, "w") as f:
            json.dump(f, ensure_ascii=False, indent=4)


class Handler(BaseHTTPRequestHandler):
    """
    method POST: 对应 git credential-store get
    method PUT: 对应 git credential-store store
    method DELETE: 对应 git credential-store erase
    """

    def do_POST(self):
        self.__authorization()

        #pr = parse.urlparse(self.path)
        #print(pr)

        js = self.rfile.read(int(self.headers["Content-Length"]))

        try:
            proto = js_data["protocol"]
            host = js_data["host"]
            username = js_data.get("username")
        except KeyError:
            self.send_response(400)
            self.end_headers()
            return 

        index, credential = self._store.get(self.headers["AUTH"], proto, host, username)

        self__response(credential)
    

    def do_PUT(self):
        self.__authorization()

        js = self.rfile.read(int(self.headers["Content-Length"]))
        js_data = json.loads(js)

        try:
            token = self.headers["AUTH"]
            proto = js_data["protocol"]
            host = js_data["host"]
            username = js_data["username"]
            password = js_data["password"]
        except KeyError:
            self.send_response(400)
            self.end_headers()
            return 

        self._store.store(token, proto, host, username, password)
    

    def do_DELETE(self):
        self.__authorization()

        try:
            token = self.headers["AUTH"]
            proto = js_data["protocol"]
            host = js_data["host"]
            username = js_data["username"]
        except KeyError:
            self.send_response(400)
            self.end_headers()
            return
        
        self._store.erase(token, proto, host, username)

        self.send_response(200)
        self.end_headers()


    def __response(self, response):

        js = json.dumps(response, ensure_ascii=False, indent=4)

        length = len(js) 

        self.send_response(200)

        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", length)
        self.end_headers()

        self.wfile.write(js)

    def __authorization(self):
        self.protocol_version = "HTTP/1.1"

        auth = self.headers.get("AUTH") 
        if auth in self._store:
            pass
        else:
            self.send_response(401)
            self.end_headers()

    def add_store(self, store):
        self._store = store



def server(port, cfg):
    store = Store(cfg)

    httpd = ThreadHTTPServer(("", port), Handler)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
        logger.info("Close server.")



for arg in sys.argv:
    if arg == "--server":
        server()
        sys.exit(0)
    elif arg == "--token":
        token = arg
    elif arg == "--token-cfg":
        cfg = arg
    elif arg == "get" or arg == "store" or arg == "erse":
        cmd = arg
    else:
        _, PROGRAM = path.split(sys.argv[0])
        usage = f"Usage: {PROGRAM} [ <--server> | [ --token | --token-cfg <filepath>] ]"
        logger.error(usage)
        sys.exit(1)
