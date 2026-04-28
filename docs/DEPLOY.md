# 部署指南 | Deployment Guide

云想衣裳支持多种部署方式，从本地开发到 Docker 一键启动再到生产环境部署，本文档提供完整指引。

---

## 目录

- [环境要求](#环境要求)
- [本地开发部署](#本地开发部署)
- [Docker Compose 一键部署](#docker-compose-一键部署)
- [生产环境部署](#生产环境部署)
- [环境变量说明](#环境变量说明)
- [特性开关](#特性开关)
- [常见问题](#常见问题)

---

## 环境要求

| 依赖 | 最低版本 | 说明 |
|:-----|:---------|:----|
| Python | 3.10+ | 推荐使用 3.11 或 3.12 |
| MySQL | 8.0+ | 需要支持 utf8mb4 字符集 |
| pip | 最新版 | 用于安装 Python 依赖 |
| NVIDIA GPU + CUDA | 可选 | 推理速度更快，无 GPU 时自动使用 CPU |
| Ollama | 可选 | AI 时尚顾问需要本地运行 Ollama |

---

## 本地开发部署

### 1. 克隆仓库

```bash
git clone https://github.com/yourname/yunxiangyishang.git
cd yunxiangyishang
```

### 2. 创建虚拟环境

```bash
# Linux / macOS
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖包括：Flask、SQLAlchemy、PyMySQL、flask-login、flask-mail、transformers、torch、clip、opencv-python、Pillow。

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入真实的数据库密码和密钥（详见下方环境变量说明）。

### 5. 初始化数据库

```sql
CREATE DATABASE fashion_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

首次启动时 Flask 会通过 SQLAlchemy 自动创建所有数据表和默认管理员账户。

默认管理员：用户名 `admin`，密码 `admin123`。**请在首次登录后立即修改密码。**

### 6. 下载 AI 模型（可选）

项目使用 CLIP 和 BLIP 做图像理解。首次启动时会自动从 HuggingFace 下载到 `app/models/` 目录，也可以手动放置：

```bash
# CLIP (OpenAI)
git clone https://huggingface.co/openai/clip-vit-base-patch32 app/models/clip-vit-base-patch32

# BLIP (Salesforce)
git clone https://huggingface.co/Salesforce/blip-image-captioning-base app/models/blip-image-captioning-base
```

如果网络环境无法访问 HuggingFace，可手动下载模型文件并��入对应目录。

### 7. 启动开发服务器

```bash
python run.py
```

启动后访问 `http://localhost:5000` 即可使用。

---

## Docker Compose 一键部署

预置 Docker Compose 编排，包含 MySQL 8.0、Flask 主应用与 Ollama 时尚顾问三个服务。

### 前置条件

- 已安装 [Docker](https://docs.docker.com/get-docker/) 和 [Docker Compose](https://docs.docker.com/compose/install/)
- 至少 4GB 可用内存（AI 模型推理需要）
- 至少 5GB 可用磁盘空间（模型权重 + MySQL 数据）

### 启动步骤

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，设置 MYSQL_PASSWORD 和 SECRET_KEY

# 2. 构建并启动所有服务
docker-compose up --build

# 3. 后台运行
docker-compose up -d

# 4. 查看运行状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f web
```

### 服务端口

| 服务 | 端口 | 说明 |
|:-----|:-----|:----|
| Flask Web 应用 | 5000 | 主应用入口 |
| MySQL 数据库 | 3306 | 数据库服务 |
| Ollama 时尚顾问 | 3001 | AI 对话服务 |

### 数据持久化

Docker Compose 使用命名卷持久化以下数据：

- `mysql_data` - MySQL 数据文件
- `upload_data` - 用户上传的衣物图片
- `model_cache` - AI 模型缓存

### 停止服务

```bash
# 停止但保留数据
docker-compose down

# 停止并清除数据卷（谨慎使用）
docker-compose down -v
```

---

## 生产环境部署

### 推荐架构

```
Internet -> Nginx (SSL + 反向代理) -> Flask (Gunicorn) -> MySQL
                                       |
                                    Ollama (可选)
```

### 1. 使用 Gunicorn 运行

```bash
pip install gunicorn

# 4 个 worker，绑定 0.0.0.0:5000
gunicorn "app:create_app()" --bind 0.0.0.0:5000 --workers 4 --timeout 120 --access-logfile logs/access.log --error-logfile logs/error.log
```

`--timeout 120` 是因为 AI 模型推理可能耗时较长，需要适当增加超时时间。

### 2. Nginx 反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate     /etc/ssl/certs/your-domain.pem;
    ssl_certificate_key /etc/ssl/private/your-domain.key;

    client_max_body_size 16M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    location /static/ {
        alias /path/to/yunxiangyishang/static/;
        expires 30d;
    }
}
```

### 3. Systemd 服务配置

创建 `/etc/systemd/system/yunxiangyishang.service`：

```ini
[Unit]
Description=YunXiangYiShang Fashion Platform
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/yunxiangyishang
Environment="PATH=/opt/yunxiangyishang/venv/bin"
ExecStart=/opt/yunxiangyishang/venv/bin/gunicorn "app:create_app()" --bind 127.0.0.1:5000 --workers 4 --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable yunxiangyishang
sudo systemctl start yunxiangyishang
```

### 4. 安全检查清单

- 修改 `SECRET_KEY` 为随机高强度字符串
- 修改默认管理员密码 `admin / admin123`
- MySQL 仅监听内网或 Docker 内部网络
- 启用 HTTPS（Nginx + Let's Encrypt）
- 确保 `.env` 文件不在版本控制中
- 定期备份 MySQL 数据

---

## 环境变量说明

所有配置通过 `.env` 文件管理，参考 `.env.example`：

| 变量名 | 必填 | 默认值 | 说明 |
|:-------|:-----|:-------|:----|
| `SECRET_KEY` | 是 | `fallback-dev-key-change-me` | Flask 会话签名密钥，生产环境必须更换 |
| `MYSQL_HOST` | 否 | `localhost` | MySQL 主机地址 |
| `MYSQL_USER` | 否 | `root` | MySQL 用户名 |
| `MYSQL_PASSWORD` | 是 | 空 | MySQL 密码 |
| `MYSQL_DATABASE` | 否 | `fashion_db` | 数据库名称 |
| `MYSQL_PORT` | 否 | `3306` | MySQL 端口 |
| `MAIL_SERVER` | 否 | `smtp.gmail.com` | 邮件服务器地址 |
| `MAIL_PORT` | 否 | `587` | 邮件服务器端口 |
| `MAIL_USE_TLS` | 否 | `true` | 是否启用 TLS |
| `MAIL_USERNAME` | 否 | 空 | 邮件账号（密码重置功能需要） |
| `MAIL_PASSWORD` | 否 | 空 | 邮件密码或应用专用密码 |
| `MAIL_DEFAULT_SENDER` | 否 | `noreply@yunxiangyishang.com` | 默认发件人地址 |
| `WEATHER_API_KEY` | 否 | 空 | 聚合数据天气 API 密钥 |
| `OLLAMA_MODEL` | 否 | `llama3.2:1b` | Ollama 使用的模型名称 |

---

## 特性开关

在 `config/default.py` 中可以控制各功能模块的开启和关闭：

| 开关名称 | 默认 | 说明 |
|:---------|:-----|:----|
| `FEATURE_WARDROBE_RECOMMENDATION` | `True` | 结合衣柜的穿搭推荐 |
| `FEATURE_ANALYTICS_EVENTS` | `True` | 用户行为埋点收集 |
| `FEATURE_SEARCH_WARDROBE_API` | `True` | 衣柜搜索 API |
| `FEATURE_ADVISOR_DIAGNOSIS` | `True` | 时尚顾问诊断功能 |
| `FEATURE_WEATHER_SERVICE` | `True` | 天气服务集成 |

---

## 常见问题

### 启动时报数据库连接失败

检查 MySQL 是否已启动、`MYSQL_HOST` / `MYSQL_PASSWORD` 是否正确。Docker 环境下 MySQL 主机应设为 `db`（服务名）。

### GPU 不可用

确认已安装 NVIDIA 驱动和 CUDA Toolkit。项目会自动检测 GPU，不可用时回退到 CPU 运行。

### 模型下载超时

可手动下载模型权重并放入 `app/models/` 目录，或配置 HTTP 代理后重试。

### 上传图片失败

确认 `static/uploads` 目录存在且有写入权限。Docker 环境下该目录已挂载为命名卷，无需手动处理。

---

更多问题请参考 [FAQ](FAQ.md) 或提交 [GitHub Issue](https://github.com/yourname/yunxiangyishang/issues)。
