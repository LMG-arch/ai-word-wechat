"""
AIWeChat 心跳服务模块
角色心跳、定时任务、后台循环。
"""

from __future__ import annotations

import os
import time
import random
from typing import Optional, List, Dict, Any

from config import MILLISECONDS_PER_DAY


async def run_character_heartbeat(character, characters: List):
    """
    单角色心跳：
    - 优先处理 pending_intents
    - 逛朋友圈
    - 点赞/评论
    - 小概率发动态
    - 小概率接取任务
    """
    if not character.is_alive:
        return

    from storage import get_moments, get_tasks, save_characters
    from services.moment_service import has_commented_moment
    from services.memory_service import can_view_moment
    from services.economy_service import economic_stress_multiplier
    from services.character_service import get_moment_frequency_multiplier

    # 1) 优先执行预设意图
    if character.pending_intents:
        intent = character.pending_intents.pop(0)
        action = intent["action"]
        params = intent["params"]
        
        # 记录日志
        from storage import get_logs, save_logs
        from models import LogEntry
        try:
            logs = get_logs()
            now_ms = int(time.time() * 1000)
            log = LogEntry(
                timestamp=time.strftime("%H:%M:%S"),
                timestamp_ms=now_ms,
                world_timestamp_ms=0,
                character_name=character.name,
                action_type="执行意图",
                description=f"Action: {action}, Params: {params}"
            )
            logs.insert(0, log)
            if len(logs) > 200:
                logs = logs[:200]
            save_logs(logs)
        except Exception:
            pass
        
        try:
            if action == "PostMoment":
                pass  # 需要导入朋友圈生成
            elif action == "TakeTask":
                pass  # 需要导入任务接取
            elif action == "SubmitTask":
                pass  # 需要导入任务提交
            elif action == "MoveTo":
                from services.world_service import update_character_location
                update_character_location(character, params, source="ai_action")
        except Exception as e:
            pass
        
        # 执行意图后不再进行其他操作
        save_characters(characters)
        return

    stress = economic_stress_multiplier(character)
    social_scale = 1.0 / max(1.0, stress * 0.82)
    like_p = min(0.32, 0.25 * social_scale)
    comment_p = min(0.18, 0.12 * social_scale)
    freq_multiplier = get_moment_frequency_multiplier(character)
    moment_p = min(0.25, 0.05 * social_scale * freq_multiplier)
    task_base = 0.08 * stress
    task_p = min(0.42, task_base)

    # 1) 逛朋友圈
    try:
        moments = get_moments()
        moments.sort(key=lambda m: m.timestamp, reverse=True)
        visible = [m for m in moments[:60] if can_view_moment(character.id, m)]
        
        for post in visible[:20]:
            if post.author_id == character.id:
                continue
            
            if character.id not in (post.liked_by or []) and random.random() < like_p:
                if post.liked_by is None:
                    post.liked_by = []
                post.liked_by.append(character.id)
            
            if not has_commented_moment(post, character.id) and random.random() < comment_p:
                pass  # 需要生成评论
        
        if random.random() < moment_p:
            pass  # 需要生成朋友圈

        if random.random() < task_p:
            tasks = get_tasks()
            open_tasks = [t for t in tasks if str(t.status) == "open"]
            if open_tasks:
                if character.money <= 0 or character.poverty_days >= 1:
                    task = max(open_tasks, key=lambda t: t.reward)
                else:
                    task = random.choice(open_tasks)
                pass  # 需要接取任务
        
    except Exception:
        pass
    
    save_characters(characters)


async def run_heartbeat_tick(limit_characters: int = 30) -> Dict[str, Any]:
    """心跳 tick - 处理所有角色"""
    from storage import get_characters, save_characters
    
    characters = get_characters()
    alive = [c for c in characters if c.is_alive]
    if not alive:
        return {"characters": 0, "ticked": 0}
    
    sampled = alive if len(alive) <= limit_characters else random.sample(alive, limit_characters)
    
    for char in sampled:
        await run_character_heartbeat(char, alive)
    
    save_characters(characters)
    return {"characters": len(alive), "ticked": len(sampled)}


