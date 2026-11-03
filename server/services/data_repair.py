"""历史数据体检与自愈（V4.1）

项目跑了很久，`data/*.json` 里积累了一批「能加载但一看就不对」的历史数据：

- 54 岁、32 岁的人职业还是「学生」（生成时没做年龄校验）
- 职业是自由文本（「独立插画师」「大学生」），落不进 16 条职业阶梯，
  推导出来的头衔全是 DEFAULT_LADDER 的「助理」
- 伴侣 / 配偶 / 孩子关系只写了一半，A 指向 B 但 B 不指向 A
- 动态 `liked_by` 里留着已删除角色的 id，点赞名单点进去没人
- `last_age_growth_time` 缺失 → 每次冷启动都给全员 +1 岁

这些不是「用户手动改坏」，是程序长期运行的沉淀。这个模块把它们一次性收敛到
自洽状态，规则全部可解释、可回滚（执行前整目录备份），并且带版本号只跑一次。

设计约束：
- 不删除任何用户内容（动态 / 消息 / 红包都不动），只修字段一致性
- 不擅自猜测「这个人应该做什么工作」，只在**明确矛盾**时降级
  （超龄学生 → 自由职业，超低龄学生 → 幼儿）
- 幂等：同一份数据跑两次，第二次报告为空
"""
from __future__ import annotations

import json
import os
import re
import shutil
import time
from typing import Any, Dict, List, Optional

from storage import (
    get_characters,
    get_moments,
    get_schedules,
    get_settings,
    save_characters,
    save_moments,
    save_schedules,
    save_settings,
)

from services.career_service import (
    DEFAULT_LADDER,
    MAX_STUDENT_AGE,
    is_student,
    ladder_key,
    level_from_exp,
    student_stage_for_age,
    title_for,
)

# 修复逻辑版本：改动规则时 +1，老库会重新体检一次
REPAIR_VERSION = 6

# 需要备份的数据文件（宁多勿少，备份很便宜）
BACKUP_FILES = (
    "characters.json",
    "moments.json",
    "settings.json",
    "messages.json",
    "red_packets.json",
    "schedules.json",
    "tasks.json",
)


def _data_dir() -> str:
    """数据目录以 storage 当前指向为准，测试里 monkeypatch 后备份不会写到真实 data/。"""
    import storage as _storage

    return os.path.dirname(os.path.abspath(_storage.CHARACTERS_FILE))


def _backup_root() -> str:
    return os.path.join(_data_dir(), "backups")


def backup_data(reason: str = "repair") -> Optional[str]:
    """把关键数据文件整份备份到 data/backups/<reason>-<ts>/，返回目录。"""
    root = _backup_root()
    try:
        os.makedirs(root, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        dest = os.path.join(root, f"{reason}-{stamp}")
        os.makedirs(dest, exist_ok=True)
        copied = 0
        data_dir = _data_dir()
        for name in BACKUP_FILES:
            src = os.path.join(data_dir, name)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(dest, name))
                copied += 1
        if not copied:
            shutil.rmtree(dest, ignore_errors=True)
            return None
        return dest
    except Exception:
        return None


# ---------------------------------------------------------------- 角色：职业

def _fix_occupation(character) -> Optional[str]:
    """职业与年龄明显矛盾时降级，返回变更说明。"""
    occ = (character.occupation or "").strip()
    age = int(getattr(character, "age", 0) or 0)

    if is_student(occ):
        if age > MAX_STUDENT_AGE:
            # 不猜具体职业，只把不可能的身份降级；等级仍由经验决定，不凭空拔高
            character.occupation = "自由职业"
            character.career_title = ""
            return f"{character.name}：{age} 岁仍是「{occ}」→ 自由职业"
        if age <= 6:
            character.occupation = "幼儿"
            character.career_level = 1
            character.career_title = ""
            return f"{character.name}：{age} 岁却是「{occ}」→ 幼儿"
        if age <= 18 and occ in ("大学生", "研究生", "博士生"):
            # 未成年人挂大学学历，按年龄回退到对应学段
            stage = student_stage_for_age(age)
            if stage and stage != occ:
                character.occupation = "学生"
                character.career_title = stage
                return f"{character.name}：{age} 岁却是「{occ}」→ {stage}"
    return None


