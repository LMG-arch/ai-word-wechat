"""消息表达形态（V4.0 包A5）

角色不只用文字说话。这里决定「这条回复以什么形态发出」：

- text    普通文字气泡
- voice   语音条（带时长 + 可展开的转写文字，不需要真实音频文件）
- sticker 表情贴纸（内置表情包，纯 emoji + 主题色，不依赖外网）

设计原则：全部本地、零成本、可测试。
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional

# 内置表情包：id 稳定，前端按 id 渲染同一套视觉
STICKERS: List[Dict[str, str]] = [
    {"id": "laugh",    "emoji": "😂", "name": "笑死",   "tone": "happy"},
    {"id": "cry",      "emoji": "😭", "name": "呜呜",   "tone": "sad"},
    {"id": "angry",    "emoji": "😤", "name": "气死",   "tone": "angry"},
    {"id": "shy",      "emoji": "😳", "name": "害羞",   "tone": "shy"},
    {"id": "ok",       "emoji": "👌", "name": "没问题", "tone": "calm"},
    {"id": "thanks",   "emoji": "🙏", "name": "谢啦",   "tone": "calm"},
    {"id": "speechless","emoji": "😑", "name": "无语",  "tone": "tired"},
    {"id": "love",     "emoji": "🥰", "name": "心动",   "tone": "love"},
    {"id": "sleepy",   "emoji": "😴", "name": "困了",   "tone": "tired"},
    {"id": "doge",     "emoji": "🐶", "name": "狗头",   "tone": "joke"},
    {"id": "clap",     "emoji": "👏", "name": "鼓掌",   "tone": "happy"},
    {"id": "sweat",    "emoji": "😅", "name": "汗",     "tone": "shy"},
]

STICKER_MAP: Dict[str, Dict[str, str]] = {s["id"]: s for s in STICKERS}

# mood → 偏好贴纸
_MOOD_STICKERS = {
    "happy": ["laugh", "clap", "doge"],
    "excited": ["clap", "laugh"],
    "sad": ["cry", "sweat"],
    "angry": ["angry", "speechless"],
    "anxious": ["sweat", "speechless"],
    "tired": ["sleepy", "speechless"],
    "shy": ["shy", "sweat"],
    "calm": ["ok", "thanks"],
}

# 语气强烈的短回复更适合用表情
_STRONG_WORDS = ("哈哈", "笑死", "无语", "服了", "气死", "谢谢", "好的", "嗯嗯", "在的", "收到")

MIN_VOICE_SECONDS = 2
MAX_VOICE_SECONDS = 30


def get_sticker(sticker_id: str) -> Optional[Dict[str, str]]:
    """按 id 取贴纸，未知 id 返回 None。"""
    return STICKER_MAP.get((sticker_id or "").strip())


def estimate_voice_duration(text: str) -> int:
    """按字数粗估语音时长（中文约 4 字/秒），限制在 2-30 秒。"""
    chars = len((text or "").strip())
    if chars <= 0:
        return MIN_VOICE_SECONDS
    seconds = round(chars / 4.0)
    return max(MIN_VOICE_SECONDS, min(MAX_VOICE_SECONDS, seconds))


def should_send_voice(text: str, mood: str = "calm", rng: Optional[random.Random] = None) -> bool:
    """是否用语音条发出。

    规则（保守）：文字 8-60 字之间、且心情非愤怒时才可能发语音；
    基础概率 18%，tired/shy 提高到 30%。
    """
    body = (text or "").strip()
    if not (8 <= len(body) <= 60):
        return False
    if (mood or "calm") == "angry":
        return False
    rng = rng or random
    chance = 0.30 if (mood or "").lower() in ("tired", "shy", "love") else 0.18
    return rng.random() < chance


def pick_sticker_for(text: str, mood: str = "calm", rng: Optional[random.Random] = None) -> Optional[str]:
    """是否额外补一条表情。

    只在「回复很短 + 含强烈语气词」或心情明显时触发，避免刷屏。
    """
    body = (text or "").strip()
    rng = rng or random
    strong = any(word in body for word in _STRONG_WORDS)
    if strong and len(body) <= 12:
        chance = 0.55
    elif len(body) <= 20:
        chance = 0.10
    else:
        chance = 0.03
    if rng.random() >= chance:
        return None
    pool = _MOOD_STICKERS.get((mood or "calm").lower()) or _MOOD_STICKERS["calm"]
    return rng.choice(pool)


def mood_from_text(text: str) -> str:
    """从文本粗判心境，供没有显式 mood 的场景使用。"""
    body = text or ""
    table = [
        ("angry", ("气死", "烦", "滚", "讨厌", "凭什么")),
        ("sad", ("难过", "哭", "累", "失望", "算了")),
        ("happy", ("哈哈", "开心", "太好了", "爽", "赞")),
        ("shy", ("害羞", "不好意思", "脸红")),
        ("tired", ("困", "睡了", "加班", "忙死")),
    ]
    for mood, words in table:
        if any(w in body for w in words):
            return mood
    return "calm"
