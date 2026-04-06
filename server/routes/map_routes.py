from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import time
import random

from config import DATA_DIR, WORLD_LOCATION_SLOT_MS, WORLD_COMPANY_BIND
from models import Character
from storage import (
    get_characters, get_settings, get_companies,
    get_active_world_map, save_persisted_world_map, load_persisted_world_map,
    get_logs, save_logs,
)
from services.world_service import (
    resolve_location_coordinates, detect_encounters,
)
from services.heartbeat_service import process_encounter_followups
from storage import get_location_history
from services.character_service import get_character_residence
from services.ai_service import llm_generate_world_map


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


class RegenerateWorldRequest(BaseModel):
    prompt: str = ""


@router.get("/api/map/meta")
async def get_world_map_meta():
    """虚拟城市地图：道路、地标、水系（与角色活动地点绑定）；来自持久化世界或默认模板。"""
    return {"success": True, "data": get_active_world_map()}


@router.get("/api/map/landmarks/{landmark_name}/detail")
async def get_landmark_detail(landmark_name: str):
    """获取地标详情及在此地的角色"""
    meta = get_active_world_map()
    landmark = None
    for lm in meta.get("landmarks") or []:
        if lm.get("name") == landmark_name or lm.get("bind") == landmark_name:
            landmark = lm
            break
    if not landmark:
        raise HTTPException(status_code=404, detail="地标未找到")

    settings = get_settings()
    drift_bucket = int(settings.world_elapsed_ms // WORLD_LOCATION_SLOT_MS)
    characters = [c for c in get_characters() if c.is_alive]
    characters_here = []
    for char in characters:
        loc = char.current_location_id or "城市"
        if loc == landmark_name or loc == landmark.get("bind"):
            x, y = resolve_location_coordinates(loc, char.id, drift_bucket=drift_bucket)
            characters_here.append({
                "id": char.id,
                "name": char.name,
                "occupation": char.occupation,
                "x": round(x, 2),
                "y": round(y, 2),
            })

    return {
        "success": True,
        "data": {
            "landmark": landmark,
            "characters_here": characters_here,
        }
    }


@router.get("/api/world/info")
async def world_info():
    """世界是否已持久化、城市名与氛围描述。"""
    persisted = load_persisted_world_map() is not None
    m = get_active_world_map()
    return {
        "success": True,
        "data": {
            "persisted": persisted,
            "city_name": m.get("city_name"),
            "lore": m.get("lore") or "",
        },
    }


@router.post("/api/world/regenerate")
async def regenerate_world(req: RegenerateWorldRequest):
    """按用户自然语言重塑城市（需可用 LLM）。会覆盖 world_map.json。"""
    prompt = (req.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    meta = await llm_generate_world_map(prompt)
    if not meta:
        raise HTTPException(status_code=400, detail="LLM 不可用或生成失败，请检查语言模型配置")
    save_persisted_world_map(meta)
    _add_log("系统", "world_regen", f"城市已重塑：{meta.get('city_name', '')}")
    return {"success": True, "data": meta}


@router.get("/api/map/world")
async def get_world_map():
    settings = get_settings()
    drift_bucket = int(settings.world_elapsed_ms // WORLD_LOCATION_SLOT_MS)
    characters = [item for item in get_characters() if item.is_alive]
    points = []
    for char in characters:
        location = char.current_location_id or get_character_residence(char.id)
        x, y = resolve_location_coordinates(location, char.id, drift_bucket=drift_bucket)
        points.append({
            "character_id": char.id,
            "name": char.name,
            "location_name": location,
            "x": x,
            "y": y,
            "company_id": char.company_id,
            "money": char.money,
        })
    
    companies = get_companies()
    company_locations = []
    for comp in companies:
        if comp.location_name:
            company_locations.append({
                "company_id": comp.id,
                "name": comp.name,
                "location_name": comp.location_name,
                "x": comp.location_x,
                "y": comp.location_y,
                "member_count": len(comp.member_ids),
            })
    
    return {"success": True, "data": {"characters": points, "companies": company_locations}}


@router.get("/api/map/characters/{character_id}/history")
async def get_character_location_history(character_id: str, limit: int = 100):
    return {"success": True, "data": [item.model_dump() for item in get_location_history(character_id=character_id, limit=limit)]}


@router.post("/api/map/encounters/run")
async def run_encounters(window_minutes: int = 5):
    summary = detect_encounters(window_minutes=window_minutes)
    await process_encounter_followups(summary.get("items") or [])
    return {"success": True, "data": summary}
