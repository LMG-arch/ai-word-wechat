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


async def run_character_heartbeat(character, all_characters: List):
    """
    单角色心跳。all_characters 须为 get_characters() 的完整列表（同引用），
    避免仅保存存活子集导致角色数据被覆盖。
    """
    if not character.is_alive:
        return

    from storage import get_moments, save_moments, get_tasks, save_tasks, save_characters, get_companies
    from services.moment_service import has_commented_moment, generate_character_moment
    from services.memory_service import can_view_moment
    from services.economy_service import economic_stress_multiplier
    from services.character_service import get_moment_frequency_multiplier
    from services.task_service import (
        apply_auto_take_task_at_index,
        try_heartbeat_take_open_task,
        apply_exec_submit_task_intent,
    )
    from services.ai_service import generate_auto_comment_text
    from models import GenerateMomentRequest, MomentComment, TaskStatus

    if character.pending_intents:
        intent = character.pending_intents.pop(0)
        action = intent["action"]
        params = intent["params"]

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
                await generate_character_moment(
                    character.id,
                    GenerateMomentRequest(
                        trigger_type="exec_intent",
                        event_text=(params or "")[:800] or None,
                    ),
                )
            elif action == "TakeTask":
                task_id = (params or "").strip()
                tasks = get_tasks()
                companies = get_companies()
                idx = next((i for i, t in enumerate(tasks) if t.id == task_id), None)
                if idx is not None:
                    try:
                        apply_auto_take_task_at_index(
                            tasks, idx, character.id, all_characters, companies
                        )
                        save_tasks(tasks)
                    except ValueError:
                        pass
            elif action == "SubmitTask":
                tasks = get_tasks()
                if apply_exec_submit_task_intent(character, params, tasks):
                    save_tasks(tasks)
            elif action == "MoveTo":
                from services.world_service import update_character_location
                update_character_location(character, params, source="ai_action")
        except Exception:
            pass

        save_characters(all_characters)
        return

    stress = economic_stress_multiplier(character)
    social_scale = 1.0 / max(1.0, stress * 0.82)
    like_p = min(0.32, 0.25 * social_scale)
    comment_p = min(0.18, 0.12 * social_scale)
    freq_multiplier = get_moment_frequency_multiplier(character)
    moment_p = min(0.25, 0.05 * social_scale * freq_multiplier)
    task_base = 0.08 * stress
    task_p = min(0.42, task_base)

    moments_dirty = False
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
                moments_dirty = True

            if not has_commented_moment(post, character.id) and random.random() < comment_p:
                author = next((c for c in all_characters if c.id == post.author_id), None)
                if author and author.is_alive:
                    try:
                        comment_text = await generate_auto_comment_text(
                            commenter=character,
                            author=author,
                            moment_content=post.content,
                        )
                        comment = MomentComment(
                            moment_id=post.id,
                            author_id=character.id,
                            author_name=character.name,
                            content=comment_text,
                        )
                        if post.comments is None:
                            post.comments = []
                        post.comments.append(comment)
                        moments_dirty = True
                    except Exception:
                        pass

        if random.random() < moment_p:
            try:
                await generate_character_moment(
                    character.id,
                    GenerateMomentRequest(trigger_type="heartbeat", mood=None),
                )
            except Exception:
                pass

        if random.random() < task_p:
            tasks = get_tasks()
            if try_heartbeat_take_open_task(character, tasks, get_companies(), all_characters):
                save_tasks(tasks)

        if moments_dirty:
            save_moments(moments)
    except Exception:
        pass

    save_characters(all_characters)


async def run_heartbeat_tick(limit_characters: int = 30) -> Dict[str, Any]:
    """心跳 tick - 处理所有角色；同步双人私聊群并小概率推进群内角色对话。"""
    from storage import get_characters, save_characters, get_private_groups
    from services.memory_service import sync_private_groups

    characters = get_characters()
    alive = [c for c in characters if c.is_alive]
    if not alive:
        return {"characters": 0, "ticked": 0}

    sampled = alive if len(alive) <= limit_characters else random.sample(alive, limit_characters)

    for char in sampled:
        await run_character_heartbeat(char, characters)

    save_characters(characters)

    sync_private_groups()
    groups = [g for g in get_private_groups() if g.is_active and len(g.member_ids) == 2]
    if groups and random.random() < 0.12:
        await append_private_group_exchange(
            random.choice(groups),
            random.choice(["近况", "闲聊", "最近怎样", "吐槽一下", "周末打算干啥"]),
        )

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


async def append_private_group_exchange(group, topic: Optional[str] = None):
    """追加私聊群对话（写入 group 会话消息）"""
    from storage import get_characters, get_messages, save_messages
    from services.ai_service import generate_ai_reply
    from models import ChatMessage

    chars = {c.id: c for c in get_characters() if c.is_alive}
    members = [chars[mid] for mid in group.member_ids if mid in chars]

    if len(members) < 2:
        return

    conv_id = f"group:{group.id}"
    topic_line = (topic or "").strip() or "随便聊聊近况"
    messages = get_messages()
    for char in members[:2]:
        prompt = (
            f"你们在私聊群里聊天。主题：{topic_line}。"
            "请简短说一句（20-60 字），像微信群聊，不要复述系统说明。"
        )
        reply = await generate_ai_reply(char, prompt, conv_id)
        messages.append(
            ChatMessage(
                conversation_id=conv_id,
                sender_id=char.id,
                content=reply,
                is_from_user=False,
            )
        )
    save_messages(messages)


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
    """后台调度器；若与 main 同时跑会重复调度，建议只启用一处。"""
    import asyncio
    from datetime import datetime
    from services.scheduler import run_scheduler_tick
    from storage import get_characters, get_messages, save_messages, get_logs, save_logs
    from services.ai_service import generate_ai_reply
    from models import LogEntry

    def add_log(character_name: str, action_type: str, description: str):
        try:
            logs = get_logs()
            now_ms = int(time.time() * 1000)
            now = datetime.now().strftime("%H:%M:%S")
            logs.insert(0, LogEntry(
                timestamp=now, timestamp_ms=now_ms, world_timestamp_ms=0,
                character_name=character_name, action_type=action_type,
                description=description,
            ))
            if len(logs) > 200:
                logs = logs[:200]
            save_logs(logs)
        except Exception:
            pass

    while True:
        try:
            characters = [c for c in get_characters() if c.is_alive]
            await run_scheduler_tick(
                characters=characters,
                get_ai_reply_func=generate_ai_reply,
                save_messages_func=save_messages,
                get_messages_func=get_messages,
                add_log_func=add_log,
            )
            await asyncio.sleep(60)
        except Exception:
            await asyncio.sleep(60)
