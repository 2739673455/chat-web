# 聊天后端系统详细设计文档

## 项目概述

本项目是一个基于 FastAPI 的聊天后端系统，支持用户与大模型进行一对一对话。系统提供用户注册、登录、模型配置、对话管理和实时聊天功能。所有消息历史将被完整保留。

### 核心功能
- 用户注册和登录 (JWT 认证)
- 用户自定义模型配置 (OpenAI 兼容 API)
- 对话管理 (创建、列表、删除，自动生成标题)
- 实时流式聊天 (WebSocket 支持)
- 完整消息历史存储
- API 密钥安全存储和传输

## 技术栈

- **后端框架**: FastAPI (异步支持，自动 API 文档)
- **数据库**: MySQL 8.0+
- **ORM**: SQLAlchemy 2.0+ (异步支持)
- **认证**: JWT (PyJWT)
- **密码哈希**: bcrypt
- **加密**: cryptography (Fernet AES 加密)
- **AI 集成**: OpenAI Python SDK
- **验证**: Pydantic
- **包管理**: uv
- **Python 版本**: 3.12+

## 数据库设计

### 数据库配置
- 字符集: utf8mb4
- 排序规则: utf8mb4_unicode_ci
- 引擎: InnoDB

### 表结构

#### user (用户表)
```sql
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    yn TINYINT DEFAULT 1,
    INDEX idx_username (username),
    INDEX idx_email (email)
);
```

#### model_config (用户模型配置表)
```sql
CREATE TABLE model_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    encrypted_api_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);
```

#### conversation (对话表)
```sql
CREATE TABLE conversation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_created (user_id, created_at DESC)
);
```

#### message (消息表)
```sql
CREATE TABLE message (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    sender ENUM('user', 'ai') NOT NULL,
    content LONGTEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    INDEX idx_conversation_timestamp (conversation_id, timestamp),
    INDEX idx_sender (sender)
);
```

## API 设计

### 认证相关