async def run_ai_company_heartbeat():
    """AI 自主管理公司"""
    from storage import get_characters, save_characters, get_companies, save_companies
    
    characters = get_characters()
    companies = get_companies()
    alive_chars = [c for c in characters if c.is_alive]
    
    if not alive_chars:
        return
    
    # 1) 没有公司但资金充裕的角色，小概率自主创业
    chars_without_company = [c for c in alive_chars if not c.company_id and c.money >= 1500 and c.age >= 18]
    if chars_without_company and random.random() < 0.2:
        founder = max(chars_without_company, key=lambda c: c.money)
        occupation = founder.occupation or "创业者"
        company_names = [
            f"{founder.name}的{occupation}工作室",
            f"云海{occupation}事务所",
            f"{founder.name}{occupation}公司",
        ]
        company_name = random.choice(company_names)
        
        from models import Company
        founder.money -= 1000
        new_company = Company(
            name=company_name,
            legal_person_id=founder.id,
            member_ids=[founder.id],
            funds=500.0,
            location_name=founder.current_location_id or "办公室",
        )
        founder.company_id = new_company.id
        companies.append(new_company)
        save_companies(companies)
        save_characters(characters)
    
    # 2) 公司法人小概率招募新成员
    for company in companies[:]:
        if random.random() < 0.15:
            founder = next((c for c in alive_chars if c.id == company.legal_person_id), None)
            if not founder or founder.money < 300:
                continue
            candidates = [c for c in alive_chars if c.id not in company.member_ids and not c.company_id and c.age >= 16]
            if candidates:
                recruit = random.choice(candidates)
                recruit.company_id = company.id
                company.member_ids.append(recruit.id)
                save_companies(companies)
                save_characters(characters)


async def process_encounter_followups(encounter_items: List[Dict[str, Any]]):
    """处理相遇后续"""
    from services.memory_service import apply_relationship_interaction, set_pair_relationship
    
    for encounter in encounter_items:
        char_ids = encounter.get("character_ids", [])
        if len(char_ids) >= 2:
            for i in range(len(char_ids)):
                for j in range(i + 1, len(char_ids)):
                    apply_relationship_interaction(char_ids[i], char_ids[j], "meet")


async def append_private_group_exchange(group, topic: str):
    """追加私聊群对话"""
    from storage import get_characters
    
    chars = {c.id: c for c in get_characters() if c.is_alive}
    members = [chars[mid] for mid in group.member_ids if mid in chars]
    
    if len(members) < 2:
        return
    
    # 模拟对话
    for char in members[:2]:
        pass  # 需要生成对话内容


async def heartbeat_task():
    """后台心跳任务（无限循环）"""
    import asyncio
    from storage import get_settings, save_settings
    
    while True:
        try:
            settings = get_settings()
            if not settings.enable_heartbeat:
                await asyncio.sleep(60)
                continue
            
            interval = settings.heartbeat_interval_seconds
            await run_heartbeat_tick()
            settings.heartbeat_last_run_time = int(time.time() * 1000)
            save_settings(settings)
            
            await asyncio.sleep(interval)
        except Exception as e:
            await asyncio.sleep(60)


async def task_engine_task():
    """后台任务引擎任务"""
    import asyncio
    from storage import get_settings, save_settings
    
    while True:
        try:
            settings = get_settings()
            if not settings.enable_task_engine:
                await asyncio.sleep(60)
                continue
            
            from services.task_service import run_task_engine
            await run_task_engine()
            
            await asyncio.sleep(300)  # 每5分钟运行一次
        except Exception:
            await asyncio.sleep(60)


async def scheduler_task():
    """后台调度器任务"""
    import asyncio
    from services.scheduler import run_scheduler_tick
    
    while True:
        try:
            await run_scheduler_tick()
            await asyncio.sleep(60)
        except Exception:
            await asyncio.sleep(60)
