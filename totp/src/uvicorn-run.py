
import uvicorn

from asgiref.wsgi import WsgiToAsgi


from totpv3 import (
    create_app
)

from pathlib import Path


def main():
    import argparse
    parse = argparse.ArgumentParser()

    parse.add_argument("--addr", action="store", type=str, default="::", help="默认listen 地址(default: [::])")

    parse.add_argument("--port", action="store", type=int, default=12201, help="默认监听端口(default: 12201)")

    parse.add_argument("--prefix", action="store", type=str, default="/", help="默认 nginx 反向代理前缀(default: /)")

    parse.add_argument("--config", type=Path, required=True, help="指定totp数据库sqlite文件(不存在则新建)")

    parse.add_argument("--vault", action="store", type=Path, default=None, help="指定密码库sqlite文件(default: 禁用密码库)")

    args = parse.parse_args()

    prefix: str = args.prefix
    if not prefix.endswith("/"):
        args.prefix = prefix + "/"
        print("--prefix 参数 必须要/结尾，已经自动添加上：", args.prefix)

    app = create_app(args.config, args.prefix, args.vault)
    
    app2 = WsgiToAsgi(app)
    
    uvicorn.run(app2, host=args.addr, port=args.port, server_header=False, log_level="info", date_header=False)

if __name__ == "__main__":
    main()
