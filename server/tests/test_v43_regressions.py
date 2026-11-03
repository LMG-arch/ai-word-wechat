"""V4.3 回归：任务状态机 + 参数错位 + 年龄上界 + 资金越权。

本轮是「逐段核验核心业务逻辑」查出来的，问题都不在页面上，
而在接口内部的契约不一致：

1. review 没有状态前置校验 → 同一任务反复审核通过，每过一次发一次奖励
   （实测 500 元任务点 5 次到账 3300）
2. submit / auto-complete / assign / auto-take 同样无守卫，能把已完成任务
   打回 pending_review 继续刷
3. refresh_character_avatar_for_stage 三个分支都不返回元组，调用方
   `success, message = await ...` 必然 TypeError → 刷新头像 100% 500
4. generate_moment_image_plan(character, request, content) 参数错位，
   带图发朋友圈必崩
5. save_image_prompt_md 多传一个参数，异常被 except 吞掉 → 任务图生成了
   却判定失败，产不出提示词 md
6. 年龄只卡 0..200，与 max_lifespan（默认 100）矛盾
7. distribute-bonus 不校验收款人是否公司成员，可把公司资金转出
"""
import storage

from services.ai_service import save_image_prompt_md
from services.task_service import ensure_task_action
from models import Character, TaskStatus


def _new_task(client, reward=500, assignee_id=None, **kw):
    body = {"title": "状态机任务", "description": "x", "task_type": "text", "reward": reward}
    if assignee_id:
        body.update({"assignee_type": "personal", "assignee_id": assignee_id})
    body.update(kw)
    resp = client.post("/api/tasks", json=body)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


def _submit(client, task_id, submitter_id):
    return client.post(f"/api/tasks/{task_id}/submit",
                       json={"submitter_id": submitter_id, "execution_notes": "做了",
                             "deliverable_text": "结果"})


# ---------------------------------------------------------------- 状态机

def test_review_cannot_run_twice(isolated_client):
    client, chars = isolated_client
    cid = chars[0].id
    task = _new_task(client, reward=500, assignee_id=cid)
    assert _submit(client, task["id"], cid).status_code == 200

    first = client.post(f"/api/tasks/{task['id']}/review",
                        json={"approved": True, "review_notes": "通过", "score": 90})
    assert first.status_code == 200
    money_after_first = next(c["money"] for c in client.get("/api/characters").json()["data"]
                             if c["id"] == cid)

    for _ in range(3):
        again = client.post(f"/api/tasks/{task['id']}/review",
                            json={"approved": True, "review_notes": "再通过", "score": 90})
        assert again.status_code == 409, "重复审核必须被拒绝，否则可无限刷奖励"

    money_final = next(c["money"] for c in client.get("/api/characters").json()["data"]
                       if c["id"] == cid)
    assert money_final == money_after_first, "重复审核不得再次发放奖励"


def test_completed_task_cannot_reopen(isolated_client):
    client, chars = isolated_client
    cid = chars[0].id
    task = _new_task(client, assignee_id=cid)
    _submit(client, task["id"], cid)
    client.post(f"/api/tasks/{task['id']}/review",
                json={"approved": True, "review_notes": "通过", "score": 88})

    assert _submit(client, task["id"], cid).status_code == 409
    assert client.post(f"/api/tasks/{task['id']}/auto-complete").status_code == 409
    assert client.post(f"/api/tasks/{task['id']}/assign",
                       json={"assignee_type": "personal", "assignee_id": cid}).status_code == 409
    assert client.post(f"/api/tasks/{task['id']}/auto-take", json={}).status_code == 409


def test_review_requires_submission(isolated_client):
    client, chars = isolated_client
    task = _new_task(client)
    resp = client.post(f"/api/tasks/{task['id']}/review",
                       json={"approved": True, "review_notes": "直接过", "score": 90})
    assert resp.status_code == 409
    assert "不允许审核" in resp.json()["detail"]


def test_task_state_machine_helper_messages():
    class _T:
        status = TaskStatus.COMPLETED

    try:
        ensure_task_action(_T(), "review")
    except ValueError as exc:
        assert "已完成" in str(exc)
    else:
        raise AssertionError("已完成任务不应通过审核守卫")


# ---------------------------------------------------------------- 参数错位

