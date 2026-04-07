import sqlite3

import pytest
from fastapi.testclient import TestClient


def _make_inmemory_relationship_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE relationships (
            id TEXT PRIMARY KEY,
            from_id TEXT NOT NULL,
            to_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            intimacy REAL DEFAULT 0,
            valid_from INTEGER NOT NULL,
            valid_to INTEGER,
            properties_json TEXT
        );
        """
    )
    conn.execute(
        "INSERT INTO relationships (id, from_id, to_id, relation_type, intimacy, valid_from, valid_to, properties_json) VALUES (?, ?, ?, 'FRIEND_WITH', 30, 1, NULL, '{}')",
        ("r1", "c1", "c2"),
    )
    conn.commit()
    return conn


def test_life_experience_route_returns_expected_shape(monkeypatch):
    from models import Character, TaskItem, TaskStatus, TaskType, Memory
    import storage
    import services.memory_service as memory_service

    # Patch data sources
    monkeypatch.setattr(
        storage,
        "get_characters",
        lambda: [
            Character(
                id="c1",
                name="测试角色",
                age=25,
                gender="女",
                occupation="程序员",
                personality="内向",
                experience_skills={
                    "text": {"count": 2, "success_count": 1, "success_rate": 0.5, "lessons": ["a", "b"]},
                },
            )
        ],
    )
    monkeypatch.setattr(
        storage,
        "get_tasks",
        lambda: [
            TaskItem(
                id="t1",
                title="任务1",
                description="d",
                task_type=TaskType.TEXT,
                status=TaskStatus.COMPLETED,
                submitter_id="c1",
                completed_at=123,
            ),
            TaskItem(
                id="t2",
                title="任务2",
                description="d",
                task_type=TaskType.CODE,
                status=TaskStatus.COMPLETED,
                assignee_id="c1",
                completed_at=124,
            ),
        ],
    )
    monkeypatch.setattr(
        memory_service,
        "get_memory_conn",
        _make_inmemory_relationship_db,
    )

    import routes.character_routes as character_routes

    monkeypatch.setattr(
        character_routes,
        "get_character_memories",
        lambda character_id, limit=80: [
            Memory(character_id=character_id, content="反思内容", memory_type="reflection", importance=0.5)
        ],
    )

    import main
    client = TestClient(main.app)
    resp = client.get("/api/characters/c1/life-experience")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["character_id"] == "c1"
    assert data["character_name"] == "测试角色"
    assert data["total_tasks_completed"] == 2
    assert isinstance(data["task_types_completed"], list)
    assert isinstance(data["experience_skills"], list)
    assert isinstance(data["relationship_count"], int)
    assert isinstance(data["recent_tasks"], list)
    assert isinstance(data["recent_reflections"], list)


def test_exec_route_create_company_and_recruit(monkeypatch):
    from models import Character
    import routes.exec_routes as exec_routes

    characters = [
        Character(id="c1", name="创始人", age=30, gender="男", occupation="创业者", personality="外向", money=2000),
        Character(id="c2", name="成员", age=22, gender="女", occupation="设计师", personality="活泼", money=100),
    ]
    companies = []

    # exec_routes 在模块级从 storage 导入了函数名，这里需要直接 patch 到 exec_routes 上
    monkeypatch.setattr(exec_routes, "get_characters", lambda: characters)
    monkeypatch.setattr(exec_routes, "save_characters", lambda data: None)
    monkeypatch.setattr(exec_routes, "get_companies", lambda: companies)
    monkeypatch.setattr(exec_routes, "save_companies", lambda data: None)

    import main
    client = TestClient(main.app)

    r1 = client.post("/api/exec", json={"action": "create_company", "params": {"legal_person_id": "c1", "name": "测试公司"}})
    assert r1.status_code == 200
    assert r1.json()["success"] is True
    company_id = r1.json()["data"]["id"]

    r2 = client.post("/api/exec", json={"action": "recruit_member", "params": {"company_id": company_id, "character_id": "c2"}})
    assert r2.status_code == 200
    assert r2.json()["success"] is True


def test_character_logs_exact_name_not_substring(monkeypatch):
    """短名不得子串匹配长名；系统日志仍可见。"""
    from models import Character, LogEntry
    import routes.stats_routes as stats_routes

    monkeypatch.setattr(
        stats_routes,
        "get_characters",
        lambda: [
            Character(
                id="c1",
                name="张三",
                age=20,
                gender="男",
                occupation="x",
                personality="y",
                money=0,
            ),
        ],
    )
    logs = [
        LogEntry(
            timestamp="1",
            timestamp_ms=1,
            world_timestamp_ms=0,
            character_name="张",
            action_type="a",
            description="短名",
        ),
        LogEntry(
            timestamp="2",
            timestamp_ms=2,
            world_timestamp_ms=0,
            character_name="张三",
            action_type="a",
            description="全名",
        ),
        LogEntry(
            timestamp="3",
            timestamp_ms=3,
            world_timestamp_ms=0,
            character_name="李四",
            action_type="a",
            description="他人",
        ),
        LogEntry(
            timestamp="4",
            timestamp_ms=4,
            world_timestamp_ms=0,
            character_name="系统",
            action_type="a",
            description="系统",
        ),
    ]
    monkeypatch.setattr(stats_routes, "get_logs", lambda: list(logs))

    import main

    client = TestClient(main.app)
    resp = client.get("/api/logs/character/c1")
    assert resp.status_code == 200
    names = {x["character_name"] for x in resp.json()["data"]}
    assert names == {"张三", "系统"}


def test_create_task_with_json_body(monkeypatch):
    """POST /api/tasks 应正确解析 JSON body。"""
    import main
    import routes.task_routes as task_routes

    bucket: list = []
    monkeypatch.setattr(task_routes, "get_tasks", lambda: list(bucket))

    def _save(ts):
        bucket.clear()
        bucket.extend(ts)

    monkeypatch.setattr(task_routes, "save_tasks", _save)
    monkeypatch.setattr(task_routes, "_add_log", lambda *a, **k: None)

    client = TestClient(main.app)
    resp = client.post(
        "/api/tasks",
        json={
            "title": "冒烟任务",
            "description": "d",
            "task_type": "text",
            "reward": 10.0,
            "assignee_type": "personal",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "冒烟任务"
    assert len(bucket) == 1


def test_map_world_and_llm_usage_stats_ok():
    """地图世界坐标与用量统计接口应返回 JSON 200（避免 500 / 混用记录解析错误）。"""
    import main

    client = TestClient(main.app)
    r = client.get("/api/map/world")
    assert r.status_code == 200
    body = r.json()
    assert body.get("success") is True
    assert "characters" in (body.get("data") or {})

    r2 = client.get("/api/llm-usage/stats")
    assert r2.status_code == 200
    assert r2.json().get("success") is True

