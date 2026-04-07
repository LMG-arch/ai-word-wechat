"""
AIWeChat 朋友圈服务模块
朋友圈生成、自动互动、评论/点赞逻辑。
"""

from __future__ import annotations

import os
import time
import random
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime

# 导入依赖（避免循环导入）
from config import DATA_DIR

def fallback_moment_image_url(seed: str) -> str:
    """配图兜底（picsum 占位，保证朋友圈始终图文并茂）。"""
    digest = hashlib.md5(seed.encode("utf-8")).hexdigest()[:12]
    return f"https://picsum.photos/seed/{digest}/800/600"


def should_continue_reply(parent_content: str, reply_content: str, intimacy: float) -> bool:
    """判断是否继续回复（避免无限循环）"""
    # 兼容两种亲密度量纲：0-1 或 0-100
    if 0 <= intimacy <= 1:
        intimacy = intimacy * 100

    # 父内容过长时停止继续回复，避免刷屏/循环对话
    if len(parent_content or "") > 300:
        return False
    if len(reply_content) < 5:
        return False
    if parent_content == reply_content:
        return False
    if intimacy <= 10:
        return False
    return True


def has_commented_moment(post, author_id: str) -> bool:
    """检查是否已评论过该朋友圈"""
    return any(
        getattr(c, "author_id", None) == author_id and getattr(c, "parent_comment_id", None) is None
        for c in (post.comments or [])
    )


def get_comment_by_id(comments: List, comment_id: str) -> Optional[Any]:
    """根据 ID 获取评论"""
    for comment in comments:
        if comment.id == comment_id:
            return comment
    return None


def has_reply_for_comment(comments: List[MomentComment], comment_id: str) -> bool:
    """检查评论是否已有回复"""
    return any(item.parent_comment_id == comment_id for item in comments)


async def run_moment_auto_interactions(limit: int = 30) -> Dict[str, int]:
    """
    自动朋友圈互动：
    - 遍历未互动的朋友圈
    - 根据亲密度决定是否点赞/评论
    - 生成 AI 评论内容
    """
    from services.memory_service import get_relationship_intimacy, can_view_moment
    from storage import get_moments, save_moments, get_characters
    from services.ai_service import generate_auto_comment_text
    
    moments = get_moments()
    characters = get_characters()
    char_map = {c.id: c for c in characters if c.is_alive}
    
    liked_count = 0
    commented_count = 0
    skipped_count = 0
    
    # 按时间排序，优先处理旧的
    moments.sort(key=lambda m: m.timestamp)
    
    for post in moments[:limit]:
        # 跳过用户自己发的
        if post.author_id == "user":
            continue
            
        # 遍历所有角色
        for char_id, character in char_map.items():
            if char_id == post.author_id:
                continue
                
            # 检查可见性
            if not can_view_moment(char_id, post):
                continue
                
            # 检查亲密度
            intimacy = get_relationship_intimacy(char_id, post.author_id)
            if intimacy < 20:
                continue
                
            # 检查是否已点赞
            if char_id not in (post.liked_by or []):
                # 根据亲密度决定点赞概率
                like_prob = min(0.6, intimacy / 100)
                if random.random() < like_prob:
                    if post.liked_by is None:
                        post.liked_by = []
                    post.liked_by.append(char_id)
                    liked_count += 1
            
            # 检查是否已评论
            if not has_commented_moment(post, char_id):
                # 根据亲密度决定评论概率
                comment_prob = min(0.3, intimacy / 200)
                if random.random() < comment_prob:
                    # 生成评论内容
                    comment_text = await generate_auto_comment_text(
                        commenter=character,
                        author=char_map.get(post.author_id, character),
                        moment_content=post.content,
                    )
                    
                    from models import MomentComment
                    comment = MomentComment(
                        moment_id=post.id,
                        author_id=char_id,
                        author_name=character.name,
                        content=comment_text,
                    )
                    
                    if post.comments is None:
                        post.comments = []
                    post.comments.append(comment)
                    commented_count += 1
    
    if liked_count > 0 or commented_count > 0:
        save_moments(moments)
    
    return {
        "liked": liked_count,
        "commented": commented_count,
        "skipped": skipped_count,
    }


async def generate_character_moment(
    character_id: str,
    request: Any
) -> Dict[str, Any]:
    """
    生成角色朋友圈（完整逻辑）：
    - 生成文字内容
    - 生成配图方案
    - 保存朋友圈
    - 记录日志
    """
    from storage import (
        get_characters, get_moments, save_moments,
        get_settings, get_api_configs
    )
    from services.ai_service import (
        generate_moment_content, generate_moment_image_plan
    )
    from services.character_service import get_moment_frequency_multiplier
    from models import MomentPost
    
    characters = get_characters()
    character = next((c for c in characters if c.id == character_id), None)
    if not character:
        raise ValueError(f"角色不存在: {character_id}")
    
    if not character.is_alive:
        raise ValueError(f"角色已死亡: {character.name}")
    
    # 生成文字内容
    content = await generate_moment_content(character, request)
    
    # 生成配图方案
    image_plan = await generate_moment_image_plan(
        character, content, getattr(request, 'mood', None)
    )
    
    now_ms = int(time.time() * 1000)
    post = MomentPost(
        author_id=character_id,
        author_name=character.name,
        content=content,
        image_prompt_file=image_plan.get("filename"),
        trigger_type=getattr(request, 'trigger_type', 'random'),
        mood=getattr(request, 'mood', None),
        timestamp=now_ms,
        visible_min_intimacy=21,
    )
    
    moments = get_moments()
    moments.append(post)
    save_moments(moments)
    
    return {"success": True, "data": post.model_dump()}
