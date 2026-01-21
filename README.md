# 聊天后端系统
## 功能
### 用户管理 [user](app/routers/api/v1/user.py)
1. 注册 `POST /user/register`
   - 请求体
      - 邮箱
      - 用户名
      - 密码
   1. 数据库中添加用户
   2. 自动登录，返回刷新令牌和访问令牌
2. 登录 `POST /user/login`
   - 请求体
      - 邮箱
      - 密码
   1. 返回刷新令牌和访问令牌
3. 获取个人信息 `GET /user/me`
   - 请求头
      - 访问令牌
   1. 返回用户名、邮箱、密码
4. 修改用户名 `POST /user/me/username`
   - 请求头
      - 访问令牌  
   - 请求体
      - 新用户名
   1. 修改用户名
5. 修改邮箱 `POST /user/me/email`
   - 请求头
      - 访问令牌
   - 请求体
      - 新邮箱
   1. 修改邮箱
6. 修改密码 `POST /user/me/password`
   - 请求头
      - 刷新令牌
   - 请求体
      - 新密码
   1. 修改密码
   2. 撤销刷新令牌
   3. 返回新的刷新令牌和访问令牌
7. 登出 `POST /user/logout`
   - 请求头
      - 刷新令牌
   1. 撤销刷新令牌
### 模型配置管理 [model_config](app/routers/api/v1/model_config.py)
1. 获取模型配置 `GET /model_config`
   - 请求头
     - 访问令牌
   1. 返回用户模型配置列表
2. 检查是否能创建新的模型配置 `POST /model_config/can_create`
   - 请求头
     - 访问令牌
   - 请求体
     - 模型配置数量
   1. 返回能否创建
3. 创建模型配置 `POST /model_config/create`
   - 请求头
     - 访问令牌
   - 请求体
     - 配置名称
     - 模型 url
     - 模型名称
     - 模型 API Key
     - 其他配置参数
   1. 创建模型配置
   2. 返回模型配置信息
4. 更新模型配置 `POST /model_config/update`
   - 请求头
     - 访问令牌
   - 请求体
     - 配置 ID
     - 配置名称
     - 模型 url
     - 模型名称
     - 模型 API Key
     - 其他配置参数
   1. 更新模型配置
5. 批量删除模型配置 `POST /model_config/delete`
   - 请求头
     - 访问令牌
   - 请求体
     - 配置 ID 列表
   1. 删除模型配置
### 对话管理 [conversation](app/routers/api/v1/conversation.py)
1. 获取对话 `GET /conversation`
   - 请求头
     - 访问令牌
   1. 返回用户对话列表
2. 创建对话 `POST /conversation/create`
   - 请求头
     - 访问令牌
   - 请求体
     - 模型配置 ID
   1. 创建对话，返回对话 ID
3. 生成对话标题 `POST /conversation/generate_title`
   - 请求头
     -  访问令牌
   - 请求体
     - 对话 ID
     - 消息 (图片url为预签名上传url)
     - 模型 url
     - 模型名称
     - 模型 API Key
     - 其他配置参数
   1. 处理消息中的预签名上传url为预签名下载url
   2. 调用模型生成标题
   3. 更新数据库中的对话标题
   4. 返回对话标题
4. 删除对话 `POST /conversation/delete`
   - 请求头
     - 访问令牌
   - 请求体
     - 对话 ID 列表
   1. 删除对话
### 聊天功能  [chat](app/routers/api/v1/chat.py)
1. 获取预签名上传url `POST /chat/get_upload_presigned_url`
   - 请求头
     - 访问令牌
   - 请求体
     - 对话 ID
     - 文件后缀名列表
   1. 使用用户ID、对话ID、文件后缀名生成cos_key
   2. 使用cos_key生成预签名上传url，返回相应数量的url
2. 获取消息记录 `GET /chat/{id}`
   - 请求头
     - 访问令牌
   - 请求体
     - 对话 ID
   1. 获取消息记录
   2. 处理消息中的cos_key为预签名下载url
   3. 返回消息记录
