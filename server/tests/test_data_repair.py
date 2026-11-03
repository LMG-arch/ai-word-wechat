"""历史数据体检与自愈的回归测试（V4.1）。

覆盖用户实际踩到的三类历史错乱：
1. 自由文本职业（「独立插画师」「大学生」）落不进职业阶梯，头衔变「助理」
2. 年龄与身份矛盾（54 岁「学生」、2 岁「学生」）
3. 关系只写了一半（动态说结婚了，字段还是陌生人）
"""
import storage

from models import Character, MomentPost
from services.career_service import (
    MAX_STUDENT_AGE,
    ladder_for,
    ladder_key,
    level_from_exp,
    student_stage_for_age,
    title_for,
)
from services.data_repair import (
    _fix_career_level,
    _fix_occupation,
    _rebuild_family_from_moments,
    run_data_repair,
)


# ---------------------------------------------------------------- 职业归类

def test_ladder_key_maps_free_text_occupation():
    assert ladder_key("独立插画师") == "设计师"
    assert ladder_key("儿童绘本插画师") == "设计师"
    assert ladder_key("UI设计师") == "设计师"
    assert ladder_key("大学生") == "学生"
    assert ladder_key("在读研究生") == "学生"
    assert ladder_key("退休教师") == "教师"
    assert ladder_key("前端开发工程师") == "程序员"
    assert ladder_key("程序员") == "程序员"
    assert ladder_key("宇航员") == ""


def test_ladder_for_uses_matched_ladder():
    assert ladder_for("独立插画师") == ladder_for("设计师")
    assert ladder_for("大学生") == ladder_for("学生")
    assert ladder_for("宇航员") == ladder_for("不存在的职业")


def test_title_for_never_returns_assistant_for_known_profession():
    assert title_for("独立插画师", 1) == "设计助理"
    assert title_for("儿童绘本插画师", 3) == "资深设计师"
    assert title_for("大学生", 1) == "大学生"


def test_student_title_follows_age():
    assert title_for("学生", 1, age=10) == "小学生"
    assert title_for("学生", 1, age=20) == "大学生"
    assert title_for("学生", 1, age=32) == "博士生"


def test_overage_student_does_not_claim_primary_school():
    # 超龄学生不猜学段，原样显示，绝不出现「54 岁 · 小学生」
    assert title_for("学生", 1, age=MAX_STUDENT_AGE + 20) == "学生"


def test_student_stage_boundaries():
    assert student_stage_for_age(6) == "幼儿园"
    assert student_stage_for_age(12) == "小学生"
    assert student_stage_for_age(15) == "初中生"
    assert student_stage_for_age(18) == "高中生"
    assert student_stage_for_age(22) == "大学生"
    assert student_stage_for_age(27) == "研究生"
    assert student_stage_for_age(35) == "博士生"
    assert student_stage_for_age(36) is None


def test_level_from_exp_is_monotonic():
    assert [level_from_exp(e) for e in (0, 119, 120, 359, 360, 799, 800, 1599, 1600)] == [
        1, 1, 2, 2, 3, 3, 4, 4, 5,
    ]
    assert level_from_exp(99999) == 5


# ---------------------------------------------------------------- 角色修复

def test_fix_occupation_demotes_overage_student():
    c = Character(name="小李", age=54, gender="男", occupation="学生", personality="温柔")
    note = _fix_occupation(c)
    assert note and "自由职业" in note
    assert c.occupation == "自由职业"


def test_fix_occupation_keeps_phd_student():
    c = Character(name="博士", age=32, gender="女", occupation="学生", personality="专注")
    assert _fix_occupation(c) is None
    assert c.occupation == "学生"


def test_fix_occupation_demotes_baby_student():
    c = Character(name="宝宝", age=2, gender="女", occupation="学生", personality="安静")
    note = _fix_occupation(c)
    assert note and c.occupation == "幼儿"


def test_fix_career_level_realigns_to_exp():
    c = Character(
        name="虚高", age=30, gender="男", occupation="程序员",
        personality="认真", career_level=4, career_exp=0,
    )
    note = _fix_career_level(c)
    assert note and c.career_level == 1


# ---------------------------------------------------------------- 关系重建

