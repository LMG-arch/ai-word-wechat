"""V4.2 回归：历史数据自洽 + 本轮巡检修掉的功能缺口。

四类问题：
1. 取消点赞 / 删除朋友圈（之前只有「点」没有「撤」）
2. 婚姻双向校验（之前可以把别人的配偶抢走）
3. 生育年龄上限（之前 71 岁还能生）
4. 兜底回复不复述场景描述、不堆性格词
"""
import storage
from models import Character

from services.ai_service import get_fallback_reply
from services.family_service import can_have_child, can_marry, detach_previous_partners


def _mk(name, age, gender="女", occupation="教师", personality="温柔"):
    return Character(name=name, age=age, gender=gender, occupation=occupation, personality=personality)


# ---------------------------------------------------------------- 朋友圈

def test_user_can_unlike(isolated_client):
    client, _ = isolated_client
    mid = client.post("/api/users/moments", json={"content": "测试动态"}).json()["data"]["id"]

    assert client.post(f"/api/moments/{mid}/like", params={"author_id": "user"}).json()["success"]
    liked = client.get("/api/moments").json()["data"]
    target = next(m for m in liked if m["id"] == mid)
    assert "user" in target["liked_by"]

    unlike = client.delete(f"/api/moments/{mid}/like", params={"author_id": "user"})
    assert unlike.status_code == 200
    after = next(m for m in client.get("/api/moments").json()["data"] if m["id"] == mid)
    assert "user" not in after["liked_by"]


def test_user_can_delete_own_moment(isolated_client):
    client, _ = isolated_client
    mid = client.post("/api/users/moments", json={"content": "待删除"}).json()["data"]["id"]

    resp = client.delete(f"/api/moments/{mid}")
    assert resp.status_code == 200
    assert all(m["id"] != mid for m in client.get("/api/moments").json()["data"])


def test_cannot_delete_character_moment(isolated_client):
    client, chars = isolated_client
    storage.save_moments([])
    created = client.post("/api/users/moments", json={"content": "用户的动态"}).json()["data"]

    # 直接改库，把作者换成角色，模拟「角色发的动态」
    moments = storage.get_moments()
    moments[0].author_id = chars[0].id
    storage.save_moments(moments)

    resp = client.delete(f"/api/moments/{created['id']}")
    assert resp.status_code == 403


# ---------------------------------------------------------------- 婚姻

def test_cannot_marry_someone_else_spouse():
    a, b, c = _mk("甲", 30), _mk("乙", 28), _mk("丙", 31)
    b.spouse_id = c.id
    c.spouse_id = b.id
    ok, reason = can_marry(a, b)
    assert not ok and "乙" in reason


def test_marry_allowed_when_both_single():
    a, b = _mk("甲", 30), _mk("乙", 28)
    ok, _ = can_marry(a, b)
    assert ok


def test_marry_rejects_minor():
    a, b = _mk("甲", 30), _mk("乙", 17)
    ok, _ = can_marry(a, b)
    assert not ok


def test_detach_previous_partners_clears_triangle():
    a, b, c = _mk("甲", 30), _mk("乙", 28), _mk("丙", 29)
    a.partner_id = c.id
    c.partner_id = a.id
    c.relationship_stage = "lover"

    notes = detach_previous_partners([a, b, c], a, b)
    assert notes
    assert a.partner_id is None
    assert c.partner_id is None
    assert c.relationship_stage == "close"


# ---------------------------------------------------------------- 生育

def test_child_rejected_when_too_old():
    a, b = _mk("甲", 70, "男"), _mk("乙", 71)
    a.relationship_stage = b.relationship_stage = "spouse"
    a.spouse_id, b.spouse_id = b.id, a.id
    ok, reason = can_have_child(a, b)
    assert not ok and "60" in reason


def test_child_rejected_for_unmarried():
    a, b = _mk("甲", 30), _mk("乙", 28)
    ok, reason = can_have_child(a, b)
    assert not ok and "夫妻" in reason


# ---------------------------------------------------------------- 兜底回复

def test_fallback_scene_replies_are_natural():
    c = _mk("林屿", 21, "男", "大学生", "内敛, 善思, 温润")
    for scene in ("（对方发来一张图片）", "（对方发来一个表情）"):
        reply = get_fallback_reply(c, scene)
        assert scene not in reply
        assert "图片消息" not in reply
        assert reply.strip()


def test_fallback_does_not_stack_personality_words():
    c = _mk("林柔", 34, "女", "插画师", "内敛, 善思, 温润, 坚韧, 细腻")
    for _ in range(6):
        reply = get_fallback_reply(c, "今天过得怎么样？")
        # 不能把整串性格词塞进句子
        assert "内敛, 善思" not in reply
        assert "的角度来看" not in reply
