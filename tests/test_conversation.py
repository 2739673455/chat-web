from faker import Faker
from sqlalchemy import create_engine, text

from app.config.config import CFG

fake = Faker("zh_CN")


def get_token(client):
    """辅助函数：注册用户并返回 access_token"""
    register_response = client.post(
        "/api/v1/user/register",
        json={
            "email": f"test_{fake.email()}",
            "username": fake.user_name(),
            "password": fake.password(),
        },
    )
    return register_response.json()["access_token"]


def get_atguigu_model_config():
    """从数据库获取 atguigu 用户的测试模型配置"""
    db_url = f"mysql+pymysql://{CFG.db.app.user}:{CFG.db.app.password}@{CFG.db.app.host}:{CFG.db.app.port}/{CFG.db.app.database}"
    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT id, base_url, model_name, encrypted_api_key FROM model_config WHERE user_id = 1 LIMIT 1"
                )
            )
            row = result.fetchone()
            if row:
                return {
                    "id": row[0],
                    "base_url": row[1],
                    "model_name": row[2],
                    "encrypted_api_key": row[3],
                }
            return None
    finally:
        engine.dispose()


def test_get_conversations_empty(client):
    """测试获取空对话列表"""
    token = get_token(client)

    response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversations" in data
    assert data["conversations"] == []


def test_get_conversations_with_data(client):
    """测试获取对话列表（包含数据）"""
    token = get_token(client)

    config = get_atguigu_model_config()
    assert config is not None

    # 创建对话
    content = "你好"
    create_response = client.post(
        "/api/v1/conversation/create",
        json={
            "content": content,
            "model_config_id": config["id"],
            "base_url": config["base_url"],
            "model_name": config["model_name"],
            "encrypted_api_key": config["encrypted_api_key"],
            "params": {"temperature": 0.7},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 201

    # 获取对话列表
    response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["conversations"]) == 1
    assert "id" in data["conversations"][0]
    assert "title" in data["conversations"][0]
    assert "update_at" in data["conversations"][0]


def test_get_conversations_no_token(client):
    """测试获取对话列表时未提供token"""
    response = client.get("/api/v1/conversation")
    assert response.status_code == 401


def test_get_conversations_invalid_token(client):
    """测试获取对话列表时token无效"""
    response = client.get(
        "/api/v1/conversation", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


def test_create_conversation_success(client):
    """测试成功创建对话"""
    token = get_token(client)
    config = get_atguigu_model_config()
    assert config is not None

    content = "你好"
    response = client.post(
        "/api/v1/conversation/create",
        json={
            "content": content,
            "model_config_id": config["id"],
            "base_url": config["base_url"],
            "model_name": config["model_name"],
            "encrypted_api_key": config["encrypted_api_key"],
            "params": {"temperature": 0.7},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "title" in data
    assert "update_at" in data


def test_create_conversation_with_list_content(client):
    """测试创建对话时使用列表格式内容"""
    token = get_token(client)
    config = get_atguigu_model_config()
    assert config is not None

    # 创建对话（使用列表格式内容）
    content = [{"type": "text", "text": "你好"}]
    response = client.post(
        "/api/v1/conversation/create",
        json={
            "content": content,
            "model_config_id": config["id"],
            "base_url": config["base_url"],
            "model_name": config["model_name"],
            "encrypted_api_key": config["encrypted_api_key"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201


def test_create_conversation_no_token(client):
    """测试创建对话时未提供token"""
    response = client.post(
        "/api/v1/conversation/create",
        json={
            "content": "测试内容",
            "model_config_id": 1,
            "base_url": "https://api.openai.com/v1",
        },
    )
    assert response.status_code == 401


def test_create_conversation_invalid_token(client):
    """测试创建对话时token无效"""
    response = client.post(
        "/api/v1/conversation/create",
        json={
            "content": "测试内容",
            "model_config_id": 1,
            "base_url": "https://api.openai.com/v1",
        },
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


def test_delete_conversations_success(client):
    """测试成功批量删除对话"""
    token = get_token(client)
    config = get_atguigu_model_config()
    assert config is not None

    # 创建多个对话
    conversation_ids = []
    for i in range(3):
        create_response = client.post(
            "/api/v1/conversation/create",
            json={
                "content": "你好",
                "model_config_id": config["id"],
                "base_url": config["base_url"],
                "model_name": config["model_name"],
                "encrypted_api_key": config["encrypted_api_key"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_response.status_code == 201
        conversation_ids.append(create_response.json()["id"])

    # 批量删除对话
    response = client.post(
        "/api/v1/conversation/delete",
        json={"ids": conversation_ids},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    # 验证已删除
    final_response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    assert final_response.json()["conversations"] == []


def test_delete_conversations_single(client):
    """测试删除单个对话"""
    token = get_token(client)
    config = get_atguigu_model_config()
    assert config is not None

    # 创建对话
    create_response = client.post(
        "/api/v1/conversation/create",
        json={
            "content": "你好",
            "model_config_id": config["id"],
            "base_url": config["base_url"],
            "model_name": config["model_name"],
            "encrypted_api_key": config["encrypted_api_key"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 201
    conversation_id = create_response.json()["id"]

    # 删除单个对话
    response = client.post(
        "/api/v1/conversation/delete",
        json={"ids": [conversation_id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


def test_delete_conversations_not_found(client):
    """测试删除不存在的对话"""
    token = get_token(client)

    response = client.post(
        "/api/v1/conversation/delete",
        json={"ids": [99999]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


def test_delete_conversations_no_token(client):
    """测试删除对话时未提供token"""
    response = client.post(
        "/api/v1/conversation/delete",
        json={"ids": [1]},
    )
    assert response.status_code == 401


def test_delete_conversations_invalid_token(client):
    """测试删除对话时token无效"""
    response = client.post(
        "/api/v1/conversation/delete",
        json={"ids": [1]},
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


def test_conversation_crud_full_flow(client):
    """测试对话的完整CRUD流程"""
    token = get_token(client)
    config = get_atguigu_model_config()
    assert config is not None

    # 1. 初始状态为空列表
    list_response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    assert list_response.status_code == 200
    assert list_response.json()["conversations"] == []

    # 2. 创建对话
    content = "听得到吗?"
    create_response = client.post(
        "/api/v1/conversation/create",
        json={
            "content": content,
            "model_config_id": config["id"],
            "base_url": config["base_url"],
            "model_name": config["model_name"],
            "encrypted_api_key": config["encrypted_api_key"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 201
    conversation_id = create_response.json()["id"]

    # 3. 验证对话已创建
    list_response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    assert list_response.status_code == 200
    conversations = list_response.json()["conversations"]
    assert len(conversations) == 1
    assert conversations[0]["id"] == conversation_id

    # 4. 创建更多对话
    for i in range(2):
        create_response = client.post(
            "/api/v1/conversation/create",
            json={
                "content": "你好",
                "model_config_id": config["id"],
                "base_url": config["base_url"],
                "model_name": config["model_name"],
                "encrypted_api_key": config["encrypted_api_key"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_response.status_code == 201

    # 5. 验证对话数量
    list_response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    assert len(list_response.json()["conversations"]) == 3

    # 6. 删除对话
    delete_response = client.post(
        "/api/v1/conversation/delete",
        json={"ids": [conversation_id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_response.status_code == 204

    # 7. 验证删除后数量
    final_response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    assert len(final_response.json()["conversations"]) == 2
