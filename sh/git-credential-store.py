#!/usr/bin/env python3
# coding=utf-8
# date 2020-05-03 13:51:17
# author calllivecn <c-all@qq.com>


import sys
import json
import logging
from os import path
from urllib import parse, request
from socketserver import ThreadingMixIn
from http.server import (
                        HTTPServer,
                        BaseHTTPRequestHandler,
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
            filename, ext = path.splitext(path.basename(sys.argv[0]))
            filename += ".json"
            self._cfg = path.join(path.expanduser("~"), ".config", filename)
        else:
            self._cfg =  cfg
        
        self._store_js = {}

        if path.exists(self._cfg):
            
            with open(self._cfg) as f:
                try:
                    self._store_js = json.load(f)
                except Exception as e:
                    logger.warning(f"{self._cfg}: 不是一个json文件。")
                    #logger.warning(f"{e}")
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
            return -1, {}
        else:
            for index, credential in enumerate(self._store_js[token]):
                if protocol == credential["protocol"] and host == credential["host"] and username == credential["username"]:
                    return index, credential
            return -1, {}

    def store(self, token, protocol, host, username, password):
        d = {
            "protocol": protocol,
            "host": host,
            "username": username,
            "password": password,
        }

        self._store_js[token].append(d)
    
    def erase(self, token, protocol, host, username):
        index, _ = self.get(token, protocol, host, username)
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
        if not self.__authorization():
            return

        #pr = parse.urlparse(self.path)
        #print(pr)

        js = self.__get_body_js()

        try:
            proto = js["protocol"]
            host = js["host"]
            username = js.get("username")
        except KeyError:
            self.send_response(400)
            self.end_headers()
            return 

        index, credential = store.get(self.headers["AUTH"], proto, host, username)

        self.__response(credential)
    

    def do_PUT(self):
        if not self.__authorization():
            return

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

        store.store(token, proto, host, username, password)
    

    def do_DELETE(self):

        if not self.__authorization():
            return

        js = self.__get_body_js()
        try:
            token = self.headers["AUTH"]
            proto = js["protocol"]
            host = js["host"]
            username = js["username"]
        except KeyError:
            self.send_error(400, "Delete Error")
            return
        
        store.erase(token, proto, host, username)

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

        auth = self.headers.get("AUTH") 
        if auth in store._store_js:
            return True
        else:
            self.send_error(401, "authorization Error")
            return False

    #def add_store(self, store):
    #    self._store = store


# client struct
class client:


    def __init__(self, token, url):

        self.token = token
        self.url = url

        self.protocol = protocol
        self.host = host
        self.username = username

    def get(self, protocol, host, username=None):

        js = {
                "protocol": protocol,
                "host": host,
                }

        if username is not None:
            js["userame"] = username

        self.__request(js, "POST")

    def store(self, protocol, host, username, passwrod):
        js = {
                "protocol": protocol,
                "host": host,
                "username": username,
                "password": password,
                }

        self.__request(js, "PUT")

    def erase(self):
        js

    def __request(self, js, method):
        js = json.dumps(js, ensure_ascii=False)
        req = request.Request(self.url, js, method=method)

        reuslt = rquest.urlopen(req)

        self.credential = json.loads(result.read())


def server(port, cfg=None):
    store = Store(cfg)

    httpd = ThreadHTTPServer(("", port), Handler)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
        logger.info("Close server.")


def client():
    


if __name__ == "__main__":
    store = Store()
    server(6789)
    sys.exit(0)


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
