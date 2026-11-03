"""
生命周期服务：年龄增长、社交自动运行等后台逻辑。

从 main.py 的 startup_event 内联实现提取而来，交由 services 层统一管理，
符合开发文档 §8.8「业务逻辑放 services/，避免继续膨胀 main.py」。

设计要点：
- 所有跨模块依赖（moment_service / world_service / memory_service / heartbeat_service）
  均在函数体内惰性导入，避免 services 包加载时的循环依赖。
- add_log 统一委托 storage.add_log，消除此前 main.py 内联的简化副本。
"""

from __future__ import annotations

import time
from typing import Optional

from storage import get_settings, save_settings, get_characters, save_characters


def add_log(character_name: str, action_type: str, description: str):
    """写入一条系统日志（统一委托 storage.add_log，避免重复实现）。"""
    from storage import add_log as _storage_add_log

    return _storage_add_log(character_name, action_type, description)


async def process_age_growth() -> None:
    """处理角色年龄增长：每天推进一次，跨年龄阶段时记录日志。"""
    from models import get_age_stage_from_age

    settings = get_settings()
    now_ms = int(time.time() * 1000)
    last = getattr(settings, "last_age_growth_time", 0)
    if now_ms - last < 24 * 3600 * 1000:  # 每天一次
        return
    characters = get_characters()
    for char in characters:
        if char.is_alive:
            char.age += 1
            new_stage = get_age_stage_from_age(char.age)
            # Character 没有 age_stage 字段，阶段由年龄实时推导，不能直接读写属性
            if char.get_age_stage() != new_stage:
                add_log(char.name, "age_growth", f"进入{new_stage}阶段，年龄: {char.age}")
    save_characters(characters)
    settings.last_age_growth_time = now_ms
    save_settings(settings)


async def process_social_autorun() -> None:
    """社交自动运行：角色自动互动、相遇后续、私群同步、关系衰减。"""
    from services.moment_service import run_moment_auto_interactions
    from services.world_service import detect_encounters
    from services.memory_service import sync_private_groups, apply_inactivity_decay
    from services.heartbeat_service import process_encounter_followups

    settings = get_settings()
    now_ms = int(time.time() * 1000)
    last = getattr(settings, "auto_moment_last_run_time", 0)
    if now_ms - last < 300000:  # 5 分钟一次
        return
    await run_moment_auto_interactions(limit=30)
    enc = detect_encounters()
    await process_encounter_followups(enc.get("items") or [])
    sync_private_groups()
    apply_inactivity_decay()
    settings.auto_moment_last_run_time = now_ms
    save_settings(settings)
