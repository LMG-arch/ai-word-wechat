from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import time

from config import DATA_DIR
from models import ChatMessage
from storage import (
    get_characters, save_characters, get_messages, save_messages,
    get_settings, save_settings, get_logs, save_logs,
)
from services.scheduler import (
    get_character_reminders, get_reminders, add_reminder, remove_reminder,
    run_scheduler_tick,
)
from services.ai_service import generate_ai_reply
from services.heartbeat_service import run_heartbeat_tick


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


class AddReminderRequest(BaseModel):
    character_id: str
    reminder_type: str = "reminder"
    trigger_time_ms: int
    content: str
    repeat: str = "none"


@router.get("/api/scheduler/reminders")
async def list_reminders(character_id: Optional[str] = None):
    """获取提醒列表"""
    if character_id:
        reminders = get_character_reminders(character_id)
    else:
        reminders = get_reminders()
    return {"success": True, "data": reminders}


@router.post("/api/scheduler/reminders")
async def create_reminder(request: AddReminderRequest):
    """创建提醒"""
    reminder = add_reminder(
        character_id=request.character_id,
        reminder_type=request.reminder_type,
        trigger_time_ms=request.trigger_time_ms,
        content=request.content,
        repeat=request.repeat,
    )
    _add_log("system", "reminder_create", f"为角色 {request.character_id} 创建提醒：{request.content[:50]}...")
    return {"success": True, "data": reminder}


@router.delete("/api/scheduler/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str):
    """删除提醒"""
    success = remove_reminder(reminder_id)
    if success:
        _add_log("system", "reminder_delete", f"删除提醒 {reminder_id}")
    return {"success": success}


@router.post("/api/scheduler/run")
async def run_scheduler_api():
    """手动触发调度器（检查到期提醒、主动对话、节日问候等）"""
    characters = [c for c in get_characters() if c.is_alive]
    results = await run_scheduler_tick(
        characters=characters,
        get_ai_reply_func=generate_ai_reply,
        save_messages_func=save_messages,
        get_messages_func=get_messages,
        add_log_func=_add_log,
    )
    return {"success": True, "data": results}


@router.post("/api/heartbeat/run")
async def run_heartbeat_api(limit_characters: int = 30):
    """手动触发一次心跳批处理"""
    summary = await run_heartbeat_tick(limit_characters=max(1, min(200, int(limit_characters))))
    settings = get_settings()
    settings.heartbeat_last_run_time = int(time.time() * 1000)
    save_settings(settings)
    return {"success": True, "data": summary}
