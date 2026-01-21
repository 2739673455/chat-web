from collections.abc import Sequence

from faker import Faker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.chat import ModelConfig
from app.exceptions.model_config import ModelConfigNotFoundError

faker = Faker()


async def get_model_configs(
    session: AsyncSession, user_id: int
) -> Sequence[ModelConfig]:
    """获取模型配置列表"""
    stmt = select(ModelConfig).where(ModelConfig.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_model_config(
    session: AsyncSession, user_id: int, model_config_id: int
) -> ModelConfig:
    """获取模型配置"""
    stmt = select(ModelConfig).where(
        ModelConfig.id == model_config_id, ModelConfig.user_id == user_id
    )
    result = await session.execute(stmt)
    model_config = result.scalar_one_or_none()
    if not model_config:
        raise ModelConfigNotFoundError
    return model_config


async def create_model_config(
    session: AsyncSession,
    user_id: int,
    name: str | None,
    base_url: str,
    model_name: str | None,
    encrypted_api_key: str | None,
    params: dict | None,
) -> ModelConfig:
    """创建模型配置"""
    model_config = ModelConfig(
        name=name or model_name or faker.word(),
        base_url=base_url,
        model_name=model_name,
        encrypted_api_key=encrypted_api_key,
        params=params,
        user_id=user_id,
    )
    session.add(model_config)
    try:
        await session.commit()
        await session.refresh(model_config)
    except Exception:
        await session.rollback()
        raise
    return model_config


async def update_model_config(
    session: AsyncSession,
    id: int,
    name: str,
    base_url: str,
    model_name: str | None,
    encrypted_api_key: str | None,
    params: dict | None,
) -> None:
    """更新模型配置"""
    stmt = select(ModelConfig).where(ModelConfig.id == id)
    result = await session.execute(stmt)
    model_config = result.scalar_one_or_none()
    if not model_config:
        raise ModelConfigNotFoundError
    model_config.name = name
    model_config.base_url = base_url
    model_config.model_name = model_name
    model_config.encrypted_api_key = encrypted_api_key
    model_config.params = params
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise


async def delete_model_configs(session: AsyncSession, ids: list[int]) -> None:
    """批量删除模型配置"""
    stmt = select(ModelConfig).where(ModelConfig.id.in_(ids))
    result = await session.execute(stmt)
    model_configs = result.scalars().all()
    if not model_configs:
        raise ModelConfigNotFoundError
    for model_config in model_configs:
        await session.delete(model_config)
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise
