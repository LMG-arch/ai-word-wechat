"""
AIWeChat 定时提醒与角色主动对话系统
从 main.py 新增的功能模块，支持：
- 角色设置提醒/定时器
- 角色主动给用户发消息（基于心情/亲密度/时间）
- 特殊日期问候（生日、节日等）
"""

from __future__ import annotations

import random
import time
from typing import Optional, List, Dict, Any

from models import Character, ChatMessage


# ==================== 提醒系统 ====================

class Reminder:
    """角色提醒"""
    def __init__(
        self,
        id: str,
        character_id: str,
        reminder_type: str,
        trigger_time_ms: int,
        content: str,
        repeat: str = "none",  # none/daily/weekly
        is_active: bool = True,
    ):
        self.id = id
        self.character_id = character_id
        self.reminder_type = reminder_type  # reminder/greeting/task_reminder
        self.trigger_time_ms = trigger_time_ms
        self.content = content
        self.repeat = repeat
        self.is_active = is_active


# 内存中的提醒列表（重启后从 JSON 恢复）
_active_reminders: List[Dict[str, Any]] = []


def get_reminders() -> List[Dict[str, Any]]:
    """获取所有提醒"""
    global _active_reminders
    return _active_reminders


def add_reminder(
    character_id: str,
    reminder_type: str,
    trigger_time_ms: int,
    content: str,
    repeat: str = "none",
) -> Dict[str, Any]:
    """添加提醒"""
    reminder = {
        "id": f"reminder_{int(time.time() * 1000)}_{character_id}",
        "character_id": character_id,
        "reminder_type": reminder_type,
        "trigger_time_ms": trigger_time_ms,
        "content": content,
        "repeat": repeat,
        "is_active": True,
        "created_at": int(time.time() * 1000),
    }
    _active_reminders.append(reminder)
    return reminder


def remove_reminder(reminder_id: str) -> bool:
    """删除提醒"""
    global _active_reminders
    before = len(_active_reminders)
    _active_reminders = [r for r in _active_reminders if r["id"] != reminder_id]
    return len(_active_reminders) < before


def get_character_reminders(character_id: str) -> List[Dict[str, Any]]:
    """获取角色的所有提醒"""
    return [r for r in _active_reminders if r["character_id"] == character_id and r["is_active"]]


def check_due_reminders() -> List[Dict[str, Any]]:
    """检查到期的提醒，返回到期的提醒列表"""
    now_ms = int(time.time() * 1000)
    due = []
    for reminder in _active_reminders:
        if not reminder["is_active"]:
            continue
        if reminder["trigger_time_ms"] <= now_ms:
            due.append(reminder)
            # 处理重复
            if reminder["repeat"] == "daily":
                reminder["trigger_time_ms"] += 24 * 60 * 60 * 1000
            elif reminder["repeat"] == "weekly":
                reminder["trigger_time_ms"] += 7 * 24 * 60 * 60 * 1000
            else:
                reminder["is_active"] = False  # 一次性提醒，触发后关闭
    return due


# ==================== 角色主动对话 ====================

# 主动对话冷却时间（毫秒），避免角色频繁打扰用户
_proactive_cooldowns: Dict[str, int] = {}
PROACTIVE_COOLDOWN_MS = 30 * 60 * 1000  # 30 分钟内不重复主动对话


def can_proactively_message(character_id: str) -> bool:
    """检查角色是否可以主动发消息"""
    now_ms = int(time.time() * 1000)
    last_time = _proactive_cooldowns.get(character_id, 0)
    return (now_ms - last_time) >= PROACTIVE_COOLDOWN_MS


def record_proactive_message(character_id: str):
    """记录角色发送了主动消息，设置冷却"""
    now_ms = int(time.time() * 1000)
    _proactive_cooldowns[character_id] = now_ms


def should_character_reach_out(character: Character, intimacy: float) -> bool:
    """
    根据角色心情、亲密度、当前状态判断是否应该主动联系用户
    Returns: True 如果角色应该主动联系用户
    """
    # 基础概率
    base_prob = 0.02  # 2% 基础概率
    
    # 亲密度影响：亲密度越高，越可能主动联系
    if intimacy > 80:
        base_prob += 0.08  # 密友 10%
    elif intimacy > 60:
        base_prob += 0.05  # 好友 7%
    elif intimacy > 40:
        base_prob += 0.03  # 熟人 5%
    elif intimacy > 20:
        base_prob += 0.01  # 认识 3%
    
    # 心情影响：心情好/不好都可能想分享
    mood_factors = {
        "开心": 0.04,
        "兴奋": 0.06,
        "难过": 0.03,
        "焦虑": 0.02,
        "疲惫": 0.01,
        "平静": 0.0,
    }
    # 这里简化处理，实际 mood 可能来自心跳系统
    base_prob += 0.01  # 默认微弱正向
    
    # 经济压力影响：压力大时更可能寻求帮助
    if character.money < 0:
        base_prob += 0.03
    elif character.poverty_days > 2:
        base_prob += 0.02
    
    # 年龄影响：青少年和青年更活跃
    if character.age <= 17:
        base_prob *= 1.3
    elif character.age <= 30:
        base_prob *= 1.2
    elif character.age > 60:
        base_prob *= 0.7
    
    return random.random() < base_prob


