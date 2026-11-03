"""家庭与关系路由（V4.0 包B1 / B4）"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from models import MomentPost
from storage import get_characters, save_characters, get_moments, save_moments, get_logs, save_logs
from services.memory_service import get_relationship_intimacy, schedule_store_memory, MemoryType
from services.family_service import (
    advance_pair, can_marry, can_have_child, create_child, bind_child,
    family_view, stage_label, stage_icon, STAGE_ORDER,
)

router = APIRouter()


class PairRequest(BaseModel):
    other_id: str = Field(min_length=1, max_length=100)


def _index(characters: List) -> Dict[str, Any]:
    return {c.id: c for c in characters}


def _pair(character_id: str, other_id: str):
    chars = get_characters()
    by_id = _index(chars)
    a = by_id.get(character_id)
    b = by_id.get(other_id)
    if not a or not b:
        raise HTTPException(status_code=404, detail="角色不存在")
    if a.id == b.id:
        raise HTTPException(status_code=400, detail="不能和自己建立关系")
    return chars, a, b


def _log(name: str, action: str, desc: str):
    try:
        from models import LogEntry
        from datetime import datetime
        logs = get_logs()
        now_ms = int(time.time() * 1000)
        logs.insert(0, LogEntry(
            timestamp=datetime.now().strftime("%H:%M:%S"), timestamp_ms=now_ms,
            world_timestamp_ms=0, character_name=name, action_type=action, description=desc,
        ))
        save_logs(logs[:200])
    except Exception:
        pass


def _announce(a, b, content: str, tag: str):
    """发一条朋友圈官宣，不生成图片（省成本），走本地占位图。"""
    try:
        moments = get_moments()
        moments.append(MomentPost(
            author_id=a.id, author_name=a.name, content=content,
            image_url=f"https://picsum.photos/seed/{tag}{int(time.time())}/800/600",
            trigger_type="family", mood="happy", visibility="public",
            visible_min_intimacy=0, topics=["喜事"], mentioned_ids=[b.id],
        ))
        save_moments(moments)
    except Exception:
        pass


def _write_memory(char, text: str):
    try:
        schedule_store_memory(character_id=char.id, content=text, memory_type=MemoryType.EVENT,
                              importance=0.9, related_entities=["家庭"])
    except Exception:
        pass


@router.get("/api/characters/{character_id}/family")
async def get_family(character_id: str):
    """角色的家庭档案：阶段、伴侣、配偶、孩子。"""
    chars = get_characters()
    by_id = _index(chars)
    char = by_id.get(character_id)
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")
    data = family_view(char, by_id)
    data["intimacy_with_partner"] = (
        get_relationship_intimacy(char.id, char.partner_id) if getattr(char, "partner_id", None) else None
    )
    return {"success": True, "data": data}


@router.post("/api/characters/{character_id}/relationship/advance")
async def advance_relationship(character_id: str, request: PairRequest):
    """按当前亲密度自动推进关系阶段（朋友→密友→情侣→夫妻）。"""
    chars, a, b = _pair(character_id, request.other_id)
    intimacy = get_relationship_intimacy(a.id, b.id)
    result = advance_pair(a, b, intimacy)

    if result["advanced"]:
        save_characters(chars)
        stage = result["to"]
        if stage in ("lover", "spouse"):
            _announce(a, b, result["event"], stage)
            _write_memory(a, result["event"])
            _write_memory(b, result["event"])
        _log(a.name, "relationship", result["event"])

    return {"success": True, "data": {
        **result, "intimacy": round(intimacy, 1),
        "stage_label": stage_label(result["to"]), "stage_icon": stage_icon(result["to"]),
    }}


@router.post("/api/characters/{character_id}/marry")
async def marry(character_id: str, request: PairRequest):
    """直接结婚（需要双方成年）。"""
    chars, a, b = _pair(character_id, request.other_id)
    ok, reason = can_marry(a, b)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)

    a.relationship_stage = "spouse"
    b.relationship_stage = "spouse"
    a.spouse_id = b.id
    b.spouse_id = a.id
    a.partner_id = b.id
    b.partner_id = a.id
    now = int(time.time() * 1000)
    a.updated_at = now
    b.updated_at = now
    save_characters(chars)

    event = f"{a.name} 和 {b.name} 结婚了"
    _announce(a, b, event, "wedding")
    _write_memory(a, event)
    _write_memory(b, event)
    _log(a.name, "marry", event)
    return {"success": True, "data": {"event": event, "stage": "spouse", "stage_label": stage_label("spouse")}}


@router.post("/api/characters/{character_id}/child")
async def have_child(character_id: str, request: PairRequest):
    """生孩子：孩子继承姓氏、性格，加入通讯录并随世界时间长大。"""
    chars, a, b = _pair(character_id, request.other_id)
    ok, reason = can_have_child(a, b)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)

    child = create_child(a, b)
    chars.append(child)
    bind_child(chars, child)
    save_characters(chars)

    event = f"{a.name} 和 {b.name} 的孩子 {child.name} 出生了"
    _announce(a, b, event, "baby")
    _write_memory(a, event)
    _write_memory(b, event)
    _log(a.name, "child", event)

    return {"success": True, "data": {
        "event": event,
        "child": {
            "id": child.id, "name": child.name, "gender": child.gender,
            "age": child.age, "age_months": child.age_months,
            "personality": child.personality, "parent_ids": child.parent_ids,
        },
    }}


@router.get("/api/relationships/graph")
async def relationship_graph(center: Optional[str] = None, limit: int = 40):
    """关系网数据（V4.0 包B4）：节点 + 带类型/粗细的边。

    边来源：情侣(partner_id)、夫妻(spouse_id)、亲子(parent_ids)、
    以及亲密度 >= 35 的普通关系。
    """
    chars = [c for c in get_characters() if getattr(c, "is_alive", True)]
    by_id = _index(chars)
    if center and center in by_id:
        # 以中心角色为焦点，收拢一跳邻居
        focus = by_id[center]
        keep = {center}
        for cid in [getattr(focus, "partner_id", None), getattr(focus, "spouse_id", None)]:
            if cid:
                keep.add(cid)
        for cid in (getattr(focus, "children_ids", []) or []) + (getattr(focus, "parent_ids", []) or []):
            keep.add(cid)
        chars = [c for c in chars if c.id in keep]
        by_id = _index(chars)

    chars = chars[: max(1, min(limit, 200))]
    ids = {c.id for c in chars}

    nodes = [{
        "id": c.id, "name": c.name, "age": c.age, "gender": c.gender,
        "occupation": c.occupation,
        "stage": getattr(c, "relationship_stage", "stranger") or "stranger",
        "stage_label": stage_label(getattr(c, "relationship_stage", "")),
        "stage_icon": stage_icon(getattr(c, "relationship_stage", "")),
        "avatar_url": c.avatar_url,
        "career_title": getattr(c, "career_title", "") or c.occupation,
    } for c in chars]

    edges: List[Dict[str, Any]] = []
    seen = set()

    def add_edge(src: str, dst: str, kind: str, weight: float):
        if src not in ids or dst not in ids or src == dst:
            return
        key = tuple(sorted((src, dst)))
        if key in seen:
            return
        seen.add(key)
        edges.append({"source": src, "target": dst, "type": kind,
                      "weight": round(weight, 1),
                      "intimacy": round(get_relationship_intimacy(src, dst), 1)})

    for c in chars:
        if getattr(c, "spouse_id", None):
            add_edge(c.id, c.spouse_id, "spouse", 100)
        elif getattr(c, "partner_id", None):
            add_edge(c.id, c.partner_id, "lover", 90)
        for pid in getattr(c, "parent_ids", []) or []:
            add_edge(c.id, pid, "parent", 95)

    # 普通关系（亲密度够高才画线，避免蜘蛛网）
    for i, a in enumerate(chars):
        for b in chars[i + 1:]:
            if tuple(sorted((a.id, b.id))) in seen:
                continue
            intimacy = get_relationship_intimacy(a.id, b.id)
            if intimacy >= 35:
                add_edge(a.id, b.id, "friend", intimacy)

    return {"success": True, "data": {"nodes": nodes, "edges": edges, "stages": STAGE_ORDER}}
