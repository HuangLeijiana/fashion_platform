# 常见问题 | FAQ

本页面汇总了云想衣裳使用和部署过程中的常见问题及解决方案。

---

## 安装与启动

### 启动时报 ModuleNotFoundError

确保已激活虚拟环境并安装所有依赖：

```bash
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

如果仍然报错，尝试升级 pip 后重新安装：

```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### PyTorch 安装失败或没有 GPU 支持

PyTorch 需要根据系统环境选择安装命令。访问 [PyTorch 官网](https://pytorch.org/get-started/locally/) 获取对应平台的安装命令。

如果有 NVIDIA GPU 但 CUDA 不可用，请确认：

1. 已安装 NVIDIA 驱动（建议最新版）
2. 已安装 CUDA Toolkit（版本与 PyTorch 匹配）
3. PyTorch 安装的是 GPU 版本而非 CPU 版本

项目在没有 GPU 的环境下也能正常运行，会自动回退到 CPU 模式。

### 启动时数据库连接失败

常见原因和排查步骤：

1. **MySQL 未启动** - 检查 MySQL 服务是否正在运行
2. **密码错误** - 确认 .env 中的 MYSQL_PASSWORD 与实际 MySQL 密码一致
3. **数据库不存在** - 先创建数据库：`CREATE DATABASE fashion_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
4. **Docker 环境** - MySQL 主机名应设为 db（Docker Compose 服务名），而非 localhost

### 端口 5000 被占用

修改 run.py 中的端口号，将 5000 改为其他可用端口即可。

---

## AI 功能

### CLIP / BLIP 模型下载很慢或失败

模型文件托管在 HuggingFace 上，国内网络可能较慢。解决方案：

1. **手动下载** - 从 HuggingFace 页面下载模型文件，放入 `app/models/clip-vit-base-patch32/` 和 `app/models/blip-image-captioning-base/` 目录
2. **使用镜像站** - 设置 `HF_ENDPOINT=https://hf-mirror.com` 环境变量
3. **配置代理** - 设置 HTTP_PROXY 和 HTTPS_PROXY 环境变量

### 推荐结果不准确

推荐质量取决于以下因素：

1. **候选图片数量** - `static/images/products/` 中的图片越多，推荐越丰富
2. **用户画像完整度** - 填写完整的身高、体重、体型、肤色等信息可提升推荐精度
3. **衣柜单品数量** - 衣柜中有 10 件以上单品时，推荐效果会明显提升
4. **上传图片质量** - 背景干净、光线充足的照片分析效果更好

### AI 时尚顾问无法使用

时尚顾问依赖 Ollama 本地 LLM 服务。排查步骤：

1. 确认已安装 [Ollama](https://ollama.ai)
2. 执行 `ollama list` 确认模型已下载
3. 执行 `ollama pull llama3.2:1b` 下载默认模型
4. 检查 Ollama 服务是否在运行（默认端口 11434）
5. Docker 环境下确认 advisor 容器正常启动

### 风格分析报"风格模型加载失败"

风格分类模型文件 `app/style_analysis/style_model.pth` 需要单独训练或获取。如果该文件不存在，风格分析功能将不可用，但不影响其他功能使用。

---

## 数据与存储

### 上传的图片存储在哪里

用户上传的衣物图片保存在 `static/uploads/` 目录，文件名使用时间戳加原始文件名的格式。Docker 环境下该目录通过命名卷 `upload_data` 持久化。

### 如何备份数据

需要备份两部分：

1. **MySQL 数据库** - 使用 `mysqldump -u root -p fashion_db > backup.sql`
2. **上传的图片** - 复制 `static/uploads/` 目录

Docker 环境下的备份：

```bash
# 备份 MySQL
docker-compose exec db mysqldump -u root -p fashion_db > backup.sql

# 备份上传文件
docker cp yunxiangyishang_web_1:/app/static/uploads ./uploads_backup
```

### 如何重置管理员密码

通过 Flask shell 直接操作数据库完成密码重置，具体命令请参考项目中的 run.py 启动方式，在 Python 交互环境中执行：

```python
from app import create_app
from app.models import User, db
app = create_app()
with app.app_context():
    u = User.query.filter_by(username='admin').first()
    u.set_password('你的新密码')
    db.session.commit()
```

---

## Docker 部署

### Docker 构建很慢

首次构建需要下载基础镜像和安装 Python 依赖，耗时较长。后续构建会利用 Docker 缓存加速。

可以预先拉取基础镜像：

```bash
docker pull python:3.11-slim
docker pull mysql:8.0
```

### Docker 容器内存不足

AI 模型推理需要较多内存。建议 Docker 至少分配 4GB 内存（Docker Desktop 可在设置中调整）。

### 如何查看容器日志

```bash
# 查看所有服务日志
docker-compose logs

# 查看 Flask 应用日志
docker-compose logs -f web

# 查看 MySQL 日志
docker-compose logs -f db
```

---

## 开发与贡献

### 如何运行测试

```bash
pytest tests/
```

### 代码风格要求

遵循 PEP 8，使用 logging 模块代替 print()。详见 [CONTRIBUTING.md](../CONTRIBUTING.md)。

### 如何添加新的 AI 功能模块

1. 在 app/ 下创建新的 Blueprint 目录
2. 在 app/__init__.py 中注册 Blueprint
3. 在 config/default.py 中添加对应的特性开关
4. 更新 docs/API.md 和 docs/ARCHITECTURE.md

---

## 其他

### 支持哪些浏览器

推荐使用 Chrome、Firefox、Edge 最新版本。Safari 基本功能可用，但部分 CSS 动画可能存在差异。

### 数据是否会上传到云端

不会。所有 AI 模型推理、图像分析、数据存储均在本地完成。天气服务是唯一需要外网访问的功能，可通过 FEATURE_WEATHER_SERVICE 开关关闭。

### 如何获取技术支持

- 提交 [GitHub Issue](https://github.com/yourname/yunxiangyishang/issues)
- 阅读项目文档：[架构总览](ARCHITECTURE.md) | [API 文档](API.md) | [部署指南](DEPLOY.md)
