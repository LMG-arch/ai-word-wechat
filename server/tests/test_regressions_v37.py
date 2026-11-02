"""V3.7 回归测试：锁定本轮静态检查（pyflakes）发现的 NameError 类缺陷。

历史教训：这些函数此前「仅被导入、从未被测试真正调用」，因此
缺少 import 的运行时错误（random / time / save_characters 等）长期潜伏，
且多被自动运行循环的 try/except 静默吞掉，导致功能整体失效却不报错。
"""

import pytest

from services.memory_service import init_memory_db, apply_relationship_interaction
from services.economy_service import (
    apply_company_task_bonus_distribution,
    COMPANY_TASK_BONUS_RATIO,
)
from storage import (
    trim_avatar_change_history,
    trim_signature_change_history,
    mark_character_deceased,
)
from models import Character, Company, TaskItem


@pytest.fixture(autouse=True)
def _ensure_memory_db():
    # 关系/记忆表需先建立，模拟应用启动时的 init_memory_db()
    init_memory_db()


def _make_char(name: str = "回归测试角色") -> Character:
    return Character(name=name, age=30, gender="男", occupation="程序员", personality="温和")


class TestMemoryRandomFix:
    """apply_relationship_interaction 曾缺 import random → 命中即 NameError"""

    def test_chat_no_nameerror(self):
        r = apply_relationship_interaction("reg_a", "reg_b", "chat")
        assert isinstance(r, (int, float))
        assert 0.0 <= r <= 100.0

    def test_like_returns_number(self):
        r = apply_relationship_interaction("reg_c", "reg_d", "like")
        assert isinstance(r, (int, float))

    def test_meet_uses_random(self):
        r = apply_relationship_interaction("reg_g", "reg_h", "meet")
        assert isinstance(r, (int, float))

    def test_conflict_uses_negative_random(self):
        # conflict 分支调用 -random.randint(5, 15)
        r = apply_relationship_interaction("reg_e", "reg_f", "conflict")
        assert isinstance(r, (int, float))
        assert r >= 0.0

    def test_self_interaction_zero(self):
        assert apply_relationship_interaction("reg_x", "reg_x", "chat") == 0.0


class TestStorageTimeFix:
    """storage 曾缺 import time，以下函数在 now_ms=None 时命中 time.time() → NameError"""

    def test_trim_avatar_change_history(self):
        c = _make_char()
        c.avatar_change_history = []
        assert trim_avatar_change_history(c) == []

    def test_trim_signature_change_history(self):
        c = _make_char()
        c.signature_change_history = []
        assert trim_signature_change_history(c) == []

    def test_mark_deceased_uses_time(self):
        c = _make_char()
        assert c.is_alive is True
        mark_character_deceased(c, "回归测试-死亡")
        assert c.is_alive is False


class TestDanglingImportFixes:
    """曾指向不存在模块/函数的悬空导入，修复后应可正常导入"""

    def test_scheduler_proactive_functions_exist(self):
        from services import scheduler
        assert callable(getattr(scheduler, "generate_proactive_message", None))
        assert callable(getattr(scheduler, "record_proactive_message", None))

    def test_memory_get_character_memories_importable(self):
        from services.memory_service import get_character_memories
        assert callable(get_character_memories)

    def test_generate_proactive_message_returns_str(self):
        from services.scheduler import generate_proactive_message
        msg = generate_proactive_message(_make_char(), context="default")
        assert isinstance(msg, str) and msg


class TestCompanyTaskBonusDistribution:
    """task_routes 曾调用不存在的 economy.apply_company_task_bonus_distribution"""

    def test_distributes_bonus_and_deducts_funds(self):
        c1 = _make_char("成员A")
        c2 = _make_char("成员B")
        c1.money = 100.0
        c2.money = 100.0
        comp = Company(name="测试公司", legal_person_id=c1.id, member_ids=[c1.id, c2.id], funds=1000.0)
        task = TaskItem(title="测试任务", description="d", reward=100.0)

        res = apply_company_task_bonus_distribution([comp], 0, task, [c1, c2])

        # 奖金池 = 100 * 0.3 = 30，两人各 15
        per = 100.0 * COMPANY_TASK_BONUS_RATIO / 2
        assert res["success"] is True
        assert abs(c1.money - (100.0 + per)) < 1e-6
        assert abs(c2.money - (100.0 + per)) < 1e-6
        assert abs(comp.funds - (1000.0 - 100.0 * COMPANY_TASK_BONUS_RATIO)) < 1e-6

    def test_empty_members_noop(self):
        comp = Company(name="空公司", legal_person_id="x", member_ids=[], funds=500.0)
        task = TaskItem(title="t", description="d", reward=50.0)
        res = apply_company_task_bonus_distribution([comp], 0, task, [])
        assert res["success"] is True
        assert res["members"] == 0

    def test_invalid_index(self):
        task = TaskItem(title="t", description="d", reward=10.0)
        res = apply_company_task_bonus_distribution([], 5, task, [])
        assert res["success"] is False

