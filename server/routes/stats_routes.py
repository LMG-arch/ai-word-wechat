from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
import time

from config import DATA_DIR
from storage import (
    get_characters, get_messages, get_settings,
    get_logs, save_logs,
)
from services.character_service import build_memorial_record, format_world_elapsed


router = APIRouter()

def _add_log(character_name: str, action_type: str, description: str):
    try:
        from models import LogEntry
        from datetime import datetime
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


@router.get("/api/stats")
async def get_statistics():
    """Get statistics"""
    characters = get_characters()
    messages = get_messages()
    settings = get_settings()

    alive_characters = [char for char in characters if char.is_alive]
    dead_characters = [char for char in characters if not char.is_alive]
    conversations: Dict[str, int] = {}
    for msg in messages:
        conv_id = msg.conversation_id
        if conv_id not in conversations:
            conversations[conv_id] = 0
        conversations[conv_id] += 1

    return {
        "success": True,
        "data": {
            "character_count": len(alive_characters),
            "dead_character_count": len(dead_characters),
            "total_character_count": len(characters),
            "message_count": len(messages),
            "conversation_count": len(conversations),
            "world_elapsed_ms": settings.world_elapsed_ms,
            "world_elapsed_text": format_world_elapsed(settings.world_elapsed_ms)
        }
    }


@router.get("/api/memorials")
async def list_memorials():
    """List dead characters and memorial summaries"""
    characters = get_characters()
    memorials = [build_memorial_record(char) for char in characters if not char.is_alive]
    memorials.sort(key=lambda item: item.get("death_time") or 0, reverse=True)
    return {"success": True, "data": memorials}


@router.get("/api/memorials/{character_id}")
async def get_memorial_detail(character_id: str):
    """Get memorial detail for a dead character"""
    from storage import get_character_histories, get_character_memories
    characters = get_characters()
    for char in characters:
        if char.id != character_id:
            continue
        if char.is_alive:
            raise HTTPException(status_code=400, detail="Character is still alive")
        data = build_memorial_record(char)
        data["histories"] = [item.model_dump() for item in get_character_histories(character_id)]
        data["memories"] = [item.model_dump() for item in get_character_memories(character_id, limit=30)]
        return {"success": True, "data": data}
    raise HTTPException(status_code=404, detail="Character not found")


@router.get("/api/logs")
async def get_recent_logs(limit: int = 50):
    """获取最近日志"""
    logs = get_logs()
    return {"success": True, "data": logs[:limit]}


@router.get("/api/logs/character/{character_id}")
async def get_character_logs(character_id: str, limit: int = 100):
    """获取角色相关日志"""
    characters = get_characters()
    char = next((c for c in characters if c.id == character_id), None)
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")
    logs = get_logs()
    char_logs = [log for log in logs if char.name in log.character_name or log.character_name == "系统"]
    char_logs.sort(key=lambda x: x.timestamp, reverse=True)
    return {"success": True, "data": char_logs[:limit]}


@router.delete("/api/logs")
async def clear_logs():
    """清空日志"""
    save_logs([])
    return {"success": True}
