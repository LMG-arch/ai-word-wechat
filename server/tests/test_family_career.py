"""V4.0 包B1 家庭 / 包B2 职业 / 包B4 关系图"""
import random

import pytest

from models import Character
from services.family_service import (
    evaluate_stage, advance_pair, can_marry, can_have_child,
    create_child, bind_child, family_view, inherit_surname,
    stage_label, stage_icon, STAGE_ORDER,
)
from services.career_service import (
    ladder_for, title_for, current_title, exp_for_next_level,
    evaluate_promotion, add_experience, career_view, MAX_LEVEL,
    PROMOTION_EXP,
)


# ---------------- B1 关系阶段 ----------------

@pytest.mark.parametrize("intimacy,expected", [
    (0, "stranger"), (34.9, "stranger"),
    (35, "friend"), (54.9, "friend"),
    (55, "close"), (74.9, "close"),
    (75, "lover"), (87.9, "lover"),
    (88, "spouse"), (100, "spouse"),
])
def test_evaluate_stage(intimacy, expected):
    assert evaluate_stage(intimacy) == expected


def test_evaluate_stage_handles_bad_input():
    assert evaluate_stage(None) == "stranger"
    assert evaluate_stage("abc") == "stranger"


def test_stage_helpers():
    assert stage_label("spouse") == "夫妻"
    assert stage_icon("lover") == "❤️"
    assert stage_label("unknown") == "陌生"


def _pair(age_a=30, age_b=28):
    a = Character(name="张三", age=age_a, gender="男", occupation="程序员", personality="开朗、直率")
    b = Character(name="李四", age=age_b, gender="女", occupation="教师", personality="温柔、细心")
    return a, b


def test_advance_pair_only_forward():
    a, b = _pair()
    res = advance_pair(a, b, 80)
    assert res["advanced"] is True
    assert res["to"] == "lover"
    assert a.partner_id == b.id and b.partner_id == a.id

    # 亲密度回落后不降级
    res2 = advance_pair(a, b, 20)
    assert res2["advanced"] is False
    assert a.relationship_stage == "lover"


def test_advance_pair_to_spouse_sets_spouse_id():
    a, b = _pair()
    res = advance_pair(a, b, 95)
    assert res["to"] == "spouse"
    assert a.spouse_id == b.id and b.spouse_id == a.id


def test_advance_pair_no_change_when_already_high():
    a, b = _pair()
    advance_pair(a, b, 95)
    again = advance_pair(a, b, 99)
    assert again["advanced"] is False


def test_can_marry_rules():
    a, b = _pair()
    ok, _ = can_marry(a, b)
    assert ok

    minor = Character(name="小张", age=16, gender="男", occupation="学生", personality="叛逆")
    ok, reason = can_marry(minor, b)
    assert not ok and "18" in reason

    a.relationship_stage = "spouse"
    ok, reason = can_marry(a, b)
    assert not ok and "结婚" in reason


def test_can_have_child_requires_spouse():
    a, b = _pair()
    ok, reason = can_have_child(a, b)
    assert not ok and "夫妻" in reason

    advance_pair(a, b, 95)
    ok, _ = can_have_child(a, b)
    assert ok


def test_can_have_child_age_limit():
    a, b = _pair(age_a=19, age_b=19)
    advance_pair(a, b, 95)
    ok, reason = can_have_child(a, b)
    assert not ok and "20" in reason


def test_inherit_surname_prefers_male():
    a, b = _pair()  # 张 / 李
    assert inherit_surname(a, b) == "张"
    assert inherit_surname(b, a) == "张"


def test_create_child_inherits_and_registers_parents():
    a, b = _pair()
    child = create_child(a, b, rng=random.Random(7))
    assert child.age == 0
    assert child.parent_ids == [a.id, b.id]
    assert child.name[0] == "张"
    assert child.personality

    chars = [a, b, child]
    bind_child(chars, child)
    assert child.id in a.children_ids
    assert child.id in b.children_ids


def test_family_view_shape():
    a, b = _pair()
    advance_pair(a, b, 95)
    child = create_child(a, b)
    bind_child([a, b], child)
    by_id = {a.id: a, b.id: b, child.id: child}

    view = family_view(a, by_id)
    assert view["stage"] == "spouse"
    assert view["spouse"]["name"] == "李四"
    assert len(view["children"]) == 1
    assert view["children"][0]["name"] == child.name


# ---------------- B2 职业 ----------------

def test_ladder_for_known_and_default():
    assert ladder_for("程序员")[0] == "初级程序员"
    assert len(ladder_for("程序员")) == 5
    assert ladder_for("宇航员") == ladder_for("不存在的职业")


def test_title_for_clamps_level():
    assert title_for("程序员", 1) == "初级程序员"
    assert title_for("程序员", 5) == "技术总监"
    assert title_for("程序员", 99) == "技术总监"
    assert title_for("程序员", 0) == "初级程序员"


def test_current_title_prefers_saved():
    c = Character(name="张三", age=30, gender="男", occupation="程序员", personality="开朗")
    assert current_title(c) == "初级程序员"
    c.career_title = "架构师"
    assert current_title(c) == "架构师"


