"""恋爱 → 结婚 → 生子（V4.0 包B1）

关系阶段由「双向亲密度」决定，角色字段持久化在 characters.json 上：

    stranger  陌生      < 35
    friend    朋友      35 - 54
    close     密友      55 - 74
    lover     情侣      75 - 87
    spouse    夫妻      >= 88

设计原则：
- 纯函数判定 + 显式写回，方便测试；
- 孩子是真正的 Character，带 parent_ids，会随世界时间长大；
- 所有对外文案走模板，不烧 token。
"""
from __future__ import annotations

import random
import time
import uuid
from typing import Dict, List, Optional, Tuple

STAGE_ORDER = ["stranger", "friend", "close", "lover", "spouse"]

STAGE_LABELS = {
    "stranger": "陌生",
    "friend": "朋友",
    "close": "密友",
    "lover": "情侣",
    "spouse": "夫妻",
}

STAGE_ICONS = {
    "stranger": "",
    "friend": "",
    "close": "⭐",
    "lover": "❤️",
    "spouse": "💍",
}

# 进入下一阶段所需的最低亲密度
STAGE_THRESHOLDS = {
    "friend": 35.0,
    "close": 55.0,
    "lover": 75.0,
    "spouse": 88.0,
}

# 求偶/结婚的最低年龄
MIN_MARRIAGE_AGE = 18
MIN_CHILD_AGE = 20
# 生育上限：原来只有下限没有上限，71 岁也能生
MAX_CHILD_AGE = 60
MAX_CHILDREN = 5


def stage_label(stage: str) -> str:
    return STAGE_LABELS.get((stage or "stranger").lower(), "陌生")


def stage_icon(stage: str) -> str:
    return STAGE_ICONS.get((stage or "stranger").lower(), "")


def evaluate_stage(intimacy: float) -> str:
    """按亲密度算出「理应处于」的阶段。"""
    try:
        value = float(intimacy)
    except (TypeError, ValueError):
        value = 0.0
    if value >= STAGE_THRESHOLDS["spouse"]:
        return "spouse"
    if value >= STAGE_THRESHOLDS["lover"]:
        return "lover"
    if value >= STAGE_THRESHOLDS["close"]:
        return "close"
    if value >= STAGE_THRESHOLDS["friend"]:
        return "friend"
    return "stranger"


def stage_index(stage: str) -> int:
    try:
        return STAGE_ORDER.index((stage or "stranger").lower())
    except ValueError:
        return 0


def can_advance(current: str, target: str) -> bool:
    """只允许单向推进，不自动降级（感情破裂另走专门流程）。"""
    return stage_index(target) > stage_index(current)


def next_stage(stage: str) -> Optional[str]:
    idx = stage_index(stage)
    return STAGE_ORDER[idx + 1] if idx + 1 < len(STAGE_ORDER) else None


# --------------------------------------------------------------------------
#  阶段推进
# --------------------------------------------------------------------------

def advance_pair(a, b, intimacy: float) -> Dict[str, object]:
    """根据亲密度尝试推进 a 与 b 的关系阶段。

    返回 {"advanced": bool, "from": str, "to": str, "event": str}
    会就地修改传入的角色对象（调用方负责 save_characters）。
    """
    from_stage = (getattr(a, "relationship_stage", "stranger") or "stranger").lower()
    to_stage = evaluate_stage(intimacy)

    if not can_advance(from_stage, to_stage):
        return {"advanced": False, "from": from_stage, "to": from_stage, "event": ""}

    # 情侣/夫妻必须双向确认：两侧都写
    a.relationship_stage = to_stage
    b.relationship_stage = to_stage

    if to_stage == "lover":
        a.partner_id = b.id
        b.partner_id = a.id
        event = f"{a.name} 和 {b.name} 确定了恋爱关系"
    elif to_stage == "spouse":
        a.spouse_id = b.id
        b.spouse_id = a.id
        a.partner_id = b.id
        b.partner_id = a.id
        event = f"{a.name} 和 {b.name} 结婚了"
    elif to_stage == "close":
        event = f"{a.name} 和 {b.name} 成了无话不谈的密友"
    else:
        event = f"{a.name} 和 {b.name} 成了朋友"

    now = int(time.time() * 1000)
    for obj in (a, b):
        try:
            obj.updated_at = now
        except Exception:
            pass

    return {"advanced": True, "from": from_stage, "to": to_stage, "event": event}


def _married_to_someone_else(person, other) -> bool:
    """person 是否已有配偶，且配偶不是 other。"""
    spouse = getattr(person, "spouse_id", None)
    return bool(spouse) and spouse != getattr(other, "id", None)


def detach_previous_partners(characters, a, b) -> List[str]:
    """结婚前解除双方与「第三者」的恋爱绑定，避免关系网出现三角。

    历史数据里存在 a.partner_id=c、c.partner_id=a，之后 a 和 b 结婚，
    c 就永远挂着一个已婚的伴侣。
    """
    by_id = {c.id: c for c in characters}
    notes: List[str] = []
    keep = {getattr(a, "id", None), getattr(b, "id", None)}

    for person in (a, b):
        old_id = getattr(person, "partner_id", None)
        if not old_id or old_id in keep:
            continue
        ex = by_id.get(old_id)
        person.partner_id = None
        notes.append(f"解除 {person.name} 与 {old_id} 的旧伴侣关系")
        if ex is not None and getattr(ex, "partner_id", None) == getattr(person, "id", None):
            ex.partner_id = None
            if (getattr(ex, "relationship_stage", "") or "").lower() == "lover":
                ex.relationship_stage = "close"
            notes.append(f"{ex.name} 恢复为密友")
    return notes


def can_marry(a, b) -> Tuple[bool, str]:
    """结婚前置校验，返回 (是否可行, 原因)。

    必须双向校验：只看 a 的话，可以把已婚的 b 抢走，
    于是 b 指向 a、b 的原配偶还指向 b，关系网出现三角。
    """
    if _married_to_someone_else(a, b):
        return False, f"{getattr(a, 'name', '对方')} 已经结婚了"
    if _married_to_someone_else(b, a):
        return False, f"{getattr(b, 'name', '对方')} 已经结婚了"
    if (getattr(a, "relationship_stage", "") or "").lower() == "spouse" and not getattr(a, "spouse_id", None):
        return False, f"{getattr(a, 'name', '对方')} 已经结婚了"
    if getattr(a, "age", 0) < MIN_MARRIAGE_AGE or getattr(b, "age", 0) < MIN_MARRIAGE_AGE:
        return False, f"未满 {MIN_MARRIAGE_AGE} 岁不能结婚"
    if not getattr(a, "is_alive", True) or not getattr(b, "is_alive", True):
        return False, "角色已离世"
    return True, ""


def can_have_child(a, b) -> Tuple[bool, str]:
    """生子前置校验。"""
    if not getattr(a, "is_alive", True) or not getattr(b, "is_alive", True):
        return False, "角色已离世"
    if (getattr(a, "relationship_stage", "") or "").lower() != "spouse":
        return False, "只有夫妻才能生孩子"
    if getattr(a, "spouse_id", None) != getattr(b, "id", None) or getattr(b, "spouse_id", None) != getattr(a, "id", None):
        return False, "两人不是夫妻"
    if getattr(a, "age", 0) < MIN_CHILD_AGE or getattr(b, "age", 0) < MIN_CHILD_AGE:
        return False, f"未满 {MIN_CHILD_AGE} 岁不考虑孩子"
    if getattr(a, "age", 0) > MAX_CHILD_AGE or getattr(b, "age", 0) > MAX_CHILD_AGE:
        return False, f"超过 {MAX_CHILD_AGE} 岁就不再考虑生育了"
    if len(getattr(a, "children_ids", []) or []) >= MAX_CHILDREN or len(getattr(b, "children_ids", []) or []) >= MAX_CHILDREN:
        return False, "孩子已经够多了"
    return True, ""


# --------------------------------------------------------------------------
#  生子
# --------------------------------------------------------------------------

def inherit_surname(parent_a, parent_b) -> str:
    """孩子随父姓（同性别时取年龄大的一方）。"""
    pa = getattr(parent_a, "gender", "")
    pb = getattr(parent_b, "gender", "")
    if pa == "男" and pb != "男":
        holder = parent_a
    elif pb == "男" and pa != "男":
        holder = parent_b
    else:
        holder = parent_a if getattr(parent_a, "age", 0) >= getattr(parent_b, "age", 0) else parent_b
    name = (getattr(holder, "name", "") or "").strip()
    return name[0] if name else "小"


def inherit_personality(parent_a, parent_b, rng: Optional[random.Random] = None) -> str:
    """性格：从父母各自抽一半特征词，去重拼接。"""
    rng = rng or random
    words: List[str] = []

    def _split(text: str) -> List[str]:
        raw = (text or "").replace("，", "、").replace(",", "、")
        return [w.strip() for w in raw.split("、") if w.strip()]

    for parent in (parent_a, parent_b):
        parts = _split(getattr(parent, "personality", ""))
        if parts:
            take = max(1, len(parts) // 2)
            for w in rng.sample(parts, min(take, len(parts))):
                if w not in words:
                    words.append(w)
    return "、".join(words) if words else "温和、好奇"


def build_child_name(surname: str, parent_a, parent_b, rng: Optional[random.Random] = None) -> str:
    """孩子名字：父姓 + 一个吉利字/父母名字里的字。"""
    rng = rng or random
    pool = ["安", "宁", "乐", "禾", "辰", "星", "昭", "沐", "知", "屿", "清", "和"]
    base = (getattr(parent_a, "name", "") or "")[1:] + (getattr(parent_b, "name", "") or "")[1:]
    candidates = [c for c in base if c.strip()]
    second = rng.choice(candidates) if candidates and rng.random() < 0.5 else rng.choice(pool)
    return f"{surname}{second}"


def create_child(parent_a, parent_b, rng: Optional[random.Random] = None):
    """生一个孩子，返回 Character 对象（未落库，调用方 save_characters）。"""
    from models import Character

    rng = rng or random
    surname = inherit_surname(parent_a, parent_b)
    name = build_child_name(surname, parent_a, parent_b, rng)
    return Character(
        id=str(uuid.uuid4()),
        name=name,
        age=0,
        gender=rng.choice(["男", "女"]),
        occupation="幼儿",
        personality=inherit_personality(parent_a, parent_b, rng),
        money=0.0,
        signature="刚来到这个世界",
        parent_ids=[parent_a.id, parent_b.id],
        age_months=0,
        mood="calm",
        relationship_stage="stranger",
        career_level=1,
        career_title="",
    )


def bind_child(characters: List, child) -> None:
    """把孩子的 id 写进父母双方的 children_ids（去重）。"""
    for parent in characters:
        if parent.id in (child.parent_ids or []):
            ids = list(getattr(parent, "children_ids", []) or [])
            if child.id not in ids:
                ids.append(child.id)
            parent.children_ids = ids


# --------------------------------------------------------------------------
#  家庭视图
# --------------------------------------------------------------------------

def family_view(character, by_id: Dict[str, object]) -> Dict[str, object]:
    """给前端用的家庭信息。"""
    partner = by_id.get(getattr(character, "partner_id", None) or "")
    spouse = by_id.get(getattr(character, "spouse_id", None) or "")
    children = [by_id[cid] for cid in (getattr(character, "children_ids", []) or []) if cid in by_id]
    return {
        "stage": (getattr(character, "relationship_stage", "stranger") or "stranger"),
        "stage_label": stage_label(getattr(character, "relationship_stage", "")),
        "stage_icon": stage_icon(getattr(character, "relationship_stage", "")),
        "partner": {"id": partner.id, "name": partner.name} if partner else None,
        "spouse": {"id": spouse.id, "name": spouse.name} if spouse else None,
        "children": [
            {"id": c.id, "name": c.name, "age": c.age, "age_months": getattr(c, "age_months", 0)}
            for c in children
        ],
    }


def family_announcement(event: str, actor_name: str, event_type: str) -> str:
    """把家庭事件写成一条朋友圈文案。"""
    templates = {
        "lover": f"脱单了。{event}",
        "spouse": f"我们结婚啦。{event}",
        "child": f"家里多了一个人。{event}",
    }
    return templates.get(event_type, event or f"{actor_name} 的关系有了变化")


# --------------------------------------------------------------------------
#  自动推进（供关系互动钩子调用）
# --------------------------------------------------------------------------

def maybe_auto_advance(a_id: str, b_id: str, intimacy: Optional[float] = None) -> Optional[Dict[str, object]]:
    """互动后尝试推进关系；有推进就落库并发一条官宣。

    全程 try/except 包裹，任何一步失败都不影响调用方（互动本身）。
    """
    try:
        from storage import get_characters, save_characters

        chars = get_characters()
        by_id = {c.id: c for c in chars}
        a = by_id.get(a_id)
        b = by_id.get(b_id)
        if not a or not b or not getattr(a, "is_alive", True) or not getattr(b, "is_alive", True):
            return None

        if intimacy is None:
            from services.memory_service import get_relationship_intimacy
            intimacy = get_relationship_intimacy(a_id, b_id)

        result = advance_pair(a, b, float(intimacy))
        if not result["advanced"]:
            return result

        save_characters(chars)

        if result["to"] in ("lover", "spouse"):
            try:
                from models import MomentPost
                from storage import get_moments, save_moments
                moments = get_moments()
                moments.append(MomentPost(
                    author_id=a.id, author_name=a.name,
                    content=str(result["event"]),
                    image_url=f"https://picsum.photos/seed/{a.id[:8]}{int(time.time())}/800/600",
                    trigger_type="family", mood="happy", visibility="public",
                    visible_min_intimacy=0, topics=["喜事"], mentioned_ids=[b.id],
                ))
                save_moments(moments)
            except Exception:
                pass

        try:
            from services.memory_service import schedule_store_memory, MemoryType
            schedule_store_memory(character_id=a.id, content=str(result["event"]),
                                  memory_type=MemoryType.EVENT, importance=0.9, related_entities=["家庭"])
            schedule_store_memory(character_id=b.id, content=str(result["event"]),
                                  memory_type=MemoryType.EVENT, importance=0.9, related_entities=["家庭"])
        except Exception:
            pass

        return result
    except Exception:
        return None
