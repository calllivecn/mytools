# Nginx location 匹配规则与优先级

## 1. 基本语法

```nginx
location [修饰符] 路径或正则表达式 {
    # 配置
}
```

`location` 用于在选定的 `server` 中，根据请求 URI 选择配置。常见形式如下：

| 形式 | 含义 | 示例 |
| --- | --- | --- |
| `location = /path` | 精确匹配 | `location = /health` |
| `location ^~ /path/` | 前缀匹配；选为最长前缀后，在当前层级跳过正则匹配 | `location ^~ /static/` |
| `location ~ regex` | 区分大小写的正则匹配 | `location ~ \.php$` |
| `location ~* regex` | 不区分大小写的正则匹配 | `location ~* \.(jpg\|png)$` |
| `location /path/` | 普通前缀匹配 | `location /images/` |
| `location @name` | 命名 location，仅供内部跳转使用 | `location @fallback` |

> 表格中正则示例的 `\|` 是为了在 Markdown 表格内显示竖线；实际 Nginx 配置中应写成 `|`，例如 `location ~* \.(jpg|png)$`。

## 2. 同一层级的匹配过程

假设所有 `location` 都定义在同一个 `server` 下，且没有嵌套：

1. **精确匹配 `=`**：如果 URI 与路径完全相同，立即选中并结束查找。
2. **查找最长前缀**：在普通前缀和 `^~` 前缀中，记住匹配的最长路径。前缀匹配不是按配置文件顺序决定的。
3. **检查最长前缀是否带 `^~`**：如果带有，直接使用它，跳过本层正则匹配。较短的 `^~` 前缀不会压过更长的普通前缀。
4. **按配置顺序检查正则**：依次检查 `~` 和 `~*`，第一个匹配的正则胜出，停止检查后续正则。两种正则修饰符之间没有固定的先后优先级。
5. **回退到最长前缀**：如果没有正则匹配，使用第 2 步记住的最长前缀。如果既无前缀也无正则匹配，则返回 404。

简化记忆：**精确匹配 → 最长前缀为 `^~` 则直接使用 → 按顺序匹配正则 → 回退到最长普通前缀**。

这不是简单地给每种修饰符排一个绝对优先级：例如，只有被选为最长前缀的 `^~` 才能跳过正则。

## 3. 完整示例

```nginx
server {
    listen 80;
    server_name example.com;

    location = / {
        return 200 "exact root\n";
    }

    location ^~ /static/ {
        return 200 "static prefix\n";
    }

    location /static/private/ {
        return 200 "private prefix\n";
    }

    location ~* \.(jpg|png)$ {
        return 200 "image regex\n";
    }

    location ~ \.php$ {
        return 200 "php regex\n";
    }

    location / {
        return 200 "default prefix\n";
    }
}
```

| 请求 URI | 选中的 location | 原因 |
| --- | --- | --- |
| `/` | `= /` | 精确匹配立即结束查找 |
| `/static/logo.jpg` | `^~ /static/` | 它是最长前缀，跳过正则 |
| `/static/private/readme.txt` | `/static/private/` | 它是最长前缀，且没有正则匹配 |
| `/static/private/logo.jpg` | `~* \.(jpg\|png)$` | 最长前缀是普通前缀，图片正则随后匹配 |
| `/index.php` | `~ \.php$` | 普通前缀 `/` 之后，PHP 正则匹配 |
| `/other` | `/` | 没有正则匹配，回退到最长前缀 |

例如，`/photo.JPG` 可以匹配 `~*` 图片规则；若改为 `~`，则不会匹配大写的 `.JPG`。

## 4. 容易忽略的细节

### 匹配的是 URI 路径，不含查询参数

对 `/search?q=nginx`，location 匹配使用 `/search`，不使用 `?q=nginx`。匹配前 Nginx 会对 URI 进行规范化，包括解码 `%XX`、处理 `.` 和 `..` 路径片段；默认还会合并相邻斜杠（可通过 `merge_slashes` 调整）。

前缀是**字符串前缀**，不自动按路径段划分。例如 `location /api` 也能匹配 `/apix`；若只想匹配 `/api/` 下的路径，应使用 `/api/`，并按需单独处理 `/api`。

### 正则顺序很重要

```nginx
location ~ \.php$ { return 200 "generic\n"; }
location ~ ^/admin/.*\.php$ { return 200 "admin\n"; }
```

`/admin/index.php` 会命中第一条，而不是更具体的第二条。若希望第二条生效，需要将它放在第一条之前。

### 嵌套 location 的情况

上面的简化流程适用于同一层级。存在嵌套时，Nginx 会先沿最长前缀深入查找，再在适用的层级检查正则；嵌套结构会影响正则检查顺序。尤其要注意：**内层 `^~` 不保证跳过外层正则**；如果外层所选前缀没有 `^~`，外层正则仍可能被检查并最终胜出。为了降低歧义，建议尽量减少嵌套，并对实际请求验证。

### 内部跳转可能重新匹配

`rewrite ... last`、`try_files` 的 URI 回退、`error_page` 等可能触发内部跳转；跳转到新 URI 时会重新选择 location，因此最终处理请求的位置可能与首次匹配的不同。`rewrite ... break` 则不会因为该指令而重新选择 location。命名 location（例如 `@fallback`）通过内部跳转进入，不参与普通 URI 匹配。

### 末尾斜杠和重定向

对于以 `/` 结尾、并使用 `proxy_pass`、`fastcgi_pass` 等相关代理处理指令的前缀 location，请求恰好等于去掉末尾 `/` 的路径时，Nginx 可能自动返回 301 跳转到带 `/` 的 URI。可用精确 location 单独处理不带斜杠的路径。

## 5. 验证方法

修改配置后先执行 `nginx -t` 检查语法，再按部署方式重载 Nginx。可以像上面的示例一样临时使用不同的 `return` 内容，然后用 `curl` 验证：

```bash
curl -i 'http://example.com/static/logo.jpg'
curl -i 'http://example.com/static/private/logo.jpg'
curl -i 'http://example.com/search?q=nginx'
```

如果域名尚未解析到目标服务器，可使用 `curl --resolve` 指定目标 IP。生产环境中不要随意覆盖现有处理逻辑；建议在测试环境验证。

参考：[Nginx 官方 location 指令文档](https://nginx.org/en/docs/http/ngx_http_core_module.html#location)。