def test_exp_for_next_level():
    assert exp_for_next_level(1) == PROMOTION_EXP[1]
    assert exp_for_next_level(MAX_LEVEL) is None


def test_add_experience_promotes_and_raises():
    c = Character(name="张三", age=30, gender="男", occupation="程序员", personality="开朗", money=100.0)
    res = add_experience(c, amount=130)
    assert res["promoted"] is True
    assert c.career_level == 2
    assert c.career_title == "程序员"
    assert c.money > 100.0
    assert c.tasks_completed == 1


def test_add_experience_no_promotion_below_threshold():
    c = Character(name="张三", age=30, gender="男", occupation="程序员", personality="开朗")
    res = add_experience(c, amount=10)
    assert res["promoted"] is False
    assert c.career_level == 1
    assert c.career_exp == 10


def test_add_experience_stops_at_max():
    c = Character(name="张三", age=30, gender="男", occupation="程序员", personality="开朗")
    for _ in range(10):
        add_experience(c, amount=5000)
    assert c.career_level == MAX_LEVEL
    assert evaluate_promotion(c) is None


def test_career_view_progress():
    c = Character(name="张三", age=30, gender="男", occupation="程序员", personality="开朗")
    c.career_exp = 60
    view = career_view(c)
    assert view["level"] == 1
    assert view["exp_next"] == PROMOTION_EXP[1]
    assert 0 < view["progress"] < 1


# ---------------- 端点级 ----------------

def test_family_endpoint(isolated_client):
    client, chars = isolated_client
    a, b = chars[0], chars[1]

    resp = client.get(f"/api/characters/{a.id}/family")
    assert resp.status_code == 200
    assert resp.json()["data"]["stage"] in STAGE_ORDER

    assert client.get("/api/characters/nope/family").status_code == 404


def test_marry_and_child_flow(isolated_client):
    client, chars = isolated_client
    a, b = chars[0], chars[1]

    married = client.post(f"/api/characters/{a.id}/marry", json={"other_id": b.id})
    assert married.status_code == 200, married.text
    assert married.json()["data"]["stage"] == "spouse"

    child = client.post(f"/api/characters/{a.id}/child", json={"other_id": b.id})
    assert child.status_code == 200, child.text
    child_data = child.json()["data"]["child"]
    assert child_data["age"] == 0
    assert a.id in child_data["parent_ids"]

    # 孩子进入通讯录
    names = [c["name"] for c in client.get("/api/characters").json()["data"]]
    assert child_data["name"] in names

    fam = client.get(f"/api/characters/{a.id}/family").json()["data"]
    assert len(fam["children"]) == 1


def test_marry_self_rejected(isolated_client):
    client, chars = isolated_client
    resp = client.post(f"/api/characters/{chars[0].id}/marry", json={"other_id": chars[0].id})
    assert resp.status_code == 400


def test_marry_minor_rejected(isolated_client):
    client, chars = isolated_client
    import storage
    from models import Character

    kid = Character(name="小学生", age=12, gender="男", occupation="学生", personality="活泼")
    all_chars = storage.get_characters() + [kid]
    storage.save_characters(all_chars)

    resp = client.post(f"/api/characters/{kid.id}/marry", json={"other_id": chars[0].id})
    assert resp.status_code == 400
    assert "18" in resp.json()["detail"]


def test_relationship_advance_endpoint_low_intimacy(isolated_client):
    client, chars = isolated_client
    resp = client.post(f"/api/characters/{chars[0].id}/relationship/advance",
                       json={"other_id": chars[1].id})
    assert resp.status_code == 200
    assert resp.json()["data"]["advanced"] is False


def test_relationship_graph_has_nodes(isolated_client):
    client, chars = isolated_client
    resp = client.get("/api/relationships/graph")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["nodes"]) == len(chars)

    client.post(f"/api/characters/{chars[0].id}/marry", json={"other_id": chars[1].id})
    data2 = client.get("/api/relationships/graph").json()["data"]
    assert any(e["type"] == "spouse" for e in data2["edges"])


def test_relationship_graph_center_filter(isolated_client):
    client, chars = isolated_client
    data = client.get("/api/relationships/graph", params={"center": chars[0].id}).json()["data"]
    # 没建立关系时只应保留中心角色
    assert all(n["id"] == chars[0].id for n in data["nodes"])


def test_career_endpoint(isolated_client):
    client, chars = isolated_client
    resp = client.get(f"/api/characters/{chars[0].id}/career")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["level"] == 1
    assert len(data["ladder"]) == 5
    assert data["title"]


def test_career_promote_endpoint(isolated_client):
    client, chars = isolated_client
    resp = client.post(f"/api/characters/{chars[0].id}/career/promote", json={"exp": 200})
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["promoted"] is True
    assert data["career"]["level"] == 2


def test_career_ladders_endpoint(isolated_client):
    client, _ = isolated_client
    resp = client.get("/api/careers/ladders")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 10
    assert all(len(item["ladder"]) == 5 for item in data)
