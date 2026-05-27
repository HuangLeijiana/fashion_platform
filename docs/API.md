# API 文档 | API Reference

云想衣裳提供 RESTful JSON API，供前端页面调用和第三方集成使用。

所有 API 均以 `/api/` 或模块前缀开头，响应格式统一为 JSON。

---

## 通用约定

### 响应格式

所有接口返回 JSON，统一包含 `success` 字段：

```json
{
  "success": true,
  ...
}
```

失败时包含 `error` 或 `message` 字段：

```json
{
  "success": false,
  "error": "错误描述"
}
```

### 认证

标注为 **需要登录** 的接口，需要先登录获取 Session Cookie。未登录访问将返回：

```json
{
  "success": false,
  "error": "需要登录",
  "redirect": "/auth/login"
}
```

HTTP 状态码：`401`

### 文件上传

文件上传接口使用 `multipart/form-data`，支持以下图片格式：

- `png`、`jpg`、`jpeg`、`gif`、`webp`
- 单文件最大 16MB

### HTTP 状态码

| 状态码 | 含义 |
|:-------|:-----|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未登录 |
| 403 | 权限不足或功能已关闭 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务暂不可用（如模型未加载） |

---

## 认证模块

### POST /auth/register

注册新用户，支持表单和 JSON 两种请求方式。

**请求参数��JSON）：**

| 字段 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| username | string | 是 | 用户名，不可重复 |
| email | string | 是 | 邮箱地址，不可重复 |
| password | string | 是 | 密码，至少 6 位 |
| confirm_password | string | 否 | 确认密码，不传时默认与 password 一致 |

**请求示例：**

```json
{
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "password": "mypassword123",
  "confirm_password": "mypassword123"
}
```

**成功响应（201）：**

```json
{
  "message": "注册成功",
  "user": {
    "id": 2,
    "email": "zhangsan@example.com",
    "username": "zhangsan"
  }
}
```

### POST /auth/login

登录并创建会话（表单提交，返回页面重定向）。

### POST /auth/api/logout

退出登录。**需要登录。**

**成功响应（200）：**

```json
{
  "message": "退出登录成功"
}
```

### POST /auth/reset_password_request

请求重置密码，发送重置邮件到注册邮箱（表单提交）。

### GET /auth/me

获取当前登录用户信息。**需要登录。**

**成功响应（200）：**

```json
{
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "username": "admin",
    "permissions": []
  }
}
```

---

## 推荐模块

### POST /recommendation/upload

上传衣物图片并自动分析属性。

**请求格式：** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| cloth_image | file | 是 | 衣物图片文件 |
| username | string | 否 | 用户标识，默认 `unknown_user` |
| style | string | 否 | 风格偏好 |

**成功响应（200）：**

```json
{
  "success": true,
  "image_url": "/static/uploads/20250401120000_photo.jpg",
  "local_path": "/abs/path/to/uploads/20250401120000_photo.jpg",
  "filename": "20250401120000_photo.jpg",
  "description": "经典黑色外套，简约风设计，适合日常穿搭",
  "color": "黑色",
  "style_tag": "简约风",
  "cloth_type": "外套"
}
```

### POST /recommendation/ai_recommend

获取 AI 穿搭推荐。**需要登录。**

**请求参数（JSON）：**

| 字段 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| local_path | string | 是 | 上传图片的本地路径 |
| city | string | 否 | 城市名称，用于获取天气 |
| include_wardrobe | boolean | 否 | 是否包含衣柜单品参与推荐 |
| user_profile | object | 否 | 用户画像信息（身高、体重等） |

**请求示例：**

```json
{
  "local_path": "/abs/path/to/uploads/20250401120000_photo.jpg",
  "city": "北京",
  "include_wardrobe": true,
  "user_profile": {
    "height": 170,
    "weight": 65,
    "body_shape": "矩形",
    "skin_tone": "自然"
  }
}
```

**成功响应（200）：**

```json
{
  "success": true,
  "city": "北京",
  "recommendations": [
    {
      "image_url": "/static/images/products/001.jpg",
      "similarity": 0.8923,
      "color": "黑色",
      "description": "经典黑色T恤，休闲风设计",
      "style_tag": "休闲风",
      "cloth_type": "T恤",
      "weather_suggestion": "适宜温度（22℃，晴朗）T恤厚度适中，适配当前气温",
      "is_wardrobe": false,
      "reason": "【精选推荐】与您上传的图片风格高度契合..."
    }
  ],
  "used_wardrobe": true
}
```

