# Architecture Overview | 架构总览

## System Diagram | 系统架构图

`
┌──────────────────────────────────────────────────────────┐
│                    Browser / Client                       │
└─────────────────────┬────────────────────────────────────┘
                      │ HTTP
┌─────────────────────▼────────────────────────────────────┐
│                  Flask Application                         │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌─────────────┐ │
│  │  Auth   │ │ Wardrobe │ │  Search   │ │ Recommender │ │
│  │  auth/  │ │ wardrobe/│ │  search/  │ │ recommend/  │ │
│  └────┬────┘ └────┬─────┘ └─────┬─────┘ └──────┬──────┘ │
│       │           │             │               │         │
│  ┌────▼───────────▼─────────────▼───────────────▼──────┐  │
│  │              AI Service Layer (services/)            │  │
│  │  CLIP · BLIP · MobileNetV2 · Style Classifier       │  │
│  └────────────────────────┬────────────────────────────┘  │
│                           │                                │
│  ┌────────────────────────▼────────────────────────────┐  │
│  │              SQLAlchemy ORM (models.py)              │  │
│  └────────────────────────┬────────────────────────────┘  │
└───────────────────────────┼────────────────────────────────┘
                      │ PyMySQL
┌─────────────────────▼────────────────────────────────────┐
│                   MySQL 8.0                               │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│              Ollama Sidecar (optional)                    │
│     Local LLM for fashion advisor chatbot                │
└──────────────────────────────────────────────────────────┘
`

## Module Responsibilities | 模块职责

| Module | Path | Responsibility |
|:-------|:-----|:---------------|
| **Auth** | pp/auth/ | User registration, login, logout, password reset |
| **Main** | pp/main/ | Homepage, account settings |
| **Wardrobe** | pp/wardrobe/ | Clothing item CRUD, batch import, deduplication |
| **Search** | pp/search/ | Text search, image-based similarity search |
| **Recommendation** | pp/recommendation/ | AI outfit recommendation with weather integration |
| **Style Analysis** | pp/style_analysis/ | Personal style profiling and distribution report |
| **Fashion Advisor** | pp/fashion_advisor/ | LLM-powered chatbot (Ollama) |
| **Analytics** | pp/analytics/ | Event tracking and logging |
| **AI Services** | pp/services/ | Shared CLIP, BLIP, and feature extraction logic |
| **Models** | pp/models/ | Local model weights (git-ignored) |

## Data Flow | 数据流

1. **Upload**: User uploads a clothing image → saved with UUID name
2. **Tagging**: CLIP extracts features → auto-generates color, style, type tags
3. **Profile**: Style classifier aggregates tags → builds personal style vector
4. **Recommend**: Combines style vector + weather + similarity → returns outfit set
5. **Search**: MobileNetV2 encodes query image → cosine similarity against wardrobe vectors

## Configuration | 配置

All configuration is managed through environment variables (.env file) and feature flags
in config/default.py. See .env.example for the full list.

## Deployment | 部署

See [DEPLOY.md](DEPLOY.md) for detailed deployment instructions including Docker Compose.