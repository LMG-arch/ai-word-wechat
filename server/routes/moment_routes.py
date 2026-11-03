"""AIWeChat moment routes"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any
import time
import os

from config import DATA_DIR
from models import MomentPost, MomentCommentRequest, GenerateMomentRequest, UserCreateMomentRequest
from storage import (
    get_moments, save_moments, get_settings, save_settings,
    get_characters, get_logs, save_logs,
)
from services.moment_service import (
    run_moment_auto_interactions, get_comment_by_id, has_reply_for_comment,
    fallback_moment_image_url,
)
from services.ai_service import (
    generate_moment_content, generate_moment_image_plan,
    generate_avatar, generate_auto_comment_text,
)
from services.moment_extras import (
    extract_topics, extract_mention_names, resolve_mentioned_ids,
    topic_leaderboard, location_leaderboard, normalize_topic, mentioned_reply_text,
)
from services.memory_service import store_memory, MemoryType, can_view_moment, apply_relationship_interaction, sync_private_groups

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


@router.get("/api/moments")
async def list_moments(
    viewer_id: Optional[str] = None,
    limit: int = 50,
    topic: Optional[str] = None,
    location: Optional[str] = None,
):
    """朋友圈时间线（按时间倒序，按亲密度过滤可见性）

    V4.0 包A4：支持 ?topic=话题 与 ?location=地标 过滤。
    """
    moments = get_moments()
    moments.sort(key=lambda m: m.timestamp, reverse=True)
    visible = [m for m in moments if can_view_moment(viewer_id, m)]
    if topic:
        key = normalize_topic(topic)
        visible = [m for m in visible if key in (m.topics or [])]
    if location:
        key = location.strip()
        visible = [m for m in visible if (m.location or "") == key]
    return {"success": True, "data": [m.model_dump() for m in visible[:max(1, min(limit, 200))]]}


@router.get("/api/moments/topics")
async def list_moment_topics(viewer_id: Optional[str] = None, limit: int = 20):
    """V4.0 包A4：话题聚合榜"""
    moments = [m for m in get_moments() if can_view_moment(viewer_id, m)]
    return {"success": True, "data": topic_leaderboard(moments, limit=limit)}


@router.get("/api/moments/locations")
async def list_moment_locations(viewer_id: Optional[str] = None, limit: int = 20):
    """V4.0 包A4：位置签到榜"""
    moments = [m for m in get_moments() if can_view_moment(viewer_id, m)]
    return {"success": True, "data": location_leaderboard(moments, limit=limit)}


@router.post("/api/users/moments")
async def create_user_moment(body: UserCreateMomentRequest, background_tasks: BackgroundTasks):
    """用户发布朋友圈（V4.0：支持话题 / 位置签到 / @好友 / 可见范围）"""
    content = (body.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    image_url = body.image_url
    prompt_file = None
    if body.generate_image:
        hint = (body.image_prompt or content).strip()[:600]
        gen = await generate_avatar({
            "avatar_prompt": f"Lifestyle / scene photograph for social feed, visual idea: {hint}. High quality, no text, no watermark.",
            "style": "realistic",
            "image_kind": "scene",
        })
        if gen.get("success"):
            image_url = gen.get("data", {}).get("image_url")
            prompt_file = gen.get("data", {}).get("prompt_file")
    if not image_url:
        image_url = fallback_moment_image_url(f"user:{content[:120]}")

    characters = get_characters()
    topics = extract_topics(content)
    names = extract_mention_names(content)
    mentioned_ids = resolve_mentioned_ids(names, characters, body.mention_names)
    mentioned_names = [n for n in names if n not in body.mention_names]

    visibility = (body.visibility or "friends").lower()
    if visibility not in ("public", "friends", "private"):
        visibility = "friends"

    moments = get_moments()
    post = MomentPost(
        author_id="user", author_name="用户", content=content,
        image_url=image_url, image_prompt_file=prompt_file,
        trigger_type="user", mood="active", visible_min_intimacy=0,
        visibility=visibility,
        location=(body.location or "").strip() or None,
        topics=topics,
        mentioned_ids=mentioned_ids,
    )
    moments.append(post)
    save_moments(moments)
    _add_log("用户", "moment_post", f"发布朋友圈：{content[:20]}")

    if mentioned_ids:
        background_tasks.add_task(_mentioned_characters_respond, post.id, mentioned_ids)

    return {"success": True, "data": post.model_dump()}


def _mentioned_characters_respond(moment_id: str, mentioned_ids: List[str]):
    """被 @ 的角色稍后到评论区出现（模板化，不消耗 token）。"""
    try:
        moments = get_moments()
        post = next((m for m in moments if m.id == moment_id), None)
        if not post:
            return
        characters = {c.id: c for c in get_characters()}
        from models import MomentComment
        added = False
        for cid in mentioned_ids:
            char = characters.get(cid)
            if not char:
                continue
            if any(c.author_id == cid for c in post.comments):
                continue
            post.comments.append(MomentComment(
                moment_id=post.id, author_id=char.id, author_name=char.name,
                content=mentioned_reply_text(post.author_name, char.name),
            ))
            apply_relationship_interaction(char.id, post.author_id, "comment")
            added = True
        if added:
            save_moments(moments)
            sync_private_groups()
    except Exception:
        pass


@router.post("/api/moments/{moment_id}/like")
async def like_moment(moment_id: str, author_id: str):
    """点赞朋友圈"""
    characters = get_characters()
    liker = next((c for c in characters if c.id == author_id), None)
    if not liker:
        raise HTTPException(status_code=404, detail="Character not found")

    moments = get_moments()
    for i, post in enumerate(moments):
        if post.id != moment_id:
            continue
        if not can_view_moment(author_id, post):
            raise HTTPException(status_code=403, detail="Moment not visible for this character")
        if author_id not in post.liked_by:
            post.liked_by.append(author_id)
            apply_relationship_interaction(author_id, post.author_id, "like")
            moments[i] = post
            save_moments(moments)
            sync_private_groups()
        return {"success": True, "data": post.model_dump()}
    raise HTTPException(status_code=404, detail="Moment not found")


@router.post("/api/moments/{moment_id}/comment")
async def comment_moment(moment_id: str, request: MomentCommentRequest):
    """评论朋友圈（支持自动生成评论）"""
    characters = get_characters()
    commenter = next((c for c in characters if c.id == request.author_id), None)
    if not commenter:
        raise HTTPException(status_code=404, detail="Character not found")

    moments = get_moments()
    for i, post in enumerate(moments):
        if post.id != moment_id:
            continue
        if not can_view_moment(request.author_id, post):
            raise HTTPException(status_code=403, detail="Moment not visible for this character")

        parent_comment = None
        if request.reply_to_comment_id:
            parent_comment = get_comment_by_id(post.comments, request.reply_to_comment_id)
            if not parent_comment:
                raise HTTPException(status_code=404, detail="Parent comment not found")
            if has_reply_for_comment(post.comments, parent_comment.id):
                raise HTTPException(status_code=400, detail="Each comment can only be replied once")
        else:
            if any(
                c.author_id == request.author_id and c.parent_comment_id is None
                for c in post.comments
            ):
                raise HTTPException(status_code=400, detail="Character already commented this moment")

        content = (request.content or "").strip()
        if request.auto_generate or not content:
            moment_author = next((c for c in characters if c.id == post.author_id), None)
            if not moment_author:
                raise HTTPException(status_code=404, detail="Moment author not found")
            content = await generate_auto_comment_text(
                commenter=commenter, moment_author=moment_author,
                moment_content=post.content, parent_comment=parent_comment
            )
        if parent_comment and f"@{parent_comment.author_name}" not in content:
            content = f"@{parent_comment.author_name} {content}"
        from models import MomentComment
        comment = MomentComment(
            moment_id=post.id, author_id=commenter.id, author_name=commenter.name,
            content=content,
            parent_comment_id=parent_comment.id if parent_comment else None,
            reply_to_author_id=parent_comment.author_id if parent_comment else None,
        )
        post.comments.append(comment)
        apply_relationship_interaction(commenter.id, post.author_id, "comment")
        if parent_comment:
            apply_relationship_interaction(commenter.id, parent_comment.author_id, "comment")
        moments[i] = post
        save_moments(moments)
        sync_private_groups()
        return {"success": True, "data": comment.model_dump()}
    raise HTTPException(status_code=404, detail="Moment not found")


@router.post("/api/moments/auto-interactions/run")
async def run_moment_auto_interactions_api(limit: int = 30):
    """手动触发朋友圈自动互动批处理"""
    summary = await run_moment_auto_interactions(limit=limit)
    settings = get_settings()
    settings.auto_moment_last_run_time = int(time.time() * 1000)
    save_settings(settings)
    return {"success": True, "data": summary}
