from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.chat import Conversation, Message
from app.exceptions.conversation import ConversationNotFoundError
from app.utils.call_model import call_model


async def get_conversations(
    db_session: AsyncSession, user_id: int
) -> Sequence[Conversation]:
    """获取对话列表"""
    stmt = select(Conversation).where(Conversation.user_id == user_id)
    result = await db_session.execute(stmt)
    return result.scalars().all()


async def create_conversation(
    db_session: AsyncSession, user_id: int, model_config_id: int
):
    """创建对话"""
    conversation = Conversation(user_id=user_id, model_config_id=model_config_id)
    db_session.add(conversation)
    try:
        await db_session.commit()
        await db_session.refresh(conversation)
    except Exception:
        await db_session.rollback()
        raise
    return conversation


async def generate_title(
    content: str | list[dict],
    base_url: str,
    model_name: str | None,
    api_key: str | None,
):
    """生成对话标题"""
    return await call_model(
        [
            {
                "role": "system",
                "content": "你需要为下面的用户提问生成一句简短的概括性标题，字数尽量在20字以内，不要带有句号",
            },
            {"role": "user", "content": content},
        ],
        base_url,
        model_name,
        api_key,
        None,
    )


async def update_conversation_title(
    db_session: AsyncSession, conversation_id: int, title: str
) -> Conversation:
    """更新对话标题"""
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db_session.execute(stmt)
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise ConversationNotFoundError
    conversation.title = title
    try:
        await db_session.commit()
        await db_session.refresh(conversation)
    except Exception:
        await db_session.rollback()
        raise
    return conversation


async def update_conversation_model_config(
    db_session: AsyncSession, conversation_id: int, model_config_id: int
) -> Conversation:
    """更新对话的模型配置"""
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db_session.execute(stmt)
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise ConversationNotFoundError
    conversation.model_config_id = model_config_id
    try:
        await db_session.commit()
        await db_session.refresh(conversation)
    except Exception:
        await db_session.rollback()
        raise
    return conversation


async def delete_conversations(db_session: AsyncSession, ids: list[int]) -> None:
    """批量删除对话"""
    stmt = select(Conversation).where(Conversation.id.in_(ids))
    result = await db_session.execute(stmt)
    conversations = result.scalars().all()
    if not conversations:
        raise ConversationNotFoundError

    # 删除关联的消息
    await db_session.execute(delete(Message).where(Message.conversation_id.in_(ids)))

    # 删除对话
    for conversation in conversations:
        await db_session.delete(conversation)

    try:
        await db_session.commit()
    except Exception:
        await db_session.rollback()
        raise
