# ChatGPT Web Share

**English Readme: [README.en.md](README.en.md)**

共享一个 ChatGPT 账号给多用户同时使用的 web 应用，使用 FastAPI + Vue3 开发。可用于朋友之间共享或合租 ChatGPT 账号。支持 ChatGPT Plus / 设置对话模型 / 用户请求限制等功能。

![screenshot](screenshot.jpeg)

## 特点

- 美观简洁的 web 界面，使用 [naive-ui](https://www.naiveui.com/)
  - 支持多语言
  - 夜间模式
  - 支持一键复制回复内容为 Markdown 格式
  - 支持显示回复中的图像/表格/数学公式/语法高亮
- 使用 unofficial ChatGPT API，支持 ChatGPT Plus 账号
- 支持选择要使用的 ChatGPT 模型
- 创建多用户用于共享一个 ChatGPT 账号
- 不同用户创建的 ChatGPT 对话互相分隔，不会相互影响
- 多用户同时请求时，会进行排队处理
- 管理员可设置用户的最大对话数量、对话次数限制等

下一步计划：

- [x] 英语界面
- [ ] 支持 official ChatGPT API

注意：当前使用 [revChatGPT](https://github.com/acheong08/ChatGPT)，使用其反向代理绕过 Cloudflare 验证，因而受到请求限制，并且不保证长期稳定性。

## 部署

### 使用 docker

推荐使用 docker-compose 部署。新建 `docker-compose.yml` 文件，内容如下：

```yaml
version: "3"

services:
  chatgpt-share:
    image: ghcr.io/moeakwak/chatgpt-web-share:0.1.1
    container_name: chatgpt-web-share
    restart: always
    network_mode: bridge
    ports:
      - 8080:80 # web 端口号
    volumes:
      - ./data:/data # 存放数据库文件
      - ./config.yaml:/app/backend/api/config/config.yaml   # 后端配置文件
```

在同文件夹下创建 config.yaml，内容如下：

```yaml
print_sql: false
host: "127.0.0.1"
port: 8000
database_url: "sqlite+aiosqlite:////data/database.db"

jwt_secret: "你的 jwt secret"    # 用于生成 jwt token，需要自行设置
jwt_lifetime_seconds: 86400
cookie_max_age: 86400           # 登录过期时间
user_secret: "你的 user secret"  # 用于生成用户密码，需要自行设置

sync_conversations_on_startup: true # 是否在启动时同步同步 ChatGPT 对话，建议启用
create_initial_admin_user: true     # 是否创建初始管理员用户
create_initial_user: false          # 是否创建初始普通用户
initial_admin_username: admin       # 初始管理员用户名
initial_admin_password: password    # 初始管理员密码
initial_user_username: user         # 初始普通用户名
initial_user_password: password     # 初始普通密码

chatgpt_access_token: "你的access_token"    # 需要从 ChatGPT 获取
chatgpt_paid: true  # 是否为 ChatGPT Plus 用户
```

`chatgpt_access_token` 获取方法：打开登录 chat.openai.com 后，打开 https://chat.openai.com/api/auth/session 并获取 accessToken 字段。

最后运行 `docker-compose up -d` 即可。

### 使用 Caddy

#### 前端

需要先安装 nodejs 以及 pnpm，然后运行：

```bash
cd frontend
pnpm install
pnpm run build
```

注意：如果你没有能够启用 https 的域名，请设置环境变量 `VITE_API_WEBSOCKET_PROTOCOL` 为 `ws` 再编译。

#### 后端

需要先安装 poetry，并将 config.yaml 放置在 backend/api/config 目录下，然后运行：

```bash
cd backend
poetry install
poetry run python main.py
```

安装 caddy 后，新建 Caddyfile 文件，内容参考 [Caddyfile](Caddyfile)。

使用 `caddy start` 启动 caddy 即可。