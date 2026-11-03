"""V4.1 浏览器实测回归：兜底回复污染 / 用户点赞评论 / 年龄增长 / 失效头像"""
import asyncio
import time

import pytest

from models import Character
from services.ai_service import _slim_fallback_input, get_fallback_reply


def test_fallback_never_echoes_scene_instruction():
    """LLM 不可用时，指令型输入不能原样拼进兜底回复。"""
    instruction = (
        "对方刚才发来一个表情「笑死」。你顺着这个情绪回一句，"
        "像微信聊天一样自然，不要提到「表情」两个字，也不要复述这段说明。"
    )
    char = Character(name="林柔", age=30, gender="女", occupation="插画师", personality="温柔")
    reply = get_fallback_reply(char, instruction)
    for leaked in ("你顺着", "不要提到", "这段说明", "「表情」两个字"):
        assert leaked not in reply
    assert reply.strip()


def test_slim_fallback_input_keeps_short_sentence():
    assert _slim_fallback_input("今天过得怎么样？") == "今天过得怎么样"
    assert _slim_fallback_input("") == "这事"
    assert _slim_fallback_input("啊" * 60) == "这事"


def test_user_can_like_and_comment_repeatedly(isolated_client):
    """真实用户（author_id=user）点赞 / 评论朋友圈不应 404 / 400。"""
    client, chars = isolated_client

    created = client.post("/api/users/moments", json={"content": "今天天气不错 #咖啡#"}).json()
    assert created["success"]
    mid = created["data"]["id"]

    like = client.post(f"/api/moments/{mid}/like", params={"author_id": "user"})
    assert like.status_code == 200, like.text

    first = client.post(
        f"/api/moments/{mid}/comment",
        json={"author_id": "user", "content": "第一条", "auto_generate": False},
    )
    assert first.status_code == 200, first.text
    second = client.post(
        f"/api/moments/{mid}/comment",
        json={"author_id": "user", "content": "第二条", "auto_generate": False},
    )
    assert second.status_code == 200, second.text

    # 角色仍然只能评论一次，避免刷屏
    char_id = chars[0].id
    ok = client.post(
        f"/api/moments/{mid}/comment",
        json={"author_id": char_id, "content": "好看", "auto_generate": False},
    )
    assert ok.status_code == 200, ok.text
    dup = client.post(
        f"/api/moments/{mid}/comment",
        json={"author_id": char_id, "content": "再来一条", "auto_generate": False},
    )
    assert dup.status_code == 400
    assert "已经评论过" in dup.json()["detail"]


def test_age_growth_runs_without_attribute_error(isolated_client, monkeypatch):
    """Character 没有 age_stage 字段，年龄增长任务不能再抛 AttributeError。"""
    import storage
    from services.lifecycle_service import process_age_growth

    settings = storage.get_settings()
    settings.last_age_growth_time = 0
    storage.save_settings(settings)

    before = {c.id: c.age for c in storage.get_characters()}
    asyncio.get_event_loop_policy()
    asyncio.run(process_age_growth())

    after = {c.id: c.age for c in storage.get_characters()}
    assert after, "角色不应被清空"
    for cid, age in before.items():
        assert after[cid] == age + 1

    settings = storage.get_settings()
    assert settings.last_age_growth_time > 0


def test_prune_missing_avatars_clears_dangling_path(isolated_client):
    import storage

    chars = storage.get_characters()
    chars[0].avatar_url = "/avatars/definitely-missing.png"
    storage.save_characters(chars)

    assert storage.prune_missing_avatars() >= 1
    refreshed = {c.id: c for c in storage.get_characters()}
    assert refreshed[chars[0].id].avatar_url is None
