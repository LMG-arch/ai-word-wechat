"""输入校验回归测试。

背景：``CreateCharacterRequest`` / ``SendMessageRequest`` 此前完全没有字段约束，
前端校验一旦被绕过（直接调 API、脚本、第三方客户端），就能写入
空角色名、负年龄、超长文本等脏数据，污染整个角色库。

现已补上长度 / 范围 / 非空白约束，本文件锁定这些防线，并验证
API 层确实返回 422（而不是把非法数据写进去或抛 500）。
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import main
from models import CreateCharacterRequest, SendMessageRequest


class TestCreateCharacterRequest:
    def test_strips_whitespace(self):
        req = CreateCharacterRequest(name="  张三  ", age=30, occupation=" 教师 ")
        assert req.name == "张三"
        assert req.occupation == "教师"

    @pytest.mark.parametrize("name", ["", "   ", "\t\n"])
    def test_blank_name_rejected(self, name):
        with pytest.raises(ValidationError):
            CreateCharacterRequest(name=name, age=30, occupation="教师")

    def test_too_long_name_rejected(self):
        with pytest.raises(ValidationError):
            CreateCharacterRequest(name="x" * 31, age=30, occupation="教师")

    @pytest.mark.parametrize("age", [-1, -100, 201, 999])
    def test_age_out_of_range_rejected(self, age):
        with pytest.raises(ValidationError):
            CreateCharacterRequest(name="测试", age=age, occupation="教师")

    @pytest.mark.parametrize("age", [0, 1, 100, 120])
    def test_age_boundaries_accepted(self, age):
        # V4.3：硬边界收紧到 120（世界寿命上限默认 100，接口层再卡一次）
        assert CreateCharacterRequest(name="测试", age=age, occupation="教师").age == age

    @pytest.mark.parametrize("age", [121, 150, 200])
    def test_age_beyond_world_lifespan_rejected(self, age):
        with pytest.raises(ValidationError):
            CreateCharacterRequest(name="测试", age=age, occupation="教师")

    def test_blank_occupation_rejected(self):
        with pytest.raises(ValidationError):
            CreateCharacterRequest(name="测试", age=30, occupation="   ")


class TestSendMessageRequest:
    def test_normal(self):
        req = SendMessageRequest(conversation_id="c1", content="你好")
        assert req.message_type == "text"

    def test_empty_conversation_rejected(self):
        with pytest.raises(ValidationError):
            SendMessageRequest(conversation_id="", content="hi")

    def test_content_too_long_rejected(self):
        with pytest.raises(ValidationError):
            SendMessageRequest(conversation_id="c1", content="x" * 5001)

    def test_content_max_boundary_ok(self):
        assert SendMessageRequest(conversation_id="c1", content="x" * 5000)


class TestApiLayer:
    """端到端：非法请求必须被 422 拦下，而不是写进库或 500。"""

    def test_create_character_blank_name_returns_422(self):
        client = TestClient(main.app)
        resp = client.post(
            "/api/characters",
            json={"name": "   ", "age": 30, "gender": "男", "occupation": "教师"},
        )
        assert resp.status_code == 422

    def test_create_character_negative_age_returns_422(self):
        client = TestClient(main.app)
        resp = client.post(
            "/api/characters",
            json={"name": "正常名字", "age": -5, "gender": "男", "occupation": "教师"},
        )
        assert resp.status_code == 422

    def test_send_message_empty_conversation_returns_422(self):
        client = TestClient(main.app)
        resp = client.post(
            "/api/messages/send",
            json={"conversation_id": "", "content": "hi", "message_type": "text"},
        )
        assert resp.status_code == 422
