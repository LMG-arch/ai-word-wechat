"""AIWeChat exec protocol routes

提供 `/api/exec`，允许以结构化请求触发世界动作（与文档保持一致）。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from storage import get_characters, save_characters, get_companies, save_companies
from models import Company


router = APIRouter()


class ExecRequest(BaseModel):
    action: str
    params: Dict[str, Any] = {}


@router.post("/api/exec")
async def exec_action(request: ExecRequest):
    action = (request.action or "").strip()
    params = request.params or {}

    if action == "create_company":
        legal_person_id = str(params.get("legal_person_id") or "").strip()
        name = str(params.get("name") or "").strip()
        if not legal_person_id or not name:
            raise HTTPException(status_code=400, detail="legal_person_id 和 name 不能为空")

        characters = get_characters()
        founder = next((c for c in characters if c.id == legal_person_id), None)
        if not founder:
            raise HTTPException(status_code=404, detail="法人角色不存在")
        if founder.money < 1000:
            raise HTTPException(status_code=400, detail="法人资金不足（至少需要1000元）")

        companies = get_companies()
        new_company = Company(
            name=name[:50],
            legal_person_id=founder.id,
            member_ids=[founder.id],
            funds=500.0,
            location_name=founder.current_location_id or "办公室",
        )
        founder.money -= 1000
        founder.company_id = new_company.id
        companies.append(new_company)
        save_companies(companies)
        save_characters(characters)
        return {"success": True, "data": new_company.model_dump()}

    if action == "recruit_member":
        company_id = str(params.get("company_id") or "").strip()
        character_id = str(params.get("character_id") or "").strip()
        if not company_id or not character_id:
            raise HTTPException(status_code=400, detail="company_id 和 character_id 不能为空")

        companies = get_companies()
        company = next((c for c in companies if c.id == company_id), None)
        if not company:
            raise HTTPException(status_code=404, detail="公司不存在")

        characters = get_characters()
        target = next((c for c in characters if c.id == character_id), None)
        if not target:
            raise HTTPException(status_code=404, detail="目标角色不存在")
        if character_id in company.member_ids:
            raise HTTPException(status_code=400, detail="该角色已是公司成员")

        company.member_ids.append(character_id)
        target.company_id = company_id
        save_companies(companies)
        save_characters(characters)
        return {"success": True, "data": company.model_dump()}

    raise HTTPException(status_code=400, detail=f"不支持的 action: {action}")

