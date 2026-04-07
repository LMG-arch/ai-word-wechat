"""AIWeChat character routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time
import os
import random
import re
import json
import aiohttp
from datetime import datetime

from config import DATA_DIR, AVATARS_DIR, IMAGE_PROMPTS_DIR
from models import (
    Character, CreateCharacterRequest, GenerateAvatarRequest, GenerateCharacterRequest,
    SuggestOccupationRequest, SuggestPersonalityRequest,
    MaybeRefreshAvatarRequest, MaybeUpdateSignatureRequest, GenerateMomentRequest,
    MomentPost, LogEntry,
)
from storage import (
    get_characters, save_characters, get_settings, save_settings,
    get_api_configs, get_api_config_by_id,
    get_moments, save_moments, get_logs, save_logs,
)
from services.character_service import (
    ensure_character_defaults, normalize_parent_ids, trim_avatar_change_history,
    can_refresh_avatar, can_refresh_signature, trim_signature_change_history,
    refresh_character_avatar_for_stage,
    get_character_histories, get_history_entry, record_character_history,
)
from services.ai_service import (
    generate_moment_content, generate_moment_image_plan,
    generate_avatar as ai_generate_avatar,
    save_image_prompt_md,
    record_llm_usage, generate_new_signature, generate_auto_comment_text,
    openai_choice_text,
)
from services.memory_service import store_memory, get_character_memories, MemoryType, build_memory_context
from services.moment_service import fallback_moment_image_url

router = APIRouter()


def _add_log(character_name: str, action_type: str, description: str):
    """Internal log helper."""
    try:
        logs = get_logs()
        now_ms = int(time.time() * 1000)
        now = datetime.now().strftime("%H:%M:%S")
        log = LogEntry(
            timestamp=now, timestamp_ms=now_ms, world_timestamp_ms=0,
            character_name=character_name, action_type=action_type,
            description=description
        )
        logs.insert(0, log)
        if len(logs) > 200:
            logs = logs[:200]
        save_logs(logs)
    except Exception:
        pass


@router.get("/api/characters")
async def list_characters(include_dead: bool = False):
    characters = get_characters()
    settings = get_settings()
    normalized = False
    for character in characters:
        if ensure_character_defaults(character, settings):
            normalized = True
    if normalized:
        save_characters(characters)
    if not include_dead:
        characters = [char for char in characters if char.is_alive]
    return {"success": True, "data": [char.model_dump() for char in characters]}


@router.get("/api/characters/{character_id}")
async def get_character(character_id: str):
    characters = get_characters()
    settings = get_settings()
    for index, char in enumerate(characters):
        if char.id == character_id:
            if ensure_character_defaults(char, settings):
                characters[index] = char
                save_characters(characters)
            return {"success": True, "data": char.model_dump()}
    raise HTTPException(status_code=404, detail="Character not found")


@router.get("/api/characters/{character_id}/history")
async def get_character_history(character_id: str):
    return {"success": True, "data": [item.model_dump() for item in get_character_histories(character_id)]}


@router.post("/api/characters/{character_id}/history/{history_id}/restore")
async def restore_character_from_history(character_id: str, history_id: str):
    history_entry = get_history_entry(character_id, history_id)
    if not history_entry:
        raise HTTPException(status_code=404, detail="History entry not found")
    characters = get_characters()
    settings = get_settings()
    all_character_ids = {item.id for item in characters}
    for index, char in enumerate(characters):
        if char.id != character_id:
            continue
        restored = Character(**history_entry.snapshot)
        restored.id = character_id
        restored.updated_at = int(time.time() * 1000)
        normalize_parent_ids(restored, all_character_ids)
        notes = ensure_character_defaults(restored, settings)
        characters[index] = restored
        save_characters(characters)
        _add_log(restored.name, "history_restore", f"已回溯到历史节点：{history_entry.event_type}")
        for note in notes:
            _add_log(restored.name, "lifecycle", note)
        record_character_history(restored, "restore", f"已从历史记录恢复到 {history_entry.event_type}", {"source_history_id": history_entry.id})
        return {"success": True, "data": restored.model_dump()}
    raise HTTPException(status_code=404, detail="Character not found")


@router.post("/api/characters")
async def create_character(request: CreateCharacterRequest):
    characters = get_characters()
    settings = get_settings()
    now_ms = int(time.time() * 1000)
    min_lifespan = min(settings.min_lifespan, settings.max_lifespan)
    max_lifespan = max(settings.min_lifespan, settings.max_lifespan)
    character = Character(
        name=request.name, age=request.age, gender=request.gender,
        occupation=request.occupation, personality=request.personality,
        signature=request.signature or "暂无签名", avatar_url=request.avatar_url,
        parent_ids=request.parent_ids or [], stage_entered_at=now_ms,
        max_lifespan=random.randint(min_lifespan, max_lifespan)
    )
    normalize_parent_ids(character, {item.id for item in characters})
    if character.avatar_url:
        character.last_avatar_change_time = now_ms
        character.avatar_change_history = [now_ms]
    notes = ensure_character_defaults(character, settings)
    characters.append(character)
    save_characters(characters)
    _add_log(character.name, "create", f"character created: {character.get_age_display()} / {character.occupation}")
    for note in notes:
        _add_log(character.name, "lifecycle", note)
    record_character_history(character, "create", "character created")
    return {"success": True, "data": character.model_dump()}


@router.delete("/api/characters/{character_id}")
async def delete_character(character_id: str):
    characters = get_characters()
    char_to_delete = None
    for char in characters:
        if char.id == character_id:
            char_to_delete = char
            break
    if not char_to_delete:
        raise HTTPException(status_code=404, detail="角色不存在")
    characters.remove(char_to_delete)
    save_characters(characters)
    _add_log(char_to_delete.name, "删除", f"角色\"{char_to_delete.name}\"被删除")
    return {"success": True}


@router.put("/api/characters/{character_id}")
async def update_character(character_id: str, request: CreateCharacterRequest):
    characters = get_characters()
    settings = get_settings()
    for index, char in enumerate(characters):
        if char.id == character_id:
            avatar_changed = request.avatar_url and request.avatar_url != char.avatar_url
            char.name = request.name
            char.age = request.age
            char.gender = request.gender
            char.occupation = request.occupation
            char.personality = request.personality
            char.signature = request.signature or char.signature or "暂无签名"
            char.parent_ids = request.parent_ids or []
            if request.llm_model_id is not None:
                char.llm_model_id = request.llm_model_id if request.llm_model_id else None
            if request.moment_frequency:
                char.moment_frequency = request.moment_frequency
            normalize_parent_ids(char, {item.id for item in characters})
            if request.avatar_url:
                char.avatar_url = request.avatar_url
            if avatar_changed:
                now_ms = int(time.time() * 1000)
                char.last_avatar_change_time = now_ms
                trim_avatar_change_history(char, now_ms)
                char.avatar_change_history.append(now_ms)
            notes = ensure_character_defaults(char, settings)
            char.updated_at = int(time.time() * 1000)
            characters[index] = char
            save_characters(characters)
            _add_log(char.name, "update", f"character updated: {char.get_age_display()} / {char.occupation}")
            for note in notes:
                _add_log(char.name, "lifecycle", note)
            record_character_history(char, "update", "character updated")
            return {"success": True, "data": char.model_dump()}
    raise HTTPException(status_code=404, detail="Character not found")


class UpdateCharacterAISettingsRequest(BaseModel):
    llm_model_id: Optional[str] = None
    moment_frequency: Optional[str] = None


@router.patch("/api/characters/{character_id}/ai-settings")
async def update_character_ai_settings(character_id: str, request: UpdateCharacterAISettingsRequest):
    characters = get_characters()
    for index, char in enumerate(characters):
        if char.id == character_id:
            if request.llm_model_id is not None:
                char.llm_model_id = request.llm_model_id if request.llm_model_id else None
            if request.moment_frequency is not None:
                char.moment_frequency = request.moment_frequency
            char.updated_at = int(time.time() * 1000)
            characters[index] = char
            save_characters(characters)
            _add_log(char.name, "ai_settings", f"AI settings updated: llm={char.llm_model_id or 'default'}, freq={char.moment_frequency}")
            return {"success": True, "data": char.model_dump()}
    raise HTTPException(status_code=404, detail="Character not found")


@router.post("/api/characters/{character_id}/maybe-refresh-avatar")
async def maybe_refresh_avatar(character_id: str, request: MaybeRefreshAvatarRequest):
    characters = get_characters()
    for index, char in enumerate(characters):
        if char.id != character_id:
            continue
        now_ms = int(time.time() * 1000)
        if not request.forced and not can_refresh_avatar(char, now_ms):
            return {"success": False, "message": "头像刷新频率已达每周上限"}
        success, message = await refresh_character_avatar_for_stage(char, forced=True)
        if success:
            char.updated_at = now_ms
            trim_avatar_change_history(char, now_ms)
            char.avatar_change_history.append(now_ms)
            characters[index] = char
            save_characters(characters)
            reason = request.reason or "心情变化/重大事件"
            _add_log(char.name, "avatar_refresh", f"{reason}，{message}")
            record_character_history(char, "avatar_refresh", f"{reason}触发头像更新")
        return {"success": success, "message": message}
    raise HTTPException(status_code=404, detail="Character not found")


@router.post("/api/characters/{character_id}/maybe-update-signature")
async def maybe_update_signature(character_id: str, request: MaybeUpdateSignatureRequest):
    characters = get_characters()
    for index, char in enumerate(characters):
        if char.id != character_id:
            continue
        now_ms = int(time.time() * 1000)
        if not can_refresh_signature(char, now_ms):
            return {"success": False, "message": "签名更新频率已达每周上限"}
        recent_memories = get_character_memories(character_id, limit=10)
        memory_context = build_memory_context(recent_memories, max_length=400)
        new_signature = await generate_new_signature(char, memory_context)
        if not new_signature:
            return {"success": False, "message": "签名生成失败，请检查 LLM 配置"}
        char.signature = new_signature
        char.last_signature_change_time = now_ms
        trim_signature_change_history(char, now_ms)
        char.signature_change_history.append(now_ms)
        char.updated_at = now_ms
        characters[index] = char
        save_characters(characters)
        reason = request.reason or "心情变化/近期经历"
        _add_log(char.name, "signature_update", f"{reason}，新签名：{new_signature}")
        record_character_history(char, "signature_update", f"{reason}触发签名更新")
        return {"success": True, "data": {"signature": new_signature}}
    raise HTTPException(status_code=404, detail="Character not found")


@router.post("/api/characters/suggest-occupation")
async def suggest_occupation(request: SuggestOccupationRequest):
    configs = get_api_configs()
    llm_config = None
    for config in configs:
        if config.api_type == 'llm' and config.is_enabled:
            llm_config = config
            break
    if not llm_config:
        default_occupations = ["程序员", "教师", "医生", "设计师", "作家", "厨师", "摄影师", "律师"]
        return {"success": True, "data": {"suggestions": default_occupations[:5]}}
    prompt = f"根据以下信息推荐3-5个适合的职业，只返回职业名称，用逗号分隔：\n"
    if request.name:
        prompt += f"名字：{request.name}\n"
    if request.personality:
        prompt += f"性格：{request.personality}\n"
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {"model": llm_config.selected_model or "gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 100}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "suggest_occupation")
                    content = openai_choice_text(result)
                    suggestions = [s.strip() for s in content.replace('，', ',').split(',') if s.strip()]
                    return {"success": True, "data": {"suggestions": suggestions[:5]}}
    except Exception:
        pass
    return {"success": True, "data": {"suggestions": ["程序员", "教师", "医生", "设计师", "作家"]}}


@router.post("/api/characters/suggest-personality")
async def suggest_personality(request: SuggestPersonalityRequest):
    configs = get_api_configs()
    llm_config = None
    for config in configs:
        if config.api_type == 'llm' and config.is_enabled:
            llm_config = config
            break
    if not llm_config:
        default_personalities = ["开朗活泼", "温柔内向", "幽默风趣", "认真严谨", "热情大方"]
        return {"success": True, "data": {"personality": default_personalities[0]}}
    prompt = f"为一个{request.occupation}生成合适的性格描述（2-4个词，用顿号分隔）：\n"
    if request.name:
        prompt = f"为名叫{request.name}的{request.occupation}生成合适的性格描述（2-4个词，用顿号分隔）：\n"
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {"model": llm_config.selected_model or "gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}], "temperature": 0.8, "max_tokens": 50}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "suggest_personality")
                    content = openai_choice_text(result)
                    return {"success": True, "data": {"personality": content or "性格温和"}}
    except Exception:
        pass
    return {"success": True, "data": {"personality": "性格温和"}}


@router.post("/api/characters/generate")
async def generate_character(request: GenerateCharacterRequest):
    configs = get_api_configs()
    llm_config = None
    for config in configs:
        if config.api_type == 'llm' and config.is_enabled:
            llm_config = config
            break
    if not llm_config:
        return {"success": False, "error": "未找到可用的语言模型配置"}
    age_ranges = {'child': (6, 12), 'teen': (13, 17), 'adult': (18, 40), 'elder': (60, 80)}
    min_age, max_age = age_ranges.get(request.age_range, (18, 40))
    system_prompt = f"""你是一个专业的角色设计师。根据用户的简单描述，创作一个有深度、有故事的角色。

