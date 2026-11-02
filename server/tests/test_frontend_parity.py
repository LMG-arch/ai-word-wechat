"""前后端联动契约 + 新接入端点回归测试。

A 组（契约测试）：从 web/index.html 中提取所有 `${API_BASE}/...` 调用及其 HTTP 方法，
与后端实际注册的 /api 路由逐条比对。任何「前端调用但后端无此路由」（断链）或
「路径存在但方法不匹配」都会让测试失败 —— 这类问题在浏览器里表现为静默 404/405，
人工审计容易漏，必须由测试长期守住。

B 组（功能测试）：覆盖 V3.9 新接入前端的 3 个端点
- POST /api/tasks/{id}/assign   手动指派执行角色
- POST /api/tasks/{id}/submit   用户本人提交成果
- POST /api/companies/{id}/recruit  招募成员加入公司
"""

import pathlib
import re

import pytest
from fastapi.testclient import TestClient

import main
from models import Character, Company, TaskItem

WEB_INDEX = pathlib.Path(__file__).resolve().parent.parent / "web" / "index.html"


# --------------------------------------------------------------------------
# A 组：前后端联动契约
# --------------------------------------------------------------------------

def _normalize(path: str) -> str:
    """把 /tasks/{task_id}/assign 与 /tasks/${id}/assign 统一成 /tasks/{}/assign。"""
    path = re.sub(r"\$\{[^}]*\}", "{}", path)
    return re.sub(r"\{[^}]+\}", "{}", path)


def _frontend_calls():
    html = WEB_INDEX.read_text(encoding="utf-8", errors="ignore")
    calls = set()
    for m in re.finditer(r"\$\{API_BASE\}(/[^`\"'\s]*)", html):
        path = m.group(1).split("?")[0]
        # 向后看一小段，捕获该 fetch 的 method（缺省 GET）
        tail = html[m.end(): m.end() + 220]
        mm = re.search(r"method\s*:\s*['\"](\w+)['\"]", tail)
        method = (mm.group(1) if mm else "GET").upper()
        calls.add((method, _normalize(path)))
    return calls


def _backend_routes():
    routes = set()
    for r in main.app.routes:
        methods = getattr(r, "methods", None)
        path = getattr(r, "path", None)
        if not methods or not path or not path.startswith("/api"):
            continue
        for m in methods:
            if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                routes.add((m, _normalize(path[len("/api"):])))
    return routes


def test_no_broken_frontend_calls():
    """前端每一处调用都必须有后端路由承接（否则浏览器里是静默 404）。"""
    front = _frontend_calls()
    assert front, "未能从 index.html 解析出任何 API 调用，解析逻辑可能失效"

    backend_paths = {p for _, p in _backend_routes()}
    broken = sorted(f"{m} {p}" for m, p in front if p not in backend_paths)
    assert not broken, "发现前端调用但后端无此路由：\n" + "\n".join(broken)


def test_no_http_method_mismatch():
    """路径存在但方法不匹配会返回 405，同样属于断链。"""
    front = _frontend_calls()
    backend = _backend_routes()
    backend_paths = {p for _, p in backend}

    mismatch = []
    for method, path in sorted(front):
        if path in backend_paths and (method, path) not in backend:
            allowed = sorted(m for m, p in backend if p == path)
            mismatch.append(f"前端 {method} {path} → 后端仅支持 {allowed}")
    assert not mismatch, "发现前后端 HTTP 方法不匹配：\n" + "\n".join(mismatch)


def test_newly_wired_endpoints_are_referenced():
    """V3.9 新接入的功能必须仍被前端引用，防止后续改动误删入口。"""
    front = _frontend_calls()
    expected = {
        ("POST", "/uploads/chat-image"),      # V3.8 聊天图片上传
        ("POST", "/tasks/{}/assign"),         # V3.9 手动指派
        ("POST", "/tasks/{}/submit"),         # V3.9 人工提交成果
        ("POST", "/companies/{}/recruit"),    # V3.9 招募成员
    }
    missing = sorted(f"{m} {p}" for m, p in expected if (m, p) not in front)
    assert not missing, "以下已接入的端点在前端已找不到调用：\n" + "\n".join(missing)


# --------------------------------------------------------------------------
# B 组：新接入端点功能回归
# --------------------------------------------------------------------------