def _fix_career_level(character) -> Optional[str]:
    """等级与经验对齐。历史 bug 会造成「等级虚高但经验为 0」，进度条永远卡满。"""
    level = int(getattr(character, "career_level", 1) or 1)
    exp = int(getattr(character, "career_exp", 0) or 0)
    want = level_from_exp(exp)
    if level != want:
        character.career_level = want
        character.career_title = ""
        return f"{character.name}：等级 {level} → {want}（经验 {exp}）"
    return None


def _fix_career_title(character) -> Optional[str]:
    """重算从没被正确推导过的头衔。

    只处理「空」和「DEFAULT_LADDER 里的通用词」这两种确定是推导失败的情况，
    用户手动改过的自定义头衔（如「架构师」）不动。
    """
    saved = (getattr(character, "career_title", "") or "").strip()
    if saved and saved not in DEFAULT_LADDER:
        return None
    want = title_for(
        character.occupation,
        int(getattr(character, "career_level", 1) or 1),
        int(getattr(character, "age", 0) or 0),
    )
    if want and want != saved:
        character.career_title = want
        return f"{character.name}：头衔「{saved or '空'}」→「{want}」（{character.occupation}）"
    return None


# ---------------------------------------------------------------- 角色：关系

def _fix_relationships(characters: List[Any]) -> List[str]:
    by_id = {c.id: c for c in characters}
    notes: List[str] = []

    for c in characters:
        for field in ("partner_id", "spouse_id"):
            target = getattr(c, field, None)
            if target and target not in by_id:
                setattr(c, field, None)
                notes.append(f"{c.name}：{field} 指向已删除角色，已清空")

        # 孩子列表去重 + 清理悬空
        kids = [k for k in (getattr(c, "children_ids", None) or []) if k in by_id]
        if len(kids) != len(getattr(c, "children_ids", None) or []):
            c.children_ids = kids
            notes.append(f"{c.name}：孩子列表中移除不存在的角色")

        parents = [p for p in (getattr(c, "parent_ids", None) or []) if p in by_id]
        if len(parents) != len(getattr(c, "parent_ids", None) or []):
            c.parent_ids = parents
            notes.append(f"{c.name}：父母列表中移除不存在的角色")

    # 双向补全：A → B 存在，但 B → A 缺失
    for c in characters:
        spouse = getattr(c, "spouse_id", None)
        if spouse and spouse in by_id:
            other = by_id[spouse]
            if getattr(other, "spouse_id", None) != c.id:
                other.spouse_id = c.id
                notes.append(f"{other.name}：补齐配偶指向 → {c.name}")
            if (getattr(other, "relationship_stage", "") or "") != "spouse":
                other.relationship_stage = "spouse"
                notes.append(f"{other.name}：关系阶段补齐为 spouse")

        partner = getattr(c, "partner_id", None)
        if partner and partner in by_id:
            other = by_id[partner]
            if not getattr(other, "partner_id", None):
                other.partner_id = c.id
                notes.append(f"{other.name}：补齐伴侣指向 → {c.name}")

    # 孩子 ↔ 父母 反向补全
    for c in characters:
        for kid in getattr(c, "children_ids", None) or []:
            child = by_id.get(kid)
            if child and c.id not in (getattr(child, "parent_ids", None) or []):
                child.parent_ids = list(getattr(child, "parent_ids", None) or []) + [c.id]
                notes.append(f"{child.name}：补齐父母指向 → {c.name}")

    return notes


# 系统发的结婚动态：「小李 和 测试角色 结婚了」
MARRIAGE_RE = re.compile(r"^(.+?)\s*和\s*(.+?)\s*结婚了$")


