# 尝试开始使用 容器 跑小服务

## 需要运行在nginx 后面，没有加密的。

- 默认监听[::]:12201

```shell
podman run -d --name totp --network host -v <加密文件.a>:/data/totp.a localhost/totpv2:latest
or  在nginx 后面添加前缀
podman run -d --name totp -p 12201:12201 -v </path/to/totp.a>:/data/totp.a localhost/totpv2:latest --prefix /totp --config /data/totp.a
```

