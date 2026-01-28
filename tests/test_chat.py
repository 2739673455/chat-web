from conftest import (
    TEST_MODEL_CONFIG,
    create_conversation,
    create_test_model_config,
    get_token,
)


# ============ 测试 get_upload_presigned_url ============


def test_get_upload_presigned_url_success(client):
    """测试成功获取上传预签名URL"""
    token = get_token(client)
    model_config_id = create_test_model_config(client, token)
    conversation_id = create_conversation(client, token, model_config_id)

    response = client.post(
        "/api/v1/chat/get_upload_presigned_url",
        json={
            "conversation_id": conversation_id,
            "suffixes": [".png", ".jpg"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "urls" in data
    assert len(data["urls"]) == 2
    assert all(isinstance(url, str) for url in data["urls"])


def test_get_upload_presigned_url_multiple_suffixes(client):
    """测试获取多个后缀名的上传预签名URL"""
    token = get_token(client)
    model_config_id = create_test_model_config(client, token)
    conversation_id = create_conversation(client, token, model_config_id)

    suffixes = [".png", ".jpg", ".jpeg", ".gif", ".webp"]
    response = client.post(
        "/api/v1/chat/get_upload_presigned_url",
        json={
            "conversation_id": conversation_id,
            "suffixes": suffixes,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["urls"]) == len(suffixes)


# ============ 测试 get_messages ============


def test_get_messages_empty(client):
    """测试获取空消息记录"""
    token = get_token(client)
    model_config_id = create_test_model_config(client, token)
    conversation_id = create_conversation(client, token, model_config_id)

    response = client.get(
        f"/api/v1/chat/{conversation_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["messages"] == []


def test_get_messages_not_found(client):
    """测试获取不存在的对话消息记录"""
    token = get_token(client)

    response = client.get(
        "/api/v1/chat/99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["messages"] == []


# ============ 测试 send_message ============


def test_send_message_with_extra_params(client):
    """测试发送消息时附带额外参数"""
    import json

    token = get_token(client)
    model_config_id = create_test_model_config(client, token)
    conversation_id = create_conversation(client, token, model_config_id)

    # 使用 app 端点直接发送请求，获取原始响应
    response = client.request(
        method="POST",
        url="/api/v1/chat/send",
        json={
            "conversation_id": conversation_id,
            "messages": [{"role": "user", "content": "你好"}],
            "base_url": TEST_MODEL_CONFIG["base_url"],
            "model_name": TEST_MODEL_CONFIG["model_name"],
            "api_key": TEST_MODEL_CONFIG["api_key"],
            "params": {"temperature": 0.7, "max_tokens": 100},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    # 解析流式响应，验证所有字段
    user_message_id = None
    ai_chunks = []
    ai_message_id = None

    content = response.content.decode("utf-8")
    for line in content.strip().split("\n"):
        if line.strip():
            data = json.loads(line)
            msg_type = data.get("type")
            if msg_type == "user_message_id":
                user_message_id = data.get("user_message_id")
            elif msg_type == "ai_chunk":
                ai_chunks.append(data.get("content"))
            elif msg_type == "complete":
                ai_message_id = data.get("ai_message_id")

    # 验证 user_message_id
    assert user_message_id is not None
    assert isinstance(user_message_id, int)
    assert user_message_id > 0

    # 验证 ai_chunk
    assert len(ai_chunks) > 0

    # 验证 ai_message_id
    assert ai_message_id is not None
    assert isinstance(ai_message_id, int)
    assert ai_message_id > 0
