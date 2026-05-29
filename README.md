# 云裳衣裳 — AI 时尚推荐平台

基于深度学习的智能时尚穿搭推荐系统，支持图片上传、AI 风格分析、天气感知推荐、知识库 RAG 和衣橱管理。

## 技术栈

| 层 | 技术选型 |
|---|---------|
| **后端框架** | Flask 3.x + Blueprint 模块化 |
| **AI/ML** | CLIP (ViT-B/32) + BLIP + MobileNetV2 |
| **LLM** | LangChain / LangGraph + Ollama / OpenAI API |
| **向量检索** | ChromaDB + sentence-transformers |
| **数据库** | MySQL + SQLAlchemy ORM |
| **异步任务** | Celery + Redis |
| **认证** | Flask-Login + Werkzeug 密码哈希 |

## 项目结构

```
fashion_platform/
├── app/
│   ├── __init__.py              # Flask 工厂函数
│   ├── models.py                # SQLAlchemy 数据模型
│   ├── extensions.py            # Flask 扩展初始化
│   ├── celery_app.py            # Celery 异步任务
│   ├── main/                    # 主页路由
│   ├── auth/                    # 用户认证
│   ├── recommendation/          # 智能推荐引擎
│   ├── search/                  # 商品搜索（文本+图片）
│   ├── wardrobe/                # 衣橱管理
│   ├── fashion_advisor/         # AI 穿搭顾问（Agent+RAG）
│   ├── style_analysis/          # 风格分析
│   ├── analytics/               # 用户行为分析
│   └── services/                # 公共服务层
│       ├── ai_service.py        # CLIP/BLIP 模型服务（单例）
│       ├── weather_service.py   # 天气查询服务
│       ├── vector_store.py      # ChromaDB 向量存储
│       ├── image_utils.py       # 图像工具（颜色提取等）
│       └── llm_observability.py # LLM 调用监控
├── config/
│   └── default.py               # 配置管理（环境变量 + Feature Flags）
├── static/
│   ├── images/products/         # 商品图库
│   └── uploads/                 # 用户上传目录
├── templates/                   # Jinja2 模板
├── tests/                       # 测试
├── logs/                        # 应用日志
├── requirements.txt             # Python 依赖
├── Dockerfile                   # 容器化
└── docker-compose.yml           # 本地开发编排
```

## 核心架构

```
用户上传图片 → CLIP 特征提取 → 向量相似度搜索
                                  ↓
                          候选池（图库+衣橱）
                                  ↓
                  KMeans 颜色分析 + BLIP 描述生成
                                  ↓
              天气 API → 穿搭建议 + 用户画像 → 推荐理由
                                  ↓
              LangGraph Agent → RAG 知识库 → 结构化搭配方案
```

## 快速启动

### 1. 环境要求

- Python 3.10+
- MySQL 8.0+
- Redis（可选，用于 Celery）

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的配置
```

关键环境变量：

| 变量 | 说明 | 示例 |
|------|------|------|
| `SECRET_KEY` | Flask 密钥 | `your-secret-key` |
| `MYSQL_HOST` | MySQL 地址 | `localhost` |
| `MYSQL_PASSWORD` | MySQL 密码 | `your-password` |
| `WEATHER_API_KEY` | 天气 API 密钥 | `your-key` |
| `ADVISOR_LLM_PROVIDER` | LLM 后端 | `ollama` / `openai` |
| `OLLAMA_MODEL` | Ollama 模型名 | `qwen2.5:3b` |

### 4. 启动

```bash
# 开发模式
flask run --debug

# 或使用 Docker
docker compose up -d
```

访问 `http://localhost:5000`。

## Docker 部署

```bash
docker compose up -d
```

服务列表：
- `web`: Flask 应用 (端口 5000)
- `mysql`: MySQL 8.0 (端口 3306)
- `redis`: Redis (端口 6379)

## Feature Flags

在 `.env` 或 `config/default.py` 中控制功能开关：

| Flag | 默认值 | 说明 |
|------|--------|------|
| `FEATURE_WEATHER_SERVICE` | `true` | 天气感知推荐 |
| `FEATURE_ADVISOR_RAG` | `true` | RAG 知识库检索 |
| `FEATURE_ADVISOR_AGENT` | `true` | Agent 编排模式 |
| `FEATURE_ADVISOR_LANGGRAPH` | `false` | LangGraph 工作流 |
| `FEATURE_ASYNC_INDEXING` | `false` | Celery 异步索引 |

## 运行测试

```bash
pytest tests/ -v
```

## License

MIT
