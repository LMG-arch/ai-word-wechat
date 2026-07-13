"""任务引擎服务单元测试（纯逻辑）"""
from models import Character, TaskItem, TaskType
from services.task_service import (
    choose_task_assignee,
    create_reflection_from_task,
    get_experience_context,
    update_character_experience,
)


def _char(cid: str = "c1", money: float = 100.0, occupation: str = "工程师", **kw) -> Character:
    return Character(
        id=cid, name=f"角色{cid}", age=30, gender="男",
        occupation=occupation, personality="", money=money, **kw,
    )


def _task(ttype: str = "code", **kw) -> TaskItem:
    return TaskItem(title="任务", description="", task_type=TaskType(ttype), **kw)


class TestChooseTaskAssignee:
    def test_preferred_wins(self):
        c1, c2 = _char("c1"), _char("c2")
        assert choose_task_assignee(_task("code"), [c1, c2], preferred_character_id="c2") is c2

    def test_preferred_dead_returns_none(self):
        c1 = _char("c1")
        c1.is_alive = False
        assert choose_task_assignee(_task("code"), [c1], preferred_character_id="c1") is None

    def test_occupation_match_scores_higher(self):
        # 职业含任务关键词（开发/工程）者稳定优先于无匹配者
        coder = _char("c1", occupation="后端开发工程师")
        baker = _char("c2", occupation="面包师")
        for _ in range(20):
            assert choose_task_assignee(_task("code"), [baker, coder]) is coder


class TestCreateReflection:
    def test_approved(self):
        r = create_reflection_from_task(_task("code"), approved=True, review_notes="good")
        assert r.success is True
        assert r.what_went_well
        assert r.review_notes == "good"

    def test_rejected(self):
        r = create_reflection_from_task(_task("code"), approved=False, review_notes="bad")
        assert r.success is False
        assert r.what_went_wrong
        assert r.root_causes


class TestExperienceContext:
    def test_empty(self):
        assert get_experience_context(_char(), "code") == ""

    def test_with_experience(self):
        c = _char()
        c.experience_skills = {
            "code": {
                "count": 3, "success_count": 2,
                "lessons": ["写好注释"], "success_rate": 0.666, "last_used": 0,
            }
        }
        ctx = get_experience_context(c, "code")
        assert "3" in ctx
        assert "66%" in ctx or "67%" in ctx
        assert "写好注释" in ctx


class TestUpdateExperience:
    def test_accumulates(self):
        c = _char()
        r = create_reflection_from_task(_task("code"), approved=True, review_notes="")
        update_character_experience(c, "code", r, success=True)
        assert c.experience_skills["code"]["count"] == 1
        assert c.experience_skills["code"]["success_rate"] == 1.0
        update_character_experience(c, "code", r, success=True)
        assert c.experience_skills["code"]["count"] == 2
