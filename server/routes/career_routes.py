"""职业路由（V4.0 包B2）"""
from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from storage import get_characters, save_characters, get_logs, save_logs
from services.career_service import (
    career_view, add_experience, announce_promotion, CAREER_LADDERS,
    PROMOTION_EXP, PROMOTION_RAISE, MAX_LEVEL, title_for,
)

router = APIRouter()


class PromoteRequest(BaseModel):
    exp: int = Field(default=60, ge=0, le=5000)


def _log(name: str, action: str, desc: str):
    try:
        from models import LogEntry
        from datetime import datetime
        logs = get_logs()
        logs.insert(0, LogEntry(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            timestamp_ms=int(time.time() * 1000), world_timestamp_ms=0,
            character_name=name, action_type=action, description=desc,
        ))
        save_logs(logs[:200])
    except Exception:
        pass


@router.get("/api/characters/{character_id}/career")
async def get_career(character_id: str):
    """角色的职业档案：等级、头衔、经验进度、阶梯。"""
    chars = get_characters()
    char = next((c for c in chars if c.id == character_id), None)
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")
    data = career_view(char)
    data["is_max"] = data["level"] >= MAX_LEVEL
    return {"success": True, "data": data}


@router.post("/api/characters/{character_id}/career/promote")
async def grant_experience(character_id: str, request: Optional[PromoteRequest] = None):
    """给角色加经验，够了就晋升（手动触发/任务外奖励）。"""
    chars = get_characters()
    idx = next((i for i, c in enumerate(chars) if c.id == character_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="角色不存在")

    char = chars[idx]
    amount = request.exp if request else 60
    result = add_experience(char, amount=amount)
    chars[idx] = char
    save_characters(chars)

    if result.get("promoted"):
        announce_promotion(char, result)
        _log(char.name, "promotion", f"晋升：{result['from_title']} → {result['to_title']}")

    return {"success": True, "data": {**result, "career": career_view(char)}}


@router.get("/api/careers/ladders")
async def list_career_ladders():
    """所有职业的职级阶梯（前端展示用）。"""
    data = []
    for occupation, ladder in CAREER_LADDERS.items():
        data.append({
            "occupation": occupation,
            "ladder": [{"level": i + 1, "title": t, "exp": PROMOTION_EXP[i],
                        "raise": PROMOTION_RAISE[i]} for i, t in enumerate(ladder)],
        })
    return {"success": True, "data": data}