def test_avatar_refresh_returns_business_result(isolated_client):
    """没有图像模型时应返回 success=False，而不是 500。"""
    client, chars = isolated_client
    resp = client.post(f"/api/characters/{chars[0].id}/maybe-refresh-avatar", json={"forced": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False and "失败" in body["message"]


def test_generate_moment_with_image_does_not_crash(isolated_client):
    client, chars = isolated_client
    resp = client.post(f"/api/characters/{chars[0].id}/moments/generate",
                       json={"trigger_type": "random", "with_image": True})
    assert resp.status_code == 200, resp.text
    assert resp.json()["success"] is True


def test_save_image_prompt_md_signature(tmp_path, monkeypatch):
    import services.ai_service as ai

    monkeypatch.setattr(ai, "IMAGE_PROMPTS_DIR", str(tmp_path))
    name = save_image_prompt_md("一只猫", "任务图像：测试", "http://example.com/a.png")
    assert name.endswith(".md")
    content = (tmp_path / name).read_text(encoding="utf-8")
    assert "一只猫" in content and "http://example.com/a.png" in content


# ---------------------------------------------------------------- 年龄上界

def test_age_upper_bound(isolated_client):
    client, _ = isolated_client
    over = client.post("/api/characters",
                       json={"name": "超龄", "age": 130, "occupation": "退休", "gender": "男"})
    assert over.status_code == 422

    settings = client.get("/api/settings").json()["data"]
    limit = max(settings["min_lifespan"], settings["max_lifespan"])
    beyond = client.post("/api/characters",
                         json={"name": "超寿命", "age": limit + 1, "occupation": "退休", "gender": "男"})
    assert beyond.status_code == 400
    assert "寿命上限" in beyond.json()["detail"]


def test_age_upper_bound_on_update(isolated_client):
    client, chars = isolated_client
    target = chars[0]
    settings = client.get("/api/settings").json()["data"]
    limit = max(settings["min_lifespan"], settings["max_lifespan"])
    resp = client.put(f"/api/characters/{target.id}",
                      json={"name": target.name, "age": limit + 5,
                            "occupation": target.occupation, "gender": target.gender})
    assert resp.status_code == 400


# ---------------------------------------------------------------- 资金越权

def test_bonus_rejects_non_member(isolated_client):
    client, chars = isolated_client
    legal = chars[0]
    outsider = chars[2]

    # 建公司要求法人出资 1000，先给法人补够
    roster = storage.get_characters()
    for c in roster:
        if c.id == legal.id:
            c.money = 5000
    storage.save_characters(roster)

    comp = client.post("/api/companies", json={
        "name": "分红公司", "description": "x", "industry": "科技", "legal_person_id": legal.id,
    })
    assert comp.status_code == 200, comp.text
    company = comp.json()["data"]

    # 给公司塞钱，确保「资金不足」不会先拦住
    companies = storage.get_companies()
    for c in companies:
        if c.id == company["id"]:
            c.funds = 5000
    storage.save_companies(companies)

    bad = client.post("/api/economy/distribute-bonus", json={
        "company_id": company["id"], "reason": "奖金",
        "bonuses": {outsider.id: 1000},
    })
    assert bad.status_code == 400
    assert "非本公司成员" in bad.json()["detail"]

    good = client.post("/api/economy/distribute-bonus", json={
        "company_id": company["id"], "reason": "奖金",
        "bonuses": {legal.id: 1000},
    })
    assert good.status_code == 200
    assert good.json()["success"] is True


# ---------------------------------------------------------------- 悬空引用

def test_assign_to_unknown_character_rejected(isolated_client):
    """不存在的接收人会让任务永远卡在 in_progress，奖励也发不出去。"""
    client, _ = isolated_client
    task = _new_task(client)
    resp = client.post(f"/api/tasks/{task['id']}/assign",
                       json={"assignee_type": "personal", "assignee_id": "___ghost___"})
    assert resp.status_code == 404
    assert "不存在" in resp.json()["detail"]


def test_memory_for_unknown_character_rejected(isolated_client):
    client, _ = isolated_client
    resp = client.post("/api/memories", json={
        "character_id": "___ghost___", "content": "幽灵记忆",
        "memory_type": "event", "importance": 0.5,
    })
    assert resp.status_code == 404


def test_relationship_interact_requires_both_sides(isolated_client):
    client, chars = isolated_client
    resp = client.post("/api/relationships/interact", json={
        "from_id": chars[0].id, "to_id": "___ghost___", "action": "chat",
    })
    assert resp.status_code == 404


def test_task_reward_and_length_bounds(isolated_client):
    client, _ = isolated_client
    negative = client.post("/api/tasks", json={
        "title": "负奖励", "task_type": "text", "reward": -100,
    })
    assert negative.status_code == 422

    huge = client.post("/api/tasks", json={
        "title": "天价奖励", "task_type": "text", "reward": 1e9,
    })
    assert huge.status_code == 422

    long_title = client.post("/api/tasks", json={
        "title": "长" * 200, "task_type": "text", "reward": 10,
    })
    assert long_title.status_code == 422


def test_review_score_bounds(isolated_client):
    client, chars = isolated_client
    cid = chars[0].id
    task = _new_task(client, assignee_id=cid)
    _submit(client, task["id"], cid)
    bad = client.post(f"/api/tasks/{task['id']}/review",
                      json={"approved": True, "review_notes": "x", "score": 500})
    assert bad.status_code == 422


# ---------------------------------------------------------------- 删除级联

def test_delete_character_detaches_references(isolated_client):
    """删掉配偶后，另一方的 family 不能还写着「夫妻」，孩子的父母列表也要断开。"""
    client, chars = isolated_client
    a, b = chars[0], chars[1]
    storage.save_characters([a, b])
    assert client.post(f"/api/characters/{a.id}/marry", json={"other_id": b.id}).status_code == 200

    client.delete(f"/api/characters/{a.id}")

    fam = client.get(f"/api/characters/{b.id}/family").json()["data"]
    assert fam["spouse"] is None
    assert fam["stage"] != "spouse", "配偶被删后不应还显示夫妻"


def test_family_view_degrades_when_spouse_missing(isolated_client):
    """即使存储里 stage=spouse 且 spouse_id 指向不存在的人，接口也要降级显示。"""
    from services.family_service import family_view

    survivor = Character(name="幸存者", age=30, gender="女", occupation="教师",
                         personality="温和")
    survivor.relationship_stage = "spouse"
    survivor.spouse_id = "___gone___"
    survivor.partner_id = "___gone___"
    view = family_view(survivor, {survivor.id: survivor})
    assert view["spouse"] is None
    assert view["stage"] in ("friend", "lover")
    assert view["stage_stored"] == "spouse"
