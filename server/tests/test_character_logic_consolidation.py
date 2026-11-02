"""storage ↔ character_service 语义分裂的修复回归测试。

背景：这两个模块曾有 24 个同名函数，实现各自演化，其中三处**语义已经不同**：

1. ``format_world_elapsed`` —— storage 出「X年X月X天」，service 出「第X天 HH:00」，
   而前端 JS 又是「X年Y个月Z天」。同一界面出现两套时间文案。
2. ``normalize_parent_ids`` —— storage 返回清理后的 ID 列表，service 返回提示信息，
   且 service 版漏了「去重」与「剔除自身」，会留下脏数据。
3. ``apply_age_stage_constraints`` —— storage 管职业（含老年退休），service 管零花钱，
   各做一半，导致「老人不变退休」「空职业青少年不补学生」等遗漏。

现已合并为单一实现（character_service 为唯一真源，storage 死代码已删除），
本文件锁定合并后的正确行为，防止再次分裂。
"""

import pytest

from models import Character
from services.character_service import (
    format_world_elapsed,
    normalize_parent_ids,
    apply_age_stage_constraints,
)

DAY = 24 * 60 * 60 * 1000


def _char(**kw) -> Character:
    base = dict(name="测试角色", age=25, gender="男", occupation="程序员", personality="温和")
    base.update(kw)
    return Character(**base)


class TestWorldElapsedFormat:
    """世界时间格式必须与前端 formatWorldTime() 一致：N年N个月N天。"""

    @pytest.mark.parametrize(
        "ms,expected",
        [
            (0, "0天"),
            (DAY, "1天"),
            (29 * DAY, "29天"),
            (30 * DAY, "1个月"),
            (360 * DAY, "1年"),
            (395 * DAY, "1年1个月5天"),
            (365 * DAY, "1年5天"),
        ],
    )
    def test_format(self, ms, expected):
        assert format_world_elapsed(ms) == expected

    def test_negative_clamped(self):
        assert format_world_elapsed(-1000) == "0天"

    def test_no_hour_suffix(self):
        """确保旧实现的「第X天 HH:00」不再出现。"""
        assert "第" not in format_world_elapsed(5 * DAY)
        assert ":" not in format_world_elapsed(5 * DAY)


class TestNormalizeParentIds:
    def test_dedup_self_and_missing(self):
        c = _char(id="a", parent_ids=["a", "b", "b", "x"])
        result = normalize_parent_ids(c, {"a", "b", "c"})
        assert result == ["b"]
        assert c.parent_ids == ["b"]  # 副作用同步写回

    def test_no_all_ids_only_cleans_self_and_dup(self):
        """all_character_ids 为 None 时只做去重与剔除自身，不过滤存在性。"""
        c = _char(id="a", parent_ids=["a", "b", "b", "z"])
        result = normalize_parent_ids(c, None)
        assert result == ["b", "z"]

    def test_empty(self):
        c = _char(id="a", parent_ids=[])
        assert normalize_parent_ids(c, {"a"}) == []
        assert c.parent_ids == []


class TestAgeStageConstraints:
    def test_child_money_capped_and_occupation(self):
        c = _char(age=8, money=500, occupation="画家")
        notes = apply_age_stage_constraints(c)
        assert c.money == 50
        assert c.occupation == "学生"
        assert any("零花钱" in n for n in notes)

    def test_teen_money_capped(self):
        c = _char(age=15, money=500, occupation="")
        notes = apply_age_stage_constraints(c)
        assert c.money == 100
        assert c.occupation == "学生"
        assert any("职业" in n for n in notes)

    def test_elder_retires_when_no_occupation(self):
        c = _char(age=70, occupation="")
        notes = apply_age_stage_constraints(c)
        assert c.occupation == "退休"
        assert any("退休" in n for n in notes)

    def test_elder_keeps_occupation(self):
        c = _char(age=70, occupation="教授")
        notes = apply_age_stage_constraints(c)
        assert c.occupation == "教授"
        assert notes == []

    def test_young_adult_untouched(self):
        c = _char(age=30, money=999, occupation="工程师")
        notes = apply_age_stage_constraints(c)
        assert c.money == 999
        assert c.occupation == "工程师"
        assert notes == []


class TestNoDuplicateInStorage:
    """确保 storage 不再重复定义这些易漂移的业务函数（单一真源原则）。"""

    def test_storage_does_not_redefine_business_logic(self):
        import storage

        for name in (
            "format_world_elapsed",
            "normalize_parent_ids",
            "apply_age_stage_constraints",
            "can_refresh_avatar",
            "can_refresh_signature",
            "ensure_character_defaults",
            "get_age_stage_from_age",
        ):
            assert not hasattr(storage, name), f"storage 不应再定义 {name}，应统一在 character_service"
