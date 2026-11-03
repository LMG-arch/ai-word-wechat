"""AIWeChat chat routes"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any
import time
import os
import random
import asyncio

from config import DATA_DIR, AVATARS_DIR, IMAGE_PROMPTS_DIR
from models import (
    ChatMessage, SendMessageRequest, Character,
    SimulatePrivateGroupChatRequest, SendPrivateGroupMessageRequest,
    SendRedPacketRequest, ClaimRedPacketRequest, RedPacket, RedPacketClaim,
    SendTransferRequest,
)
from storage import (
    get_messages, save_messages, get_characters, save_characters,
    get_private_groups, save_private_groups, get_logs, save_logs,
    get_red_packets, save_red_packets,
)
from services.economy_service import next_claim_amount
from services.ai_service import (
    generate_ai_reply,
    user_wants_self_portrait,
    try_chat_self_portrait_image,
)
from services.memory_service import sync_private_groups
from services.heartbeat_service import append_private_group_exchange
from services.character_service import get_residential_landmarks
from services.message_style import (
    should_send_voice, estimate_voice_duration, pick_sticker_for, get_sticker,
)

router = APIRouter()


async def _background_ai_reply(conversation_id: str, req_data: Dict[str, Any]):
    """用户消息已落库后异步生成角色回复，避免前端长时间等待才能看到自己的消息。"""
    from models import SendMessageRequest, ChatMessage

    request = SendMessageRequest(**req_data)
    characters = get_characters()
    character = next((c for c in characters if c.id == conversation_id), None)
    if not character:
        return

    user_text = request.content or ""
    if request.message_type == "sticker":
        reply_prompt = (
            f"对方刚才发来一个表情「{user_text}」。你顺着这个情绪回一句，"
            "像微信聊天一样自然，不要提到「表情」两个字，也不要复述这段说明。"
        )
    elif request.message_type == "voice":
        reply_prompt = getattr(request, "voice_text", None) or user_text or "用户发来一条语音"
    elif request.message_type == "image":
        reply_prompt = (
            "对方发来一张图片。你看不清具体画面，就自然回应一句——猜猜是什么、"
            "或者让对方说说拍的是什么。不要出现「图片消息」这个词，也不要复述这段说明。"
        )
    else:
        reply_prompt = user_text if user_text else "用户发来一条消息"

    # 兜底回复（LLM 不可用时）只能拼接「人话」，指令型场景统一换成自然描述，避免回显提示词
    if request.message_type == "sticker":
        display_input = "（对方发来一个表情）"
    elif request.message_type == "image":
        display_input = "（对方发来一张图片）"
    else:
        display_input = getattr(request, "voice_text", None) or user_text
    reply_content = await generate_ai_reply(
        character, reply_prompt, conversation_id, display_input=display_input
    )
    if not reply_content:
        reply_content = "……"

    portrait_url: Optional[str] = None
    if request.message_type == "text" and user_text and user_wants_self_portrait(user_text):
        portrait_url = await try_chat_self_portrait_image(character)
        if portrait_url:
            reply_content = (reply_content or "").strip()
            if reply_content and "图" not in reply_content[-20:] and "画" not in reply_content[-10:]:
                reply_content = reply_content + "\n\n（已按你的请求生成一张我此刻的状态截图）"
            elif not reply_content:
                reply_content = "（已按你的请求生成一张我此刻的状态截图）"

    ai_message = ChatMessage(
        conversation_id=conversation_id,
        sender_id=character.id,
        content=reply_content,
        is_from_user=False,
        message_type="image" if portrait_url else "text",
        image_url=portrait_url,
    )

    # V4.0 包A5：按心情决定这条回复用文字 / 语音条发出
    if not portrait_url and request.message_type == "text":
        mood = getattr(character, "mood", "calm") or "calm"
        if should_send_voice(reply_content, mood):
            ai_message.message_type = "voice"
            ai_message.voice_text = reply_content
            ai_message.voice_duration = estimate_voice_duration(reply_content)
            ai_message.content = "[语音]"

    messages = get_messages()
    messages.append(ai_message)

    # 短促有情绪的回复，追加一条内置表情
    if not portrait_url:
        mood = getattr(character, "mood", "calm") or "calm"
        sticker_id = pick_sticker_for(reply_content, mood)
        if sticker_id:
            messages.append(ChatMessage(
                conversation_id=conversation_id,
                sender_id=character.id,
                content=get_sticker(sticker_id)["name"],
                is_from_user=False,
                message_type="sticker",
                sticker_id=sticker_id,
            ))

    save_messages(messages)
    save_characters(characters)
    _add_log(character.name, "对话", f"回复：\"{reply_content[:30]}...\"")

    # V4.0：和用户聊天也累积亲密度（影响朋友圈可见范围）
    try:
        from services.memory_service import apply_relationship_interaction
        apply_relationship_interaction("user", character.id, "chat")
    except Exception:
        pass


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


@router.get("/api/stickers")
async def list_stickers():
    """V4.0 包A5：内置表情包清单（纯本地，不依赖外网）"""
    from services.message_style import STICKERS
    return {"success": True, "data": STICKERS}


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
async def send_message(request: SendMessageRequest, background_tasks: BackgroundTasks):
    """先保存用户消息并立即返回；角色回复在后台生成。"""
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
        # V4.0 包A5：前端语音条不发真实音频，允许用 voice_text/时长表达
        if not user_text or user_text.startswith("["):
            raise HTTPException(status_code=400, detail="voice_url is required for voice message")

    # V4.0 包A5：用户发表情贴纸，content 传的就是 sticker_id
    sticker_id = None
    sticker_duration = None
    if request.message_type == "sticker":
        sticker = get_sticker(user_text)
        if not sticker:
            raise HTTPException(status_code=400, detail="未知的表情")
        sticker_id = sticker["id"]
        user_text = sticker["name"]
    elif request.message_type == "voice" and not request.voice_url:
        sticker_duration = estimate_voice_duration(user_text)

    user_message = ChatMessage(
        conversation_id=request.conversation_id,
        sender_id="user",
        content=user_text if user_text else ("[图片消息]" if request.message_type == "image" else "[语音消息]"),
        message_type=request.message_type,
        image_url=request.image_url,
        voice_url=request.voice_url,
        voice_text=user_text if (request.message_type == "voice" and not request.voice_url) else None,
        voice_duration=sticker_duration,
        sticker_id=sticker_id,
        is_from_user=True,
    )
    messages.append(user_message)
    save_messages(messages)

    # 贴纸消息的 content 已被换成中文名，后台回复要用这个名字而不是 id
    payload = request.model_dump()
    payload["content"] = user_text
    background_tasks.add_task(_background_ai_reply, request.conversation_id, payload)

    return {
        "success": True,
        "data": {
            "user_message": user_message.model_dump(),
            "pending_reply": True,
        },
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
    """同步双人私聊群：亲密度>15 自动建群，降至阈值以下自动解散"""
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
async def simulate_private_group_chat(
    group_id: str, body: SimulatePrivateGroupChatRequest
):
    """模拟私人群聊对话（系统生成，用户只读）"""
    groups = get_private_groups()
    group = next((g for g in groups if g.id == group_id and g.is_active), None)
    if not group:
        raise HTTPException(status_code=404, detail="Private group not found")

    characters = get_characters()
    char_map = {c.id: c for c in characters}
    if any(mid not in char_map for mid in group.member_ids):
        raise HTTPException(status_code=400, detail="Group members not found")

    await append_private_group_exchange(group, body.topic)
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


async def _background_group_reply(group, user_text: str):
    """用户在群里发言后，让 1-2 名成员接话（被 @ 的优先）。"""
    from services.ai_service import generate_ai_reply

    try:
        chars = {c.id: c for c in get_characters() if c.is_alive}
        members = [chars[mid] for mid in group.member_ids if mid in chars]
        if not members:
            return
        conv_id = f"group:{group.id}"

        mentioned = [m for m in members if ("@" + m.name) in user_text]
        first = random.choice(mentioned) if mentioned else random.choice(members)
        prompt = (
            f"你们是「{'、'.join(group.member_names)}」的微信群。用户刚在群里说：{user_text}。"
            "请你用一句话回应（20-60 字），像真实群聊，不要复述系统说明。"
        )
        reply = await generate_ai_reply(first, prompt, conv_id) or "……"
        msgs = get_messages()
        msgs.append(ChatMessage(conversation_id=conv_id, sender_id=first.id, content=reply, is_from_user=False))
        save_messages(msgs)

        others = [m for m in members if m.id != first.id]
        if others and random.random() < 0.45:
            second = random.choice(others)
            prompt2 = f"{first.name} 刚在群里回了：{reply}。你可以顺着接一句（20-50 字），像群聊。"
            reply2 = await generate_ai_reply(second, prompt2, conv_id) or "……"
            msgs = get_messages()
            msgs.append(ChatMessage(conversation_id=conv_id, sender_id=second.id, content=reply2, is_from_user=False))
            save_messages(msgs)
    except Exception:
        # 后台回复失败不应影响用户已发送的消息
        pass


@router.post("/api/groups/private/{group_id}/send")
async def send_private_group_message(
    group_id: str, request: SendPrivateGroupMessageRequest, background_tasks: BackgroundTasks
):
    """用户在私人群里发言，角色在后台接话。"""
    groups = get_private_groups()
    group = next((g for g in groups if g.id == group_id and g.is_active), None)
    if not group:
        raise HTTPException(status_code=404, detail="Private group not found")

    conv_id = f"group:{group.id}"
    # V4.0 包A5：群里也能发表情贴纸
    content = request.content
    sticker_id = None
    if (request.message_type or "text") == "sticker":
        sticker = get_sticker(content)
        if not sticker:
            raise HTTPException(status_code=400, detail="未知的表情")
        sticker_id = sticker["id"]
        content = sticker["name"]

    user_message = ChatMessage(
        conversation_id=conv_id,
        sender_id="user",
        content=content,
        is_from_user=True,
        message_type=request.message_type or "text",
        sticker_id=sticker_id,
    )
    messages = get_messages()
    messages.append(user_message)
    save_messages(messages)

    if sticker_id is None:
        background_tasks.add_task(_background_group_reply, group, request.content)
    return {"success": True, "data": {"message": user_message.model_dump(), "pending_reply": True}}


# ==================== 红包（V4.0 包A2）====================

def _resolve_conversation_members(conversation_id: str):
    """返回该会话里可抢红包的存活角色列表（单聊=对方，群聊=全部成员）。"""
    chars = {c.id: c for c in get_characters() if c.is_alive}
    if conversation_id.startswith("group:"):
        gid = conversation_id.split(":", 1)[1]
        group = next((g for g in get_private_groups() if g.id == gid), None)
        if not group:
            return []
        return [chars[mid] for mid in group.member_ids if mid in chars]
    ch = chars.get(conversation_id)
    return [ch] if ch else []


def _thank_text(amount: float) -> str:
    """按抢到的金额生成不同的感谢话术（不调用 LLM，零成本）。"""
    if amount >= 5:
        return random.choice(["哇，谢谢老板！", "老板大气！", "手气真好，谢谢！"])
    if amount >= 1:
        return random.choice(["谢谢老板~", "收下啦，谢谢！", "嗯，谢啦"])
    return random.choice(["就几分钱…谢谢啊", "蚊子腿也是肉，谢谢", "聊胜于无吧哈哈"])


def _claim_packet_inner(packet: RedPacket, actor_id: str, actor_name: str):
    """在内存中的 packet 上执行一次领取。返回 (ok, amount_or_reason)。调用方负责落库与加钱。"""
    if packet.is_finished:
        return False, "红包已被抢完"
    if any(c.actor_id == actor_id for c in packet.claims):
        return False, "你已经抢过这个红包了"
    remain_cents = int(round(packet.remaining * 100))
    left = packet.count - len(packet.claims)
    cents = next_claim_amount(remain_cents, left)
    amount = cents / 100
    packet.claims.append(RedPacketClaim(actor_id=actor_id, actor_name=actor_name, amount=amount))
    return True, amount


def _packet_to_dict(packet: RedPacket) -> Dict[str, Any]:
    data = packet.model_dump()
    data["remaining"] = packet.remaining
    data["is_finished"] = packet.is_finished
    return data


@router.post("/api/red-packets")
async def create_red_packet(request: SendRedPacketRequest, background_tasks: BackgroundTasks):
    """发一个拼手气红包（单聊或群聊）。"""
    chars = {c.id: c for c in get_characters()}
    if request.conversation_id.startswith("group:"):
        gid = request.conversation_id.split(":", 1)[1]
        group = next((g for g in get_private_groups() if g.id == gid and g.is_active), None)
        if not group:
            raise HTTPException(status_code=404, detail="群聊不存在")
    elif request.conversation_id not in chars:
        raise HTTPException(status_code=404, detail="角色不存在")

    packet = RedPacket(
        conversation_id=request.conversation_id,
        sender_id="user",
        sender_name="我",
        blessing=request.blessing or "恭喜发财，大吉大利",
        total_amount=round(float(request.total_amount), 2),
        count=request.count,
    )
    packets = get_red_packets()
    packets.append(packet)
    save_red_packets(packets)

    msg = ChatMessage(
        conversation_id=request.conversation_id,
        sender_id="user",
        content=packet.blessing,
        message_type="red_packet",
        red_packet_id=packet.id,
        is_from_user=True,
    )
    messages = get_messages()
    messages.append(msg)
    save_messages(messages)

    background_tasks.add_task(_auto_claim_red_packet, packet.id)
    return {"success": True, "data": {"packet": _packet_to_dict(packet), "message": msg.model_dump()}}


@router.get("/api/red-packets/{packet_id}")
async def get_red_packet(packet_id: str):
    packet = next((p for p in get_red_packets() if p.id == packet_id), None)
    if not packet:
        raise HTTPException(status_code=404, detail="红包不存在")
    return {"success": True, "data": _packet_to_dict(packet)}


@router.post("/api/red-packets/{packet_id}/claim")
async def claim_red_packet(packet_id: str, request: ClaimRedPacketRequest):
    """领取红包。actor_id='user' 表示用户本人，否则按角色 id 加钱。"""
    packets = get_red_packets()
    packet = next((p for p in packets if p.id == packet_id), None)
    if not packet:
        raise HTTPException(status_code=404, detail="红包不存在")
    actor_name = request.actor_name or ("我" if request.actor_id == "user" else request.actor_id)
    ok, res = _claim_packet_inner(packet, request.actor_id, actor_name)
    if not ok:
        raise HTTPException(status_code=400, detail=res)
    save_red_packets(packets)
    if request.actor_id != "user":
        characters = get_characters()
        target = next((c for c in characters if c.id == request.actor_id), None)
        if target:
            target.money = round(target.money + res, 2)
            save_characters(characters)
    return {"success": True, "data": {"amount": res, "packet": _packet_to_dict(packet)}}


async def _auto_claim_red_packet(packet_id: str):
    """发红包后让会话内角色依次抢（拟人化：随机顺序、随机间隔、抢完说谢谢）。"""
    try:
        await asyncio.sleep(0.6)
        packets = get_red_packets()
        packet = next((p for p in packets if p.id == packet_id), None)
        if not packet:
            return
        members = _resolve_conversation_members(packet.conversation_id)
        if not members:
            return
        random.shuffle(members)
        for char in members:
            packets = get_red_packets()
            packet = next((p for p in packets if p.id == packet_id), None)
            if not packet or packet.is_finished:
                break
            ok, amount = _claim_packet_inner(packet, char.id, char.name)
            if not ok:
                continue
            save_red_packets(packets)
            characters = get_characters()
            target = next((c for c in characters if c.id == char.id), None)
            if target:
                target.money = round(target.money + amount, 2)
                save_characters(characters)
            thanks = ChatMessage(
                conversation_id=packet.conversation_id,
                sender_id=char.id,
                content=f"{_thank_text(amount)}（抢到 {amount:.2f} 元）",
                is_from_user=False,
            )
            msgs = get_messages()
            msgs.append(thanks)
            save_messages(msgs)
            await asyncio.sleep(random.uniform(0.3, 0.8))
    except Exception:
        pass


# ==================== 转账（V4.0 包A3）====================

@router.post("/api/transfers")
async def send_transfer(request: SendTransferRequest):
    """用户向角色转账（带备注）。角色按金额与性格倾向决定收/拒。"""
    conv = request.conversation_id
    if conv.startswith("group:"):
        raise HTTPException(status_code=400, detail="转账仅支持单聊")
    chars = {c.id: c for c in get_characters()}
    char = chars.get(conv)
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")

    amount = round(float(request.amount), 2)
    # 大额一律拒收；中等金额有概率客气地拒收
    reject = amount >= 1000 or (amount >= 200 and random.random() < 0.3)
    status = "rejected" if reject else "accepted"

    msg = ChatMessage(
        conversation_id=conv,
        sender_id="user",
        content=request.note or "转账",
        message_type="transfer",
        transfer_amount=amount,
        transfer_note=request.note,
        transfer_status=status,
        is_from_user=True,
    )
    messages = get_messages()
    messages.append(msg)

    if status == "accepted":
        characters = get_characters()
        target = next((c for c in characters if c.id == conv), None)
        if target:
            target.money = round(target.money + amount, 2)
            save_characters(characters)
        reply_text = random.choice(["那我收下啦，谢谢", "收到，下次请你吃饭", "嗯…谢了哈", "怎么突然转账，谢谢啦"])
    else:
        reply_text = random.choice(["这么多钱我不能收，你收回去", "你这是干嘛，咱俩谁跟谁", "收回去，别乱花钱"])

    reply = ChatMessage(conversation_id=conv, sender_id=char.id, content=reply_text, is_from_user=False)
    messages.append(reply)
    save_messages(messages)

    return {
        "success": True,
        "data": {"message": msg.model_dump(), "status": status, "reply": reply_text, "amount": amount},
    }
