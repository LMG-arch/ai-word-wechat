"""
AIWeChat 经济服务模块
经济系统、日常结算、公司奖金分配。
"""

from __future__ import annotations

import os
import time
import random
from typing import Optional, List, Dict, Any

from config import MILLISECONDS_PER_DAY


def economic_stress_multiplier(character) -> float:
    """经济压力乘数（缺钱时更高）"""
    if character.money <= 0:
        return 3.0
    if character.money < 50:
        return 2.0
    if character.money < 100:
        return 1.5
    return 1.0


def run_daily_economy(world_elapsed_ms: int):
    """日常经济结算"""
    from storage import (
        get_characters, save_characters,
        get_economy_logs, save_economy_logs
    )
    from models import EconomyLog
    
    if world_elapsed_ms < MILLISECONDS_PER_DAY:
        return
    
    characters = get_characters()
    if not characters:
        return
    
    days = int(world_elapsed_ms // MILLISECONDS_PER_DAY)
    if days <= 0:
        return
    
    logs = get_economy_logs()
    
    for index, char in enumerate(characters):
        if not char.is_alive:
            continue
        
        detail_parts = []
        
        # 日常消耗
        daily_cost = 5 * days
        char.money -= daily_cost
        detail_parts.append(f"日常消耗 -{daily_cost:.0f}（{days}天）")
        
        if char.money <= 0:
            char.poverty_days += days
        else:
            char.poverty_days = 0

        # 贫困贷款
        if char.poverty_days >= 3 and char.debt_balance <= 0:
            char.debt_balance += 100
            char.money += 100
            char.poverty_days = 0
            detail_parts.append("连续贫困触发贷款 +100")

        # 贷款利息
        if char.debt_balance > 0:
            interest = round(char.debt_balance * 0.01 * days, 2)
            char.debt_balance += interest
            detail_parts.append(f"贷款利息 +{interest:.2f}")
            
            # 自动还款
            repay = min(max(char.money - 20, 0), char.debt_balance)
            if repay > 0:
                char.money -= repay
                char.debt_balance -= repay
                detail_parts.append(f"自动还款 -{repay:.2f}")
            
            if char.debt_balance > 0 and char.money <= 0:
                char.debt_days_overdue += days
                if char.debt_days_overdue >= 7:
                    detail_parts.append("贷款逾期>=7天，触发高风险状态")
            else:
                char.debt_days_overdue = 0
        else:
            char.debt_days_overdue = 0

        char.updated_at = int(time.time() * 1000)
        detail = "；".join(detail_parts)
        
        logs.insert(0, EconomyLog(
            character_id=char.id,
            action="daily_settlement",
            amount=-daily_cost,
            balance_after=char.money,
            detail=detail
        ))
        
        characters[index] = char
    
    if len(logs) > 400:
        logs = logs[:400]
    
    save_economy_logs(logs)
    save_characters(characters)


def distribute_company_bonus(company_id: str, bonuses: Dict[str, float], reason: str = "任务奖金分配"):
    """分配公司奖金"""
    from storage import (
        get_companies, save_companies, get_characters, save_characters,
        get_economy_logs, save_economy_logs,
    )
    from models import EconomyLog
    
    companies = get_companies()
    company = next((c for c in companies if c.id == company_id), None)
    if not company:
        return {"success": False, "error": "公司不存在"}
    
    characters = get_characters()
    logs = get_economy_logs()
    
    for char_id, amount in bonuses.items():
        char = next((c for c in characters if c.id == char_id), None)
        if not char:
            continue
        
        char.money += amount
        char.updated_at = int(time.time() * 1000)
        
        logs.insert(0, EconomyLog(
            character_id=char_id,
            action="company_bonus",
            amount=amount,
            balance_after=char.money,
            detail=f"{company.name} 发放奖金：{reason}"
        ))
    
    # 从公司资金扣除
    total_bonus = sum(bonuses.values())
    company.funds -= total_bonus
    
    save_companies(companies)
    save_characters(characters)
    save_economy_logs(logs)
    
    return {"success": True, "total_distributed": total_bonus}


COMPANY_TASK_BONUS_RATIO = 0.3  # 公司任务奖励中用于成员奖金分配的比例


def apply_company_task_bonus_distribution(companies, cidx, task, characters, ratio: float = COMPANY_TASK_BONUS_RATIO):
    """公司任务完成后，将部分奖励按成员均分作为奖金。

    为避免与调用方的持久化冲突，本函数直接就地修改传入的 companies / characters
    列表（调用方随后会统一 save_companies / save_characters）；经济流水单独持久化。
    """
    if not isinstance(cidx, int) or cidx < 0 or cidx >= len(companies):
        return {"success": False, "error": "无效的公司索引"}
    company = companies[cidx]
    member_ids = list(company.member_ids or [])
    if not member_ids:
        return {"success": True, "distributed": 0.0, "members": 0}

    pool = max(0.0, float(getattr(task, "reward", 0.0)) * ratio)
    if pool <= 0:
        return {"success": True, "distributed": 0.0, "members": 0}

    per = pool / len(member_ids)
    now_ms = int(time.time() * 1000)
    char_by_id = {c.id: c for c in characters}
    title = getattr(task, "title", "任务")

    from models import EconomyLog
    from storage import get_economy_logs, save_economy_logs
    logs = get_economy_logs()

    distributed = 0.0
    for mid in member_ids:
        char = char_by_id.get(mid)
        if not char:
            continue
        char.money += per
        char.updated_at = now_ms
        distributed += per
        logs.insert(0, EconomyLog(
            character_id=mid,
            action="company_task_bonus",
            amount=per,
            balance_after=char.money,
            detail=f"{company.name} 任务「{title}」奖金分配",
        ))

    if distributed > 0:
        company.funds = max(0.0, company.funds - distributed)
        company.updated_at = now_ms
        save_economy_logs(logs)
    return {"success": True, "distributed": distributed, "members": len(member_ids)}


def run_daily_settlement(days: int = 1) -> Dict[str, Any]:
    """运行日常结算"""
    from storage import get_settings, save_settings
    from config import MILLISECONDS_PER_DAY
    
    settings = get_settings()
    world_elapsed_ms = settings.world_elapsed_ms + (days * MILLISECONDS_PER_DAY)
    settings.world_elapsed_ms = world_elapsed_ms
    save_settings(settings)
    
    run_daily_economy(world_elapsed_ms)
    
    return {"success": True, "days": days}