### POST /recommendation/weather

获取指定城市的天气信息和穿搭建议。

**请求参数（JSON）：**

| 字段 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| city | string | 是 | 城市名称 |

**成功响应（200）：**

```json
{
  "success": true,
  "city": "北京",
  "temperature": 22,
  "condition": "晴朗",
  "suggestion": "当前北京晴朗，气温22℃，穿搭可灵活选择"
}
```

### POST /recommendation/import_local

批量导入本地图库图片到推荐候选池。

**请求参数（JSON）：**

| 字段 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| local_dir | string | 否 | 图片目录路径，默认 `images/products` |

**成功响应（200）：**

```json
{
  "success": true,
  "message": "本地图库导入完成，共处理 25 张图片",
  "stats": {
    "总图片数": 25,
    "成功导入数": 20,
    "重复跳过数": 3,
    "导入失败数": 2
  },
  "dest_folder": "static/images/products"
}
```

---

## 衣柜模块

以下接口均 **需要登录**。

### GET /wardrobe/api/items

获取当前用户的所有衣柜物品。

**成功响应（200）：**

```json
{
  "success": true,
  "items": [
    {
      "id": 1,
      "name": "白色衬衫",
      "category": "衬衫",
      "color": "白色",
      "brand": "UNIQLO",
      "season": "春夏",
      "occasion": "日常",
      "image_path": "uploads/20250401_shirt.jpg"
    }
  ],
  "count": 1
}
```

### POST /wardrobe/add

添加衣物到衣柜。

**请求格式：** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| name | string | 是 | 物品名称 |
| category | string | 是 | 分类（衬衫、裤子、外套等） |
| image | file | 否 | 衣物图片 |
| color | string | 否 | 颜色 |
| brand | string | 否 | 品牌 |
| season | string | 否 | 适合季节 |
| occasion | string | 否 | 适合场合 |

### POST /wardrobe/delete/{item_id}

删除衣柜中的物品。

### GET /wardrobe/edit/{item_id}

获取指定物品的详情（JSON）。

### POST /wardrobe/update/{item_id}

更新物品信息（表单提交）。

### GET /wardrobe/search

搜索衣柜物品。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| q | string | 否 | 关键词搜索（名称、品牌） |
| category | string | 否 | 按分类筛选 |
| color | string | 否 | 按颜色筛选 |

### GET /wardrobe/smart_search

智能搜索衣柜物品，支持多字段模糊匹配。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| q | string | 是 | 搜索关键词（匹配名称、品牌、颜色、分类、季节、场合、风格标签） |

### GET /wardrobe/diagnosis

衣柜诊断，分析衣柜构成并给出建议。

**成功响应（200）：**

```json
{
  "success": true,
  "color_distribution": {"白色": 3, "黑色": 2, "蓝色": 1},
  "category_distribution": {"衬衫": 2, "裤子": 2, "外套": 1},
  "style_distribution": {"日常": 4, "正式": 1},
  "diagnosis": [
    "下装数量偏少，建议补充黑色、米色或牛仔基础款。"
  ],
  "outfit_recommendations": [
    {
      "top_name": "白色衬衫",
      "bottom_name": "黑色裤子"
    }
  ]
}
```

### POST /wardrobe/batch_add

批量导入衣物图片。**需要登录。**

**请求格式：** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| images | file[] | 是 | 多个图片文件 |
| category | string | 否 | 默认分类，默认 `未分类` |
| skip_duplicate | string | 否 | 跳过重复图片，默认 `true` |

支持自动去重（基于感知哈希）和自动标注。

---

## 搜索模块

### GET /search/api/wardrobe

搜索衣柜中的物品。**需要登录。**

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| q | string | 否 | 搜索关键词 |
| category | string | 否 | 按分类筛选 |
| page | int | 否 | 页码，默认 1 |
| per_page | int | 否 | 每页数量，默认 50 |

**成功响应（200）：**

