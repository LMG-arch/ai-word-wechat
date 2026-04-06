"""AIWeChat chat routes"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
import time
import os

from config import DATA_DIR, AVATARS_DIR, IMAGE_PROMPTS_DIR
from models import ChatMessage, SendMessageRequest, Character
from storage import (
    get_messages, save_messages, get_characters, save_characters,
    get_private_groups, save_private_groups, get_logs, save_logs,
)
from services.ai_service import generate_ai_reply
from services.memory_service import sync_private_groups
from services.heartbeat_service import append_private_group_exchange
from services.character_service import get_residential_landmarks

router = APIRouter()


def _add_log(character_name: str, action_type: str, description: str):
    """Internal log helper."""
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


@router.get("/api/messages/{conversation_id}")
async def get_conversation_messages(conversation_id: str):
    """获取会话消息"""
    messages = get_messages()
    conv_messages = [msg for msg in messages if msg.conversation_id == conversation_id]
    conv_messages.sort(key=lambda x: x.timestamp)
    return {"success": True, "data": [msg.model_dump() for msg in conv_messages]}


@router.post("/api/messages/{conversation_id}/read")
async def mark_conversation_read(conversation_id: str):
    """将会话中的 AI 消息标记为已读"""
    messages = get_messages()
    updated_count = 0
    for message in messages:
        if (
            message.conversation_id == conversation_id
            and not message.is_from_user
            and not message.is_read
        ):
            message.is_read = True
            updated_count += 1
    if updated_count > 0:
        save_messages(messages)
    return {"success": True, "data": {"updated_count": updated_count}}


@router.post("/api/messages/send")
async def send_message(request: SendMessageRequest):
    """发送消息并获取 AI 回复"""
    messages = get_messages()
    characters = get_characters()
    
    character = None
    for char in characters:
        if char.id == request.conversation_id:
            character = char
            break
    
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    user_text = request.content or ""
    if request.message_type == "image" and not request.image_url:
        raise HTTPException(status_code=400, detail="image_url is required for image message")
    if request.message_type == "voice" and not request.voice_url:
        raise HTTPException(status_code=400, detail="voice_url is required for voice message")

    user_message = ChatMessage(
        conversation_id=request.conversation_id,
        sender_id="user",
        content=user_text if user_text else ("[图片消息]" if request.message_type == "image" else "[语音消息]"),
        message_type=request.message_type,
        image_url=request.image_url,
        voice_url=request.voice_url,
        is_from_user=True
    )
    messages.append(user_message)
    save_messages(messages)
    
    reply_prompt = user_text if user_text else ("用户发送了图片消息" if request.message_type == "image" else "用户发送了语音消息")
    reply_content = await generate_ai_reply(character, reply_prompt)
    
    ai_message = ChatMessage(
        conversation_id=request.conversation_id,
        sender_id=character.id,
        content=reply_content,
        is_from_user=False
    )
    messages.append(ai_message)
    save_messages(messages)
    
    save_characters(characters)
    _add_log(character.name, "对话", f"回复：\"{reply_content[:30]}...\"")

    return {
        "success": True,
        "data": {
            "user_message": user_message.model_dump(),
            "ai_message": ai_message.model_dump()
        }
    }


@router.delete("/api/messages/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """清空会话消息"""
    messages = get_messages()
    messages = [msg for msg in messages if msg.conversation_id != conversation_id]
    save_messages(messages)
    return {"success": True}


@router.post("/api/groups/private/sync")
async def sync_private_groups_api():
    """同步私人群聊：亲密度>=21自动建群，失效自动解散"""
    summary = sync_private_groups()
    return {"success": True, "data": summary}


@router.get("/api/groups/private")
async def list_private_groups():
    """获取私人群聊列表（仅供查看，不可发送）"""
    sync_private_groups()
    groups = [g for g in get_private_groups() if g.is_active]
    groups.sort(key=lambda item: item.created_at, reverse=True)
    return {"success": True, "data": [g.model_dump() for g in groups]}


@router.get("/api/groups/private/{group_id}/messages")
async def get_private_group_messages(group_id: str):
    """查看私人群聊消息（只读）"""
    groups = get_private_groups()
    group = next((g for g in groups if g.id == group_id and g.is_active), None)
    if not group:
        raise HTTPException(status_code=404, detail="Private group not found")
    conv_id = f"group:{group.id}"
    messages = get_messages()
    conv_messages = [msg for msg in messages if msg.conversation_id == conv_id]
    conv_messages.sort(key=lambda x: x.timestamp)
    return {
        "success": True,
        "data": {
            "group": group.model_dump(),
            "messages": [m.model_dump() for m in conv_messages],
            "read_only": True,
        },
    }


@router.post("/api/groups/private/{group_id}/simulate")
async def simulate_private_group_chat(group_id: str, request):
    """模拟私人群聊对话（系统生成，用户只读）"""
    # Dynamic import to avoid circular dependency
    from pydantic import BaseModel
    class SimulatePrivateGroupChatRequest(BaseModel):
        topic: Optional[str] = None
    req = SimulatePrivateGroupChatRequest(**(request.__dict__ if hasattr(request, '__dict__') else {}))
    
    groups = get_private_groups()
    group = next((g for g in groups if g.id == group_id and g.is_active), None)
    if not group:
        raise HTTPException(status_code=404, detail="Private group not found")

    characters = get_characters()
    char_map = {c.id: c for c in characters}
    if any(mid not in char_map for mid in group.member_ids):
        raise HTTPException(status_code=400, detail="Group members not found")

    await append_private_group_exchange(group, req.topic if hasattr(req, 'topic') else None)
    conv_id = f"group:{group.id}"
    messages = get_messages()
    recent = [m for m in messages if m.conversation_id == conv_id]
    recent.sort(key=lambda m: m.timestamp, reverse=True)
    last_two = list(reversed(recent[:2]))

    return {
        "success": True,
        "data": {
            "group": group.model_dump(),
            "messages": [m.model_dump() for m in last_two],
            "read_only": True,
        },
    }
