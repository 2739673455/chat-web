from datetime import datetime

from pydantic import BaseModel, Field


class MessageItem(BaseModel):
    message_id: int | None = Field(default=None, description="消息ID")
    role: str = Field(..., description="发送者 (user/assistant)")
    content: str | list[dict] = Field(..., description="消息内容")
    timestamp: datetime | None = Field(default=None, description="发送时间")


class GetUploadPresignedUrlRequest(BaseModel):
    conversation_id: int
    suffixes: list[str]


class SendMessageRequest(BaseModel):
    conversation_id: int = Field(..., description="对话ID")
    messages: list[MessageItem] = Field(..., description="消息列表")
    base_url: str = Field(..., description="OpenAI 兼容 API URL")
    model_name: str | None = Field(None, description="模型名称")
    encrypted_api_key: str | None = Field(None, description="API 密钥")
    params: dict | None = Field(None, description="配置参数")


class GetUploadPresignedUrlResponse(BaseModel):
    urls: list[str]


class MessageListResponse(BaseModel):
    messages: list[MessageItem]