3. 发送消息并获取AI流式回复 `POST /chat/send`
   - 请求头
     - 访问令牌
   - 请求体
     - 对话 ID
     - 消息
     - 模型 url
     - 模型名称
     - 模型 API Key
     - 其他配置参数
   1. 处理消息中的图片url为cos_url
   2. 用户消息存入数据库
   3. 处理消息中的cos_url为预签名下载url
   4. 流式返回AI回复
   5. 生成完毕后，AI回复存入数据库
   6. 返回用户消息ID和AI回复消息ID

## 图片存储
腾讯云COS: https://console.cloud.tencent.com/cos  
使用主用户;或者创建子用户并绑定权限 `QcloudCOSFullAccess`  
Python SDK: https://cloud.tencent.com/document/product/436/12269  
使用时需要用到子用户的 `secret_id` 和 `secret_key`，以及主用户的 `APPID`  
图片的key格式为 `user_id/conversation_id/images/xxx.jpg`  
暂时只支持用户发送图片，不支持模型发送图片

## 关键流程
### 创建新模型配置时
1. 用户点击创建新模型配置
2. 前端请求检查是否能创建新模型配置
3. 后端从访问令牌中获取权限范围，检查是否有权限创建新模型配置
4. 后端返回是否有权限
5. 前端根据返回结果创建新模型配置或提醒无权创建新配置
### 新建对话时
1. 用户通过新对话发送消息
2. 前端请求生成新对话
3. 后端返回对话ID
4. 前端根据消息中的图片，请求预签名上传url(带有用户ID和对话ID)
5. 后端生成cos_key和预签名上传url，返回前端
6. 前端通过预签名上传url上传图片
7. 前端同时请求生成对话标题和获取AI回复
8. 后端接收消息，从消息中的预签名上传url中提取出cos_key，生成预签名下载url，输入模型
9. 后端返回对话标题和AI回复
### 聊天时
1. 用户上传图片
2. 前端根据消息中的图片，请求预签名上传url
3. 后端生成cos_key和预签名上传url，返回前端
4. 前端通过预签名上传url上传图片
5. 前端将消息列表发给后端，请求AI回复
6. 后端接收消息，从消息中的预签名上传url中提取出cos_key ，替换为预签名下载url，输入模型
7. 后端返回AI回复
### 加载消息历史时
1. 加载历史消息时，后端将消息中的cos_key替换为预签名下载url，发给前端
2. 前端获取消息，用预签名下载url下载图片

## 📝 日志系统设计文档

### 设计目标

为系统添加请求追踪日志功能，实现：
- **request_id**: 唯一请求标识
- **trace_id**: 分布式追踪标识
- **client_ip / user_agent**: 客户端信息
- **method / path**: 请求信息
- **status_code / response_time_ms**: 响应信息

### 核心设计

**一个中间件 + 一个上下文工具**，简单但完整。

### 1. 日志中间件 (`app/middleware/logging.py`)

```python
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.log import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    """极简日志中间件 - 一个中间件搞定所有需求"""
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. 生成请求标识
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        trace_id = request.headers.get("X-Trace-ID", request_id)
        
        # 2. 采集基本信息
        ctx = {
            "request_id": request_id,
            "trace_id": trace_id,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", "")[:200],
            "method": request.method,
            "path": request.url.path,
        }
        
        # 3. 记录开始
        logger.info(f"Incoming: {request.method} {request.url.path}", **ctx)
        
        # 4. 执行请求
        start_time = time.time()
        try:
            response = await call_next(request)
            status_code = response.status_code
            error = None
        except Exception as e:
            status_code = 500
            error = str(e)
            raise
        finally:
            # 5. 记录完成
            response_time = (time.time() - start_time) * 1000
            log_ctx = {**ctx, "status_code": status_code, "response_time_ms": round(response_time, 2)}
            
            if error:
                logger.error(f"Request failed: {request.method} {request.url.path}", error=error, **log_ctx)
            else:
                logger.info(f"Request completed: {request.method} {request.url.path}", **log_ctx)
        
        # 6. 添加标识到响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
```

