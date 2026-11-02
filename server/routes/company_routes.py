"""AIWeChat company routes"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
import time
import random

from config import DATA_DIR, WORLD_COMPANY_BIND
from models import Company, CreateCompanyRequest, AddCompanyMemberRequest, Character
from storage import (
    get_companies, save_companies, get_characters, save_characters,
    get_logs, save_logs, get_active_world_map, save_persisted_world_map,
)
router = APIRouter()


def get_preset_models(api_type: str) -> list:
    """获取预设模型列表"""
    if api_type == 'llm':
        return ['gpt-3.5-turbo', 'gpt-4', 'gpt-4o', 'claude-3-haiku', 'claude-3-sonnet']
    elif api_type == 'image':
        return ['dall-e-3', 'dall-e-2', 'stable-diffusion']
    return []


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


@router.get("/api/companies")
async def list_companies():
    companies = get_companies()
    return {"success": True, "data": [item.model_dump() for item in companies]}


@router.get("/api/companies/{company_id}")
async def get_company_detail(company_id: str):
    companies = get_companies()
    company = next((item for item in companies if item.id == company_id), None)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    members = [item for item in get_characters() if item.id in company.member_ids]
    return {
        "success": True,
        "data": {
            **company.model_dump(),
            "members": [item.model_dump() for item in members],
        }
    }


@router.post("/api/companies")
async def create_company(request: CreateCompanyRequest):
    characters = get_characters()
    legal_person = next((c for c in characters if c.id == request.legal_person_id), None)
    if not legal_person:
        raise HTTPException(status_code=404, detail="法人角色不存在")
    if legal_person.money < 1000:
        raise HTTPException(status_code=400, detail="法人资金不足（至少需要1000元）")
    companies = get_companies()
    legal_person.money -= 1000
    legal_person.company_id = None
    new_company = Company(
        name=request.name,
        legal_person_id=request.legal_person_id,
        member_ids=[request.legal_person_id] + request.member_ids,
        funds=500.0,
        location_name=legal_person.current_location_id or "办公室",
    )
    legal_person.company_id = new_company.id
    for member_id in request.member_ids:
        member = next((c for c in characters if c.id == member_id), None)
        if member:
            member.company_id = new_company.id
    companies.append(new_company)
    save_companies(companies)
    save_characters(characters)
    _add_log(legal_person.name, "创建公司", f"成功创建公司「{request.name}」，投入500元启动资金")
    for mid in request.member_ids:
        m = next((c for c in characters if c.id == mid), None)
        if m:
            _add_log(m.name, "加入公司", f"成为 {request.name} 的创始成员")
    return {"success": True, "data": new_company.model_dump()}


@router.post("/api/companies/{company_id}/recruit")
async def recruit_company_member(company_id: str, request: AddCompanyMemberRequest):
    """招募角色加入公司"""
    companies = get_companies()
    company = next((c for c in companies if c.id == company_id), None)
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    characters = get_characters()
    target = next((c for c in characters if c.id == request.character_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="目标角色不存在")
    if request.character_id in company.member_ids:
        raise HTTPException(status_code=400, detail="该角色已是公司成员")
    company.member_ids.append(request.character_id)
    target.company_id = company_id
    save_companies(companies)
    save_characters(characters)
    _add_log(company.name, "招募", f"成功招募 {target.name} 加入公司")
    return {"success": True, "data": company.model_dump()}


@router.post("/api/companies/ai-manage")
async def ai_manage_companies():
    """AI 自主管理公司：有经济压力且有钱的角色可能创建公司，公司可能招募成员"""
    characters = get_characters()
    companies = get_companies()
    alive_chars = [c for c in characters if c.is_alive]
    
    chars_without_company = [c for c in alive_chars if not c.company_id and c.money >= 1500]
    if chars_without_company and random.random() < 0.15:
        founder = random.choice(chars_without_company)
        occupation = founder.occupation or "创业者"
        company_names = [
            f"{founder.name}的{occupation}工作室",
            f"{occupation}事务所",
            f"{founder.name}的{occupation}公司",
            f"云海{occupation}中心",
        ]
        company_name = random.choice(company_names)
        
        founder.money -= 1000
        new_company = Company(
            name=company_name,
            legal_person_id=founder.id,
            member_ids=[founder.id],
            funds=500.0,
            location_name=founder.current_location_id or "办公室",
        )
        founder.company_id = new_company.id
        companies.append(new_company)
        save_companies(companies)
        save_characters(characters)
        _add_log(founder.name, "AI创业", f"自主创建公司「{company_name}」，投入500元启动资金")
    
    for company in companies:
        if random.random() < 0.1:
            founder = next((c for c in alive_chars if c.id == company.legal_person_id), None)
            if founder and founder.money >= 500:
                candidates = [c for c in alive_chars if c.id not in company.member_ids and not c.company_id]
                if candidates:
                    candidates.sort(key=lambda c: random.random(), reverse=True)
                    recruit = candidates[0]
                    recruit.company_id = company.id
                    company.member_ids.append(recruit.id)
                    save_companies(companies)
                    save_characters(characters)
                    _add_log(company.name, "AI招募", f"自主招募 {recruit.name} 加入公司")
    
    return {"success": True}


@router.post("/api/companies/{company_id}/members")
async def add_company_member(company_id: str, request: AddCompanyMemberRequest):
    """[Deprecated] 与 `POST /api/companies/{company_id}/recruit` 语义重复。

    差异仅在于：本接口对"已是成员"的请求静默返回成功（幂等），
    而 `/recruit` 会返回 400 明确提示冲突。
    保留本接口仅为兼容既有调用方，新调用请使用 `/recruit`。
    """
    companies = get_companies()
    characters = get_characters()
    member = next((c for c in characters if c.id == request.character_id), None)
    if not member:
        raise HTTPException(status_code=404, detail="Character not found")
    for cidx, company in enumerate(companies):
        if company.id != company_id:
            continue
        if request.character_id not in company.member_ids:
            company.member_ids.append(request.character_id)
            company.updated_at = int(time.time() * 1000)
            companies[cidx] = company
            save_companies(companies)
        for idx, char in enumerate(characters):
            if char.id == request.character_id:
                char.company_id = company.id
                char.updated_at = int(time.time() * 1000)
                characters[idx] = char
                break
        save_characters(characters)
        return {"success": True, "data": company.model_dump()}
    raise HTTPException(status_code=404, detail="Company not found")