#### POST /auth/register
注册新用户
- 请求体:
```json
{
  "username": "string (3-50字符)",
  "email": "string (有效邮箱)",
  "password": "string (8-128字符)"
}
```
- 响应: 201 Created
```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### POST /auth/login
用户登录
- 请求体:
```json
{
  "username_or_email": "string",
  "password": "string"
}
```
- 响应: 200 OK
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### GET /auth/me
获取当前用户信息
- 认证: Bearer Token
- 响应: 200 OK
```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "has_config": true
}
```

### 配置管理

#### PUT /auth/config
更新用户模型配置
- 认证: Bearer Token
- 请求体:
```json
{
  "model_url": "string (OpenAI 兼容 API URL)",
  "model_name": "string (模型名称，如 gpt-3.5-turbo)",
  "api_key": "string (API 密钥)"
}
```
- 响应: 200 OK
```json
{
  "message": "配置已更新"
}
```

#### GET /auth/config
获取用户模型配置 (不含 API 密钥)
- 认证: Bearer Token
- 响应: 200 OK
```json
{
  "model_url": "string",
  "model_name": "string",
  "configured_at": "2024-01-01T00:00:00Z"
}
```

### 对话管理

#### POST /conversations
创建新对话
- 认证: Bearer Token
- 请求体: 可选
```json
{
  "title": "string (可选，自定义标题)"
}
```
- 响应: 201 Created
```json
{
  "id": 1,
  "title": "新对话",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### GET /conversations
获取用户对话列表
- 认证: Bearer Token
- 查询参数:
  - limit: int (默认 20, 最大 100)
  - offset: int (默认 0)
- 响应: 200 OK
```json
{
  "conversations": [
    {
      "id": 1,
      "title": "string",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "message_count": 5
    }
  ],
  "total": 10
}
```

#### GET /conversations/{id}
获取对话详情
- 认证: Bearer Token
- 路径参数: id (对话 ID)
- 响应: 200 OK
```json
{
  "id": 1,
  "title": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### DELETE /conversations/{id}
删除对话
- 认证: Bearer Token
- 路径参数: id (对话 ID)
- 响应: 204 No Content

### 聊天功能

#### GET /conversations/{id}/messages
获取对话消息历史
- 认证: Bearer Token
- 路径参数: id (对话 ID)
- 查询参数:
  - limit: int (默认 50, 最大 200)
  - before_id: int (分页用)
- 响应: 200 OK
```json
{
  "messages": [
    {
      "id": 1,
      "sender": "user",
      "content": "你好",
      "timestamp": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "sender": "ai",
      "content": "你好！有什么可以帮助您的吗？",
      "timestamp": "2024-01-01T00:00:01Z"
    }
  ],
  "has_more": false
}
```

#### POST /conversations/{id}/messages
发送消息并获取 AI 回复
- 认证: Bearer Token
- 路径参数: id (对话 ID)
- 请求体:
```json
{
  "content": "string (用户消息内容)"
}
```
- 响应: 200 OK (流式回复通过 WebSocket)

#### WebSocket /ws/conversations/{id}
实时流式聊天
- 认证: URL 查询参数 token
- 消息格式:
  - 发送: `{"type": "message", "content": "用户消息"}`
  - 接收: `{"type": "chunk", "content": "AI回复片段"}`
  - 完成: `{"type": "done"}`
  - 错误: `{"type": "error", "message": "错误信息"}`

## 安全设计

### API 密钥管理
- **加密存储**: 使用 Fernet 对称加密
- **密钥来源**: 环境变量 `ENCRYPTION_KEY` (32字节 base64 编码)
- **传输安全**: HTTPS + JWT 认证
- **使用策略**: 临时解密，仅在 API 调用时

### 认证安全
- **JWT 配置**:
  - 算法: HS256
  - 过期时间: 1小时 (access token)
  - 刷新机制: 支持 refresh token (可选扩展)
- **密码策略**: bcrypt 哈希，盐值自动生成
- **会话管理**: 无状态，token 黑名单机制 (可选)

### 输入验证
- **Pydantic 模型**: 所有输入自动验证
- **SQL 注入防护**: SQLAlchemy 参数化查询
- **XSS 防护**: 内容转义 (前端负责)
- **速率限制**: 每分钟 60 次请求 (全局)

### 其他安全措施
- **CORS**: 配置允许的前端域名
- **HTTPS 强制**: 生产环境必须启用
- **日志记录**: 敏感操作审计日志
- **数据备份**: 定期数据库备份

## 项目结构

```
web/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   ├── encryption.py           # 加密工具
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── config.py
│   │   ├── conversation.py
│   │   └── message.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── config.py
│   │   ├── conversation.py
│   │   └── message.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── conversations.py
│   │   └── chat.py
│   ├── dependencies/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── database.py
│   │   └── user.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py       # AI 集成服务
│   │   └── conversation_service.py
│   └── utils/
│       ├── __init__.py
│       ├── security.py
│       └── websocket.py
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_conversations.py
│   ├── test_chat.py
│   └── conftest.py
├── .env.example
├── pyproject.toml
├── README.md
└── Dockerfile
```

## 依赖管理

### pyproject.toml 配置
```toml
[project]
name = "chat-backend"
version = "1.0.0"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.0",
    "pymysql>=1.1.0",
    "cryptography>=41.0.0",
    "openai>=1.3.0",
    "pyjwt>=2.8.0",
    "bcrypt>=4.1.0",
    "python-multipart>=0.0.6",
    "python-dotenv>=1.0.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0"
]
```

## 环境配置

### .env 文件
```env
# 数据库配置
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/chat_db

# JWT 配置
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# 加密配置
ENCRYPTION_KEY=your-32-byte-base64-encoded-key

# OpenAI 默认配置 (可选)
DEFAULT_MODEL_URL=https://api.openai.com/v1
DEFAULT_MODEL_NAME=gpt-3.5-turbo

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

## 部署配置

### Docker 配置
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen --no-install-project

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 生产部署注意事项
- 使用反向代理 (Nginx)
- 配置 SSL 证书
- 设置数据库连接池
- 监控日志和性能
- 定期备份数据
- 配置防火墙

## 开发指南

### 本地开发设置
1. 安装 uv: `pip install uv`
2. 克隆项目: `git clone <repo>`
3. 安装依赖: `uv sync`
4. 配置环境变量: `cp .env.example .env`
5. 启动服务器: `uv run uvicorn app.main:app --reload`

### 测试运行
```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_auth.py

# 带覆盖率
uv run pytest --cov=app --cov-report=html
```

### API 文档访问
启动服务器后，访问 `http://localhost:8000/docs` 查看自动生成的 API 文档。

## 扩展计划

### 未来功能
- 消息搜索功能
- 对话导出/导入
- 多模型支持切换
- 用户头像和资料管理
- 消息编辑和删除
- 对话分享功能
- 管理员面板

### 性能优化
- 数据库索引优化
- Redis 缓存层
- 消息分页优化
- 连接池配置
- 异步任务队列

这个文档提供了完整的开发指南。请按照实施步骤逐步实现，确保每个模块都经过充分测试。