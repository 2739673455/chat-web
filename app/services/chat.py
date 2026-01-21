import asyncio
import json
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.chat import Message
from app.schemas.chat import MessageItem
from app.utils.cos import extract_cos_key, get_get_presigned_url


async def get_messages(
    session: AsyncSession, conversation_id: int
) -> Sequence[Message]:
    """获取消息列表"""
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.asc())
    )
    result = await session.execute(stmt)
    messages = result.scalars().all()
    for message in messages:  # 将json字符串转换为str或list[dict]
        message.content = json.loads(message.content)
    return messages


async def image_url_to_get_presigned_url(messages: Sequence[Message | MessageItem]):
    """处理消息中的 cos_url 或 旧的预签名url 为 新的为预签名下载url"""
    tasks = []
    for message in messages:
        if message.role == "user" and isinstance(message.content, list):
            for c_dict in message.content:
                if "image_url" in c_dict:
                    # 提取cos_key
                    cos_key = extract_cos_key(c_dict["image_url"])
                    # 获取预签名下载url
                    tasks.append((c_dict, get_get_presigned_url(cos_key)))
    if tasks:
        results = await asyncio.gather(*tasks)
        for (c_dict, _), presinged_url in zip(tasks, results):
            c_dict["image_url"] = presinged_url


async def image_url_to_cos_url(messages: Sequence[MessageItem]):
    """处理消息中的图片url 为 cos_url"""
    for message in messages:
        if isinstance(message.content, list):
            for c_dict in message.content:
                if "image_url" in c_dict:
                    # 提取cos_key
                    cos_key = extract_cos_key(c_dict["image_url"])
                    c_dict["image_url"] = "cos://" + cos_key


async def save_message_in_db(
    session: AsyncSession,
    last_message: MessageItem,
    user_id: int,
    conversation_id: int,
) -> Message:
    """保存消息到数据库"""
    message = Message(
        user_id=user_id,
        conversation_id=conversation_id,
        role=last_message.role,
        content=json.dumps(last_message.content),  # 将str或list[dict]转换为json字符串
    )
    session.add(message)
    try:
        await session.commit()
        await session.refresh(message)
    except Exception:
        await session.rollback()
        raise
    return message
