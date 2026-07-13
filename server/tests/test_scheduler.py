"""调度器 / 角色主动对话单元测试"""
import random
import pytest
from models import Character
from services.scheduler import (
    Reminder,
    can_proactively_message,
    record_proactive_message,
    should_character_reach_out,
    check_special_date_greetings,
)


def _char(cid: str = "c1", money: float = 100.0, age: int = 30, **kw) -> Character:
    return Character(
        id=cid, name=f"角色{cid}", age=age, gender="男",
        occupation="工程师", personality="", money=money, **kw,
    )


class TestReminder:
    def test_construction(self):
        r = Reminder("r1", "c1", "reminder", 123456, "喝水")
        assert r.id == "r1"
        assert r.is_active is True
        assert r.repeat == "none"


class TestProactiveCooldown:
    def test_cooldown_blocks_immediately(self):
        record_proactive_message("c-cool")
        assert can_proactively_message("c-cool") is False

    def test_fresh_character_can(self):
        assert can_proactively_message("never-seen-char") is True


class TestShouldReachOut:
    def test_deterministic_true(self, monkeypatch):
        monkeypatch.setattr(random, "random", lambda: 0.0)
        # 高亲密 + 负资产 + 青少年 => 高概率，random=0 必为 True
        assert should_character_reach_out(_char(money=-10, age=16), intimacy=90) is True

    def test_deterministic_false(self, monkeypatch):
        monkeypatch.setattr(random, "random", lambda: 1.0)
        assert should_character_reach_out(_char(money=500, age=40), intimacy=5) is False

    def test_probability_direction(self, monkeypatch):
        # 固定 random=0.1：高亲密/高压力者必主动，低亲密/宽裕者必不主动
        monkeypatch.setattr(random, "random", lambda: 0.1)
        low = sum(1 for _ in range(200) if should_character_reach_out(_char(money=500, age=40), intimacy=5))
        high = sum(1 for _ in range(200) if should_character_reach_out(_char(money=-10, age=16), intimacy=90))
        assert high > low


class TestSpecialDateGreetings:
    def test_empty_characters(self):
        assert check_special_date_greetings([]) == []