def _rebuild_family_from_moments(characters: List[Any]) -> List[str]:
    """从「结婚了」动态反向补回丢失的配偶关系。

    历史上有过一段丢字段的时期：动态明明写了「A 和 B 结婚了」，但两个角色的
    `spouse_id` / `relationship_stage` 全是空的，家庭页显示陌生人。
    既然系统自己发过这条动态，它就是事实记录——只在双方都还没有配偶时补回。
    """
    by_name: Dict[str, List[Any]] = {}
    for c in characters:
        by_name.setdefault(c.name, []).append(c)

    notes: List[str] = []
    for m in get_moments():
        if (getattr(m, "trigger_type", "") or "") != "family":
            continue
        matched = MARRIAGE_RE.match((m.content or "").strip())
        if not matched:
            continue
        a_list = by_name.get(matched.group(1).strip()) or []
        b_list = by_name.get(matched.group(2).strip()) or []
        if len(a_list) != 1 or len(b_list) != 1:
            # 重名角色无法确定是哪两位，留给人判断
            continue
        a, b = a_list[0], b_list[0]
        if a.id == b.id:
            continue
        if (a.spouse_id and a.spouse_id != b.id) or (b.spouse_id and b.spouse_id != a.id):
            continue  # 已有其他配偶，不覆盖当前状态

        touched = False
        for me, other in ((a, b), (b, a)):
            if getattr(me, "spouse_id", None) != other.id:
                me.spouse_id = other.id
                touched = True
            if getattr(me, "partner_id", None) != other.id:
                me.partner_id = other.id
                touched = True
            if (getattr(me, "relationship_stage", "") or "") != "spouse":
                me.relationship_stage = "spouse"
                touched = True
        if touched:
            notes.append(f"依据历史动态补回婚姻关系：{a.name} ↔ {b.name}")
    return notes


# ---------------------------------------------------------------- 日程

SCHEDULE_SUMMARY_RE = re.compile(r"^(.+?)（(.+?)）第 (\d+) 天的安排$")


def _fix_schedules(characters: List[Any]) -> List[str]:
    """日程与角色档案对齐：摘要里的职业、事件模板、以及指向已删除角色的残留。"""
    from services.world_service import schedule_events_for

    by_id = {c.id: c for c in characters}
    schedules = get_schedules()
    notes: List[str] = []
    dirty = False
    kept: List[Any] = []

    for item in schedules:
        char = by_id.get(getattr(item, "character_id", ""))
        if char is None:
            # 角色已删除，日程成了孤儿
            dirty = True
            notes.append(f"清理孤儿日程：{getattr(item, 'summary', '')[:24]}")
            continue
        kept.append(item)

        summary = getattr(item, "summary", "") or ""
        matched = SCHEDULE_SUMMARY_RE.match(summary)
        old_occ = matched.group(2) if matched else None
        day_index = int(matched.group(3)) if matched else int(getattr(item, "day_index", 0) or 0)

        changed_here = False
        if matched and old_occ != (char.occupation or ""):
            item.summary = f"{char.name}（{char.occupation or '自由职业'}）第 {day_index} 天的安排"
            notes.append(f"{char.name}：日程摘要「{old_occ}」→「{char.occupation}」")
            changed_here = True

        # 规则引擎生成的日程要跟着职业走；用户/LLM 自定义过的（generated_by 不是 rule_engine）不动
        if (getattr(item, "generated_by", "") or "").startswith("rule_engine"):
            want = schedule_events_for(char)
            cur = [(e.start_time, e.end_time, e.location, e.activity) for e in (item.events or [])]
            fresh = [(e.start_time, e.end_time, e.location, e.activity) for e in want]
            if cur != fresh:
                item.events = want
                notes.append(f"{char.name}：日程安排按「{char.occupation or '自由职业'}」重排")
                changed_here = True

        if changed_here:
            dirty = True

    if dirty:
        save_schedules(kept)
    return notes


# ---------------------------------------------------------------- 动态

