from datetime import datetime

from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    model_config_id: int = Field(..., description="模型配置ID")


class UpdateConversationRequest(BaseModel):
    conversation_id: int = Field(..., description="对话ID")
    model_config_id: int = Field(..., description="模型配置ID")


class DeleteConversationRequest(BaseModel):
    ids: list[int] = Field(..., description="对话ID列表")


class ConversationResponse(BaseModel):
    conversation_id: int
    title: str | None
    update_at: datetime
    model_config_id: int | None


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
