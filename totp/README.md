# 尝试开始使用 容器 跑小服务

## 需要运行在nginx 后面，没有加密的。

- 默认监听[::]:12201

```shell
or  在nginx 后面添加前缀
podman run -d --name totp -p 12201:12201 -v </path/to/totp.a>:/data/totp.a localhost/totp:latest --prefix /totp --config /data/totp.a

or  使用 secret podman secret create <totp.a>
podman run -d --name totp -p 12201:12201 --secret totp localhost/totp:latest --prefix /totp --config /run/secrets/totp

```