### 2. 上下文工具 (`app/utils/context.py`)

```python
from contextvars import ContextVar
from typing import Optional, Dict, Any

_request_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar("request_context")

def set_context(ctx: Dict[str, Any]) -> None:
    """设置请求上下文"""
    _request_context.set(ctx)

def get_context() -> Optional[Dict[str, Any]]:
    """获取当前请求上下文"""
    return _request_context.get()

def get_trace_info() -> Dict[str, str]:
    """获取追踪信息"""
    ctx = get_context()
    if ctx:
        return {"request_id": ctx.get("request_id", ""), "trace_id": ctx.get("trace_id", "")}
    return {"request_id": "", "trace_id": ""}

def log_context(message: str, level: str = "info", **extra) -> None:
    """带上下文的日志记录 - 一行代码搞定
    
    使用示例:
        from app.utils.context import log_context
        log_context("用户操作", user_id="123")
    """
    from app.utils.log import logger
    
    ctx = get_context()
    log_data = extra.copy()
    
    if ctx:
        log_data.update({"request_id": ctx.get("request_id", ""), "trace_id": ctx.get("trace_id", "")})
    
    getattr(logger, level)(message, **log_data)
```

### 3. 日志配置 (`app/utils/log.py`)

```python
from loguru import logger
import sys
from pathlib import Path

LOG_DIR = Path("app/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging():
    """配置日志系统"""
    
    # JSON 格式日志
    logger.add(
        LOG_DIR / "app.log",
        rotation="10 MB",
        retention="10 days",
        compression="gz",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        serialize=True,
    )
    
    # 错误日志
    logger.add(
        LOG_DIR / "error.log",
        rotation="10 MB",
        retention="30 days",
        compression="gz",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        serialize=True,
        backtrace=True,
    )
    
    # 控制台输出（开发环境）
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
    )
    
    return logger

logger = setup_logging()
```

### 4. 主应用集成 (`app/main.py`)

```python
from fastapi import FastAPI
from app.middleware.logging import LoggingMiddleware
from app.utils.log import logger

app = FastAPI()

# 添加日志中间件（就一行）
app.add_middleware(LoggingMiddleware)

@app.on_event("startup")
async def startup():
    logger.info("Application started")
```

### 5. 使用示例

```python
from app.utils.context import log_context, get_trace_info

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    # 一行代码记录日志，自动包含 request_id, trace_id
    log_context(f"Fetching user {user_id}", user_id=user_id)
    
    # 或者获取追踪信息
    trace = get_trace_info()
    print(f"当前请求: {trace}")
    
    return {"user_id": user_id}
```

### 6. 文件结构

```
app/
├── middleware/
│   └── logging.py              # 1个文件：中间件
├── utils/
│   ├── log.py                  # 日志配置
│   └── context.py              # 1个文件：上下文工具
└── main.py                     # 集成

app/logs/
├── app.log
└── error.log
```

### 7. 日志输出示例

```json
{
  "timestamp": "2026-01-21 15:30:00",
  "level": "INFO",
  "message": "Request completed: GET /api/users",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "method": "GET",
  "path": "/api/users",
  "status_code": 200,
  "response_time_ms": 45.23
}
```

### 8. 实施步骤

1. 创建目录：`mkdir -p app/middleware app/logs`
2. 创建 `app/middleware/logging.py`
3. 创建 `app/utils/context.py`
4. 更新 `app/utils/log.py`
5. 集成到 `app/main.py`

### 10. 总结

极简方案保留了所有需要的上下文信息：
- ✅ request_id / trace_id
- ✅ client_ip / user_agent
- ✅ method / path
- ✅ status_code / response_time_ms

代码量减少 70%，复杂度大幅降低。所有日志写入 `app/logs/` 目录。