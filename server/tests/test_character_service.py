"""测试 character_service 模块"""
import pytest
from services.character_service import (
    get_age_stage_from_age,
    get_age_personality_modifier,
    format_world_elapsed,
    get_moment_frequency_multiplier,
    can_refresh_avatar,
    can_refresh_signature,
)
from models import Character


class TestAgeStage:
    """测试年龄阶段判断"""
    
    def test_child(self):
        assert get_age_stage_from_age(5) == "儿童"
        assert get_age_stage_from_age(12) == "儿童"
    
    def test_teen(self):
        assert get_age_stage_from_age(13) == "青少年"
        assert get_age_stage_from_age(17) == "青少年"
    
    def test_youth(self):
        assert get_age_stage_from_age(18) == "青年"
        assert get_age_stage_from_age(40) == "青年"
    
    def test_middle_aged(self):
        assert get_age_stage_from_age(41) == "中年"
        assert get_age_stage_from_age(60) == "中年"
    
    def test_elderly(self):
        assert get_age_stage_from_age(61) == "老年"
        assert get_age_stage_from_age(100) == "老年"


class TestAgePersonalityModifier:
    """测试年龄性格修饰语"""
    
    def test_child_modifier(self):
        result = get_age_personality_modifier(8, "内向")
        assert "天真" in result or "儿童" in result
    
    def test_teen_modifier(self):
        result = get_age_personality_modifier(15, "内向")
        assert "叛逆" in result or "青少年" in result
    
    def test_youth_modifier(self):
        result = get_age_personality_modifier(25, "内向")
        assert "青年" in result or "精力" in result


class TestWorldTimeFormat:
    """测试世界时间格式化"""
    
    def test_zero_elapsed(self):
        result = format_world_elapsed(0)
        assert result is not None
    
    def test_one_day(self):
        result = format_world_elapsed(24 * 60 * 60 * 1000)
        assert result is not None
    
    def test_one_month(self):
        result = format_world_elapsed(30 * 24 * 60 * 60 * 1000)
        assert result is not None


class TestCharacterUtils:
    """测试角色工具函数"""
    
    def test_moment_frequency_multiplier_default(self):
        char = Character(
            id="test1",
            name="测试",
            gender="女",
            age=25,
            personality="测试性格",
            occupation="测试职业",
            age_stage="青年",
            is_alive=True,
        )
        result = get_moment_frequency_multiplier(char)
        assert result > 0
    
    def test_can_refresh_avatar_initial(self):
        char = Character(
            id="test2",
            name="测试",
            gender="女",
            age=25,
            personality="测试性格",
            occupation="测试职业",
            age_stage="青年",
            is_alive=True,
        )
        # 初始状态应该可以刷新
        result = can_refresh_avatar(char)
        assert result is True
