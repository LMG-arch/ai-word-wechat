"""端到端冒烟测试（V4.0 审核固化的防线）。

背景：V3.x 的 141 个测试全绿，但「生成日程 / 查询日程 / 创建记忆 / 生成头像」
4 个核心端点稳定返回 500 —— 因为测试只覆盖函数，不覆盖「用户真实请求路径」。
本文件把这类问题变成断言：

1. 全端点冒烟：遍历 app.routes，用「按模型自动构造的合法请求体」逐个请求，
   任何 5xx 立即失败。数据目录隔离到 tmp_path，出站网络被阻断（走降级路径）。
2. 主链路：日程生成→查询一致、记忆创建→可检索、朋友圈发布→记忆落库。
"""

import enum
import typing

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

import main
import storage
from models import Character


# --------------------------------------------------------------------------
# 数据隔离 + 网络阻断
# --------------------------------------------------------------------------

# 不参与冒烟：可执行任意代码的调试端点
_SKIP_PATHS = {"/api/exec"}


# --------------------------------------------------------------------------
# 按 Pydantic 模型自动构造合法请求体
# --------------------------------------------------------------------------

def _value_for(tp, depth=0):
    if depth > 3:
        return None
    origin = typing.get_origin(tp)
    args = typing.get_args(tp)
    if origin is typing.Union:
        non_none = [a for a in args if a is not type(None)]
        return _value_for(non_none[0], depth + 1) if non_none else None
    if origin in (list, typing.List):
        return []
    if origin in (dict, typing.Dict):
        return {}
    if origin is typing.Literal:
        return args[0] if args else None
    if isinstance(tp, type):
        if issubclass(tp, enum.Enum):
            return list(tp)[0].value
        if issubclass(tp, BaseModel):
            return _build_model(tp, depth + 1)
        if tp is str:
            return "测试文本"
        if tp is int:
            return 1
        if tp is float:
            return 1.0
        if tp is bool:
            return True
    return None


def _build_model(cls, depth=0):
    data = {}
    for name, field in cls.model_fields.items():
        if not field.is_required():
            continue
        data[name] = _value_for(field.annotation, depth + 1)
    return data


def _build_body(route):
    body_params = route.dependant.body_params
    if not body_params:
        return None
    ann = body_params[0].field_info.annotation
    if isinstance(ann, type) and issubclass(ann, BaseModel):
        return _build_model(ann)
    return {}


def _iter_api_routes():
    for route in main.app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api") or path in _SKIP_PATHS:
            continue
        methods = getattr(route, "methods", set()) or set()
        for method in sorted(methods):
            if method in ("HEAD", "OPTIONS"):
                continue
            yield method, path, route


# --------------------------------------------------------------------------
# 1. 全端点冒烟：任何 5xx 都是缺陷
# --------------------------------------------------------------------------

def test_all_endpoints_return_no_5xx(isolated_client):
    client, chars = isolated_client
    cid = chars[0].id
    id_map = {
        "character_id": cid, "char_id": cid, "conversation_id": cid,
        "task_id": "nonexistent", "company_id": "nonexistent",
        "group_id": "nonexistent", "config_id": "nonexistent",
        "api_config_id": "nonexistent", "moment_id": "nonexistent",
        "memory_id": "nonexistent", "reminder_id": "nonexistent", "packet_id": "nonexistent",
    }

    failures = []
    for method, path, route in _iter_api_routes():
        url = path
        for key, val in id_map.items():
            url = url.replace("{" + key + "}", val)
        body = _build_body(route) if method in ("POST", "PUT", "PATCH") else None
        try:
            resp = client.request(method, url, json=body)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{method} {path} -> EXCEPTION {type(exc).__name__}: {exc}")
            continue
        if resp.status_code >= 500:
            snippet = (resp.text or "")[:120].replace("\n", " ")
            failures.append(f"{method} {path} -> {resp.status_code} {snippet}")

    assert not failures, "以下端点返回 5xx / 抛异常：\n" + "\n".join(failures)


# --------------------------------------------------------------------------
# 2. 主链路
# --------------------------------------------------------------------------

def test_schedule_generate_then_query_consistent(isolated_client):
    client, chars = isolated_client
    cid = chars[0].id

    gen = client.post("/api/schedules/generate", json={})
    assert gen.status_code == 200, gen.text
    assert gen.json()["success"] is True

    query = client.get(f"/api/schedules/{cid}")
    assert query.status_code == 200, query.text
    payload = query.json()["data"]
    assert payload["character_id"] == cid
    assert payload["events"], "日程不应为空"
    # 事件字段符合模型定义（start_time/end_time/location/activity）
    first = payload["events"][0]
    for key in ("start_time", "end_time", "location", "activity"):
        assert key in first and first[key], f"日程事件缺少字段 {key}"
    assert payload["summary"], "日程 summary 不应为空"


def test_manual_memory_create_and_recall(isolated_client):
    client, chars = isolated_client
    cid = chars[0].id

    created = client.post("/api/memories", json={
        "character_id": cid,
        "content": "用户提过他在做冰晶石实验",
        "memory_type": "event",
        "importance": 0.8,
        "related_entities": ["实验"],
    })
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["success"] is True
    assert body["data"]["content"] == "用户提过他在做冰晶石实验"

    listed = client.get(f"/api/memories/{cid}")
    assert listed.status_code == 200, listed.text
    contents = [m["content"] for m in listed.json()["data"]]
    assert "用户提过他在做冰晶石实验" in contents


def test_character_creation_flow(isolated_client):
    client, _ = isolated_client
    resp = client.post("/api/characters", json={
        "name": "新来的同事",
        "age": 26,
        "gender": "女",
        "occupation": "设计师",
        "personality": "安静、有想法",
    })
    assert resp.status_code == 200, resp.text
    created = resp.json()["data"]
    assert created["name"] == "新来的同事"

    all_chars = client.get("/api/characters")
    assert all_chars.status_code == 200
    names = [c["name"] for c in all_chars.json()["data"]]
    assert "新来的同事" in names


def test_private_group_can_send_message(isolated_client):
    """V4.0 包A1：用户在私人群里可以发言（此前只读）。"""
    client, chars = isolated_client
    from models import PrivateGroupChat

    group = PrivateGroupChat(
        member_ids=[chars[0].id, chars[1].id],
        member_names=[chars[0].name, chars[1].name],
    )
    storage.save_private_groups([group])

    sent = client.post(f"/api/groups/private/{group.id}/send", json={"content": "在吗？周末聚一下？"})
    assert sent.status_code == 200, sent.text
    assert sent.json()["data"]["message"]["sender_id"] == "user"

    listed = client.get(f"/api/groups/private/{group.id}/messages")
    assert listed.status_code == 200, listed.text
    contents = [m["content"] for m in listed.json()["data"]["messages"]]
    assert "在吗？周末聚一下？" in contents


def test_private_group_send_rejects_empty(isolated_client):
    client, chars = isolated_client
    from models import PrivateGroupChat

    group = PrivateGroupChat(
        member_ids=[chars[0].id, chars[1].id],
        member_names=[chars[0].name, chars[1].name],
    )
    storage.save_private_groups([group])

    resp = client.post(f"/api/groups/private/{group.id}/send", json={"content": ""})
    assert resp.status_code == 422  # Field(min_length=1) 校验


# --------------------------------------------------------------------------
# 红包（包A2）
# --------------------------------------------------------------------------

def test_red_packet_single_chat_auto_claimed(isolated_client):
    client, chars = isolated_client
    cid = chars[0].id

    before = next(c for c in client.get("/api/characters").json()["data"] if c["id"] == cid)["money"]

    resp = client.post("/api/red-packets", json={
        "conversation_id": cid, "total_amount": 10, "count": 1, "blessing": "请你的",
    })
    assert resp.status_code == 200, resp.text
    packet = resp.json()["data"]["packet"]
    assert packet["total_amount"] == 10.0
    assert resp.json()["data"]["message"]["message_type"] == "red_packet"

    detail = client.get(f"/api/red-packets/{packet['id']}").json()["data"]
    assert detail["is_finished"] is True
    assert len(detail["claims"]) == 1
    assert detail["claims"][0]["amount"] == 10.0

    after = next(c for c in client.get("/api/characters").json()["data"] if c["id"] == cid)["money"]
    assert after == round(before + 10.0, 2)


def test_red_packet_group_split_sums_correctly(isolated_client):
    client, chars = isolated_client
    from models import PrivateGroupChat

    group = PrivateGroupChat(
        member_ids=[c.id for c in chars],
        member_names=[c.name for c in chars],
    )
    storage.save_private_groups([group])

    resp = client.post("/api/red-packets", json={
        "conversation_id": f"group:{group.id}", "total_amount": 3.0, "count": 3,
    })
    assert resp.status_code == 200, resp.text
    pid = resp.json()["data"]["packet"]["id"]

    detail = client.get(f"/api/red-packets/{pid}").json()["data"]
    assert detail["is_finished"] is True
    amounts = [c["amount"] for c in detail["claims"]]
    assert len(amounts) == 3
    assert abs(sum(amounts) - 3.0) < 0.02
    assert all(a >= 0.01 for a in amounts)


def test_red_packet_double_claim_rejected(isolated_client):
    client, chars = isolated_client
    cid = chars[0].id
    resp = client.post("/api/red-packets", json={
        "conversation_id": cid, "total_amount": 5, "count": 5,
    })
    pid = resp.json()["data"]["packet"]["id"]

    first = client.post(f"/api/red-packets/{pid}/claim", json={"actor_id": "user"})
    assert first.status_code == 200, first.text
    assert first.json()["data"]["amount"] > 0

    second = client.post(f"/api/red-packets/{pid}/claim", json={"actor_id": "user"})
    assert second.status_code == 400




# --------------------------------------------------------------------------
# 转账（包A3）
# --------------------------------------------------------------------------

def test_transfer_small_amount_accepted(isolated_client):
    client, chars = isolated_client
    cid = chars[0].id
    before = next(c for c in client.get("/api/characters").json()["data"] if c["id"] == cid)["money"]

    resp = client.post("/api/transfers", json={"conversation_id": cid, "amount": 50, "note": "上次饭钱"})
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["status"] == "accepted"

    after = next(c for c in client.get("/api/characters").json()["data"] if c["id"] == cid)["money"]
    assert after == round(before + 50, 2)


def test_transfer_large_amount_rejected(isolated_client):
    client, chars = isolated_client
    cid = chars[0].id
    resp = client.post("/api/transfers", json={"conversation_id": cid, "amount": 2000, "note": "拿去花"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["status"] == "rejected"


def test_transfer_in_group_rejected(isolated_client):
    client, _ = isolated_client
    resp = client.post("/api/transfers", json={"conversation_id": "group:whatever", "amount": 10})
    assert resp.status_code == 400
