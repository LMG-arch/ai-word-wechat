from fastapi import APIRouter, HTTPException
from typing import Optional
import time

from config import DATA_DIR, MILLISECONDS_PER_DAY
from models import DistributeBonusRequest
from storage import (
    get_companies, save_companies, get_characters, save_characters,
    get_economy_logs, get_logs, save_logs,
)
from services.economy_service import run_daily_economy


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


@router.post("/api/economy/distribute-bonus")
async def distribute_bonus(request: DistributeBonusRequest):
    companies = get_companies()
    characters = get_characters()
    for cidx, company in enumerate(companies):
        if company.id != request.company_id:
            continue
        total = sum(max(0.0, float(v)) for v in request.bonuses.values())
        if total > company.funds:
            raise HTTPException(status_code=400, detail="Company funds not enough")
        company.funds -= total
        company.updated_at = int(time.time() * 1000)
        companies[cidx] = company
        for idx, char in enumerate(characters):
            bonus = float(request.bonuses.get(char.id, 0.0))
            if bonus <= 0:
                continue
            char.money += bonus
            char.updated_at = int(time.time() * 1000)
            characters[idx] = char
            _add_log(char.name, "bonus", f"{request.reason} +{bonus:.0f}")
        save_companies(companies)
        save_characters(characters)
        return {"success": True, "data": {"distributed": total, "remaining_funds": company.funds}}
    raise HTTPException(status_code=404, detail="Company not found")


@router.post("/api/economy/daily-settle")
async def run_daily_settle(days: int = 1):
    days = max(1, min(30, int(days)))
    run_daily_economy(days * MILLISECONDS_PER_DAY)
    return {"success": True, "data": {"days": days}}


@router.get("/api/economy/overview")
async def economy_overview():
    characters = get_characters()
    alive = [item for item in characters if item.is_alive]
    total_money = sum(item.money for item in alive)
    total_debt = sum(item.debt_balance for item in alive)
    poor_count = len([item for item in alive if item.money <= 0])
    overdue_count = len([item for item in alive if item.debt_days_overdue > 0])
    return {
        "success": True,
        "data": {
            "character_count": len(alive),
            "total_money": round(total_money, 2),
            "total_debt": round(total_debt, 2),
            "poor_count": poor_count,
            "overdue_count": overdue_count,
        },
    }


@router.get("/api/economy/logs")
async def list_economy_logs(limit: int = 100):
    logs = get_economy_logs()
    logs.sort(key=lambda x: x.timestamp, reverse=True)
    return {"success": True, "data": [item.model_dump() for item in logs[:max(1, min(limit, 500))]]}