def _fix_moments(characters: List[Any]) -> List[str]:
    valid = {c.id for c in characters}
    valid.add("user")
    moments = get_moments()
    notes: List[str] = []
    dirty = False

    for m in moments:
        liked = m.liked_by or []
        cleaned = []
        for uid in liked:
            if uid in valid and uid not in cleaned:
                cleaned.append(uid)
        if cleaned != liked:
            dropped = len(liked) - len(cleaned)
            m.liked_by = cleaned
            dirty = True
            notes.append(
                f"动态「{(m.content or '')[:12]}」：点赞名单清理 {dropped} 条悬空/重复 id"
            )

        mentioned = [uid for uid in (m.mentioned_ids or []) if uid in valid]
        if mentioned != (m.mentioned_ids or []):
            m.mentioned_ids = mentioned
            dirty = True
            notes.append(f"动态「{(m.content or '')[:12]}」：@ 名单移除不存在的角色")

    if dirty:
        save_moments(moments)
    return notes


def _fix_tasks(characters: List[Any]) -> List[str]:
    """任务里指向已删除角色的接收人 / 协作人。

    这类任务会永久卡在 in_progress：审核时找不到人，奖励发不出去，
    用户看到的是「进行中」但永远推不动。这里把悬空的人摘掉、退回待接取。
    已完成的任务只清协作者，不回退状态（那是已经结算过的历史）。
    """
    from storage import get_tasks, save_tasks
    from models import TaskStatus

    valid = {c.id for c in characters}
    tasks = get_tasks()
    notes: List[str] = []
    dirty = False

    for t in tasks:
        status = getattr(getattr(t, "status", None), "value", str(getattr(t, "status", "")))
        assignee = getattr(t, "assignee_id", None)
        if assignee and assignee not in valid and status not in ("completed",):
            t.assignee_id = None
            t.submitter_id = None
            t.status = TaskStatus.OPEN
            dirty = True
            notes.append(f"任务「{t.title[:14]}」：接收人已不存在，退回待接取")

        collaborators = list(getattr(t, "collaborator_ids", []) or [])
        kept = [cid for cid in collaborators if cid in valid]
        if kept != collaborators:
            t.collaborator_ids = kept
            dirty = True
            notes.append(f"任务「{t.title[:14]}」：移除 {len(collaborators) - len(kept)} 个不存在的协作者")

    if dirty:
        save_tasks(tasks)
    return notes


def count_orphans(characters: List[Any]) -> Dict[str, int]:
    """只统计不删除：聊天记录和红包属于历史，删了就真没了。

    这些数字会出现在启动报告里，让「数据里有多少指向空处的引用」可见。
    """
    from storage import get_messages, get_red_packets

    valid = {c.id for c in characters}
    orphan_messages = sum(
        1 for m in get_messages()
        if str(getattr(m, "conversation_id", "")) not in valid
        and not str(getattr(m, "conversation_id", "")).startswith("group:")
    )
    orphan_packets = sum(
        1 for p in get_red_packets()
        if str(getattr(p, "conversation_id", "")) not in valid
        and not str(getattr(p, "conversation_id", "")).startswith("group:")
    )
    return {"messages": orphan_messages, "red_packets": orphan_packets}


# ---------------------------------------------------------------- 主入口

def normalize_new_character(character) -> List[str]:
    """新建角色时就把职业/等级/头衔校准好，避免脏数据要等下次启动体检才修。

    返回变更说明（用于写日志），无变更返回空列表。
    """
    notes: List[str] = []
    note = _fix_occupation(character)
    if note:
        notes.append(note)
    note = _fix_career_level(character)
    if note:
        notes.append(note)
    if not (getattr(character, "career_title", "") or "").strip():
        character.career_title = title_for(
            character.occupation,
            int(getattr(character, "career_level", 1) or 1),
            int(getattr(character, "age", 0) or 0),
        )
    return notes