def _make_task(task_id: str = "t1") -> TaskItem:
    return TaskItem(
        id=task_id,
        title="回归任务",
        description="用于回归测试",
        task_type="text",
        reward=10.0,
    )


def _patch_task_storage(monkeypatch, bucket):
    import routes.task_routes as task_routes

    monkeypatch.setattr(task_routes, "get_tasks", lambda: [t.model_copy(deep=True) for t in bucket])

    def _save(tasks):
        bucket.clear()
        bucket.extend(tasks)

    monkeypatch.setattr(task_routes, "save_tasks", _save)
    monkeypatch.setattr(task_routes, "_add_log", lambda *a, **k: None)


def test_assign_task_moves_to_in_progress(monkeypatch):
    bucket = [_make_task()]
    _patch_task_storage(monkeypatch, bucket)

    client = TestClient(main.app)
    resp = client.post(
        "/api/tasks/t1/assign",
        json={"assignee_type": "personal", "assignee_id": "c1", "company_id": None},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["assignee_id"] == "c1"
    assert data["status"] == "in_progress"


def test_assign_unknown_task_returns_404(monkeypatch):
    bucket = [_make_task()]
    _patch_task_storage(monkeypatch, bucket)

    client = TestClient(main.app)
    resp = client.post("/api/tasks/nope/assign", json={"assignee_id": "c1"})
    assert resp.status_code == 404


def test_submit_task_sets_pending_review(monkeypatch):
    bucket = [_make_task()]
    _patch_task_storage(monkeypatch, bucket)

    client = TestClient(main.app)
    resp = client.post(
        "/api/tasks/t1/submit",
        json={
            "submitter_id": "user",
            "execution_notes": "已完成",
            "deliverable_text": "这是成果正文",
            "deliverable_code": "print(1)",
            "deliverable_image_url": None,
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "pending_review"
    assert data["submitter_id"] == "user"
    assert data["deliverable_text"] == "这是成果正文"
    assert data["deliverable_code"] == "print(1)"


def test_recruit_member_adds_to_company(monkeypatch):
    import routes.company_routes as company_routes

    companies_bucket = [Company(id="co1", name="回归公司", legal_person_id="c1")]
    chars_bucket = [
        Character(id="c1", name="甲", age=30, gender="男", occupation="程序员", personality="温和"),
        Character(id="c2", name="乙", age=28, gender="女", occupation="设计师", personality="开朗"),
    ]

    monkeypatch.setattr(company_routes, "get_companies", lambda: [c.model_copy(deep=True) for c in companies_bucket])
    monkeypatch.setattr(company_routes, "get_characters", lambda: [c.model_copy(deep=True) for c in chars_bucket])

    def _save_companies(items):
        companies_bucket.clear()
        companies_bucket.extend(items)

    def _save_characters(items):
        chars_bucket.clear()
        chars_bucket.extend(items)

    monkeypatch.setattr(company_routes, "save_companies", _save_companies)
    monkeypatch.setattr(company_routes, "save_characters", _save_characters)
    monkeypatch.setattr(company_routes, "_add_log", lambda *a, **k: None)

    client = TestClient(main.app)
    resp = client.post("/api/companies/co1/recruit", json={"character_id": "c2"})
    assert resp.status_code == 200
    assert "c2" in resp.json()["data"]["member_ids"]

    # 招募成功后角色的 company_id 应同步
    assert any(c.id == "c2" and c.company_id == "co1" for c in chars_bucket)

    # 重复招募同一角色应被拒绝
    resp2 = client.post("/api/companies/co1/recruit", json={"character_id": "c2"})
    assert resp2.status_code == 400


def test_recruit_unknown_character_returns_404(monkeypatch):
    import routes.company_routes as company_routes

    monkeypatch.setattr(company_routes, "get_companies", lambda: [Company(id="co1", name="回归公司", legal_person_id="c1")])
    monkeypatch.setattr(company_routes, "get_characters", lambda: [])
    monkeypatch.setattr(company_routes, "save_companies", lambda items: None)
    monkeypatch.setattr(company_routes, "save_characters", lambda items: None)
    monkeypatch.setattr(company_routes, "_add_log", lambda *a, **k: None)

    client = TestClient(main.app)
    resp = client.post("/api/companies/co1/recruit", json={"character_id": "ghost"})
    assert resp.status_code == 404
