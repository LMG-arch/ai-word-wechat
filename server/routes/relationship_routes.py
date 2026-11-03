from fastapi import APIRouter, HTTPException
from typing import Optional
import time

from config import DATA_DIR
from models import RelationshipInteractRequest
from storage import get_characters, get_logs, save_logs
from services.memory_service import (
    get_relationship_intimacy, apply_inactivity_decay,
    apply_relationship_interaction, sync_private_groups,
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


@router.get("/api/relationships/{from_id}/{to_id}")
async def get_relationship_snapshot(from_id: str, to_id: str):
    intimacy = get_relationship_intimacy(from_id, to_id)
    if intimacy <= 20:
        state = "陌生人"
    elif intimacy <= 40:
        state = "认识"
    elif intimacy <= 60:
        state = "熟人"
    elif intimacy <= 80:
        state = "好友"
    else:
        state = "密友"
    return {"success": True, "data": {"from_id": from_id, "to_id": to_id, "intimacy": intimacy, "state": state}}


@router.post("/api/relationships/interact")
async def relationship_interact(request: RelationshipInteractRequest):
    known = {c.id for c in get_characters()}
    if request.from_id not in known or request.to_id not in known:
        raise HTTPException(status_code=404, detail="角色不存在")
    new_intimacy = apply_relationship_interaction(request.from_id, request.to_id, request.action)
    sync_private_groups()
    return {"success": True, "data": {"intimacy": new_intimacy}}


@router.post("/api/relationships/maintenance")
async def run_relationship_maintenance():
    decayed = apply_inactivity_decay()
    sync_summary = sync_private_groups()
    return {"success": True, "data": {"decayed_pairs": decayed, "groups": sync_summary}}
