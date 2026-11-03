"""pytest 配置 - 修复 Windows stdout wrapper 冲突"""
import sys
import os
import io

# 在 pytest 启动时恢复原始 stdout
# 这必须在导入 main.py/config.py 之前执行
_original_stdout = sys.stdout
_original_stderr = sys.stderr

# 确保 PYTEST_CURRENT_TEST 环境变量存在（pytest 通常已设置）
if not os.environ.get("PYTEST_CURRENT_TEST"):
    os.environ["PYTEST_CURRENT_TEST"] = "pytest_setup"

# 尝试恢复原始 stdout（如果被包装了）
if hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = sys.stdout.buffer
    except (AttributeError, ValueError):
        sys.stdout = _original_stdout

if hasattr(sys.stderr, 'buffer'):
    try:
        sys.stderr = sys.stderr.buffer
    except (AttributeError, ValueError):
        sys.stderr = _original_stderr


# --------------------------------------------------------------------------
# 共享夹具：数据目录隔离 + 出站网络阻断 + 预置角色
# --------------------------------------------------------------------------

import pytest


_FILE_CONSTANTS = {
    "CHARACTERS_FILE": "characters.json",
    "MESSAGES_FILE": "messages.json",
    "MOMENTS_FILE": "moments.json",
    "SCHEDULES_FILE": "schedules.json",
    "SETTINGS_FILE": "settings.json",
    "LOGS_FILE": "logs.json",
    "TASKS_FILE": "tasks.json",
    "COMPANIES_FILE": "companies.json",
    "ECONOMY_LOGS_FILE": "economy_logs.json",
    "LOCATION_HISTORY_FILE": "location_history.json",
    "CHARACTER_HISTORY_FILE": "character_history.json",
    "API_CONFIGS_FILE": "api_configs.json",
    "LLM_USAGE_FILE": "llm_usage.json",
    "PRIVATE_GROUPS_FILE": "private_groups.json",
}


@pytest.fixture
def isolated_client(tmp_path, monkeypatch):
    """隔离数据目录 + 阻断出站网络 + 预置 3 个角色，返回 (client, characters)。"""
    import storage

    for const, fname in _FILE_CONSTANTS.items():
        monkeypatch.setattr(storage, const, str(tmp_path / fname), raising=False)

    import services.memory_service as ms
    monkeypatch.setattr(ms, "MEMORY_DB_FILE", str(tmp_path / "memory.db"), raising=False)
    monkeypatch.setattr(ms, "_memory_conn", None, raising=False)
    ms.init_memory_db()

    import aiohttp

    class _BlockedSession:
        def __init__(self, *a, **k):
            raise RuntimeError("network disabled in tests")

    monkeypatch.setattr(aiohttp, "ClientSession", _BlockedSession)

    from models import Character
    import main

    chars = [
        Character(name="张小满", age=28, gender="女", occupation="程序员", personality="外向、爱吐槽、热心"),
        Character(name="李建国", age=35, gender="男", occupation="教师", personality="稳重、话少"),
        Character(name="王小虎", age=24, gender="男", occupation="销售", personality="油嘴滑舌"),
    ]
    storage.save_characters(chars)

    from fastapi.testclient import TestClient
    return TestClient(main.app), chars
