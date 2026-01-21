import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.config.config import CFG
from app.main import app


@pytest.fixture(scope="session")
def client():
    """Synchronous test client for FastAPI."""
    with TestClient(app) as tc:
        yield tc


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_users():
    """在测试会话结束后清理测试用户数据"""
    yield
    # 获取测试用户的 ID
    auth_db_url = f"mysql+pymysql://{CFG.db.auth.user}:{CFG.db.auth.password}@{CFG.db.auth.host}:{CFG.db.auth.port}/{CFG.db.auth.database}"
    auth_engine = create_engine(auth_db_url)
    with auth_engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM user WHERE email LIKE 'test_%'"))
        user_ids = [row[0] for row in result.fetchall()]

        if user_ids:
            placeholders = ", ".join([f":id_{i}" for i in range(len(user_ids))])
            params = {f"id_{i}": uid for i, uid in enumerate(user_ids)}

            conn.execute(
                text(f"DELETE FROM group_user_rel WHERE user_id IN ({placeholders})"),
                params,
            )
            conn.execute(
                text(f"DELETE FROM refresh_token WHERE user_id IN ({placeholders})"),
                params,
            )
            conn.execute(text("DELETE FROM user WHERE email LIKE 'test_%'"))
            conn.commit()
    auth_engine.dispose()

    # 清理 app 库
    if user_ids:
        app_db_url = f"mysql+pymysql://{CFG.db.app.user}:{CFG.db.app.password}@{CFG.db.app.host}:{CFG.db.app.port}/{CFG.db.app.database}"
        app_engine = create_engine(app_db_url)
        with app_engine.connect() as conn:
            placeholders = ", ".join([f":id_{i}" for i in range(len(user_ids))])
            params = {f"id_{i}": uid for i, uid in enumerate(user_ids)}

            conn.execute(
                text(
                    f"DELETE FROM message WHERE conversation_id IN (SELECT id FROM conversation WHERE user_id IN ({placeholders}))"
                ),
                params,
            )
            conn.execute(
                text(f"DELETE FROM conversation WHERE user_id IN ({placeholders})"),
                params,
            )
            conn.execute(
                text(f"DELETE FROM model_config WHERE user_id IN ({placeholders})"),
                params,
            )
            conn.commit()
        app_engine.dispose()
