# flask-speedtest-api

基于 Flask 的上传 / 下载测速 API。服务端**不保存任何文件**：

- 上传：读取并丢弃请求体，只返回收到的字节数。
- 下载：实时生成数据流，可用 `size` 参数指定下载多少 MB；不指定就无限下载。
- 下载返回的文件名固定为 `speedtest.bin`。
- 支持 `--prefix`，方便挂在 Nginx 的子路径后面。

需要 Python 3.9+。

## 安装与运行

```bash
cd flask-speedtest-api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

# 直接监听 8000 端口
python app.py --host 0.0.0.0 --port 8000

# 挂在 Nginx 的 /speedtest/ 后面
python app.py --host 127.0.0.1 --port 8000 --prefix /speedtest
```

配置项：

| 参数 / 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `--host` / `HOST` | `0.0.0.0` | 监听地址 |
| `--port` / `PORT` | `8000` | 监听端口 |
| `--prefix` / `PREFIX` | 空 | URL 路径前缀，例如 `/speedtest` |
| `MAX_UPLOAD_MB` | `0` | 上传大小上限（MB），`0` 表示不限制 |

## API

### 1. 上传测速

```http
POST <prefix>/api/upload
Content-Type: application/octet-stream
```

请求体会被直接读取并丢弃，不落盘、不保留。推荐用 `--data-binary`：

```bash
# 上传 100 MB 的数据（从 /dev/zero 读取）
head -c 104857600 /dev/zero | \
  curl -X POST --data-binary @- http://127.0.0.1:8000/api/upload
```

返回：

```json
{"ok": true, "filename": "upload.bin", "received_bytes": 104857600}
```

也可以继续用 `-F` 表单上传，同样不会保存文件，只是 `received_bytes` 会包含 multipart 边界等额外开销：

```bash
curl -F "file=@/tmp/test.bin" http://127.0.0.1:8000/api/upload
```

### 2. 下载测速

```http
GET <prefix>/api/download?size=<MB>
```

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `size` | 否 | 下载多少 MB（`1 MB = 1024 * 1024` 字节），支持小数 |

- 指定 `size`：下载固定大小的数据，响应带 `Content-Length`。
- 不指定 `size`：一直生成数据，直到客户端主动断开（没有 `Content-Length`，HTTP/1.1 下为 chunked）。
- 数据是随机内容，不会被 gzip 等压缩影响测速结果。
- 返回文件名固定为 `speedtest.bin`。

```bash
# 下载 100 MB 到 /dev/null，测下载速度
curl -o /dev/null "http://127.0.0.1:8000/api/download?size=100"

# 下载 1.5 MB 并保存，文件名由服务端指定为 speedtest.bin
curl -OJ "http://127.0.0.1:8000/api/download?size=1.5"

# 不限大小，一直下载，按 Ctrl+C 停止
curl -o /dev/null "http://127.0.0.1:8000/api/download"
```

响应头：

- `Content-Length`：指定 `size` 时存在
- `X-Download-Bytes`：本次发送的字节数，不限大小时为 `unlimited`
- `Content-Disposition`：固定为 `attachment; filename="speedtest.bin"`

## Nginx 配置

**方式一：保留前缀（应用使用 `--prefix /speedtest`）**

```nginx
location /speedtest/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    client_max_body_size 0;
    proxy_request_buffering off;
    proxy_buffering off;
}
```

此时访问 `http://example.com/speedtest/api/download?size=100`。

**方式二：由 Nginx 去掉前缀（应用不加 `--prefix`）**

```nginx
location /speedtest/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    client_max_body_size 0;
    proxy_request_buffering off;
    proxy_buffering off;
}
```

注意 `proxy_pass` 末尾的 `/` 会把前缀去掉，所以后端地址是 `/api/download`。

测速场景建议关闭 `proxy_buffering` 和 `proxy_request_buffering`，并放开 `client_max_body_size`，否则大文件上传会在 Nginx 层被拦截。

## 生产部署

```bash
pip install gunicorn
PREFIX=/speedtest gunicorn -w 2 -k gthread --threads 8 -b 0.0.0.0:8000 "app:create_app()"
```

## 测试

```bash
python -m unittest discover -s tests -v
```
