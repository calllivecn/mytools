
from totplib import issecretfile

from totpv3 import (
    create_app
)


def main():
    import argparse
    parse = argparse.ArgumentParser()

    parse.add_argument("--addr", action="store", type=str, default="::", help="默认listen 地址(default: [::])")

    parse.add_argument("--port", action="store", type=int, default=12201, help="默认监听端口(default: 12201)")

    parse.add_argument("--prefix", action="store", type=str, default="/", help="默认 nginx 反向代理前缀(default: /)")

    parse.add_argument("--config", type=issecretfile, required=True, help="指定配置文件json")

    args = parse.parse_args()

    prefix: str = args.prefix
    if not prefix.endswith("/"):
        args.prefix = prefix + "/"
        print("--prefix 参数 必须要/结尾，已经自动添加上：", args.prefix)

    app = create_app(args.config, args.prefix)
    app.run(args.addr, args.port)


if __name__ == "__main__":
    main()