```json
{
  "success": true,
  "results": [
    {
      "id": 1,
      "name": "白色衬衫",
      "category": "衬衫",
      "color": "白色",
      "image_url": "/static/uploads/20250401_shirt.jpg"
    }
  ],
  "count": 1
}
```

### POST /search/api/search_by_image

以图搜图，上传图片在商品库中查找相似商品。

**请求格式：** `multipart/form-data`（上传文件）或 JSON（Base64 图片）

**multipart 请求：** 字段名 `image`

**JSON 请求：**

```json
{
  "image_data": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**成功响应（200）：**

```json
{
  "success": true,
  "results": [
    {
      "name": "黑色休闲外套",
      "similarity_score": 0.85,
      "similarity_percent": 85.0,
      "images": ["/static/images/products/001.jpg"]
    }
  ],
  "message": "找到 5 个相似商品"
}
```

### GET /search/api/suggestions

获取搜索建议。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| q | string | 是 | 搜索关键词前缀 |

### 购物车接口

| 接口 | 方法 | 说明 |
|:-----|:-----|:-----|
| /search/api/add_to_cart | POST | 添加商品到购物车 |
| /search/api/update_cart | POST | 更新购物车商品数量 |
| /search/api/remove_from_cart | POST | 移除购物车商品 |
| /search/api/clear_cart | POST | 清空购物车 |
| /search/api/get_cart_count | GET | 获取购物车商品数量 |

购物车请求体均包含 `product_id` 字段，响应包含 `cart_count`（商品总数）和 `total_amount`（总金额）。

### 搜索历史接口

| 接口 | 方法 | 说明 |
|:-----|:-----|:-----|
| /search/api/get_search_history | GET | 获取搜索历史记录 |
| /search/api/clear_search_history | POST | 清除搜索历史 |

---

## 时尚顾问模块

### GET /fashion-advisor/api/health

健康检查，检测 Ollama 服务是否可用。

**成功响应（200）：**

```json
{
  "status": "ok",
  "ollama_connected": true
}
```

### POST /fashion-advisor/api/advice

获取时尚穿搭建议。

**请求参数（JSON）：**

| 字段 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| message | string | 是 | 用户提问内容 |

**请求示例：**

```json
{
  "message": "黑色外套怎么搭配"
}
```

### POST /fashion-advisor/api/reset

重置对话上下文，开始新的对话。

---

## 风格分析模块

以下接口均 **需要登录**。

### POST /style-analysis/analyze

分析单张图片的风格。

**请求格式：** `multipart/form-data`，字段名 `image`

**成功响应（200）：**

```json
{
  "style": "极简风",
  "confidence": 0.87
}
```

支持的风格标签：法式风、复古风、极简风、街头风、甜美风、通勤风。

### POST /style-analysis/generate_profile

根据衣柜中所有单品的特征向量，生成个人风格画像。

**成功响应（200）：**

```json
{
  "success": true,
  "data": {
    "style_distribution": {
      "极简风": 45.0,
      "通勤风": 30.0,
      "街头风": 25.0
    },
    "report": "系统分析了你衣柜中的 12 件有效单品，当前主风格倾向为"极简风"。同时也包含一定比例的"通勤风"元素。该画像可用于后续推荐结果的个性化调整。"
  }
}
```

---

## 埋点模块

### POST /analytics/track

上报用户行为事件。需开启特性开关 `FEATURE_ANALYTICS_EVENTS`。

**请求参数（JSON）：**

| 字段 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| event | string | 否 | 事件名称，默认 `unknown_event` |
| payload | object | 否 | 事件附加数据 |

**成功响应（200）：**

```json
{
  "success": true
}
```

---

## 特性开关

部分 API 受特性开关控制，关闭时返回 `403`：

| 开关名称 | 影响的接口 |
|:---------|:-----------|
| `FEATURE_WARDROBE_RECOMMENDATION` | 推荐模块中的衣柜联动功能 |
| `FEATURE_ANALYTICS_EVENTS` | `POST /analytics/track` |
| `FEATURE_SEARCH_WARDROBE_API` | `GET /search/api/wardrobe` |
| `FEATURE_ADVISOR_DIAGNOSIS` | 时尚顾问诊断功能 |
| `FEATURE_WEATHER_SERVICE` | `POST /recommendation/weather` |

特性开关在 `config/default.py` 中配置。
