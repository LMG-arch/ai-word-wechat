"""朋友圈进阶能力（V4.0 包A4）

提供三件事：
1. 话题标签解析：从正文里抠出 `#话题#`
2. @好友解析：把 `@名字` 映射成角色 id
3. 被 @ 角色的回应文案（模板化，零 LLM 成本）
"""
from __future__ import annotations

import random
import re
from typing import Iterable, List, Optional, Sequence

# `#话题#`，允许中英文、数字、下划线，1-20 字
_TOPIC_RE = re.compile(r"#([^#\s]{1,20})#")
# `@名字`，遇到空白或标点截止
_MENTION_RE = re.compile(r"@([^\s@#，,。.！!？?：:；;]{1,12})")

MAX_TOPICS = 5
MAX_MENTIONS = 5


def normalize_topic(raw: str) -> str:
    """话题统一去掉首尾空白与包围的井号。"""
    return raw.strip().strip("#").strip()


def extract_topics(content: str) -> List[str]:
    """从正文中提取话题标签，去重且保持出现顺序。"""
    if not content:
        return []
    seen: List[str] = []
    for match in _TOPIC_RE.finditer(content):
        topic = normalize_topic(match.group(1))
        if topic and topic not in seen:
            seen.append(topic)
        if len(seen) >= MAX_TOPICS:
            break
    return seen


def extract_mention_names(content: str) -> List[str]:
    """从正文中提取 @ 的名字，去重保序。"""
    if not content:
        return []
    names: List[str] = []
    for match in _MENTION_RE.finditer(content):
        name = match.group(1).strip()
        if name and name not in names:
            names.append(name)
        if len(names) >= MAX_MENTIONS:
            break
    return names


def resolve_mentioned_ids(
    names: Sequence[str], characters: Iterable, extra_names: Sequence[str] = ()
) -> List[str]:
    """把名字映射成角色 id。同名取第一个，找不到就跳过（不报错）。"""
    by_name = {}
    for char in characters:
        by_name.setdefault(getattr(char, "name", ""), getattr(char, "id", ""))
    ids: List[str] = []
    for name in list(names) + list(extra_names):
        cid = by_name.get((name or "").strip())
        if cid and cid not in ids:
            ids.append(cid)
    return ids[:MAX_MENTIONS]


def mentioned_reply_text(mentioner: str, author_name: str) -> str:
    """被 @ 的角色在评论区留下的回应。模板化，不消耗 token。"""
    mentioner = mentioner or "用户"
    return random.choice([
        f"@{mentioner} 叫我了？来了来了",
        f"@{mentioner} 刚看到，什么事呀",
        f"@{mentioner} 在的，怎么啦",
        f"@{mentioner} 秒回一下，别嫌我慢",
        f"@{mentioner} 我看到这条了，点赞！",
    ])


def topic_leaderboard(moments: Iterable, limit: int = 20) -> List[dict]:
    """话题热度榜：按出现次数倒序，附带最近一条的时间。"""
    stats = {}
    for post in moments:
        for topic in getattr(post, "topics", None) or []:
            item = stats.setdefault(topic, {"topic": topic, "count": 0, "last_at": 0})
            item["count"] += 1
            item["last_at"] = max(item["last_at"], getattr(post, "timestamp", 0))
    ranked = sorted(stats.values(), key=lambda x: (-x["count"], -x["last_at"]))
    return ranked[: max(1, limit)]


def location_leaderboard(moments: Iterable, limit: int = 20) -> List[dict]:
    """位置签到榜：哪些地标被打卡最多。"""
    stats = {}
    for post in moments:
        loc = (getattr(post, "location", None) or "").strip()
        if not loc:
            continue
        item = stats.setdefault(loc, {"location": loc, "count": 0, "last_at": 0})
        item["count"] += 1
        item["last_at"] = max(item["last_at"], getattr(post, "timestamp", 0))
    ranked = sorted(stats.values(), key=lambda x: (-x["count"], -x["last_at"]))
    return ranked[: max(1, limit)]