def run_data_repair(force: bool = False) -> Dict[str, Any]:
    """体检并修复历史数据，返回报告。已修复过则直接返回 skipped。"""
    settings = get_settings()
    version = int(getattr(settings, "data_repair_version", 0) or 0)
    if not force and version >= REPAIR_VERSION:
        return {"skipped": True, "version": version}

    report: Dict[str, Any] = {
        "version": REPAIR_VERSION,
        "backup": None,
        "occupation": [],
        "career_level": [],
        "career_title": [],
        "relationship": [],
        "moments": [],
        "schedules": [],
        "tasks": [],
        "orphans": {},
        "settings": [],
        "duplicate_names": [],
        "ok": True,
    }

    characters = get_characters()
    if characters:
        report["backup"] = backup_data("repair")

    changed = False

    for c in characters:
        note = _fix_occupation(c)
        if note:
            report["occupation"].append(note)
            changed = True

    for c in characters:
        note = _fix_career_level(c)
        if note:
            report["career_level"].append(note)
            changed = True

    for c in characters:
        note = _fix_career_title(c)
        if note:
            report["career_title"].append(note)
            changed = True

    rel_notes = _fix_relationships(characters)
    marriage_notes = _rebuild_family_from_moments(characters)
    if rel_notes or marriage_notes:
        report["relationship"] = rel_notes + marriage_notes
        changed = True

    if changed:
        save_characters(characters)

    report["moments"] = _fix_moments(characters)
    report["schedules"] = _fix_schedules(characters)
    report["tasks"] = _fix_tasks(characters)
    report["orphans"] = count_orphans(characters)

    # 重名只报告，不自动改：名字是角色人设的一部分，改名会误导用户
    seen: Dict[str, List[str]] = {}
    for c in characters:
        seen.setdefault(c.name, []).append(f"{c.age}岁")
    report["duplicate_names"] = [
        f"「{name}」有 {len(ages)} 个角色（{', '.join(ages)}）"
        for name, ages in seen.items()
        if len(ages) > 1
    ]

    # 年龄增长时间戳缺失 → 冷启动不会立刻给全员 +1 岁
    last_growth = int(getattr(settings, "last_age_growth_time", 0) or 0)
    if last_growth <= 0:
        settings.last_age_growth_time = int(time.time() * 1000)
        report["settings"].append("补齐 last_age_growth_time，避免启动即全员 +1 岁")

    settings.data_repair_version = REPAIR_VERSION
    save_settings(settings)

    total = (
        len(report["occupation"])
        + len(report["career_level"])
        + len(report["career_title"])
        + len(report["relationship"])
        + len(report["moments"])
        + len(report["schedules"])
        + len(report["tasks"])
    )
    report["fixed_count"] = total

    # 没有任何实质修复就不留备份，避免每次冷启动堆一个空目录
    if total == 0 and report.get("backup"):
        shutil.rmtree(report["backup"], ignore_errors=True)
        report["backup"] = None
    return report


def format_report(report: Dict[str, Any]) -> str:
    """把报告渲染成可打印的多行文本。"""
    if report.get("skipped"):
        return f"[数据体检] 已是最新（v{report.get('version')}），跳过"

    lines = [f"[数据体检] v{report['version']} 修复 {report.get('fixed_count', 0)} 项"]
    if report.get("backup"):
        lines.append(f"  备份：{report['backup']}")
    for key, label in (
        ("occupation", "职业与年龄矛盾"),
        ("career_level", "等级与经验不一致"),
        ("career_title", "头衔推导失败"),
        ("relationship", "家庭关系不一致"),
        ("moments", "动态悬空引用"),
        ("schedules", "日程摘要与职业不一致"),
        ("tasks", "任务里的悬空接收人"),
        ("settings", "设置项缺失"),
        ("duplicate_names", "重名提醒"),
    ):
        items = report.get(key) or []
        if not items:
            continue
        lines.append(f"  · {label}（{len(items)}）")
        for item in items[:12]:
            lines.append(f"    - {item}")
        if len(items) > 12:
            lines.append(f"    - …… 另有 {len(items) - 12} 条")

    orphans = report.get("orphans") or {}
    if orphans.get("messages") or orphans.get("red_packets"):
        lines.append(
            f"  · 历史遗留引用（不删除，仅提示）：{orphans.get('messages', 0)} 条消息、"
            f"{orphans.get('red_packets', 0)} 个红包指向已删除的会话"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print(format_report(run_data_repair(force=True)))