def test_rebuild_marriage_from_moment(isolated_client, monkeypatch):
    client, chars = isolated_client
    a, b = chars[0], chars[1]
    storage.save_moments([MomentPost(
        author_id=a.id, author_name=a.name,
        content=f"{a.name} 和 {b.name} 结婚了", trigger_type="family",
    )])

    notes = _rebuild_family_from_moments(chars)
    assert notes and a.spouse_id == b.id and b.spouse_id == a.id
    assert a.relationship_stage == "spouse"
    assert a.partner_id == b.id and b.partner_id == a.id


def test_rebuild_marriage_skips_ambiguous_names(isolated_client):
    client, chars = isolated_client
    dup = Character(name=chars[0].name, age=30, gender="女", occupation="教师", personality="安静")
    storage.save_characters(chars + [dup])
    storage.save_moments([MomentPost(
        author_id=chars[0].id, author_name=chars[0].name,
        content=f"{chars[0].name} 和 {chars[1].name} 结婚了", trigger_type="family",
    )])
    notes = _rebuild_family_from_moments(chars + [dup])
    assert notes == []
    assert chars[0].spouse_id is None


def test_rebuild_marriage_does_not_override_existing_spouse(isolated_client):
    client, chars = isolated_client
    a, b, c = chars
    a.spouse_id = c.id
    c.spouse_id = a.id
    storage.save_characters(chars)
    storage.save_moments([MomentPost(
        author_id=a.id, author_name=a.name,
        content=f"{a.name} 和 {b.name} 结婚了", trigger_type="family",
    )])
    _rebuild_family_from_moments(chars)
    assert a.spouse_id == c.id


# ---------------------------------------------------------------- 端到端

def test_run_data_repair_end_to_end_and_idempotent(isolated_client):
    client, chars = isolated_client
    dirty = Character(
        name="老张", age=58, gender="男", occupation="学生", personality="温和",
        career_level=3, career_exp=0,
    )
    storage.save_characters(chars + [dirty])

    report = run_data_repair(force=True)
    assert report["fixed_count"] >= 2
    assert report["backup"]  # 有修复就留备份

    saved = {c.name: c for c in storage.get_characters()}
    assert saved["老张"].occupation == "自由职业"
    assert saved["老张"].career_level == 1
    assert saved["老张"].career_title == "新手"

    second = run_data_repair()
    assert second.get("skipped") is True


def test_run_data_repair_marks_settings_version(isolated_client):
    run_data_repair(force=True)
    settings = storage.get_settings()
    assert settings.data_repair_version >= 1
    assert settings.last_age_growth_time > 0


# ---------------------------------------------------------------- 日程

def test_schedule_events_follow_occupation():
    from services.world_service import schedule_events_for

    coder = Character(name="阿码", age=28, gender="男", occupation="程序员", personality="专注")
    illustrator = Character(name="阿画", age=30, gender="女", occupation="独立插画师", personality="安静")
    assert [e.activity for e in schedule_events_for(coder)] == ["写代码", "午餐休息", "继续编码", "放松时间"]
    # 自由文本职业先归类到「设计师」，不能落回 default 的「工作/午餐/工作」
    assert "画稿" in [e.activity for e in schedule_events_for(illustrator)]


def test_fix_schedules_realigns_events_and_drops_orphan(isolated_client):
    from models import CharacterSchedule, ScheduleEvent
    from services.data_repair import _fix_schedules

    client, chars = isolated_client
    boss = chars[0]
    boss.occupation = "程序员"
    storage.save_characters(chars)

    stale = CharacterSchedule(
        character_id=boss.id, day_index=1,
        summary=f"{boss.name}（学生）第 1 天的安排",
        events=[
            ScheduleEvent(start_time="08:00", end_time="12:00", location="学校", activity="上课"),
            ScheduleEvent(start_time="14:00", end_time="17:00", location="学校", activity="自习"),
        ],
        generated_by="rule_engine_v3",
    )
    orphan = CharacterSchedule(
        character_id="ghost-id", day_index=1, summary="幽灵（学生）第 1 天的安排",
        events=[], generated_by="rule_engine_v3",
    )
    storage.save_schedules([stale, orphan])

    notes = _fix_schedules(chars)
    assert notes

    saved = storage.get_schedules()
    assert len(saved) == 1                    # 孤儿被清掉
    only = saved[0]
    assert "（程序员）" in only.summary
    assert [e.activity for e in only.events][0] == "写代码"