请返回严格的 JSON 格式，包含以下字段：
{{
    "name": "角色名字（中文，2-4字）",
    "age": 年龄数字（{min_age}-{max_age}之间）,
    "gender": "性别（男/女）",
    "occupation": "职业",
    "personality": "性格描述（3-5个形容词，用逗号分隔）",
    "signature": "个性签名（体现角色特点，15字以内）",
    "background": "背景故事（200字以内的身世背景）",
    "life_experience": "人生经历（3个重要经历，数组格式）",
    "hobbies": "兴趣爱好（2-3个）",
    "avatar_description": "详细的外貌描述（中文，用于生成头像）",
    "avatar_prompt": "Avatar generation prompt in English, detailed description of appearance for AI image generation"
}}

注意：
1. 角色要有深度，背景故事要符合年龄段
2. 人生经历要与年龄匹配
3. avatar_prompt 需要详细的英文描述，包含：face, hair, eyes, clothing, expression, style
4. 只返回 JSON，不要任何其他文字"""
    user_prompt = f"请根据以下描述创建一个角色：{request.prompt}"
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        request_data = {"model": llm_config.selected_model or "gpt-3.5-turbo", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": 0.8, "max_tokens": 800}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "generate_character")
                    content = openai_choice_text(result)
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        character_data = json.loads(json_match.group())
                        _add_log("系统", "角色生成", f"AI生成角色：{character_data.get('name', '未知')}")
                        return {"success": True, "data": character_data}
                    else:
                        return {"success": False, "error": "AI 返回格式不正确", "raw": content}
                else:
                    return {"success": False, "error": f"AI 服务失败 (HTTP {response.status})"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON 解析失败：{str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"生成失败：{str(e)}"}


@router.post("/api/characters/generate-avatar")
async def generate_avatar_route(request: GenerateAvatarRequest):
    result = await ai_generate_avatar(request)
    return result


@router.post("/api/characters/{character_id}/moments/generate")
async def generate_character_moment(character_id: str, request: GenerateMomentRequest):
    characters = get_characters()
    character = next((c for c in characters if c.id == character_id), None)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    content = await generate_moment_content(character, request)
    image_url = None
    if request.with_image:
        plan = await generate_moment_image_plan(character, request, content or "")
        kind = plan.get("image_kind") or "scene"
        avatar_prompt = plan.get("image_prompt") or ""
        if kind not in ("selfie", "scene", "portrait"):
            kind = "scene"
        generated = await ai_generate_avatar(GenerateAvatarRequest(avatar_prompt=avatar_prompt, style="realistic", image_kind=kind))
        if generated.get("success"):
            image_url = generated.get("data", {}).get("image_url")
    if request.with_image and not image_url:
        image_url = fallback_moment_image_url(f"{character.id}:{content[:80]}")
    moments = get_moments()
    post = MomentPost(author_id=character.id, author_name=character.name, content=content, image_url=image_url, trigger_type=request.trigger_type, mood=request.mood)
    moments.append(post)
    save_moments(moments)
    _add_log(character.name, "moment_post", f"发布朋友圈：{content[:20]}")
    store_memory(character_id=character.id, content=f"我发布了一条朋友圈：{content}", memory_type=MemoryType.EVENT, importance=0.65, related_entities=["朋友圈", request.trigger_type])
    return {"success": True, "data": post.model_dump()}


@router.post("/api/characters/{character_id}/proactive-message")
async def trigger_proactive_message(character_id: str, context: str = "default"):
    characters = get_characters()
    char = next((c for c in characters if c.id == character_id), None)
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")
    if not char.is_alive:
        raise HTTPException(status_code=400, detail="角色已不在世")
    from services.scheduler import trigger_proactive_message as trigger_msg
    result = await trigger_msg(char, context=context)
    return {"success": True, "data": result}


@router.get("/api/characters/{character_id}/life-experience")
async def get_character_life_experience(character_id: str):
    """获取角色人生经历摘要（任务/关系/反思/经验汇总）"""
    from storage import get_tasks
    from services.memory_service import get_memory_conn
    from models import MemoryType

    characters = get_characters()
    char = next((c for c in characters if c.id == character_id), None)
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")

    tasks = get_tasks()
    completed = [
        t for t in tasks
        if (t.status.value if hasattr(t.status, "value") else str(t.status)) == "completed"
        and (t.submitter_id == character_id or t.assignee_id == character_id or character_id in (t.collaborator_ids or []))
    ]
    completed.sort(key=lambda x: int(getattr(x, "completed_at", 0) or 0), reverse=True)

    task_types_completed = []
    seen_types = set()
    for t in completed:
        ttype = t.task_type.value if hasattr(t.task_type, "value") else str(t.task_type)
        if ttype not in seen_types:
            seen_types.add(ttype)
            task_types_completed.append(ttype)

    # 经验技能库：转为前端期望的列表结构
    exp_list = []
    exp_map = getattr(char, "experience_skills", {}) or {}
    for task_type, exp in exp_map.items():
        if not isinstance(exp, dict):
            continue
        count = int(exp.get("count", 0) or 0)
        success_count = int(exp.get("success_count", 0) or 0)
        success_rate = float(exp.get("success_rate") or (success_count / count if count else 0.0))
        exp_list.append({
            "task_type": str(task_type),
            "count": count,
            "success_rate": round(success_rate, 3),
            "lessons": (exp.get("lessons") or [])[:10],
        })
    exp_list.sort(key=lambda x: x.get("count", 0), reverse=True)

    # 关系数：SQLite relationships 表里以 from_id 为主（近似统计）
    relationship_count = 0
    try:
        with get_memory_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(DISTINCT to_id) AS c FROM relationships WHERE from_id = ? AND valid_to IS NULL",
                (character_id,),
            ).fetchone()
            relationship_count = int(row["c"] if row and "c" in row.keys() else (row[0] if row else 0))
    except Exception:
        relationship_count = 0

    # 最近反思：从 SQLite memories 取 reflection
    recent_reflections = []
    try:
        mems = get_character_memories(character_id, limit=80)
        for m in mems:
            mtype = m.memory_type.value if hasattr(m.memory_type, "value") else str(m.memory_type)
            if mtype == MemoryType.REFLECTION.value:
                recent_reflections.append({
                    "id": m.id,
                    "content": (m.content or "")[:300],
                    "created_at": m.timestamp,
                })
            if len(recent_reflections) >= 5:
                break
    except Exception:
        recent_reflections = []

    recent_tasks = [
        {
            "id": t.id,
            "title": t.title,
            "type": t.task_type.value if hasattr(t.task_type, "value") else str(t.task_type),
            "status": t.status.value if hasattr(t.status, "value") else str(t.status),
            "completed_at": t.completed_at or 0,
        }
        for t in completed[:5]
    ]

    data = {
        "character_id": char.id,
        "character_name": char.name,
        "total_tasks_completed": len(completed),
        "task_types_completed": task_types_completed,
        "experience_skills": exp_list,
        "relationship_count": relationship_count,
        "recent_tasks": recent_tasks,
        "recent_reflections": recent_reflections,
    }
    return {"success": True, "data": data}
