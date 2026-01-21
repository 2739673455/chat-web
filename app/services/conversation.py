from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.chat import Conversation
from app.exceptions.conversation import ConversationNotFoundError
from app.utils.call_model import call_model


async def get_conversations(
    session: AsyncSession, user_id: int
) -> Sequence[Conversation]:
    """获取对话列表"""
    stmt = select(Conversation).where(Conversation.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def create_conversation(
    session: AsyncSession, user_id: int, model_config_id: int
):
    """创建对话"""
    conversation = Conversation(user_id=user_id, model_config_id=model_config_id)
    session.add(conversation)
    try:
        await session.commit()
        await session.refresh(conversation)
    except Exception:
        await session.rollback()
        raise
    return conversation


async def generate_title(
    content: str | list[dict],
    base_url: str,
    model_name: str | None,
    encrypted_api_key: str | None,
):
    """生成对话标题"""
    return await call_model(
        [
            {"role": "system", "content": "为下面的对话生成简短标题"},
            {"role": "user", "content": content},
        ],
        base_url,
        model_name,
        encrypted_api_key,
        None,
    )


async def update_conversation_title(
    session: AsyncSession, conversation_id: int, title: str
) -> Conversation:
    """更新对话标题"""
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await session.execute(stmt)
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise ConversationNotFoundError
    conversation.title = title
    try:
        await session.commit()
        await session.refresh(conversation)
    except Exception:
        await session.rollback()
        raise
    return conversation


async def delete_conversations(session: AsyncSession, ids: list[int]) -> None:
    """批量删除对话"""
    stmt = select(Conversation).where(Conversation.id.in_(ids))
    result = await session.execute(stmt)
    conversations = result.scalars().all()
    if not conversations:
        raise ConversationNotFoundError
    for conversation in conversations:
        await session.delete(conversation)
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise
