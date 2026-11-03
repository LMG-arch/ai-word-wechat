"""职业晋升（V4.0 包B2）

每个职业一条 5 级阶梯。经验来自「任务审核通过」，达到阈值即晋升：
加薪、改头衔、发一条朋友圈。

设计原则：
- 表驱动，新增职业只加一行；
- 纯函数判定，副作用集中在 apply_promotion；
- 不调 LLM。
"""
from __future__ import annotations

import random
import time
from typing import Dict, List, Optional, Tuple

# 五级阶梯：初级 → 顶级
CAREER_LADDERS: Dict[str, List[str]] = {
    "程序员": ["初级程序员", "程序员", "高级程序员", "技术主管", "技术总监"],
    "教师": ["实习教师", "教师", "骨干教师", "年级主任", "校长"],
    "销售": ["销售助理", "销售专员", "销售经理", "销售总监", "区域总经理"],
    "设计师": ["设计助理", "设计师", "资深设计师", "设计主管", "设计总监"],
    "医生": ["实习医生", "住院医师", "主治医师", "副主任医师", "主任医师"],
    "律师": ["律师助理", "执业律师", "资深律师", "合伙人", "高级合伙人"],
    "会计": ["会计助理", "会计", "主管会计", "财务经理", "财务总监"],
    "记者": ["实习记者", "记者", "资深记者", "主编", "总编"],
    "厨师": ["帮厨", "厨师", "主厨", "行政总厨", "餐厅合伙人"],
    "服务员": ["见习服务员", "服务员", "领班", "前厅主管", "店长"],
    "司机": ["代驾", "司机", "车队司机", "调度主管", "车队经理"],
    "警察": ["见习警员", "警员", "警长", "副所长", "所长"],
    "自由职业": ["新手", "自由职业者", "小有名气", "业内熟面孔", "独立工作室主理人"],
    "学生": ["小学生", "中学生", "大学生", "研究生", "博士生"],
    "幼儿": ["婴儿", "幼儿", "学龄前", "学前班", "小学生"],
    "无业": ["待业", "临时工", "稳定零工", "小生意人", "个体老板"],
}

DEFAULT_LADDER = ["助理", "专员", "主管", "经理", "总监"]

# 升到第 N 级所需的累计经验（索引 = level - 1）
PROMOTION_EXP = [0, 120, 360, 800, 1600]

# 每次晋升的加薪金额
PROMOTION_RAISE = [0, 800.0, 2000.0, 5000.0, 12000.0]

MAX_LEVEL = 5


def ladder_for(occupation: str) -> List[str]:
    return CAREER_LADDERS.get((occupation or "").strip(), DEFAULT_LADDER)


def title_for(occupation: str, level: int) -> str:
    ladder = ladder_for(occupation)
    idx = max(0, min(len(ladder) - 1, int(level or 1) - 1))
    return ladder[idx]


def current_title(character) -> str:
    """优先用已保存的头衔，没有就按等级推导。"""
    saved = (getattr(character, "career_title", "") or "").strip()
    if saved:
        return saved
    return title_for(getattr(character, "occupation", ""), getattr(character, "career_level", 1))


def exp_for_next_level(level: int) -> Optional[int]:
    """升到下一级需要的累计经验；已满级返回 None。"""
    lv = int(level or 1)
    if lv >= MAX_LEVEL:
        return None
    return PROMOTION_EXP[lv]


def evaluate_promotion(character) -> Optional[Dict[str, object]]:
    """根据经验判断能否晋升，返回晋升信息或 None。"""
    level = int(getattr(character, "career_level", 1) or 1)
    exp = int(getattr(character, "career_exp", 0) or 0)
    if level >= MAX_LEVEL:
        return None
    need = PROMOTION_EXP[level]
    if exp < need:
        return None
    new_level = level + 1
    return {
        "from_level": level,
        "to_level": new_level,
        "from_title": current_title(character),
        "to_title": title_for(getattr(character, "occupation", ""), new_level),
        "raise": PROMOTION_RAISE[new_level - 1],
        "exp": exp,
        "need": need,
    }


def add_experience(character, amount: int = 50) -> Dict[str, object]:
    """给角色加经验（任务审核通过时调用），返回晋升结果（可能未晋升）。"""
    char = character
    gain = max(0, int(amount))
    char.career_exp = int(getattr(char, "career_exp", 0) or 0) + gain
    char.tasks_completed = int(getattr(char, "tasks_completed", 0) or 0) + 1

    info = evaluate_promotion(char)
    if not info:
        return {"promoted": False, "exp": char.career_exp, "gain": gain}

    char.career_level = int(info["to_level"])
    char.career_title = str(info["to_title"])
    char.money = round(float(getattr(char, "money", 0.0) or 0.0) + float(info["raise"]), 2)
    char.updated_at = int(time.time() * 1000)

    return {"promoted": True, "gain": gain, **info, "money": char.money}


def promotion_text(character, info: Dict[str, object]) -> str:
    """升职朋友圈文案。"""
    return (
        f"升职了：{info['from_title']} → {info['to_title']}。"
        f"工资涨了 {int(float(info['raise']))}，今晚请大家吃饭。"
    ) if random.random() < 0.8 else (
        f"新的头衔：{info['to_title']}。继续努力。"
    )


def announce_promotion(character, info: Dict[str, object]) -> None:
    """晋升后发一条朋友圈，失败不影响主流程。"""
    try:
        from models import MomentPost
        from storage import get_moments, save_moments

        moments = get_moments()
        moments.append(MomentPost(
            author_id=getattr(character, "id", ""),
            author_name=getattr(character, "name", ""),
            content=promotion_text(character, info),
            image_url=f"https://picsum.photos/seed/promo{int(time.time())}/800/600",
            trigger_type="career", mood="happy", visibility="public",
            visible_min_intimacy=0, topics=["升职"],
        ))
        save_moments(moments)
    except Exception:
        pass


def career_view(character) -> Dict[str, object]:
    """给前端用的职业档案。"""
    level = int(getattr(character, "career_level", 1) or 1)
    exp = int(getattr(character, "career_exp", 0) or 0)
    need = exp_for_next_level(level)
    ladder = ladder_for(getattr(character, "occupation", ""))
    return {
        "occupation": getattr(character, "occupation", ""),
        "level": level,
        "max_level": MAX_LEVEL,
        "title": current_title(character),
        "ladder": ladder,
        "exp": exp,
        "exp_next": need,
        "progress": round(min(1.0, exp / need), 3) if need else 1.0,
        "tasks_completed": int(getattr(character, "tasks_completed", 0) or 0),
        "salary_raise_total": sum(PROMOTION_RAISE[: max(0, level - 1)]),
    }
