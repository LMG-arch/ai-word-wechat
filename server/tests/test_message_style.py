"""V4.0 包A5：语音条与内置表情包"""
import random

import pytest

from services.message_style import (
    STICKERS, get_sticker, estimate_voice_duration,
    should_send_voice, pick_sticker_for, mood_from_text,
)


def test_sticker_pack_is_local_and_unique():
    assert len(STICKERS) >= 10
    ids = [s["id"] for s in STICKERS]
    assert len(ids) == len(set(ids))
    for s in STICKERS:
        assert s["emoji"] and s["name"]
        # 不依赖任何外网资源
        assert "http" not in s["emoji"]


def test_get_sticker():
    assert get_sticker("laugh")["emoji"] == "😂"
    assert get_sticker("nope") is None
    assert get_sticker("") is None


def test_estimate_voice_duration_bounds():
    assert estimate_voice_duration("") == 2
    assert estimate_voice_duration("你好") == 2
    assert estimate_voice_duration("一" * 40) == 10
    assert estimate_voice_duration("一" * 400) == 30


def test_should_send_voice_length_gate():
    assert should_send_voice("短", "calm") is False
    assert should_send_voice("一" * 200, "calm") is False


def test_should_send_voice_never_when_angry():
    for seed in range(20):
        rng = random.Random(seed)
        assert should_send_voice("今天真的有点想跟你说说话", "angry", rng) is False


def test_should_send_voice_probability_range():
    text = "今天下班路上看到一只很小的猫，特别可爱"
    hits = sum(should_send_voice(text, "tired", random.Random(i)) for i in range(200))
    assert 30 <= hits <= 100  # 30% 左右，留足浮动空间


def test_pick_sticker_short_strong_triggers():
    hits = sum(bool(pick_sticker_for("哈哈哈", "happy", random.Random(i))) for i in range(100))
    assert hits > 30


def test_pick_sticker_long_text_rare():
    hits = sum(bool(pick_sticker_for("一" * 80, "calm", random.Random(i))) for i in range(100))
    assert hits <= 15


def test_mood_from_text():
    assert mood_from_text("气死了") == "angry"
    assert mood_from_text("好难过") == "sad"
    assert mood_from_text("哈哈哈真开心") == "happy"
    assert mood_from_text("今天星期三") == "calm"


# ---------------- 端点级 ----------------


def test_stickers_endpoint(isolated_client):
    client, _ = isolated_client
    resp = client.get("/api/stickers")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 10
    assert {"id", "emoji", "name"} <= set(data[0].keys())


def test_send_sticker_message(isolated_client):
    client, chars = isolated_client
    cid = chars[0].id

    resp = client.post("/api/messages/send", json={
        "conversation_id": cid, "content": "laugh", "message_type": "sticker",
    })
    assert resp.status_code == 200, resp.text
    msg = resp.json()["data"]["user_message"]
    assert msg["message_type"] == "sticker"
    assert msg["sticker_id"] == "laugh"
    assert msg["content"] == "笑死"


def test_send_unknown_sticker_rejected(isolated_client):
    client, chars = isolated_client
    resp = client.post("/api/messages/send", json={
        "conversation_id": chars[0].id, "content": "not-a-sticker", "message_type": "sticker",
    })
    assert resp.status_code == 400


def test_send_voice_without_audio_uses_text(isolated_client):
    client, chars = isolated_client
    resp = client.post("/api/messages/send", json={
        "conversation_id": chars[0].id,
        "content": "这是一条没有音频文件的语音条",
        "message_type": "voice",
    })
    assert resp.status_code == 200, resp.text
    msg = resp.json()["data"]["user_message"]
    assert msg["message_type"] == "voice"
    assert msg["voice_text"] == "这是一条没有音频文件的语音条"
    assert msg["voice_duration"] >= 2


def test_send_voice_without_text_rejected(isolated_client):
    client, chars = isolated_client
    resp = client.post("/api/messages/send", json={
        "conversation_id": chars[0].id, "content": "[语音]", "message_type": "voice",
    })
    assert resp.status_code == 400


def test_group_sticker_send(isolated_client):
    client, chars = isolated_client
    from models import PrivateGroupChat
    import storage

    group = PrivateGroupChat(member_ids=[chars[0].id, chars[1].id], member_names=[chars[0].name, chars[1].name])
    storage.save_private_groups([group])

    resp = client.post(f"/api/groups/private/{group.id}/send", json={
        "content": "ok", "message_type": "sticker",
    })
    assert resp.status_code == 200, resp.text
    msg = resp.json()["data"]["message"]
    assert msg["message_type"] == "sticker"
    assert msg["sticker_id"] == "ok"
