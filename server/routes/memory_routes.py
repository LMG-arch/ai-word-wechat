from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import time

from config import DATA_DIR
from models import MemoryType
from storage import (
    get_logs, save_logs, get_characters,
)
from services.memory_service import (
    get_character_memories, recall_memories, store_memory,
    get_memories, save_memories,
)


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


class RecallMemoriesRequest(BaseModel):
    character_id: str
    query: str
    top_k: Optional[int] = 5


class CreateMemoryRequest(BaseModel):
    character_id: str
    content: str
    memory_type: str = "event"
    importance: float = 0.5
    related_entities: Optional[List[str]] = None


@router.get("/api/memories/{character_id}")
async def get_character_memories_api(character_id: str, limit: int = 20):
    """获取角色记忆列表"""
    memories = get_character_memories(character_id)
    memories.sort(key=lambda x: x.timestamp, reverse=True)
    return {"success": True, "data": memories[:limit]}


@router.post("/api/memories/recall")
async def recall_memories_api(request: RecallMemoriesRequest):
    """召回相关记忆"""
    memories = await recall_memories(
        character_id=request.character_id,
        query=request.query,
        top_k=request.top_k or 5
    )
    return {"success": True, "data": memories}


@router.post("/api/memories")
async def create_memory(request: CreateMemoryRequest):
    """手动创建记忆"""
    try:
        mem_type = MemoryType(request.memory_type)
    except ValueError:
        mem_type = MemoryType.EVENT
    
    memory = await store_memory(
        character_id=request.character_id,
        content=request.content,
        memory_type=mem_type,
        importance=request.importance,
        related_entities=request.related_entities
    )
    return {"success": True, "data": memory.model_dump()}


@router.delete("/api/memories/character/{character_id}")
async def clear_character_memories(character_id: str):
    """清空角色所有记忆"""
    memories = get_memories()
    original_count = len(memories)
    memories = [m for m in memories if m.character_id != character_id]
    save_memories(memories)
    deleted_count = original_count - len(memories)
    _add_log("系统", "记忆", f"已清空角色 {character_id} 的 {deleted_count} 条记忆")
    return {"success": True, "message": f"已删除 {deleted_count} 条记忆"}
