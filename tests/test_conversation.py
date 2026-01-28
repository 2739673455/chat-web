from conftest import (
    TEST_MODEL_CONFIG,
    create_conversation,
    create_model_config,
    create_test_model_config,
    get_token,
)


def test_get_conversations_empty(client):
    """测试获取空对话列表"""
    token = get_token(client)

    response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["conversations"] == []


def test_get_conversations_with_data(client):
    """测试获取对话列表（包含数据）"""
    token = get_token(client)

    # 创建模型配置和对话
    model_config_id = create_model_config(
        client,
        token,
        name="test_config",
        base_url="https://api.openai.com/v1",
        model_name="gpt-4",
        api_key="sk-test",
    )
    conversation_id = create_conversation(client, token, model_config_id)

    # 获取对话列表
    response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["conversations"]) == 1
    assert data["conversations"][0]["conversation_id"] == conversation_id


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
    model_config_id = create_model_config(client, token)

    response = client.post(
        "/api/v1/conversation/create",
        json={"model_config_id": model_config_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "conversation_id" in data
    assert data["title"] is None


def test_create_conversation_no_token(client):
    """测试创建对话时未提供token"""
    response = client.post(
        "/api/v1/conversation/create",
        json={"model_config_id": 1},
    )
    assert response.status_code == 401


def test_create_conversation_invalid_token(client):
    """测试创建对话时token无效"""
    response = client.post(
        "/api/v1/conversation/create",
        json={"model_config_id": 1},
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


def test_create_conversation_multiple(client):
    """测试创建多个对话"""
    token = get_token(client)
    model_config_id = create_model_config(client, token)

    # 创建多个对话
    conversation_ids = []
    for _ in range(3):
        conversation_id = create_conversation(client, token, model_config_id)
        conversation_ids.append(conversation_id)

    # 验证对话列表
    response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    data = response.json()
    assert len(data["conversations"]) == 3


def test_delete_conversations_success(client):
    """测试成功批量删除对话"""
    token = get_token(client)
    model_config_id = create_model_config(client, token)

    # 创建多个对话
    conversation_ids = []
    for _ in range(3):
        conversation_id = create_conversation(client, token, model_config_id)
        conversation_ids.append(conversation_id)

    # 批量删除
    response = client.post(
        "/api/v1/conversation/delete",
        json={"ids": conversation_ids},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    # 验证已删除
    get_response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    data = get_response.json()
    assert data["conversations"] == []


def test_delete_conversations_single(client):
    """测试删除单个对话（批量接口）"""
    token = get_token(client)
    model_config_id = create_model_config(client, token)

    # 创建对话
    conversation_id = create_conversation(client, token, model_config_id)

    # 删除单个对话
    response = client.post(
        "/api/v1/conversation/delete",
        json={"ids": [conversation_id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


def test_delete_conversations_not_found(client):
    """测试批量删除不存在的对话"""
    token = get_token(client)

    response = client.post(
        "/api/v1/conversation/delete",
        json={"ids": [99999]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


def test_delete_conversations_no_token(client):
    """测试批量删除对话时未提供token"""
    response = client.post(
        "/api/v1/conversation/delete",
        json={"ids": [1]},
    )
    assert response.status_code == 401


def test_delete_conversations_invalid_token(client):
    """测试批量删除对话时token无效"""
    response = client.post(
        "/api/v1/conversation/delete",
        json={"ids": [1]},
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


def test_conversation_crud_full_flow(client):
    """测试对话的完整CRUD流程"""
    token = get_token(client)

    # 1. 创建模型配置
    model_config_id = create_model_config(
        client,
        token,
        name="CRUD Test Config",
        base_url="https://api.test.com/v1",
        model_name="test-model",
        api_key="sk-test",
    )

    # 2. 创建对话
    create_response = client.post(
        "/api/v1/conversation/create",
        json={"model_config_id": model_config_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 201
    conversation_id = create_response.json()["conversation_id"]

    # 3. 读取对话列表
    list_response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    assert list_response.status_code == 200
    assert len(list_response.json()["conversations"]) == 1

    # 4. 删除对话
    delete_response = client.post(
        "/api/v1/conversation/delete",
        json={"ids": [conversation_id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_response.status_code == 204

    # 5. 验证删除
    final_response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    assert final_response.json()["conversations"] == []


def test_generate_title_no_token(client):
    """测试生成标题时未提供token"""
    response = client.post(
        "/api/v1/conversation/generate_title",
        json={
            "conversation_id": 1,
            "messages": [{"role": "user", "content": "你好"}],
            "base_url": "https://api.test.com/v1",
        },
    )
    assert response.status_code == 401


def test_generate_title_invalid_token(client):
    """测试生成标题时token无效"""
    response = client.post(
        "/api/v1/conversation/generate_title",
        json={
            "conversation_id": 1,
            "messages": [{"role": "user", "content": "你好"}],
            "base_url": "https://api.test.com/v1",
        },
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


def test_generate_title_success(client):
    """测试成功生成对话标题"""
    token = get_token(client)

    # 创建测试专用模型配置和对话
    model_config_id = create_test_model_config(client, token)
    conversation_id = create_conversation(client, token, model_config_id)

    # 生成标题
    response = client.post(
        "/api/v1/conversation/generate_title",
        json={
            "conversation_id": conversation_id,
            "messages": [{"role": "user", "content": "请帮我写一个快速排序算法"}],
            "base_url": TEST_MODEL_CONFIG["base_url"],
            "model_name": TEST_MODEL_CONFIG["model_name"],
            "api_key": TEST_MODEL_CONFIG["api_key"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["conversation_id"] == conversation_id
    assert data["title"] is not None
    assert len(data["title"]) > 0
