from fastapi import APIRouter
from typing import Optional
import time

from config import DATA_DIR, MILLISECONDS_PER_DAY
from storage import (
    get_schedules, save_schedules, get_characters, get_settings,
    get_logs, save_logs,
)
from services.world_service import generate_schedule_for_character


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


@router.get("/api/schedules")
async def list_daily_schedules(day_index: Optional[int] = None):
    settings = get_settings()
    query_day = day_index if day_index is not None else int(settings.world_elapsed_ms // MILLISECONDS_PER_DAY)
    schedules = [item for item in get_schedules() if item.day_index == query_day]
    return {"success": True, "data": [item.model_dump() for item in schedules]}


@router.post("/api/schedules/generate")
async def generate_daily_schedules():
    settings = get_settings()
    day_index = int(settings.world_elapsed_ms // MILLISECONDS_PER_DAY)
    characters = get_characters()
    schedules = [item for item in get_schedules() if item.day_index != day_index]
    for char in characters:
        if not char.is_alive:
            continue
        schedules.append(generate_schedule_for_character(char, day_index))
    save_schedules(schedules)
    return {"success": True, "data": {"day_index": day_index, "count": len(schedules)}}


@router.get("/api/schedules/{character_id}")
async def get_character_schedule(character_id: str, day_index: Optional[int] = None):
    settings = get_settings()
    query_day = day_index if day_index is not None else int(settings.world_elapsed_ms // MILLISECONDS_PER_DAY)
    schedules = get_schedules()
    target = [item for item in schedules if item.character_id == character_id and item.day_index == query_day]
    if target:
        return {"success": True, "data": target[0].model_dump()}
    characters = get_characters()
    char = next((c for c in characters if c.id == character_id), None)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    generated = generate_schedule_for_character(char, query_day)
    schedules.append(generated)
    save_schedules(schedules)
    return {"success": True, "data": generated.model_dump()}
