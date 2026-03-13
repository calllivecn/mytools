# 尝试开始使用 容器 跑小服务

## 需要运行在nginx 后面，没有加密的。

- 默认监听[::1]:12201
- 如果在 nginx 中配置了 location /prefix/ {} 路径的， 需要通过 --prefix /prefix 参数指定前缀。

```shell
or  在nginx 后面添加前缀
podman run -d --name totp -p 12201:12201 -v </path/to/totp.a>:/data/totp.a localhost/totp:latest --prefix /totp --config /data/totp.a

or  使用 secret podman secret create <totp.a>
podman run -d --name totp -p 12201:12201 --secret totp localhost/totp:latest --prefix /totp --config /run/secrets/totp

```


## 在浏览器中使用时

- 登录后。可以在地址栏原本的路径后面追加 ?all=1 的参数，回车，就是查询所有。