def generate_proactive_message(character: Character, context: str = "") -> str:
    """
    生成角色主动消息内容
    context: 触发原因（如 "reminder_triggered", "mood_change", "special_occasion"）
    """
    name = character.name
    
    messages_by_context = {
        "reminder_triggered": [
            f"嘿，提醒你一下！{character.experience_skills.get('last_reminder', '记得按时完成重要的事情哦')}",
            f"时间到了！你之前设置的事情该处理了。",
        ],
        "mood_change": [
            f"在吗？今天发生了些有趣的事，想跟你分享一下~",
            f"最近心情不错，出来聊聊？",
            f"有点感慨，想跟你聊聊近况。",
        ],
        "special_occasion": [
            f"今天是特别的日子！祝你一切顺利~ 🎉",
            f"节日快乐！有什么计划吗？",
        ],
        "default": [
            f"在吗？最近在忙什么呢？",
            f"嘿，好久没聊了，最近怎么样？",
            f"突然想到你，就发条消息问问近况~",
            f"最近有个想法，想跟你聊聊。",
        ],
    }
    
    candidates = messages_by_context.get(context, messages_by_context["default"])
    return random.choice(candidates)


# ==================== 特殊日期问候 ====================

_special_greetings_sent: Dict[str, int] = {}  # {date_key: last_sent_timestamp}


def check_special_date_greetings(characters: List[Character]) -> List[Dict[str, Any]]:
    """
    检查是否有特殊日期需要问候（生日、节日等）
    Returns: 需要发送的问候列表
    """
    now_ms = int(time.time() * 1000)
    today = time.strftime("%m-%d")
    date_key = f"greeting_{today}"
    
    # 每天只发送一次
    if date_key in _special_greetings_sent:
        last_sent = _special_greetings_sent[date_key]
        if now_ms - last_sent < 24 * 60 * 60 * 1000:
            return []
    
    greetings = []
    
    # 检查角色生日
    for char in characters:
        if not char.is_alive:
            continue
        # 假设角色的 created_at 包含生日信息（月-日）
        # 这里简化为检查是否接近角色创建日
        # 实际应用中可以从角色数据中提取生日
        pass
    
    # 节日问候（简化版）
    holidays = {
        "01-01": "元旦快乐！新的一年有什么计划？🎆",
        "02-14": "情人节快乐！❤️",
        "05-01": "劳动节快乐！好好休息一下吧。",
        "10-01": "国庆节快乐！🎉",
        "12-25": "圣诞节快乐！🎄",
    }
    
    if today in holidays:
        greetings.append({
            "type": "holiday",
            "message": holidays[today],
            "date": today,
        })
    
    if greetings:
        _special_greetings_sent[date_key] = now_ms
    
    return greetings


# ==================== 心跳集成 ====================

async def run_scheduler_tick(
    characters: List[Character],
    get_ai_reply_func=None,
    save_messages_func=None,
    get_messages_func=None,
    add_log_func=None,
) -> Dict[str, Any]:
    """
    调度器心跳：在后台任务中定期调用
    - 检查到期的提醒
    - 角色主动联系用户
    - 特殊日期问候
    
    需要传入 main.py 中的函数引用以避免循环导入。
    """
    results = {
        "reminders_triggered": 0,
        "proactive_messages": 0,
        "special_greetings": 0,
    }
    
    if not get_ai_reply_func or not save_messages_func:
        return results  # 依赖函数未提供，跳过
    
    # 1) 检查到期的提醒
    due_reminders = check_due_reminders()
    for reminder in due_reminders:
        char_id = reminder["character_id"]
        char = next((c for c in characters if c.id == char_id), None)
        if char and char.is_alive:
            # 通过 AI 生成提醒消息
            prompt = f"你是一个助手，请转达这条提醒：{reminder['content']}"
            reply = await get_ai_reply_func(char, prompt)
            msg = ChatMessage(
                conversation_id=char.id,
                sender_id=char.id,
                content=f"⏰ 提醒：{reply}",
                is_from_user=False,
            )
            messages = get_messages_func()
            messages.append(msg)
            save_messages_func(messages)
            if add_log_func:
                add_log_func(char.name, "提醒触发", f"提醒内容：{reminder['content'][:50]}...")
            results["reminders_triggered"] += 1
    
    # 2) 角色主动联系用户
    for char in characters:
        if not char.is_alive:
            continue
        if not can_proactively_message(char.id):
            continue
        
        # 简化：这里用随机判断，实际应该用更复杂的逻辑
        if random.random() < 0.01:  # 1% 概率
            message = generate_proactive_message(char, "mood_change")
            msg = ChatMessage(
                conversation_id=char.id,
                sender_id=char.id,
                content=message,
                is_from_user=False,
            )
            messages = get_messages_func()
            messages.append(msg)
            save_messages_func(messages)
            record_proactive_message(char.id)
            if add_log_func:
                add_log_func(char.name, "主动联系", f"主动发送：{message[:30]}...")
            results["proactive_messages"] += 1
    
    # 3) 特殊日期问候
    greetings = check_special_date_greetings(characters)
    for greeting in greetings:
        # 随机选一个在线角色发送节日问候
        alive_chars = [c for c in characters if c.is_alive]
        if alive_chars:
            sender = random.choice(alive_chars)
            msg = ChatMessage(
                conversation_id=sender.id,
                sender_id=sender.id,
                content=f"🎊 {greeting['message']}",
                is_from_user=False,
            )
            messages = get_messages_func()
            messages.append(msg)
            save_messages_func(messages)
            if add_log_func:
                add_log_func(sender.name, "节日问候", greeting['message'])
            results["special_greetings"] += 1
    
    return results
