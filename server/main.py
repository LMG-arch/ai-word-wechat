"""
AI 社交世界 - 后端服务
提供 RESTful API 接口，数据存储在本地 JSON 文件
"""

from __future__ import annotations

import sys
import io
import os

# 修复 Windows CMD 编码和颜色问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    # 禁用 uvicorn 的彩色日志
    os.environ['LOGURU_COLORIZE'] = 'False'

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import json
import hashlib
import math
import os as os_module
import random
import re
import sqlite3
import uuid
import time

app = FastAPI(title="AI 社交世界 API")

# 配置 uvicorn 日志不使用颜色
import logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 启用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 头像存储目录
AVATARS_DIR = os.path.join(os.path.dirname(__file__), "data", "avatars")
os.makedirs(AVATARS_DIR, exist_ok=True)

# 数据文件路径
CHARACTERS_FILE = os.path.join(DATA_DIR, "characters.json")
MESSAGES_FILE = os.path.join(DATA_DIR, "messages.json")
LOGS_FILE = os.path.join(DATA_DIR, "logs.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
API_CONFIGS_FILE = os.path.join(DATA_DIR, "api_configs.json")
MEMORIES_FILE = os.path.join(DATA_DIR, "memories.json")
EMMBEDDINGS_FILE = os.path.join(DATA_DIR, "embeddings.json")
CHARACTER_HISTORY_FILE = os.path.join(DATA_DIR, "character_history.json")
MEMORY_DB_FILE = os.path.join(DATA_DIR, "memory.db")
MOMENTS_FILE = os.path.join(DATA_DIR, "moments.json")
PRIVATE_GROUPS_FILE = os.path.join(DATA_DIR, "private_groups.json")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
COMPANIES_FILE = os.path.join(DATA_DIR, "companies.json")
SCHEDULES_FILE = os.path.join(DATA_DIR, "schedules.json")
ECONOMY_LOGS_FILE = os.path.join(DATA_DIR, "economy_logs.json")
LOCATION_HISTORY_FILE = os.path.join(DATA_DIR, "location_history.json")
LLM_USAGE_FILE = os.path.join(DATA_DIR, "llm_usage.json")
WORLD_MAP_FILE = os.path.join(DATA_DIR, "world_map.json")
WORLD_BIND_KEYS = ("办公室", "工作室", "学校", "医院", "书房", "餐厅", "社交场所", "城市")
WORLD_RESIDENTIAL_BIND = "住宅"
WORLD_COMPANY_BIND = "公司"

WORLD_DAYS_PER_MONTH = 30
MONTHS_PER_YEAR = 12
MILLISECONDS_PER_DAY = 24 * 60 * 60 * 1000
WORLD_MONTH_MS = WORLD_DAYS_PER_MONTH * MILLISECONDS_PER_DAY
MS_PER_HOUR = 60 * 60 * 1000
IMAGE_PROMPTS_DIR = os.path.join(DATA_DIR, "image_prompts")
os.makedirs(IMAGE_PROMPTS_DIR, exist_ok=True)

WORLD_LOCATION_SLOT_MS = 15 * 60 * 1000  # 世界时间 15 分钟一格位置微漂移

def fallback_moment_image_url(seed: str) -> str:
    """配图兜底（picsum 占位，保证朋友圈始终图文并茂）。"""
    digest = hashlib.md5(seed.encode("utf-8")).hexdigest()[:12]
    return f"https://picsum.photos/seed/{digest}/800/600"

# ==================== 调度器模块（提醒 + 主动对话） ====================
# 新增 V3.3：角色定时提醒与主动联系用户系统
try:
    from services.scheduler import (
        get_reminders, add_reminder, remove_reminder, get_character_reminders,
        check_due_reminders, can_proactively_message, record_proactive_message,
        generate_proactive_message, should_character_reach_out,
        check_special_date_greetings, run_scheduler_tick
    )
except ImportError:
    pass


# ==================== 图片提示词管理 ====================
VALID_IMAGE_SIZES = ("1920x1080", "1080x1920", "1024x1024")

def save_image_prompt_md(prompt: str, title: str = "", image_url: str = "") -> str:
    """保存绘画提示词为MD文件，返回文件名"""
    import time
    filename = f"{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}.md"
    filepath = os.path.join(IMAGE_PROMPTS_DIR, filename)
    title = title or f"图片提示词 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    md_content = f"""# {title}

## 图片信息
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **图片链接**: {image_url or '（暂无）'}

## 绘画提示词

```
{prompt}
```
"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        return filename
    except Exception:
        return ""


def get_image_prompt_md(filename: str) -> Optional[str]:
    """读取图片提示词MD文件内容"""
    if not filename:
        return None
    filepath = os.path.join(IMAGE_PROMPTS_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def get_image_prompt_url(filename: str) -> Optional[str]:
    """获取图片提示词MD文件的API URL"""
    if not filename:
        return None
    return f"/api/image-prompts/{filename}"


async def llm_choose_image_size(prompt: str, context: str = "") -> str:
    """调用LLM根据提示词内容自行选择图片大小"""
    import aiohttp
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return "1024x1024"  # 默认返回
    
    system_prompt = f"""你是一个图片生成助手，需要根据提示词选择最合适的图片尺寸。
可选尺寸只有以下三种：
- 1920x1080（横屏，适合风景、全景、宽场景）
- 1080x1920（竖屏，适合人像、自拍、竖屏内容）
- 1024x1024（正方形，适合一般内容、头像、产品展示）

请直接回复尺寸字符串（如 1024x1024），不要回复其他内容。"""
    
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"提示词：{prompt[:500]}\n\n上下文：{context[:200]}"}
            ],
            "temperature": 0.3,
            "max_tokens": 20,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "image_size_selection")
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    # 验证返回的尺寸是否有效
                    for size in VALID_IMAGE_SIZES:
                        if size in content:
                            return size
    except Exception:
        pass
    return "1024x1024"  # 失败时返回默认值


DEFAULT_WORLD_MAP_META: Dict[str, Any] = {
    "city_name": "云海城",
    "roads": [
        {"name": "中山大道", "points": [[12, 44], [92, 48]]},
        {"name": "滨江路", "points": [[48, 8], [52, 92]]},
        {"name": "学府路", "points": [[10, 30], [28, 75]]},
        {"name": "环市东路", "points": [[6, 58], [94, 62]]},
        {"name": "文化街", "points": [[30, 20], [88, 22]]},
        {"name": "青年路", "points": [[18, 12], [85, 16]]},
        {"name": "绿荫环路", "points": [[8, 78], [92, 82]]},
        {"name": "地铁一号线（地上段）", "points": [[15, 52], [88, 54]]},
        {"name": "商业街", "points": [[62, 38], [90, 72]]},
        {"name": "环湖步道", "points": [[32, 68], [68, 88], [82, 74]]},
    ],
    "landmarks": [
        {"name": "科创写字楼", "x": 72, "y": 32, "bind": "办公室", "type": "office"},
        {"name": "设计师工坊", "x": 64, "y": 24, "bind": "工作室", "type": "creative"},
        {"name": "市立医院", "x": 38, "y": 58, "bind": "医院", "type": "hospital"},
        {"name": "云海第一中学", "x": 22, "y": 26, "bind": "学校", "type": "school"},
        {"name": "滨河公园", "x": 45, "y": 72, "type": "park"},
        {"name": "滨江美食街", "x": 52, "y": 44, "bind": "餐厅", "type": "food"},
        {"name": "星光 SOHO", "x": 78, "y": 66, "bind": "社交场所", "type": "mall"},
        {"name": "云海湾公寓", "x": 50, "y": 50, "bind": "住宅", "type": "residential"},
        {"name": "作家书房阁", "x": 14, "y": 70, "bind": "书房", "type": "culture"},
        {"name": "云海站（地铁）", "x": 48, "y": 54, "type": "transit"},
        {"name": "市民广场", "x": 34, "y": 48, "type": "plaza"},
        {"name": "滨江码头", "x": 50, "y": 12, "type": "waterfront"},
        {"name": "24h 便利店", "x": 58, "y": 38, "type": "shop"},
        # 多个住宅区，让角色分散居住
        {"name": "翠湖花园", "x": 18, "y": 42, "bind": "住宅", "type": "residential"},
        {"name": "云顶山庄", "x": 82, "y": 18, "bind": "住宅", "type": "residential"},
        {"name": "学府雅苑", "x": 26, "y": 68, "bind": "住宅", "type": "residential"},
        {"name": "阳光新城", "x": 70, "y": 80, "bind": "住宅", "type": "residential"},
    ],
    "water": {"name": "滨江", "polygon": [[40, 5], [60, 5], [58, 35], [42, 35]]},
}


def get_residential_landmarks() -> List[Dict[str, Any]]:
    """获取所有住宅类地标，用于随机分配角色住处"""
    meta = get_active_world_map()
    return [lm for lm in (meta.get("landmarks") or []) if lm.get("type") == "residential"]


def assign_random_residence(character_id: str) -> str:
    """为角色随机分配一个住宅地标作为住处"""
    residential = get_residential_landmarks()
    if not residential:
        return "城市"
    lm = random.choice(residential)
    # 存储到 settings 的 character_residences 中
    settings = get_settings()
    if not hasattr(settings, 'character_residences') or not settings.character_residences:
        settings.character_residences = {}
    settings.character_residences[character_id] = lm["name"]
    save_settings(settings)
    return lm["name"]


def get_character_residence(character_id: str) -> str:
    """获取角色的住处地标名称"""
    settings = get_settings()
    residences = getattr(settings, 'character_residences', None) or settings.api_configs.get('character_residences', {})
    if character_id in residences:
        return residences[character_id]
    # 未分配则随机分配一个
    return assign_random_residence(character_id)


AVATAR_LIMIT_WINDOW_MS = 7 * MILLISECONDS_PER_DAY
AVATAR_LIMIT_MAX_CHANGES = 2
SIGNATURE_LIMIT_WINDOW_MS = 7 * MILLISECONDS_PER_DAY
SIGNATURE_LIMIT_MAX_CHANGES = 2


# ==================== 数据模型 ====================

class Character(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    age: int
    gender: str
    occupation: str
    personality: str
    money: float = 50.0
    signature: str = "暂无签名"
    avatar_url: Optional[str] = None
    current_location_id: Optional[str] = None
    company_id: Optional[str] = None
    parent_ids: List[str] = Field(default_factory=list)
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    last_avatar_change_time: int = 0
    last_signature_change_time: int = 0
    avatar_change_history: List[int] = Field(default_factory=list)
    signature_change_history: List[int] = Field(default_factory=list)
    age_months: int = 0
    growth_progress_ms: int = 0
    stage_entered_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    is_alive: bool = True
    death_time: Optional[int] = None
    death_cause: Optional[str] = None
    max_lifespan: int = 90
    debt_balance: float = 0.0
    debt_days_overdue: int = 0
    poverty_days: int = 0
    pending_intents: List[Dict[str, Any]] = Field(default_factory=list)
    experience_skills: Dict[str, Any] = Field(default_factory=dict)  # 角色经验技能库 {"task_type": {"count": 0, "lessons": [], "success_rate": 0.0, "last_used": ts}}
    llm_model_id: Optional[str] = None  # 角色单独使用的LLM模型（来自api_configs中的模型名称）
    moment_frequency: str = "normal"  # 朋友圈频率：low/normal/high

    def get_age_stage(self) -> str:
        return get_age_stage_from_age(self.age)

    def get_age_display(self) -> str:
        if self.age_months > 0:
            return f"{self.age}岁{self.age_months}个月"
        return f"{self.age}岁"

    def get_avatar_initials(self) -> str:
        return self.name[0] if self.name else "?"


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    sender_id: str
    content: str
    message_type: str = "text"  # text, image, voice
    image_url: Optional[str] = None
    voice_url: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    is_read: bool = False
    is_from_user: bool = True


class MomentComment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    moment_id: str
    author_id: str
    author_name: str
    content: str
    parent_comment_id: Optional[str] = None
    reply_to_author_id: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))


class MomentPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    author_id: str
    author_name: str
    content: str
    image_url: Optional[str] = None
    image_prompt_file: Optional[str] = None  # 关联的提示词 MD 文件路径（相对于 image_prompts/）
    trigger_type: str = "random"  # schedule|emotion|event|random
    mood: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    visible_min_intimacy: int = 21
    liked_by: List[str] = Field(default_factory=list)
    comments: List[MomentComment] = Field(default_factory=list)


class TaskType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    CODE = "code"
    RESEARCH = "research"
    DESIGN = "design"


class TaskStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskAssigneeType(str, Enum):
    PERSONAL = "personal"
    COMPANY = "company"


class ReflectionReport(BaseModel):
    task_id: str
    task_name: str
    success: bool
    what_went_well: List[str] = Field(default_factory=list)
    what_went_wrong: List[str] = Field(default_factory=list)
    root_causes: List[str] = Field(default_factory=list)
    lessons_learned: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    skill_improvements: Dict[str, int] = Field(default_factory=dict)
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))


class TaskItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    task_type: TaskType = TaskType.TEXT
    reward: float = 100.0
    creator: str = "user"
    status: TaskStatus = TaskStatus.OPEN
    assignee_type: TaskAssigneeType = TaskAssigneeType.PERSONAL
    assignee_id: Optional[str] = None
    company_id: Optional[str] = None
    submitter_id: Optional[str] = None
    execution_notes: str = ""
    deliverable_text: str = ""
    deliverable_image_url: Optional[str] = None
    deliverable_code: str = ""
    review_history: List[Dict[str, Any]] = Field(default_factory=list)
    collaborator_ids: List[str] = Field(default_factory=list)
    review_notes: str = ""
    reflection: Optional[ReflectionReport] = None
    review_round: int = 0
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    completed_at: Optional[int] = None
    image_model_id: Optional[str] = None  # 任务使用的绘画模型（来自api_configs中的模型名称）


class Company(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    legal_person_id: str
    member_ids: List[str] = Field(default_factory=list)
    funds: float = 0.0
    knowledge_base: List[Dict[str, Any]] = Field(default_factory=list)
    location_name: Optional[str] = None  # 公司在地图上的地标名称
    location_x: float = 0.0  # 公司地图 X 坐标
    location_y: float = 0.0  # 公司地图 Y 坐标
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = Field(default_factory=lambda: int(time.time() * 1000))


class EconomyLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    character_id: str
    action: str
    amount: float
    balance_after: float
    detail: str = ""
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))


class ScheduleEvent(BaseModel):
    start_time: str
    end_time: str
    location: str
    activity: str


class CharacterSchedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    character_id: str
    day_index: int
    summary: str
    events: List[ScheduleEvent] = Field(default_factory=list)
    generated_by: str = "rule_engine_v2"
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))


class LocationRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    character_id: str
    location_name: str
    x: float
    y: float
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    source: str = "schedule"


class PrivateGroupChat(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    member_ids: List[str]
    member_names: List[str]
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    is_active: bool = True
    dissolved_at: Optional[int] = None
    dissolve_reason: Optional[str] = None


class LogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str
    timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    world_timestamp_ms: int = 0
    character_name: str
    action_type: str
    description: str


class CharacterHistoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    character_id: str
    event_type: str
    description: str
    real_timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    world_timestamp_ms: int = 0
    snapshot: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryType(str, Enum):
    CONVERSATION = "conversation"  # 对话记忆
    EVENT = "event"  # 事件记忆
    TASK = "task"  # 任务记忆
    RELATIONSHIP = "relationship"  # 关系变化记忆
    REFLECTION = "reflection"  # 反思记忆


class Memory(BaseModel):
    """记忆条目 - 每个角色独立存储"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    character_id: str  # 所属角色ID
    memory_type: MemoryType  # 记忆类型
    content: str  # 记忆内容
    importance: float = 0.5  # 重要性 0-1
    emotion: Optional[str] = None  # 情感标签
    related_entities: List[str] = []  # 相关实体（其他角色、地点等）
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    valid_from: int = Field(default_factory=lambda: int(time.time() * 1000))
    valid_to: Optional[int] = None  # 记忆有效期（None表示永久）
    embedding: Optional[List[float]] = None  # 向量嵌入（用于语义检索）
    access_count: int = 0  # 访问次数
    last_accessed: Optional[int] = None  # 最后访问时间
    metadata: dict = {}  # 额外元数据


class EmbeddingCache(BaseModel):
    """向量嵌入缓存"""
    memory_id: str
    embedding: List[float]
    model: str
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))


class Settings(BaseModel):
    time_speed: int = 30
    enable_death_mechanism: bool = False
    enable_accidental_death: bool = False
    enable_auto_avatar_update: bool = True
    min_lifespan: int = 80
    max_lifespan: int = 100
    ui_language: str = "zh-CN"
    enable_auto_moment_interactions: bool = True
    auto_moment_interval_minutes: int = 5
    auto_moment_last_run_time: int = 0
    enable_heartbeat: bool = True
    heartbeat_interval_seconds: int = 60
    heartbeat_last_run_time: int = 0
    enable_task_engine: bool = True  # 是否启用任务引擎
    last_world_update_time: int = Field(default_factory=lambda: int(time.time() * 1000))
    world_elapsed_ms: int = 0
    api_configs: Dict[str, Any] = Field(default_factory=dict)
    character_residences: Dict[str, str] = Field(default_factory=dict)  # 角色住处映射
    default_image_size: str = "1024x1024"  # 默认图片大小


class CreateCharacterRequest(BaseModel):
    name: str
    age: int = 25
    gender: str = "男"
    occupation: str
    personality: str = ""
    signature: str = ""
    avatar_url: Optional[str] = None
    parent_ids: Optional[List[str]] = None
    llm_model_id: Optional[str] = None
    moment_frequency: str = "normal"


class SendMessageRequest(BaseModel):
    conversation_id: str
    content: str
    message_type: str = "text"
    image_url: Optional[str] = None
    voice_url: Optional[str] = None


class ChatResponse(BaseModel):
    content: str
    character_id: str
    timestamp: int


class LlmUsageRecord(BaseModel):
    """单次 LLM 调用的 token 使用记录"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config_id: str = ""  # API 配置 ID
    config_name: str = ""  # 配置名称
    model_name: str = ""  # 使用的模型名称
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    endpoint: str = ""  # 调用场景（如 generate_ai_reply, suggest_occupation 等）
    character_id: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))


class LlmUsageStats(BaseModel):
    """LLM 使用统计汇总（含图像API）"""
    total_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    # 图像统计
    image_total_calls: int = 0
    image_success_calls: int = 0
    image_failed_calls: int = 0
    by_model: Dict[str, Dict[str, int]] = Field(default_factory=dict)  # {model: {calls, tokens}}
    by_endpoint: Dict[str, Dict[str, int]] = Field(default_factory=dict)  # {endpoint: {calls, tokens}}
    by_config: Dict[str, Dict[str, int]] = Field(default_factory=dict)  # {config_name: {calls, tokens}}
    # 图像按配置聚合
    image_by_config: Dict[str, Dict[str, int]] = Field(default_factory=dict)  # {config_name: {calls, success, failed}}


def get_llm_usage_records(limit: int = 200) -> List[LlmUsageRecord]:
    data = load_json(LLM_USAGE_FILE, [])
    records = [LlmUsageRecord(**item) for item in data]
    records.sort(key=lambda x: x.timestamp, reverse=True)
    return records[:limit]


def save_llm_usage_record(record: LlmUsageRecord):
    data = load_json(LLM_USAGE_FILE, [])
    data.append(record.model_dump())
    # 保留最近 2000 条
    if len(data) > 2000:
        data = data[-2000:]
    save_json(LLM_USAGE_FILE, data)


def compute_llm_usage_stats() -> LlmUsageStats:
    records = get_llm_usage_records(limit=2000)
    stats = LlmUsageStats()
    for r in records:
        # 区分LLM记录和图像记录
        if r.endpoint in ('avatar_generation', 'avatar_refresh', 'task_image', 'moment_image', 'task_image_generation'):
            # 图像类记录 - 使用 success 字段判断
            stats.image_total_calls += 1
            is_success = getattr(r, 'success', False)
            if is_success:
                stats.image_success_calls += 1
            else:
                stats.image_failed_calls += 1
            if r.config_name not in stats.image_by_config:
                stats.image_by_config[r.config_name] = {"calls": 0, "success": 0, "failed": 0}
            stats.image_by_config[r.config_name]["calls"] += 1
            if is_success:
                stats.image_by_config[r.config_name]["success"] += 1
            else:
                stats.image_by_config[r.config_name]["failed"] += 1
        else:
            # LLM记录
            stats.total_calls += 1
            stats.total_prompt_tokens += r.prompt_tokens
            stats.total_completion_tokens += r.completion_tokens
            stats.total_tokens += r.total_tokens
            # 按模型聚合
            if r.model_name not in stats.by_model:
                stats.by_model[r.model_name] = {"calls": 0, "total_tokens": 0}
            stats.by_model[r.model_name]["calls"] += 1
            stats.by_model[r.model_name]["total_tokens"] += r.total_tokens
            # 按端点聚合
            if r.endpoint not in stats.by_endpoint:
                stats.by_endpoint[r.endpoint] = {"calls": 0, "total_tokens": 0}
            stats.by_endpoint[r.endpoint]["calls"] += 1
            stats.by_endpoint[r.endpoint]["total_tokens"] += r.total_tokens
            # 按配置聚合
            if r.config_name not in stats.by_config:
                stats.by_config[r.config_name] = {"calls": 0, "total_tokens": 0}
            stats.by_config[r.config_name]["calls"] += 1
            stats.by_config[r.config_name]["total_tokens"] += r.total_tokens
    return stats


def record_llm_usage(
    response_json: dict,
    config,
    endpoint: str = "",
    character_id: Optional[str] = None
):
    """从 LLM API 响应中提取 token 用量并保存"""
    try:
        usage = response_json.get("usage", {})
        if not usage:
            return
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
        record = LlmUsageRecord(
            config_id=config.id,
            config_name=config.name,
            model_name=config.selected_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            endpoint=endpoint,
            character_id=character_id,
        )
        save_llm_usage_record(record)
    except Exception:
        pass  # 静默失败，不影响主流程


class ImageUsageRecord(BaseModel):
    """单次图像API调用的使用记录"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config_id: str = ""
    config_name: str = ""
    model_name: str = ""
    images_generated: int = 1
    endpoint: str = ""  # 调用场景
    character_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))


def record_image_usage(config, endpoint: str = "", character_id: Optional[str] = None, success: bool = True, error_message: Optional[str] = None):
    """记录图像API调用"""
    try:
        record = ImageUsageRecord(
            config_id=config.id,
            config_name=config.name,
            model_name=config.selected_model,
            endpoint=endpoint,
            character_id=character_id,
            success=success,
            error_message=error_message,
        )
        data = load_json(LLM_USAGE_FILE, [])  # 复用同一文件，按endpoint区分
        data.append(record.model_dump())
        # 只保留最近2000条
        if len(data) > 2000:
            data = data[-2000:]
        save_json(LLM_USAGE_FILE, data)
    except Exception:
        pass


class ImageUsageStats(BaseModel):
    """图像API使用统计汇总"""
    total_calls: int = 0
    total_images: int = 0
    success_calls: int = 0
    failed_calls: int = 0


class ApiConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    api_type: str  # llm, image, vector, rerank
    provider: str  # openai, azure, baidu, etc.
    api_url: str
    api_key: str
    models: List[str] = []  # 支持多个模型
    selected_model: str = ""  # 当前选择的模型
    is_enabled: bool = True
    priority: int = 0
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = Field(default_factory=lambda: int(time.time() * 1000))


class CreateApiConfigRequest(BaseModel):
    name: str
    api_type: str
    provider: str
    api_url: str
    api_key: str
    models: List[str] = []  # 支持多个模型
    selected_model: str = ""  # 当前选择的模型
    is_enabled: bool = True
    priority: int = 0


class MaybeRefreshAvatarRequest(BaseModel):
    reason: Optional[str] = None
    forced: bool = False


class MaybeUpdateSignatureRequest(BaseModel):
    reason: Optional[str] = None


class GenerateMomentRequest(BaseModel):
    trigger_type: str = "random"  # schedule|emotion|event|random
    mood: Optional[str] = None
    event_text: Optional[str] = None
    with_image: bool = True  # 朋友圈默认图文并茂；失败时用占位图


class MomentCommentRequest(BaseModel):
    author_id: str
    content: Optional[str] = None
    auto_generate: bool = False
    reply_to_comment_id: Optional[str] = None


class UserCreateMomentRequest(BaseModel):
    content: str
    image_url: Optional[str] = None  # 可不传；可与 generate_image 二选一或并存（优先生图）
    generate_image: bool = False  # True 时用图像模型根据 image_prompt/正文生成配图
    image_prompt: Optional[str] = None  # 传给文生图的视觉描述（可选，默认用正文摘要）


class CreateTaskRequest(BaseModel):
    title: str
    description: str = ""
    task_type: TaskType = TaskType.TEXT
    reward: float = 100.0
    assignee_type: TaskAssigneeType = TaskAssigneeType.PERSONAL
    assignee_id: Optional[str] = None
    company_id: Optional[str] = None


class AssignTaskRequest(BaseModel):
    assignee_type: TaskAssigneeType = TaskAssigneeType.PERSONAL
    assignee_id: str
    company_id: Optional[str] = None


class SubmitTaskRequest(BaseModel):
    submitter_id: str
    execution_notes: str = ""
    deliverable_text: str = ""
    deliverable_image_url: Optional[str] = None
    deliverable_code: str = ""


class ReviewTaskRequest(BaseModel):
    approved: bool = True
    review_notes: str = ""
    score: int = 80
    checklist: Dict[str, bool] = Field(default_factory=dict)


class CreateCompanyRequest(BaseModel):
    name: str
    legal_person_id: str
    member_ids: List[str] = Field(default_factory=list)


class AddCompanyMemberRequest(BaseModel):
    character_id: str


class DistributeBonusRequest(BaseModel):
    company_id: str
    bonuses: Dict[str, float] = Field(default_factory=dict)
    reason: str = "任务奖金分配"


class AutoTakeTaskRequest(BaseModel):
    preferred_character_id: Optional[str] = None


class SimulatePrivateGroupChatRequest(BaseModel):
    topic: str = "最近怎么样？"


class RelationshipInteractRequest(BaseModel):
    from_id: str
    to_id: str
    action: str  # chat|like|comment|meet|collaborate|conflict
class RecallMemoriesRequest(BaseModel):
    character_id: str
    query: str
    top_k: Optional[int] = 5


class CreateMemoryRequest(BaseModel):
    character_id: str
    content: str
    memory_type: str = "event"
    importance: float = 0.5
    related_entities: Optional[List[str]] = None




class TestApiConfigRequest(BaseModel):
    api_url: str
    api_key: str
    api_type: str
    selected_model: str = ""  # 使用选择的模型


class GenerateCharacterRequest(BaseModel):
    prompt: str  # 用户提示词
    age_range: str = "adult"  # 年龄段：child, teen, adult, elder


class SessionManager:
    """
    管理对话 Session，负责短期上下文维护与长文本压缩
    """
    def __init__(self, max_context_len: int = 10):
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.max_context_len = max_context_len

    def get_context(self, conversation_id: str) -> List[Dict[str, str]]:
        return self.sessions.get(conversation_id, [])

    def add_message(self, conversation_id: str, role: str, content: str):
        if conversation_id not in self.sessions:
            self.sessions[conversation_id] = []
        self.sessions[conversation_id].append({"role": role, "content": content})
        
        # 保持内存中的上下文不超标
        if len(self.sessions[conversation_id]) > self.max_context_len * 3:
            # 仅保留最近的几轮，其余部分依赖长期记忆召回
            self.sessions[conversation_id] = self.sessions[conversation_id][-(self.max_context_len * 2):]

    def clear_session(self, conversation_id: str):
        if conversation_id in self.sessions:
            del self.sessions[conversation_id]

class ExecProtocol:
    """
    定义 AI 执行协议，允许 AI 在输出中包含特定指令
    格式：[EXEC:ActionName(args)]
    """
    @staticmethod
    def parse_instructions(content: str) -> List[Dict[str, Any]]:
        instructions = []
        # 匹配 [EXEC:Action(params)] 格式
        pattern = r"\[EXEC:(\w+)\((.*?)\)\]"
        matches = re.finditer(pattern, content)
        for match in matches:
            action = match.group(1)
            params_raw = match.group(2)
            instructions.append({"action": action, "params": params_raw})
        return instructions

# 初始化全局管理器
session_manager = SessionManager()

# ==================== 数据存储函数 ====================

def load_json(filename: str, default=None):
    if default is None:
        default = []
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
    return default


def save_json(filename: str, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving {filename}: {e}")


def _deep_copy_world_template() -> Dict[str, Any]:
    return json.loads(json.dumps(DEFAULT_WORLD_MAP_META))


def load_persisted_world_map() -> Optional[Dict[str, Any]]:
    data = load_json(WORLD_MAP_FILE, None)
    if isinstance(data, dict) and data.get("city_name"):
        return data
    return None


def save_persisted_world_map(meta: Dict[str, Any]):
    save_json(WORLD_MAP_FILE, meta)


def get_active_world_map() -> Dict[str, Any]:
    p = load_persisted_world_map()
    if p:
        return p
    return _deep_copy_world_template()


def randomized_default_world_map() -> Dict[str, Any]:
    m = _deep_copy_world_template()
    for lm in m.get("landmarks") or []:
        lm["x"] = round(max(10, min(90, float(lm["x"]) + random.uniform(-7, 7))), 2)
        lm["y"] = round(max(10, min(90, float(lm["y"]) + random.uniform(-7, 7))), 2)
    for r in m.get("roads") or []:
        for pt in r.get("points") or []:
            pt[0] = round(max(5, min(95, float(pt[0]) + random.uniform(-5, 5))), 2)
            pt[1] = round(max(5, min(95, float(pt[1]) + random.uniform(-5, 5))), 2)
    return m


def _clamp_map_xy(x: Any, y: Any, lo: float = 8.0, hi: float = 92.0) -> tuple[float, float]:
    try:
        xf = float(x)
        yf = float(y)
    except (TypeError, ValueError):
        xf, yf = 50.0, 50.0
    return max(lo, min(hi, xf)), max(lo, min(hi, yf))


def normalize_world_map_payload(obj: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(obj, dict):
        return None
    city = str(obj.get("city_name") or "云海城").strip()[:40]
    lore = str(obj.get("lore") or "").strip()[:500]
    roads_out: List[Dict[str, Any]] = []
    for r in obj.get("roads") or []:
        if not isinstance(r, dict):
            continue
        name = str(r.get("name") or "道路")[:28]
        pts: List[List[float]] = []
        for p in r.get("points") or []:
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                cx, cy = _clamp_map_xy(p[0], p[1])
                pts.append([round(cx, 2), round(cy, 2)])
        if len(pts) >= 2:
            roads_out.append({"name": name, "points": pts})
    if len(roads_out) < 3:
        roads_out = json.loads(json.dumps(DEFAULT_WORLD_MAP_META.get("roads") or []))

    landmarks_out: List[Dict[str, Any]] = []
    seen_bind: set[str] = set()
    for lm in obj.get("landmarks") or []:
        if not isinstance(lm, dict):
            continue
        bind_raw = lm.get("bind")
        bind = str(bind_raw).strip() if bind_raw else ""
        name = str(lm.get("name") or bind or "地标")[:36]
        x, y = _clamp_map_xy(lm.get("x", 50), lm.get("y", 50))
        typ = str(lm.get("type") or "mixed")[:24]
        item: Dict[str, Any] = {"name": name, "x": round(x, 2), "y": round(y, 2), "type": typ}
        if bind:
            item["bind"] = bind
            seen_bind.add(bind)
        landmarks_out.append(item)

    bind_tpl = {x.get("bind"): x for x in DEFAULT_WORLD_MAP_META.get("landmarks") or [] if x.get("bind")}
    for key in WORLD_BIND_KEYS:
        if key in seen_bind:
            continue
        tpl = bind_tpl.get(key) or {"name": key, "type": "mixed", "x": 50.0, "y": 50.0}
        x, y = _clamp_map_xy(
            float(tpl.get("x", 50)) + random.uniform(-6, 6),
            float(tpl.get("y", 50)) + random.uniform(-6, 6),
        )
        landmarks_out.append({
            "name": str(tpl.get("name", key))[:36],
            "x": round(x, 2),
            "y": round(y, 2),
            "bind": key,
            "type": str(tpl.get("type", "mixed"))[:24],
        })
        seen_bind.add(key)

    water_out: Optional[Dict[str, Any]] = None
    water = obj.get("water")
    if isinstance(water, dict) and water.get("polygon"):
        poly: List[List[float]] = []
        for p in water["polygon"]:
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                cx, cy = _clamp_map_xy(p[0], p[1], 5.0, 95.0)
                poly.append([round(cx, 2), round(cy, 2)])
        if len(poly) >= 3:
            water_out = {"name": str(water.get("name") or "水域")[:20], "polygon": poly}
    if not water_out:
        w0 = DEFAULT_WORLD_MAP_META.get("water")
        if isinstance(w0, dict):
            water_out = json.loads(json.dumps(w0))

    return {
        "city_name": city,
        "lore": lore,
        "roads": roads_out[:18],
        "landmarks": landmarks_out[:28],
        "water": water_out,
    }


def get_characters() -> List[Character]:
    data = load_json(CHARACTERS_FILE, [])
    return [Character(**char) for char in data]


def save_characters(characters: List[Character]):
    save_json(CHARACTERS_FILE, [char.model_dump() for char in characters])


def get_messages() -> List[ChatMessage]:
    data = load_json(MESSAGES_FILE, [])
    return [ChatMessage(**msg) for msg in data]


def save_messages(messages: List[ChatMessage]):
    save_json(MESSAGES_FILE, [msg.model_dump() for msg in messages])


def get_private_groups() -> List[PrivateGroupChat]:
    data = load_json(PRIVATE_GROUPS_FILE, [])
    return [PrivateGroupChat(**item) for item in data]


def save_private_groups(groups: List[PrivateGroupChat]):
    save_json(PRIVATE_GROUPS_FILE, [item.model_dump() for item in groups])


def get_moments() -> List[MomentPost]:
    data = load_json(MOMENTS_FILE, [])
    return [MomentPost(**item) for item in data]


def save_moments(moments: List[MomentPost]):
    save_json(MOMENTS_FILE, [item.model_dump() for item in moments])


def get_tasks() -> List[TaskItem]:
    data = load_json(TASKS_FILE, [])
    return [TaskItem(**item) for item in data]


def save_tasks(tasks: List[TaskItem]):
    save_json(TASKS_FILE, [item.model_dump() for item in tasks])


def get_companies() -> List[Company]:
    data = load_json(COMPANIES_FILE, [])
    return [Company(**item) for item in data]


def save_companies(companies: List[Company]):
    save_json(COMPANIES_FILE, [item.model_dump() for item in companies])


def get_schedules() -> List[CharacterSchedule]:
    data = load_json(SCHEDULES_FILE, [])
    return [CharacterSchedule(**item) for item in data]


def save_schedules(schedules: List[CharacterSchedule]):
    save_json(SCHEDULES_FILE, [item.model_dump() for item in schedules])


def get_economy_logs() -> List[EconomyLog]:
    data = load_json(ECONOMY_LOGS_FILE, [])
    return [EconomyLog(**item) for item in data]


def save_economy_logs(logs: List[EconomyLog]):
    save_json(ECONOMY_LOGS_FILE, [item.model_dump() for item in logs])


def get_location_history(character_id: Optional[str] = None, limit: int = 500) -> List[LocationRecord]:
    data = load_json(LOCATION_HISTORY_FILE, [])
    items = [LocationRecord(**item) for item in data]
    if character_id:
        items = [item for item in items if item.character_id == character_id]
    items.sort(key=lambda x: x.timestamp, reverse=True)
    return items[:max(1, min(limit, 5000))]


def save_location_history(records: List[LocationRecord]):
    save_json(LOCATION_HISTORY_FILE, [item.model_dump() for item in records])


def get_logs() -> List[LogEntry]:
    data = load_json(LOGS_FILE, [])
    return [LogEntry(**log) for log in data]


def save_logs(logs: List[LogEntry]):
    save_json(LOGS_FILE, [log.model_dump() for log in logs])


def get_settings() -> Settings:
    data = load_json(
        SETTINGS_FILE,
        {
            "time_speed": 30,
            "enable_death_mechanism": False,
            "enable_accidental_death": False,
            "enable_auto_avatar_update": True,
            "min_lifespan": 80,
            "max_lifespan": 100,
            "ui_language": "zh-CN",
            "enable_auto_moment_interactions": True,
            "auto_moment_interval_minutes": 5,
            "auto_moment_last_run_time": 0,
            "enable_heartbeat": True,
            "heartbeat_interval_seconds": 60,
            "heartbeat_last_run_time": 0,
            "world_elapsed_ms": 0,
        }
    )
    settings = Settings(**data) if isinstance(data, dict) else Settings()
    settings.time_speed = max(1, min(30, int(settings.time_speed)))
    settings.auto_moment_interval_minutes = max(1, min(120, int(settings.auto_moment_interval_minutes)))
    settings.heartbeat_interval_seconds = max(10, min(600, int(getattr(settings, "heartbeat_interval_seconds", 60) or 60)))
    if settings.min_lifespan > settings.max_lifespan:
        settings.min_lifespan, settings.max_lifespan = settings.max_lifespan, settings.min_lifespan
    return settings


def save_settings(settings: Settings):
    save_json(SETTINGS_FILE, settings.model_dump())


def get_api_configs() -> List[ApiConfig]:
    data = load_json(API_CONFIGS_FILE, [])
    return [ApiConfig(**config) for config in data]


def save_api_configs(configs: List[ApiConfig]):
    save_json(API_CONFIGS_FILE, [config.model_dump() for config in configs])


def get_api_config_by_id(config_id: str) -> Optional[ApiConfig]:
    configs = get_api_configs()
    for config in configs:
        if config.id == config_id:
            return config
    return None


def get_age_stage_from_age(age: int) -> str:
    if age <= 12:
        return "儿童"
    if age <= 17:
        return "青少年"
    if age <= 40:
        return "青年"
    if age <= 60:
        return "中年"
    return "老年"


def get_age_personality_modifier(age: int, base_personality: str) -> str:
    """根据年龄段生成性格修饰词，使角色表现符合年龄特征"""
    stage = get_age_stage_from_age(age)
    modifiers = {
        "儿童": "天真烂漫、好奇活泼、说话简单直接、充满想象力",
        "青少年": "朝气蓬勃、叛逆独立、追求自我、对新事物充满热情、偶尔冲动",
        "青年": "积极进取、务实理性、有一定社会经验、追求事业与情感的平衡",
        "中年": "沉稳内敛、经验丰富、看问题更全面、注重家庭与责任、偶尔感慨时光流逝",
        "老年": "豁达通透、慈祥和蔼、人生阅历丰富、喜欢回忆往事、说话语速较慢、看淡名利"
    }
    modifier = modifiers.get(stage, "")
    if modifier:
        return f"{base_personality}\n\n【年龄特征({stage}·{age}岁)】：{modifier}请在言行中体现出{stage}人的气质和心态。"
    return base_personality


def get_moment_frequency_multiplier(character: Character) -> float:
    """根据角色设置和年龄获取发朋友圈频率倍率"""
    freq_map = {"low": 0.4, "normal": 1.0, "high": 2.0}
    base = freq_map.get(character.moment_frequency, 1.0)
    # 年龄影响：青少年和青年更爱发朋友圈，中年减少，老年偶尔
    age = character.age
    if age <= 12:
        age_factor = 0.3  # 儿童很少发
    elif age <= 17:
        age_factor = 1.5  # 青少年爱分享
    elif age <= 30:
        age_factor = 1.3  # 青年活跃
    elif age <= 40:
        age_factor = 1.0  # 青年后期正常
    elif age <= 60:
        age_factor = 0.6  # 中年减少
    else:
        age_factor = 0.3  # 老年偶尔
    return base * age_factor


def normalize_parent_ids(character: Character, all_character_ids: Optional[set[str]] = None) -> List[str]:
    cleaned = []
    seen = set()
    for parent_id in character.parent_ids or []:
        if not parent_id or parent_id == character.id or parent_id in seen:
            continue
        if all_character_ids is not None and parent_id not in all_character_ids:
            continue
        cleaned.append(parent_id)
        seen.add(parent_id)
    character.parent_ids = cleaned
    return cleaned


def get_dialogue_style_hint(character: Character) -> str:
    stage = character.get_age_stage()
    hints = {
        "儿童": "语气天真直接，关注学校、家庭、兴趣和身边的小事。",
        "青少年": "语气带一点冲劲和敏感，关注学业、朋友、自我认同和未来。",
        "青年": "语气自然成熟，更多表达工作、理想、情感和现实压力。",
        "中年": "语气稳重务实，关注责任、家庭、事业和长期规划。",
        "老年": "语气平和从容，带有人生经验，关注健康、回忆和晚年生活。",
    }
    return hints.get(stage, "语气自然，符合当前年龄阶段和人生经历。")


def get_occupation_hint(character: Character) -> str:
    stage = character.get_age_stage()
    hints = {
        "儿童": "职业应以学生或儿童身份为主，不应出现正式工作。",
        "青少年": "职业应以学生、实习生、兼职等阶段性身份为主。",
        "青年": "职业应体现职业起步或发展阶段，符合技能和背景。",
        "中年": "职业应体现成熟稳定，和家庭与事业阶段相匹配。",
        "老年": "职业可为退休、顾问、店主等更符合晚年状态的身份。",
    }
    return hints.get(stage, "职业设定应与年龄和经历一致。")


def format_world_elapsed(world_elapsed_ms: int) -> str:
    total_days = world_elapsed_ms // MILLISECONDS_PER_DAY
    years = total_days // (WORLD_DAYS_PER_MONTH * MONTHS_PER_YEAR)
    remain_days = total_days % (WORLD_DAYS_PER_MONTH * MONTHS_PER_YEAR)
    months = remain_days // WORLD_DAYS_PER_MONTH
    days = remain_days % WORLD_DAYS_PER_MONTH
    parts = []
    if years:
        parts.append(f"{years}年")
    if months:
        parts.append(f"{months}个月")
    if days or not parts:
        parts.append(f"{days}天")
    return "".join(parts)


def trim_avatar_change_history(character: Character, now_ms: Optional[int] = None) -> List[int]:
    if now_ms is None:
        now_ms = int(time.time() * 1000)
    character.avatar_change_history = [
        ts for ts in (character.avatar_change_history or [])
        if now_ms - ts <= AVATAR_LIMIT_WINDOW_MS
    ]
    return character.avatar_change_history


def trim_signature_change_history(character: Character, now_ms: Optional[int] = None) -> List[int]:
    if now_ms is None:
        now_ms = int(time.time() * 1000)
    character.signature_change_history = [
        ts for ts in (character.signature_change_history or [])
        if now_ms - ts <= SIGNATURE_LIMIT_WINDOW_MS
    ]
    return character.signature_change_history


def can_refresh_avatar(character: Character, now_ms: Optional[int] = None) -> bool:
    recent_changes = trim_avatar_change_history(character, now_ms)
    return len(recent_changes) < AVATAR_LIMIT_MAX_CHANGES


def can_refresh_signature(character: Character, now_ms: Optional[int] = None) -> bool:
    recent_changes = trim_signature_change_history(character, now_ms)
    return len(recent_changes) < SIGNATURE_LIMIT_MAX_CHANGES


def apply_age_stage_constraints(character: Character) -> List[str]:
    notes = []
    stage = character.get_age_stage()
    if stage == "儿童":
        if character.occupation != "学生":
            old_occupation = character.occupation or "?"
            character.occupation = "学生"
            notes.append(f"年龄阶段调整，职业已从“{old_occupation}”修正为“学生”")
    elif stage == "青少年":
        if not character.occupation:
            character.occupation = "学生"
            notes.append("青少年阶段默认职业已设置为“学生”")
    elif stage == "老年" and character.age >= 65 and character.occupation in ["", "无业", "待定"]:
        character.occupation = "退休"
        notes.append("老年阶段默认职业已设置为“退休”")
    return notes


def ensure_character_defaults(character: Character, settings: Optional[Settings] = None) -> List[str]:
    settings = settings or get_settings()
    notes = []
    if character.stage_entered_at <= 0:
        character.stage_entered_at = character.created_at or int(time.time() * 1000)
        notes.append("已补齐阶段进入时间")
    if character.max_lifespan <= 0:
        min_lifespan = min(settings.min_lifespan, settings.max_lifespan)
        max_lifespan = max(settings.min_lifespan, settings.max_lifespan)
        character.max_lifespan = random.randint(min_lifespan, max_lifespan)
        notes.append(f"已补齐最大寿命：{character.max_lifespan}岁")
    if character.avatar_url and character.last_avatar_change_time and not character.avatar_change_history:
        character.avatar_change_history = [character.last_avatar_change_time]
        notes.append("已补齐头像变更历史")
    if character.signature and character.last_signature_change_time and not character.signature_change_history:
        character.signature_change_history = [character.last_signature_change_time]
        notes.append("已补齐签名变更历史")
    if character.debt_balance < 0:
        character.debt_balance = 0
    if character.debt_days_overdue < 0:
        character.debt_days_overdue = 0
    if character.poverty_days < 0:
        character.poverty_days = 0
    normalize_parent_ids(character)
    notes.extend(apply_age_stage_constraints(character))
    return notes


def get_character_histories(character_id: Optional[str] = None) -> List[CharacterHistoryEntry]:
    data = load_json(CHARACTER_HISTORY_FILE, [])
    histories = [CharacterHistoryEntry(**item) for item in data]
    if character_id:
        histories = [item for item in histories if item.character_id == character_id]
    histories.sort(key=lambda item: item.real_timestamp_ms, reverse=True)
    return histories


def get_history_entry(character_id: str, history_id: str) -> Optional[CharacterHistoryEntry]:
    for item in get_character_histories(character_id):
        if item.id == history_id:
            return item
    return None


def save_character_histories(histories: List[CharacterHistoryEntry]):
    save_json(CHARACTER_HISTORY_FILE, [item.model_dump() for item in histories])


def get_world_time_ms(settings: Optional[Settings] = None) -> int:
    settings = settings or get_settings()
    return max(0, int(settings.world_elapsed_ms))


def get_world_time_text(settings: Optional[Settings] = None) -> str:
    settings = settings or get_settings()
    return format_world_elapsed(settings.world_elapsed_ms)


def record_character_history(character: Character, event_type: str, description: str, metadata: Optional[Dict[str, Any]] = None):
    histories = get_character_histories()
    entry = CharacterHistoryEntry(
        character_id=character.id,
        event_type=event_type,
        description=description,
        world_timestamp_ms=get_world_time_ms(),
        snapshot=character.model_dump(),
        metadata=metadata or {}
    )
    histories.insert(0, entry)
    if len(histories) > 5000:
        histories = histories[:5000]
    save_character_histories(histories)
    return entry


def build_memorial_record(character: Character) -> Dict[str, Any]:
    histories = get_character_histories(character.id)
    memories = get_character_memories(character.id, limit=5)
    parent_names = []
    if character.parent_ids:
        char_map = {item.id: item for item in get_characters()}
        parent_names = [char_map[parent_id].name for parent_id in character.parent_ids if parent_id in char_map]
    epitaph = character.signature or f"{character.name}曾在这里生活过。"
    return {
        "id": character.id,
        "name": character.name,
        "avatar_url": character.avatar_url,
        "gender": character.gender,
        "age": character.age,
        "age_display": character.get_age_display(),
        "life_stage": character.get_age_stage(),
        "occupation": character.occupation,
        "signature": character.signature,
        "epitaph": epitaph,
        "death_time": character.death_time,
        "death_cause": character.death_cause,
        "world_time_text": get_world_time_text(),
        "parent_names": parent_names,
        "history_count": len(histories),
        "recent_histories": [item.model_dump() for item in histories[:5]],
        "recent_memories": [item.model_dump() for item in memories[:5]],
    }


def store_memorial_memory(character: Character, cause: str):
    try:
        store_memory(
            character_id=character.id,
            content=f"角色 {character.name} 于 {character.age} 岁离世，原因：{cause}。",
            memory_type=MemoryType.EVENT,
            importance=1.0,
            related_entities=["死亡", "人生终点"]
        )
    except Exception:
        pass


def mark_character_deceased(character: Character, cause: str, now_ms: Optional[int] = None):
    if now_ms is None:
        now_ms = int(time.time() * 1000)
    if not character.is_alive:
        return False
    character.is_alive = False
    character.death_time = now_ms
    character.death_cause = cause
    character.updated_at = now_ms
    add_log(character.name, "死亡", cause)
    store_memorial_memory(character, cause)
    record_character_history(character, "death", cause, {"death_time": now_ms})
    return True


def apply_parental_support(character: Character, characters: List[Character], stage: str) -> float:
    if stage not in {"儿童", "青少年"}:
        return 0.0
    if not character.parent_ids:
        return 0.0

    support_total = 0.0
    per_parent_cap = 18.0 if stage == "儿童" else 10.0
    minimum_reserve = 20.0

    for parent in characters:
        if parent.id not in character.parent_ids or not parent.is_alive:
            continue
        available = max(0.0, parent.money - minimum_reserve)
        if available <= 0:
            continue
        contribution = min(per_parent_cap, available)
        if stage == "青少年" and character.money >= 10:
            contribution = min(contribution, 4.0)
        if contribution <= 0:
            continue
        parent.money -= contribution
        parent.updated_at = int(time.time() * 1000)
        support_total += contribution

    return round(support_total, 2)


def maybe_get_accidental_death_cause(character: Character) -> Optional[str]:
    chance = 0.0
    if character.money < 0:
        chance += 0.0015
    if character.age >= 70:
        chance += 0.001
    elif character.age >= 50:
        chance += 0.0004
    if character.get_age_stage() == "老年":
        chance += 0.0002
    if chance > 0 and random.random() < chance:
        causes = [
            "突发疾病离世",
            "意外事故离世",
            "长期劳累引发并发症离世",
        ]
        return random.choice(causes)
    return None


async def refresh_character_avatar_for_stage(character: Character, forced: bool = False):
    settings = get_settings()
    if not settings.enable_auto_avatar_update:
        return False, "已关闭自动头像刷新"

    now_ms = int(time.time() * 1000)
    if not forced and not can_refresh_avatar(character, now_ms):
        return False, "头像刷新频率已达上限"

    configs = get_api_configs()
    has_image_config = any(config.api_type == 'image' and config.is_enabled for config in configs)
    if not has_image_config:
        return False, "未配置可用的图像模型"

    avatar_prompt = (
        f"{character.name}，{character.gender}，{character.get_age_display()}，"
        f"{character.get_age_stage()}阶段，职业{character.occupation}，性格{character.personality}"
    )
    result = await generate_avatar(GenerateAvatarRequest(
        avatar_prompt=avatar_prompt,
        style="realistic",
        character_id=character.id,
        image_kind="portrait"
    ))
    if not result.get("success"):
        return False, result.get("error", "头像生成失败")

    avatar_url = result.get("data", {}).get("image_url")
    if not avatar_url:
        return False, "头像生成结果缺少 image_url"

    character.avatar_url = avatar_url
    character.last_avatar_change_time = now_ms
    trim_avatar_change_history(character, now_ms)
    character.avatar_change_history.append(now_ms)
    character.updated_at = now_ms
    record_character_history(character, "avatar_refresh", f"已按年龄阶段刷新头像：{character.get_age_stage()}")
    return True, "头像已刷新"


async def generate_new_signature(character: Character, memory_context: str = "") -> Optional[str]:
    """调用 LLM 为角色生成新的个性签名"""
    import aiohttp

    world_time = get_world_time_text()

    configs = get_api_configs()
    llm_config = None
    for config in configs:
        if config.api_type == 'llm' and config.is_enabled:
            llm_config = config
            break

    if not llm_config:
        return None

    # 使用年龄性格修饰
    personality_with_age = get_age_personality_modifier(character.age, character.personality)
    # 优先使用角色指定的LLM模型
    model_name = character.llm_model_id if character.llm_model_id else (llm_config.selected_model or "gpt-3.5-turbo")

    system_prompt = f"""你是一个擅长写文案的助手，需要为一个虚拟角色生成一句【个性签名】。

当前世界时间：{world_time}

角色信息：
- 昵称：{character.name}
- 性别：{character.gender}
- 年龄：{character.get_age_display()}
- 职业：{character.occupation}
- 性格：{personality_with_age}
- 当前签名：{character.signature}

近期记忆摘要（可选）：
{memory_context or "（暂无特别事件）"}

要求：
1. 用中文输出一条新的签名，长度不超过20个字
2. 必须符合该角色的人设、年龄段特征和近期状态
3. 考虑当前世界时间（如早晨/下午/夜晚等）
4. 不要说明你是AI，也不要加引号、表情或多句，只返回签名内容本身"""

    try:
        headers = {
            "Authorization": f"Bearer {llm_config.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
            ],
            "temperature": 0.8,
            "max_tokens": 60,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status != 200:
                    return None
                result = await response.json()
                record_llm_usage(result, llm_config, "generate_signature", character.id if character else None)
                content = (
                    result.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                return content or None
    except Exception:
        return None


# ==================== 记忆系统函数 ====================

def get_memory_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(MEMORY_DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_memory_db():
    with get_memory_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                character_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                importance REAL NOT NULL DEFAULT 0.5,
                emotion TEXT,
                related_entities_json TEXT NOT NULL DEFAULT '[]',
                timestamp INTEGER NOT NULL,
                valid_from INTEGER NOT NULL,
                valid_to INTEGER,
                embedding_json TEXT,
                access_count INTEGER NOT NULL DEFAULT 0,
                last_accessed INTEGER,
                metadata_json TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                intimacy REAL NOT NULL DEFAULT 0,
                valid_from INTEGER NOT NULL,
                valid_to INTEGER,
                properties_json TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_character_time ON memories(character_id, timestamp DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_validity ON memories(valid_from, valid_to)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_lookup ON relationships(from_id, to_id, relation_type)")
        conn.commit()


def migrate_legacy_memories_if_needed():
    if not os.path.exists(MEMORIES_FILE):
        return
    try:
        with get_memory_conn() as conn:
            count_row = conn.execute("SELECT COUNT(1) AS c FROM memories").fetchone()
            if count_row and int(count_row["c"]) > 0:
                return
        legacy_data = load_json(MEMORIES_FILE, [])
        if not isinstance(legacy_data, list) or not legacy_data:
            return
        parsed = [Memory(**item) for item in legacy_data]
        save_memories(parsed)
    except Exception as e:
        print(f"Legacy memory migration skipped: {e}")


def memory_to_row(memory: Memory) -> tuple:
    return (
        memory.id,
        memory.character_id,
        memory.memory_type.value if isinstance(memory.memory_type, MemoryType) else str(memory.memory_type),
        memory.content,
        float(memory.importance),
        memory.emotion,
        json.dumps(memory.related_entities or [], ensure_ascii=False),
        int(memory.timestamp),
        int(memory.valid_from),
        memory.valid_to,
        json.dumps(memory.embedding, ensure_ascii=False) if memory.embedding is not None else None,
        int(memory.access_count),
        memory.last_accessed,
        json.dumps(memory.metadata or {}, ensure_ascii=False),
    )


def row_to_memory(row: sqlite3.Row) -> Memory:
    return Memory(
        id=row["id"],
        character_id=row["character_id"],
        memory_type=MemoryType(row["memory_type"]),
        content=row["content"],
        importance=float(row["importance"]),
        emotion=row["emotion"],
        related_entities=json.loads(row["related_entities_json"] or "[]"),
        timestamp=int(row["timestamp"]),
        valid_from=int(row["valid_from"]),
        valid_to=row["valid_to"],
        embedding=json.loads(row["embedding_json"]) if row["embedding_json"] else None,
        access_count=int(row["access_count"]),
        last_accessed=row["last_accessed"],
        metadata=json.loads(row["metadata_json"] or "{}"),
    )


def get_relationship_intimacy(viewer_id: str, author_id: str) -> float:
    if not viewer_id or not author_id or viewer_id == author_id:
        return 100.0
    with get_memory_conn() as conn:
        row = conn.execute(
            """
            SELECT intimacy FROM relationships
            WHERE (
                (from_id = ? AND to_id = ?)
                OR (from_id = ? AND to_id = ?)
            )
            AND relation_type = 'FRIEND_WITH'
            AND valid_to IS NULL
            ORDER BY valid_from DESC
            LIMIT 1
            """,
            (viewer_id, author_id, author_id, viewer_id),
        ).fetchone()
    return float(row["intimacy"]) if row else 0.0


def can_view_moment(viewer_id: Optional[str], post: MomentPost) -> bool:
    if not viewer_id:
        return True
    if viewer_id == post.author_id:
        return True
    intimacy = get_relationship_intimacy(viewer_id, post.author_id)
    return intimacy >= post.visible_min_intimacy


def _get_active_relationship_row(a: str, b: str) -> Optional[sqlite3.Row]:
    with get_memory_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM relationships
            WHERE (
                (from_id = ? AND to_id = ?)
                OR (from_id = ? AND to_id = ?)
            )
            AND relation_type = 'FRIEND_WITH'
            AND valid_to IS NULL
            ORDER BY valid_from DESC
            LIMIT 1
            """,
            (a, b, b, a),
        ).fetchone()
    return row


def _close_active_relationships(conn: sqlite3.Connection, a: str, b: str, now_ms: int):
    conn.execute(
        """
        UPDATE relationships
        SET valid_to = ?
        WHERE relation_type = 'FRIEND_WITH'
          AND valid_to IS NULL
          AND (
            (from_id = ? AND to_id = ?)
            OR (from_id = ? AND to_id = ?)
          )
        """,
        (now_ms, a, b, b, a),
    )


def set_pair_relationship(a: str, b: str, intimacy: float, metadata: Optional[Dict[str, Any]] = None):
    if not a or not b or a == b:
        return
    now_ms = int(time.time() * 1000)
    metadata = metadata or {}
    with get_memory_conn() as conn:
        _close_active_relationships(conn, a, b, now_ms)
        if intimacy >= 20:
            properties = {
                "last_interaction_at": now_ms,
                "last_decay_at": now_ms,
                **metadata,
            }
            for from_id, to_id in ((a, b), (b, a)):
                conn.execute(
                    """
                    INSERT INTO relationships (
                        id, from_id, to_id, relation_type, intimacy, valid_from, valid_to, properties_json
                    ) VALUES (?, ?, ?, 'FRIEND_WITH', ?, ?, NULL, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        from_id,
                        to_id,
                        float(max(0, min(100, intimacy))),
                        now_ms,
                        json.dumps(properties, ensure_ascii=False),
                    ),
                )
        conn.commit()


def apply_relationship_interaction(from_id: str, to_id: str, action: str) -> float:
    if not from_id or not to_id or from_id == to_id:
        return 0.0
    action = (action or "").lower()
    if action == "chat":
        delta = random.randint(1, 3)
    elif action == "like":
        delta = 1
    elif action == "comment":
        delta = 2
    elif action == "meet":
        delta = random.randint(2, 5)
    elif action == "collaborate":
        delta = random.randint(1, 10)
    elif action == "conflict":
        delta = -random.randint(5, 15)
    else:
        delta = 0

    current = get_relationship_intimacy(from_id, to_id)
    if current <= 20:
        coefficient = 1.2
    elif current >= 81:
        coefficient = 0.8
    else:
        coefficient = 1.0
    new_intimacy = max(0.0, min(100.0, current + delta * coefficient))
    set_pair_relationship(from_id, to_id, new_intimacy, {"last_action": action})
    return new_intimacy


def apply_inactivity_decay() -> int:
    now_ms = int(time.time() * 1000)
    with get_memory_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM relationships
            WHERE relation_type = 'FRIEND_WITH'
              AND valid_to IS NULL
            ORDER BY valid_from DESC
            """
        ).fetchall()
    seen = set()
    changed = 0
    for row in rows:
        a, b = row["from_id"], row["to_id"]
        key = _pair_key(a, b)
        if key in seen:
            continue
        seen.add(key)
        properties = json.loads(row["properties_json"] or "{}")
        last_interaction = int(properties.get("last_interaction_at", row["valid_from"]))
        elapsed_days = int((now_ms - last_interaction) // MILLISECONDS_PER_DAY)
        if elapsed_days <= 3:
            continue
        decay = elapsed_days - 3
        current = float(row["intimacy"])
        new_intimacy = max(0.0, current - decay)
        set_pair_relationship(a, b, new_intimacy, {"last_decay_at": now_ms, "last_action": "inactivity_decay"})
        changed += 1
    return changed


def get_comment_by_id(comments: List[MomentComment], comment_id: str) -> Optional[MomentComment]:
    for comment in comments:
        if comment.id == comment_id:
            return comment
    return None


def has_reply_for_comment(comments: List[MomentComment], comment_id: str) -> bool:
    return any(item.parent_comment_id == comment_id for item in comments)


def _pair_key(a: str, b: str) -> str:
    x, y = sorted([a, b])
    return f"{x}:{y}"


def get_active_friend_pairs(min_intimacy: float = 21.0) -> Dict[str, Dict[str, Any]]:
    with get_memory_conn() as conn:
        rows = conn.execute(
            """
            SELECT from_id, to_id, intimacy
            FROM relationships
            WHERE relation_type = 'FRIEND_WITH'
              AND valid_to IS NULL
              AND intimacy >= ?
            ORDER BY valid_from DESC
            """,
            (min_intimacy,),
        ).fetchall()
    pairs: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        key = _pair_key(row["from_id"], row["to_id"])
        if key in pairs:
            continue
        pairs[key] = {
            "member_ids": sorted([row["from_id"], row["to_id"]]),
            "intimacy": float(row["intimacy"]),
        }
    return pairs


def sync_private_groups() -> Dict[str, int]:
    groups = get_private_groups()
    chars = {c.id: c for c in get_characters()}
    active_pairs = get_active_friend_pairs(21.0)
    now_ms = int(time.time() * 1000)
    created = 0
    dissolved = 0

    existing_active: Dict[str, PrivateGroupChat] = {}
    for g in groups:
        if g.is_active and len(g.member_ids) == 2:
            existing_active[_pair_key(g.member_ids[0], g.member_ids[1])] = g

    for key, pair in active_pairs.items():
        if key in existing_active:
            continue
        member_ids = pair["member_ids"]
        member_names = [chars[mid].name for mid in member_ids if mid in chars]
        if len(member_names) != 2:
            continue
        new_group = PrivateGroupChat(
            member_ids=member_ids,
            member_names=member_names,
            created_at=now_ms,
            is_active=True,
        )
        groups.append(new_group)
        created += 1

    for g in groups:
        if not g.is_active or len(g.member_ids) != 2:
            continue
        key = _pair_key(g.member_ids[0], g.member_ids[1])
        if key in active_pairs:
            continue
        g.is_active = False
        g.dissolved_at = now_ms
        g.dissolve_reason = "关系亲密度低于21或关系失效"
        dissolved += 1

    if created or dissolved:
        save_private_groups(groups)
    return {"created": created, "dissolved": dissolved}


async def generate_moment_content(character: Character, request: GenerateMomentRequest) -> str:
    import aiohttp

    world_time = get_world_time_text()
    trigger_text = request.event_text or request.trigger_type
    # 使用年龄性格修饰
    personality_with_age = get_age_personality_modifier(character.age, character.personality)
    # 根据当前时间判断场景感
    hour_hint = ""
    if world_time:
        if "早晨" in world_time or "早上" in world_time:
            hour_hint = "（早晨场景）"
        elif "中午" in world_time or "午" in world_time:
            hour_hint = "（午休场景）"
        elif "晚上" in world_time or "傍晚" in world_time:
            hour_hint = "（傍晚/晚上场景）"
        elif "深夜" in world_time or "凌晨" in world_time:
            hour_hint = "（深夜场景，适合感慨/emo）"
    
    base_prompt = (
        f"你是{character.name}，{character.get_age_display()}，{character.gender}，{character.occupation}。\n"
        f"现在{world_time}{hour_hint}。\n"
        f"性格：{personality_with_age}\n"
        f"触发来源：{trigger_text}\n"
        f"当前情绪：{request.mood or '平静'}\n\n"
        "请生成一条朋友圈文案。要求：\n"
        "1. 用日常口语，像真人在朋友圈发的内容一样自然\n"
        "2. 可以带emoji但不要堆砌，偶尔用一个就好\n"
        "3. 可以有小情绪：吐槽、感慨、分享欲、开心、疲惫等\n"
        "4. 20-50字左右，不要太长\n"
        "5. 不要像新闻或报告一样正式\n"
        "6. 不要出现"作为一个AI""根据我的分析"等打破人设的话\n"
        "7. 考虑当前时间和场景（比如深夜感慨、早安问候、午间吐槽）\n"
        "8. 可以提到工作内容、生活琐事、人际关系等\n"
        "9. 口语化表达，可以适当省略主语或用"了""嘛""呢"等语气词\n"
        "10. 不同职业要有不同的关注点（比如学生关注考试、上班族关注工作、老板关注生意）\n"
        "直接输出文案，不要解释，不要加引号。"
    )
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == "llm" and c.is_enabled), None)
    if not llm_config:
        return f"{character.name}今天想记录一下：{trigger_text}"

    # 优先使用角色指定的LLM模型
    model_name = character.llm_model_id if character.llm_model_id else (llm_config.selected_model or "gpt-3.5-turbo")

    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": base_prompt}],
            "temperature": 0.9,
            "max_tokens": 120,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    return f"{character.name}今天想记录一下：{trigger_text}"
                data = await resp.json()
                record_llm_usage(data, llm_config, "generate_moment_content", character.id)
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                return content or f"{character.name}今天想记录一下：{trigger_text}"
    except Exception:
        return f"{character.name}今天想记录一下：{trigger_text}"


def _fallback_moment_image_plan(
    character: Character, request: GenerateMomentRequest, moment_text: str
) -> Dict[str, str]:
    """无 LLM 时：按哈希抖动在 selfie / scene / portrait 间分配，避免每条都是自拍。"""
    seed = abs(hash(f"{character.id}:{moment_text[:48]}")) % 100
    if seed < 22 or ("脸" in moment_text or "自拍" in moment_text):
        kind = "selfie"
        prompt = (
            f"Smartphone selfie of {character.name}, {character.gender}, age {character.age}, {character.occupation}. "
            f"Personality: {character.personality}. Mood: {request.mood or 'everyday'}. Post says: {moment_text[:160]}. "
            f"Front camera, natural lighting, casual background, no text."
        )
    elif seed < 78:
        kind = "scene"
        prompt = (
            f"Lifestyle photo illustrating this social post (subject may be food, desk, street, sky, objects—avoid mandatory face close-up): "
            f"{moment_text[:220]}. Character context: {character.occupation}, mood {request.mood or 'neutral'}. "
            f"No text, no watermark."
        )
    else:
        kind = "portrait"
        prompt = (
            f"Half-body or three-quarter portrait of {character.name}, {character.gender}, {character.get_age_display()}, "
            f"{character.occupation}, personality {character.personality}. Relates to: {moment_text[:120]}. "
            f"Professional casual portrait, not smartphone selfie angle, soft light."
        )
    return {"image_kind": kind, "image_prompt": prompt}


async def generate_moment_image_plan(
    character: Character, request: GenerateMomentRequest, moment_text: str
) -> Dict[str, str]:
    """
    由角色「配图想法」决定类型与英文提示：selfie（仅当合适）、scene（环境/静物/美食等）、portrait（展示型人像）。
    有 LLM 时让其根据正文与人设选择；无则走 _fallback_moment_image_plan。
    """
    import aiohttp
    import re

    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == "llm" and c.is_enabled), None)
    if not llm_config:
        return _fallback_moment_image_plan(character, request, moment_text)

    system = """你是角色的内容助理，要为一条朋友圈决定**配图类型**和**英文生图提示**。只输出一个 JSON，不要 markdown：
{"image_kind":"selfie"|"scene"|"portrait","image_prompt":"English, detailed, for text-to-image"}

类型含义：
- **selfie**：仅当正文适合「晒自己、心情、日常面貌、随手立照」时选用；强调手机自拍、前置感。
- **scene**：风景、美食、物件、工位、街景、天气等，**不必**脸部特写；与配文意境一致即可。
- **portrait**：偏正式或展示的半身/人像，**不是**手机自拍质感（如形象照、工作照感）。

重要：**不要每条动态都用 selfie**；根据正文语义、职业与性格灵活选 scene 或 portrait 常更合适。"""

    # 使用年龄性格修饰
    personality_with_age = get_age_personality_modifier(character.age, character.personality)
    user_msg = (
        f"角色：{character.name}，{character.get_age_display()}，{character.gender}，职业{character.occupation}。"
        f"\n性格特征：{personality_with_age}"
        f"\n情绪标签：{request.mood or '未写'}"
        f"\n触发：{request.trigger_type} {request.event_text or ''}"
        f"\n朋友圈中文正文：{moment_text}"
        f"\n请输出 JSON。"
    )
    try:
        # 优先使用角色指定的LLM模型
        model_name = character.llm_model_id if character.llm_model_id else (llm_config.selected_model or "gpt-3.5-turbo")
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            "temperature": 0.75,
            "max_tokens": 400,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=35)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    return _fallback_moment_image_plan(character, request, moment_text)
                data = await resp.json()
                record_llm_usage(data, llm_config, "moment_image_plan", character.id)
                raw_txt = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                m = re.search(r"\{[\s\S]*\}", raw_txt)
                if not m:
                    return _fallback_moment_image_plan(character, request, moment_text)
                raw = json.loads(m.group())
                kind = str(raw.get("image_kind") or "scene").lower().strip()
                if kind not in ("selfie", "scene", "portrait"):
                    kind = "scene"
                prompt = str(raw.get("image_prompt") or "").strip()
                if not prompt:
                    return _fallback_moment_image_plan(character, request, moment_text)
                return {"image_kind": kind, "image_prompt": prompt[:1200]}
    except Exception:
        return _fallback_moment_image_plan(character, request, moment_text)


async def generate_auto_comment_text(
    commenter: Character,
    moment_author: Character,
    moment_content: str,
    parent_comment: Optional[MomentComment] = None
) -> str:
    import aiohttp

    world_time = get_world_time_text()
    base_prompt = (
        f"你是{commenter.name}，性格{commenter.personality}。当前世界时间：{world_time}。"
        f"请对{moment_author.name}的朋友圈写一句自然中文回复（10-30字）。"
        f"朋友圈内容：{moment_content}。"
        f"注意考虑当前时间段来回复。"
    )
    if parent_comment:
        base_prompt += f"当前你要回复评论：{parent_comment.author_name}说“{parent_comment.content}”。请生成带@的单句回复。"
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == "llm" and c.is_enabled), None)
    if not llm_config:
        if parent_comment:
            return f"@{parent_comment.author_name} 说得有道理。"
        return "这条动态很有意思。"
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": base_prompt}],
            "temperature": 0.8,
            "max_tokens": 80,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    return f"@{parent_comment.author_name} 说得有道理。" if parent_comment else "这条动态很有意思。"
                data = await resp.json()
                record_llm_usage(data, llm_config, "auto_comment", commenter.id)
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                return content or (f"@{parent_comment.author_name} 说得有道理。" if parent_comment else "这条动态很有意思。")
    except Exception:
        return f"@{parent_comment.author_name} 说得有道理。" if parent_comment else "这条动态很有意思。"


def should_continue_reply(parent_content: str, reply_content: str, intimacy: float) -> bool:
    score = 0.0
    if "?" in parent_content or "？" in parent_content:
        score += 0.3
    if "@" in reply_content:
        score += 0.2
    score += min(0.4, intimacy / 250.0)
    score += random.uniform(0.0, 0.2)
    return score >= 0.55


async def run_moment_auto_interactions(limit: int = 30) -> Dict[str, int]:
    moments = get_moments()
    if not moments:
        return {"likes": 0, "comments": 0, "replies": 0, "updated_posts": 0, "relationship_updates": 0}

    characters = [c for c in get_characters() if c.is_alive]
    char_map = {c.id: c for c in characters}
    now_ms = int(time.time() * 1000)
    settings = get_settings()
    window_ms = max(1, int(settings.auto_moment_interval_minutes)) * 60 * 1000 * 3
    recent_posts = [m for m in sorted(moments, key=lambda x: x.timestamp, reverse=True) if now_ms - m.timestamp <= window_ms][:limit]

    likes = comments = replies = updated_posts = relationship_updates = 0
    changed = False
    for post in recent_posts:
        author = char_map.get(post.author_id)
        if not author:
            continue
        post_changed = False
        top_level_authors = {c.author_id for c in post.comments if c.parent_comment_id is None}

        candidates = [
            c for c in characters
            if c.id != post.author_id and can_view_moment(c.id, post)
        ]
        for candidate in candidates:
            intimacy = get_relationship_intimacy(candidate.id, post.author_id)
            like_prob = 0.25 + min(0.45, intimacy / 200.0)
            if candidate.id not in post.liked_by and random.random() < like_prob:
                post.liked_by.append(candidate.id)
                post_changed = True
                likes += 1
                apply_relationship_interaction(candidate.id, post.author_id, "like")
                relationship_updates += 1

            # 每个动态，每个角色只允许一条顶层评论
            if candidate.id in top_level_authors:
                continue
            comment_prob = 0.18 + min(0.35, intimacy / 220.0)
            if random.random() < comment_prob:
                text = await generate_auto_comment_text(candidate, author, post.content)
                comment = MomentComment(
                    moment_id=post.id,
                    author_id=candidate.id,
                    author_name=candidate.name,
                    content=text,
                )
                post.comments.append(comment)
                top_level_authors.add(candidate.id)
                post_changed = True
                comments += 1
                apply_relationship_interaction(candidate.id, post.author_id, "comment")
                relationship_updates += 1

        # 每个评论只能被回复一次；回复方根据内容判断是否继续
        for comment in list(sorted(post.comments, key=lambda x: x.timestamp)):
            if has_reply_for_comment(post.comments, comment.id):
                continue
            if comment.parent_comment_id:
                parent = get_comment_by_id(post.comments, comment.parent_comment_id)
                replier_id = parent.author_id if parent and parent.author_id != comment.author_id else None
            else:
                replier_id = post.author_id if comment.author_id != post.author_id else None
            if not replier_id:
                continue
            replier = char_map.get(replier_id)
            commenter = char_map.get(comment.author_id)
            if not replier or not commenter:
                continue
            intimacy = get_relationship_intimacy(replier.id, commenter.id)
            if not should_continue_reply(comment.content, comment.content, intimacy):
                continue
            reply_text = await generate_auto_comment_text(
                replier, author, post.content, parent_comment=comment
            )
            reply = MomentComment(
                moment_id=post.id,
                author_id=replier.id,
                author_name=replier.name,
                content=reply_text,
                parent_comment_id=comment.id,
                reply_to_author_id=comment.author_id,
            )
            post.comments.append(reply)
            post_changed = True
            replies += 1
            apply_relationship_interaction(replier.id, comment.author_id, "comment")
            relationship_updates += 1

        if post_changed:
            updated_posts += 1
            changed = True

    if changed:
        save_moments(moments)
    return {
        "likes": likes,
        "comments": comments,
        "replies": replies,
        "updated_posts": updated_posts,
        "relationship_updates": relationship_updates,
    }


def get_memories() -> List[Memory]:
    """获取所有记忆"""
    with get_memory_conn() as conn:
        rows = conn.execute("SELECT * FROM memories ORDER BY timestamp DESC").fetchall()
    return [row_to_memory(row) for row in rows]


def save_memories(memories: List[Memory]):
    """保存所有记忆（全量覆盖，用于兼容旧调用）"""
    with get_memory_conn() as conn:
        conn.execute("DELETE FROM memories")
        if memories:
            conn.executemany(
                """
                INSERT INTO memories (
                    id, character_id, memory_type, content, importance, emotion,
                    related_entities_json, timestamp, valid_from, valid_to,
                    embedding_json, access_count, last_accessed, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [memory_to_row(mem) for mem in memories],
            )
        conn.commit()


def get_character_memories(character_id: str, limit: int = 100) -> List[Memory]:
    """获取特定角色的记忆（独立隔离）"""
    with get_memory_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM memories WHERE character_id = ? ORDER BY timestamp DESC LIMIT ?",
            (character_id, limit),
        ).fetchall()
    return [row_to_memory(row) for row in rows]


def store_memory(
    character_id: str,
    content: str,
    memory_type: MemoryType,
    importance: float = 0.5,
    emotion: str = None,
    related_entities: List[str] = None,
    metadata: dict = None
) -> Memory:
    """存储新记忆"""
    memory = Memory(
        character_id=character_id,
        content=content,
        memory_type=memory_type,
        importance=importance,
        emotion=emotion,
        related_entities=related_entities or [],
        metadata=metadata or {}
    )

    with get_memory_conn() as conn:
        conn.execute(
            """
            INSERT INTO memories (
                id, character_id, memory_type, content, importance, emotion,
                related_entities_json, timestamp, valid_from, valid_to,
                embedding_json, access_count, last_accessed, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            memory_to_row(memory),
        )
        conn.commit()

    return memory


def time_decay_weight(timestamp: int, is_reflection: bool = False) -> float:
    """
    时间衰减函数
    - 普通记忆：半衰期约2.5天 (72小时)
    - 反思记忆：半衰期约7天 (168小时)
    """
    import math
    hours_since = (time.time() * 1000 - timestamp) / (1000 * 60 * 60)
    half_life = 168 if is_reflection else 72
    return math.exp(-hours_since / half_life)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算余弦相似度"""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


async def get_embedding(text: str) -> Optional[List[float]]:
    """获取文本的向量嵌入"""
    import aiohttp
    
    configs = get_api_configs()
    vector_config = None
    for config in configs:
        if config.api_type == 'vector' and config.is_enabled:
            vector_config = config
            break
    
    if not vector_config:
        return None
    
    try:
        headers = {
            "Authorization": f"Bearer {vector_config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": vector_config.selected_model or "text-embedding-ada-002",
            "input": text[:8000]  # 限制输入长度
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(vector_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    embedding = result.get('data', [{}])[0].get('embedding', [])
                    return embedding
    except Exception as e:
        print(f"Embedding error: {e}")
    
    return None


async def recall_memories(
    character_id: str,
    query: str,
    top_k: int = 10,
    time_range: tuple = None
) -> List[Memory]:
    """
    召回相关记忆
    1. 获取向量嵌入
    2. 语义相似度检索 Top 50
    3. 时间衰减加权
    4. 返回 Top K
    """
    char_memories = get_character_memories(character_id, limit=300)
    
    # 时间范围过滤
    if time_range:
        start_time, end_time = time_range
        char_memories = [
            m for m in char_memories 
            if start_time <= m.timestamp <= end_time
        ]
    
    # 获取查询向量
    query_embedding = await get_embedding(query)
    
    scored_memories = []
    for memory in char_memories:
        # 计算相似度分数
        if query_embedding and memory.embedding:
            similarity = cosine_similarity(query_embedding, memory.embedding)
        else:
            # 没有向量时使用关键词匹配
            similarity = simple_text_similarity(query, memory.content)
        
        # 时间衰减权重
        is_reflection = memory.memory_type == MemoryType.REFLECTION
        time_weight = time_decay_weight(memory.timestamp, is_reflection)
        
        # 重要性权重
        importance_weight = memory.importance
        
        # 综合分数
        final_score = similarity * time_weight * (0.5 + importance_weight * 0.5)
        
        scored_memories.append((memory, final_score))
    
    # 按分数排序，取 Top K
    scored_memories.sort(key=lambda x: x[1], reverse=True)
    result = [m for m, score in scored_memories[:top_k]]
    
    # 更新访问计数
    for memory in result:
        memory.access_count += 1
        memory.last_accessed = int(time.time() * 1000)
    
    if result:
        with get_memory_conn() as conn:
            conn.executemany(
                "UPDATE memories SET access_count = ?, last_accessed = ? WHERE id = ?",
                [(m.access_count, m.last_accessed, m.id) for m in result],
            )
            conn.commit()
    
    return result


def simple_text_similarity(query: str, content: str) -> float:
    """简单的文本相似度计算（关键词匹配）"""
    query_words = set(query.lower().split())
    content_words = set(content.lower().split())
    
    if not query_words:
        return 0.0
    
    intersection = query_words & content_words
    return len(intersection) / len(query_words)


def build_memory_context(memories: List[Memory], max_length: int = 1000) -> str:
    """构建记忆上下文"""
    if not memories:
        return ""
    
    context_parts = []
    total_length = 0
    
    for memory in memories:
        # 格式化记忆
        time_str = datetime.fromtimestamp(memory.timestamp / 1000).strftime("%Y-%m-%d %H:%M")
        memory_text = f"[{time_str}] {memory.content}"
        
        if total_length + len(memory_text) > max_length:
            break
        
        context_parts.append(memory_text)
        total_length += len(memory_text)
    
    return "\n".join(context_parts)


def add_log(character_name: str, action_type: str, description: str):
    logs = get_logs()
    now_ms = int(time.time() * 1000)
    now = datetime.now().strftime("%H:%M:%S")
    log = LogEntry(
        timestamp=now,
        timestamp_ms=now_ms,
        world_timestamp_ms=get_world_time_ms(),
        character_name=character_name,
        action_type=action_type,
        description=description
    )
    logs.insert(0, log)
    if len(logs) > 200:
        logs = logs[:200]
    save_logs(logs)
    return log


def create_reflection_from_task(task: TaskItem, approved: bool, review_notes: str) -> ReflectionReport:
    """从任务审核结果生成个性化反思报告"""
    task_type_name = {
        TaskType.TEXT: "文本创作",
        TaskType.IMAGE: "图像创作",
        TaskType.CODE: "代码开发",
        TaskType.RESEARCH: "调研分析",
        TaskType.DESIGN: "创意设计",
    }.get(task.task_type, "通用任务")
    
    if approved:
        # 成功反思：根据任务类型和审核反馈生成个性化内容
        success_items = [
            f"顺利完成{task_type_name}任务「{task.title}」",
            f"理解了客户需求并针对性完成交付物",
        ]
        if task.review_notes:
            success_items.append(f"审核评价：{task.review_notes[:50]}")
        
        lessons = [
            f"做{task_type_name}时先拆解需求再动手，效率更高",
            "提交前自检一遍交付物质量和格式",
            f"对{task.title}这类任务积累了宝贵经验",
        ]
        skills = {
            "需求理解": 2 + (3 if task.task_type == TaskType.RESEARCH else 0),
            "执行质量": 2,
            "时间管理": 1,
        }
        # 根据任务类型添加专项技能
        if task.task_type == TaskType.CODE:
            skills["代码质量"] = 3
            skills["架构设计"] = 1
            lessons.append("写代码前先设计结构，再填充实现，避免写成一团")
        elif task.task_type == TaskType.IMAGE:
            skills["视觉表达"] = 3
            lessons.append("做图前先构思整体风格和构图，再细化细节")
        elif task.task_type == TaskType.TEXT:
            skills["文案能力"] = 3
            skills["创意表达"] = 2
            lessons.append("好的文案要有吸引力和信息密度，不能只是堆砌词汇")
        elif task.task_type == TaskType.RESEARCH:
            skills["数据分析"] = 3
            skills["逻辑推理"] = 2
            lessons.append("调研要有信息来源的可靠性和分析的客观性")
        elif task.task_type == TaskType.DESIGN:
            skills["设计思维"] = 3
            skills["用户体验"] = 2
            lessons.append("设计不只是好看，更要好用和解决实际问")
        
        return ReflectionReport(
            task_id=task.id,
            task_name=task.title,
            success=True,
            what_went_well=success_items,
            what_went_wrong=[],
            root_causes=[],
            lessons_learned=lessons[:6],
            action_items=["将本次经验沉淀为个人能力", f"总结{task_type_name}的标准执行流程"],
            skill_improvements=skills,
        )
    else:
        # 失败反思：从审核反馈中提取教训
        issues = [review_notes or f"{task_type_name}审核未通过"]
        causes = ["对需求的理解可能不够深入", "交付物质量有待提升"]
        lessons = [
            f"做{task_type_name}前先和审核方对齐标准",
            "不要急于动手，先把需求和验收标准理解清楚",
            f"「{task.title}」的失败教训要记住",
        ]
        
        if "格式" in review_notes or "规范" in review_notes:
            issues.append("交付物格式不符合要求")
            causes.append("没有仔细阅读任务说明")
            lessons.append("提交前必须对照需求清单逐项检查")
        elif "内容" in review_notes or "质量" in review_notes:
            issues.append("交付物内容质量不足")
            causes.append("可能没有投入足够的精力")
            lessons.append("任务质量是底线，不能因为时间压力而降低标准")
        
        return ReflectionReport(
            task_id=task.id,
            task_name=task.title,
            success=False,
            what_went_well=[f"按时提交了{task_type_name}初稿"],
            what_went_wrong=issues[:3],
            root_causes=causes[:3],
            lessons_learned=lessons[:5],
            action_items=["仔细复盘审核反馈", "修改后重新提交", "向有经验的人请教"],
            skill_improvements={"需求理解": 4, "风险识别": 3, "质量意识": 3},
        )


def choose_task_assignee(task: TaskItem, characters: List[Character], preferred_character_id: Optional[str] = None) -> Optional[Character]:
    alive_chars = [char for char in characters if char.is_alive]
    if not alive_chars:
        return None
    if preferred_character_id:
        preferred = next((char for char in alive_chars if char.id == preferred_character_id), None)
        if preferred:
            return preferred
    type_keywords = {
        TaskType.CODE: ["程序", "开发", "工程", "前端", "后端"],
        TaskType.DESIGN: ["设计", "美术", "视觉", "品牌"],
        TaskType.RESEARCH: ["研究", "分析", "咨询", "运营"],
        TaskType.IMAGE: ["设计", "美术", "摄影", "画"],
        TaskType.TEXT: ["作家", "编辑", "文案", "老师"],
    }
    keywords = type_keywords.get(task.task_type, [])
    scored = []
    for char in alive_chars:
        occupation = (char.occupation or "").lower()
        score = 0
        for keyword in keywords:
            if keyword.lower() in occupation:
                score += 3
        score += random.randint(0, 2)
        scored.append((score, char))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored else random.choice(alive_chars)


def generate_schedule_for_character(character: Character, day_index: int) -> CharacterSchedule:
    occupation_activity = {
        "程序员": ("办公室", "编码"),
        "设计师": ("工作室", "设计稿迭代"),
        "教师": ("学校", "备课与授课"),
        "医生": ("医院", "门诊与查房"),
        "作家": ("书房", "写作"),
    }
    
    # 如果角色在公司工作，使用公司位置作为工作地点
    work_location = None
    work_activity = None
    if character.company_id:
        companies = get_companies()
        company = next((c for c in companies if c.id == character.company_id), None)
        if company:
            work_location = company.location_name or "办公室"
            work_activity = f"{company.name}工作"
    
    if not work_location:
        work_location, work_activity = occupation_activity.get(character.occupation, ("城市", "工作"))
    
    evening_activity = "社交/学习"
    if character.money <= 0:
        evening_activity = "低消费休息/兼职"
    elif "内向" in (character.personality or ""):
        evening_activity = "独处学习/阅读"
    events = [
        ScheduleEvent(start_time="09:00", end_time="12:00", location=work_location, activity=work_activity),
        ScheduleEvent(start_time="12:00", end_time="13:00", location="餐厅", activity="午餐"),
        ScheduleEvent(start_time="18:00", end_time="20:00", location="社交场所", activity=evening_activity),
    ]
    summary = "；".join([f"{item.start_time}-{item.end_time} {item.location} {item.activity}" for item in events])
    return CharacterSchedule(
        character_id=character.id,
        day_index=day_index,
        summary=summary,
        events=events,
        context={
            "occupation_weight": 0.4,
            "personality_weight": 0.3,
            "relationship_weight": 0.2,
            "economy_weight": 0.1,
            "money": character.money,
            "personality": character.personality,
        },
    )


async def llm_generate_world_map(user_prompt: str) -> Optional[Dict[str, Any]]:
    """调用 LLM 生成 / 重塑城市 JSON，失败返回 None。"""
    import aiohttp
    import re

    configs = get_api_configs()
    llm_config = None
    for config in configs:
        if config.api_type == 'llm' and config.is_enabled:
            llm_config = config
            break
    if not llm_config:
        return None

    system = """你是虚拟城市地图设计师。根据用户描述输出**仅一个** JSON 对象，不要 markdown 代码围栏，不要任何解释文字。
必须包含字段：
- city_name: string 城市名
- lore: string 一句话世界氛围（可选）
- roads: 数组，元素 {"name": string, "points": [[x,y], ...]}，至少 5 条路；x,y 为 0-100 的数字
- landmarks: 数组，元素 {"name", "x", "y", "bind", "type"}；其中 bind 必须覆盖且仅使用这些词各至少一次：办公室、工作室、学校、医院、书房、餐厅、社交场所、城市、住宅（可额外增加地标，额外项可不写 bind）
  住宅类型（type=residential）必须至少 3 个不同地标，分布在地图不同区域
  每个地标坐标在 8-92 之间
- water: {"name": string, "polygon": [[x,y], ...]} 可选
约束：路名与地名要有生活感；polygon 至少 3 个点。"""

    user = f"用户期望的世界：{user_prompt[:900]}"
    try:
        headers = {
            "Authorization": f"Bearer {llm_config.api_key}",
            "Content-Type": "application/json",
        }
        request_data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.85,
            "max_tokens": 2800,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=request_data) as response:
                if response.status != 200:
                    return None
                result = await response.json()
                record_llm_usage(result, llm_config, "generate_world_map")
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                json_match = re.search(r'\{[\s\S]*\}', content)
                if not json_match:
                    return None
                raw = json.loads(json_match.group())
                return normalize_world_map_payload(raw)
    except Exception:
        return None


async def ensure_world_map_initialized():
    """首次启动且无持久化地图时：优先 LLM 生成世界，否则使用随机化的默认模板。"""
    if load_persisted_world_map() is not None:
        return
    meta = await llm_generate_world_map(
        "一座融合了唐代政治风格（Tang-Political）与虚拟城市架构的都市，包含太子府（Taizi Palace）、政事堂等传统地标，整体宏伟且充满科技感。"
    )
    if not meta:
        # 优化：如果生成失败，尝试使用更通用的唐风描述再次生成，而不是直接 fallback
        meta = await llm_generate_world_map(
            "A grand city blending ancient Tang Dynasty architecture with futuristic cyber elements, featuring palaces and traditional government halls."
        )
    if not meta:
        meta = randomized_default_world_map()
    save_persisted_world_map(meta)
    add_log("系统", "world_init", f"世界已初始化：{meta.get('city_name', '')}")


def resolve_location_base(location_name: str) -> tuple[float, float]:
    meta = get_active_world_map()
    for lm in meta.get("landmarks") or []:
        if lm.get("bind") == location_name:
            return float(lm["x"]), float(lm["y"])
    seed = abs(hash(location_name)) % 10000
    x = 10 + (seed % 81)
    y = 10 + ((seed // 100) % 81)
    return float(x), float(y)


def resolve_location_coordinates(
    location_name: str,
    character_id: str,
    drift_bucket: int = 0,
) -> tuple[float, float]:
    """同一地点内随时间漂移，模拟真实移动（地图点会缓慢变化）。"""
    bx, by = resolve_location_base(location_name)
    h = abs(hash(f"{character_id}:{location_name}:{drift_bucket}")) % 10000
    jx = (h % 17 - 8) * 0.35
    jy = ((h // 17) % 17 - 8) * 0.35
    return bx + jx, by + jy


def world_hour_of_day(world_elapsed_ms: int) -> float:
    return (world_elapsed_ms % MILLISECONDS_PER_DAY) / MS_PER_HOUR


def pick_schedule_location_for_world_time(character: Character, world_elapsed_ms: int) -> tuple[str, str]:
    """按世界时间落在日程时段：工作/午休/午后/晚间/通勤/休息。"""
    day_index = int(world_elapsed_ms // MILLISECONDS_PER_DAY)
    schedules = get_schedules()
    schedule = next(
        (s for s in schedules if s.character_id == character.id and s.day_index == day_index),
        None,
    )
    if not schedule:
        schedule = generate_schedule_for_character(character, day_index)
    events = schedule.events
    if not events:
        return "城市", "休息"
    h = world_hour_of_day(world_elapsed_ms)
    # 夜间休息时返回角色住处
    if 23 <= h or h < 7:
        residence = get_character_residence(character.id)
        return residence, "休息/睡眠"
    if 7 <= h < 9:
        return events[0].location, "通勤/出门"
    if 9 <= h < 12:
        return events[0].location, events[0].activity
    if 12 <= h < 13:
        return events[1].location if len(events) > 1 else "餐厅", "午餐"
    if 13 <= h < 18:
        return events[0].location, "午后工作/外出"
    if 18 <= h < 20:
        return events[2].location if len(events) > 2 else events[0].location, events[2].activity if len(events) > 2 else "晚间安排"
    return "社交场所", "晚间放松"


def update_character_location(
    character: Character,
    location_name: str,
    source: str = "schedule",
    world_elapsed_ms: Optional[int] = None,
):
    settings = get_settings()
    world_ms = int(world_elapsed_ms if world_elapsed_ms is not None else settings.world_elapsed_ms)
    drift_bucket = int(world_ms // WORLD_LOCATION_SLOT_MS)
    x, y = resolve_location_coordinates(location_name, character.id, drift_bucket=drift_bucket)
    character.current_location_id = location_name
    records = get_location_history(limit=2000)
    records.insert(0, LocationRecord(
        character_id=character.id,
        location_name=location_name,
        x=x,
        y=y,
        source=source,
    ))
    if len(records) > 2000:
        records = records[:2000]
    save_location_history(records)


def detect_encounters(window_minutes: int = 5) -> Dict[str, Any]:
    characters = [item for item in get_characters() if item.is_alive]
    now_ms = int(time.time() * 1000)
    threshold_ms = max(1, window_minutes) * 60 * 1000
    latest_by_character: Dict[str, LocationRecord] = {}
    for record in get_location_history(limit=2000):
        if now_ms - record.timestamp > threshold_ms:
            continue
        if record.character_id not in latest_by_character:
            latest_by_character[record.character_id] = record
    encounters = []
    for i in range(len(characters)):
        for j in range(i + 1, len(characters)):
            a = characters[i]
            b = characters[j]
            ra = latest_by_character.get(a.id)
            rb = latest_by_character.get(b.id)
            if not ra or not rb:
                continue
            distance = math.sqrt((ra.x - rb.x) ** 2 + (ra.y - rb.y) ** 2)
            if distance <= 6:
                intimacy = apply_relationship_interaction(a.id, b.id, "meet")
                encounters.append({
                    "a_id": a.id,
                    "a_name": a.name,
                    "b_id": b.id,
                    "b_name": b.name,
                    "location": ra.location_name,
                    "distance": round(distance, 2),
                    "intimacy": intimacy,
                })
    if encounters:
        sync_private_groups()
    return {"count": len(encounters), "items": encounters}


def economic_stress_multiplier(character: Character) -> float:
    """资金压力越大返回值越高：用于降低社交、提高接任务意愿。"""
    if character.money <= 0:
        return 1.85
    if character.poverty_days >= 3:
        return 1.55
    if character.poverty_days >= 1:
        return 1.25
    if character.money < 25:
        return 1.12
    if character.debt_balance > 50:
        return 1.15
    return 1.0


async def append_private_group_exchange(group: PrivateGroupChat, topic: str):
    """在私人群里追加一轮双人对话（与 simulate 接口共用）。"""
    characters = get_characters()
    char_map = {c.id: c for c in characters}
    if len(group.member_ids) != 2 or any(mid not in char_map for mid in group.member_ids):
        return
    speaker_a = char_map[group.member_ids[0]]
    speaker_b = char_map[group.member_ids[1]]
    conv_id = f"group:{group.id}"
    messages = get_messages()
    prompt_a = f"在你和{speaker_b.name}的私人群聊里，话题：{topic}"
    reply_a = await generate_ai_reply(speaker_a, prompt_a, peer=speaker_b, chat_with_character=True)
    msg_a = ChatMessage(
        conversation_id=conv_id,
        sender_id=speaker_a.id,
        content=reply_a,
        is_from_user=False,
    )
    messages.append(msg_a)
    prompt_b = f"{speaker_a.name}刚说：{reply_a}\n请在私人群聊中自然回复。"
    reply_b = await generate_ai_reply(speaker_b, prompt_b, peer=speaker_a, chat_with_character=True)
    msg_b = ChatMessage(
        conversation_id=conv_id,
        sender_id=speaker_b.id,
        content=reply_b,
        is_from_user=False,
    )
    messages.append(msg_b)
    save_messages(messages)


async def process_encounter_followups(encounter_items: List[Dict[str, Any]]):
    """相遇后：协作亲密度 + 若已有私人群则自动生成一轮闲聊。"""
    if not encounter_items:
        return
    characters = get_characters()
    char_map = {c.id: c for c in characters}
    sync_private_groups()
    groups = [g for g in get_private_groups() if g.is_active and len(g.member_ids) == 2]
    for item in encounter_items:
        a_id = item.get("a_id")
        b_id = item.get("b_id")
        loc = item.get("location") or "附近"
        if not a_id or not b_id:
            continue
        ca, cb = char_map.get(a_id), char_map.get(b_id)
        if not ca or not cb:
            continue
        stress = max(economic_stress_multiplier(ca), economic_stress_multiplier(cb))
        chat_prob = 0.62 / max(stress, 0.55)
        if random.random() > min(chat_prob, 0.92):
            add_log(ca.name, "encounter_skip", f"与 {cb.name} 相遇但匆匆离开（经济/状态）")
            continue
        apply_relationship_interaction(a_id, b_id, "collaborate")
        apply_relationship_interaction(b_id, a_id, "collaborate")
        key = _pair_key(a_id, b_id)
        group = next(
            (g for g in groups if _pair_key(g.member_ids[0], g.member_ids[1]) == key),
            None,
        )
        if group:
            topic = f"在{loc}偶遇，随便聊两句，或商量一件能一起协作的小事"
            try:
                await append_private_group_exchange(group, topic)
                add_log(ca.name, "encounter_chat", f"与 {cb.name} 相遇后私聊")
            except Exception as e:
                add_log("system", "encounter_chat_error", str(e)[:100])
        else:
            add_log(ca.name, "encounter", f"与 {cb.name} 在{loc}相遇（尚未开通私人群或亲密度不足）")


def apply_company_task_bonus_distribution(
    companies: List[Company],
    company_index: int,
    task: TaskItem,
    characters: List[Character],
) -> Optional[float]:
    """公司任务通过后：按贡献倾向从公司资金向成员分红（主执行多、协作次之、法人协调）。"""
    company = companies[company_index]
    reward = float(task.reward)
    if reward <= 0:
        return None
    bonuses: Dict[str, float] = {}
    if task.assignee_id:
        bonuses[task.assignee_id] = reward * 0.48
    collabs = [cid for cid in task.collaborator_ids if cid and cid != task.assignee_id]
    if collabs:
        per = reward * 0.27 / len(collabs)
        for cid in collabs:
            bonuses[cid] = bonuses.get(cid, 0.0) + per
    if company.legal_person_id:
        bonuses[company.legal_person_id] = bonuses.get(company.legal_person_id, 0.0) + reward * 0.10
    total = sum(max(0.0, v) for v in bonuses.values())
    cap = reward * 0.82
    if total > cap > 0:
        scale = cap / total
        bonuses = {k: v * scale for k, v in bonuses.items()}
        total = cap
    if total <= 0:
        return None
    if company.funds < total:
        scale = company.funds / total
        bonuses = {k: v * scale for k, v in bonuses.items()}
        total = company.funds
    if total <= 0:
        return None
    company.funds -= total
    company.updated_at = int(time.time() * 1000)
    for idx, char in enumerate(characters):
        bonus = float(bonuses.get(char.id, 0.0))
        if bonus <= 0:
            continue
        char.money += bonus
        char.updated_at = int(time.time() * 1000)
        characters[idx] = char
        add_log(char.name, "company_task_bonus", f"公司任务分红 +{bonus:.0f}")
    add_log(company.name, "company_bonus", f"任务《{task.title}》分红支出 -{total:.0f}")
    return total


def has_commented_moment(post: MomentPost, author_id: str) -> bool:
    return any(c.author_id == author_id and c.parent_comment_id is None for c in post.comments or [])


# ==================== 任务引擎 ====================

async def run_task_engine(max_tasks_per_tick: int = 5):
    """
    任务引擎 - 后台定期运行，驱动角色/公司自动接取和完成任务。
    - 为缺钱角色优先接取高奖励任务
    - 为公司自动匹配协作任务
    - 推进 in_progress 任务到完成
    - 基于职业匹配度、亲密度、经济状况智能分配
    """
    try:
        tasks = get_tasks()
        characters = get_characters()
        companies = get_companies()
        alive_chars = [c for c in characters if c.is_alive]
        
        if not alive_chars:
            return
            
        open_tasks = [t for t in tasks if t.status == TaskStatus.OPEN]
        in_progress_tasks = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        tasks_changed = False
        chars_changed = False
        action_count = 0
        
        # === 阶段 1: 公司自动接取公司任务 ===
        company_tasks_open = [t for t in open_tasks if t.assignee_type == TaskAssigneeType.COMPANY and t.company_id]
        for task in company_tasks_open[:max_tasks_per_tick]:
            company = next((c for c in companies if c.id == task.company_id), None)
            if not company:
                continue
            alive_members = [mid for mid in company.member_ids if any(ch.id == mid and ch.is_alive for ch in alive_chars)]
            if not alive_members:
                continue
            
            # 自动分配
            task.assignee_id = company.legal_person_id if company.legal_person_id in alive_members else alive_members[0]
            task.collaborator_ids = [mid for mid in alive_members if mid != task.assignee_id][:2]
            task.status = TaskStatus.IN_PROGRESS
            task.updated_at = int(time.time() * 1000)
            
            t_idx = tasks.index(task)
            tasks[t_idx] = task
            tasks_changed = True
            action_count += 1
            
            assignee_char = next((c for c in alive_chars if c.id == task.assignee_id), None)
            assignee_name = assignee_char.name if assignee_char else "未知"
            add_log(company.name, "task_auto_take", f"公司自动接取任务《{task.title}》，主执行：{assignee_name}")
        
        # === 阶段 2: 个人角色自动接取任务 ===
        # 按经济压力、空闲状态、职业匹配度排序
        char_needs = []
        for char in alive_chars:
            # 检查是否已经在做任务
            busy = any(t.assignee_id == char.id and t.status in (TaskStatus.IN_PROGRESS, TaskStatus.PENDING_REVIEW) for t in tasks)
            if busy:
                continue
            
            # 经济压力评分
            pressure_score = 0
            if char.money < 50:
                pressure_score += 3
            elif char.money < 100:
                pressure_score += 2
            elif char.money < 200:
                pressure_score += 1
            
            if char.debt_balance > 0:
                pressure_score += 2
            
            # 职业匹配加分
            occupation_score = 0
            for ot in open_tasks:
                keywords = _get_task_keywords(ot.task_type)
                for kw in keywords:
                    if kw in (char.occupation or ""):
                        occupation_score += 2
                        break
            
            total_score = pressure_score + occupation_score + random.uniform(0, 1)
            char_needs.append((char, total_score))
        
        char_needs.sort(key=lambda x: x[1], reverse=True)
        
        for char, score in char_needs[:max_tasks_per_tick]:
            if score < 0.5:  # 太低概率不接取
                continue
            if not open_tasks:
                break
                
            # 智能选择任务
            personal_tasks = [t for t in open_tasks if t.assignee_type != TaskAssigneeType.COMPANY]
            if not personal_tasks:
                continue
                
            # 按奖励和匹配度排序
            scored_tasks = []
            for task in personal_tasks:
                match_score = 0
                keywords = _get_task_keywords(task.task_type)
                for kw in keywords:
                    if kw in (char.occupation or ""):
                        match_score += 3
                # 经济压力时偏好高奖励
                if char.money < 100:
                    match_score += task.reward / 100
                scored_tasks.append((task, match_score + random.uniform(0, 2)))
            
            scored_tasks.sort(key=lambda x: x[1], reverse=True)
            chosen_task = scored_tasks[0][0]
            
            # 自动接取
            task_idx = tasks.index(chosen_task)
            chosen_task.assignee_id = char.id
            chosen_task.assignee_type = TaskAssigneeType.PERSONAL
            chosen_task.status = TaskStatus.IN_PROGRESS
            chosen_task.updated_at = int(time.time() * 1000)
            tasks[task_idx] = chosen_task
            tasks_changed = True
            action_count += 1
            
            add_log(char.name, "task_auto_take", f"自动接取任务《{chosen_task.title}》（奖励：{chosen_task.reward:.0f}元）")
            
            # 从 open_tasks 中移除
            open_tasks.remove(chosen_task)
        
        # === 阶段 3: 自动完成任务 ===
        for task in in_progress_tasks[:max_tasks_per_tick]:
            assignee = next((c for c in alive_chars if c.id == task.assignee_id), None)
            if not assignee:
                continue
            
            # 随机决定是否完成（基于经济压力、任务类型等）
            complete_prob = 0.15  # 基础完成概率
            if assignee.money < 50:
                complete_prob += 0.15  # 缺钱时更积极完成任务
            if assignee.debt_balance > 0:
                complete_prob += 0.1   # 有债务时更积极
            
            # 公司任务协作加成
            if task.assignee_type == TaskAssigneeType.COMPANY and task.collaborator_ids:
                complete_prob += 0.1  # 团队协作效率更高
            
            if random.random() < complete_prob:
                task_idx = tasks.index(task)
                task.status = TaskStatus.PENDING_REVIEW
                task.updated_at = int(time.time() * 1000)
                
                # 生成执行说明
                collab_names = []
                for cid in task.collaborator_ids or []:
                    cm = next((c for c in alive_chars if c.id == cid), None)
                    if cm:
                        collab_names.append(cm.name)
                
                if task.assignee_type == TaskAssigneeType.COMPANY and collab_names:
                    task.execution_notes = f"公司协作完成：主执行 {assignee.name}，协作 {', '.join(collab_names)}"
                else:
                    task.execution_notes = f"{assignee.name} 自主完成任务并提交审核"
                
                # 调用真实生成函数，而非占位符
                if task.task_type == TaskType.IMAGE:
                    task.deliverable_image_url = await _generate_task_image(task, assignee)
                    task.deliverable_text = f"{assignee.name} 完成了图像创作：「{task.title}」"
                elif task.task_type == TaskType.CODE:
                    task.deliverable_code = await _generate_task_code(task, assignee)
                    task.deliverable_text = f"{assignee.name} 完成了代码实现：「{task.title}」"
                elif task.task_type == TaskType.RESEARCH:
                    task.deliverable_text = await _generate_task_research(task, assignee)
                else:
                    if task.assignee_type == TaskAssigneeType.COMPANY and collab_names:
                        task.deliverable_text = f"{assignee.name} 牵头，与 {', '.join(collab_names)} 协作产出：\n\n{await _generate_task_text(task, assignee)}"
                    else:
                        task.deliverable_text = f"{assignee.name} 完成任务：「{task.title}」\n\n{await _generate_task_text(task, assignee)}"
                
                tasks[task_idx] = task
                tasks_changed = True
                action_count += 1
                
                add_log(assignee.name, "task_auto_complete", f"自动完成任务《{task.title}》并提交审核")
        
        # 保存更改
        if tasks_changed:
            save_tasks(tasks)
        if chars_changed:
            save_characters(characters)
            
        if action_count > 0:
            add_log("system", "task_engine", f"本轮处理 {action_count} 个任务操作")
        
        # 阶段 4: 自动审核待审核任务
        await auto_review_pending_tasks(max_tasks=3)
            
    except Exception as e:
        add_log("system", "task_engine_error", f"任务引擎异常：{str(e)[:200]}")


def _get_task_keywords(task_type: TaskType) -> List[str]:
    """获取任务类型对应的职业关键词"""
    keywords_map = {
        TaskType.CODE: ["程序", "开发", "工程", "前端", "后端", "码", "软件", "IT", "计算机"],
        TaskType.DESIGN: ["设计", "美术", "视觉", "品牌", "艺术", "创意"],
        TaskType.RESEARCH: ["研究", "分析", "咨询", "运营", "学术", "科研"],
        TaskType.IMAGE: ["设计", "美术", "摄影", "画", "视觉", "创意"],
        TaskType.TEXT: ["作家", "编辑", "文案", "老师", "写", "文字", "内容", "记者"],
    }
    return keywords_map.get(task_type, [])


# ==================== 反思与经验系统 ====================

def update_character_experience(character: Character, task_type: TaskType, reflection: ReflectionReport, success: bool):
    """更新角色经验技能库"""
    exp = character.experience_skills
    task_type_key = task_type.value
    
    if task_type_key not in exp:
        exp[task_type_key] = {
            "count": 0,
            "success_count": 0,
            "lessons": [],
            "action_items_done": [],
            "skill_improvements": {},
            "last_updated": int(time.time() * 1000),
        }
    
    entry = exp[task_type_key]
    entry["count"] += 1
    if success:
        entry["success_count"] += 1
    
    # 整合经验教训（去重，最多保留 10 条）
    for lesson in reflection.lessons_learned:
        if lesson not in entry["lessons"]:
            entry["lessons"].append(lesson)
    entry["lessons"] = entry["lessons"][:10]
    
    # 记录已完成的行动项
    for item in reflection.action_items:
        if item not in entry["action_items_done"]:
            entry["action_items_done"].append(item)
    entry["action_items_done"] = entry["action_items_done"][:10]
    
    # 累加技能提升
    for skill, points in reflection.skill_improvements.items():
        entry["skill_improvements"][skill] = entry["skill_improvements"].get(skill, 0) + points
    
    entry["last_updated"] = int(time.time() * 1000)
    character.experience_skills = exp


def get_experience_context(character: Character, task_type: TaskType) -> str:
    """获取角色在特定任务类型上的经验上下文（用于 LLM 注入）"""
    exp = character.experience_skills
    task_type_key = task_type.value
    
    if task_type_key not in exp:
        return f"\n[经验提示] 你尚未积累 {task_type.value} 类型的任务经验，请从头开始认真完成。"
    
    entry = exp[task_type_key]
    count = entry["count"]
    success_count = entry["success_count"]
    success_rate = (success_count / count * 100) if count > 0 else 0
    lessons = entry.get("lessons", [])
    skills = entry.get("skill_improvements", {})
    
    ctx = f"\n[经验提示] 你已完成 {count} 次 {task_type.value} 类型任务，成功率 {success_rate:.0f}%。\n"
    if lessons:
        ctx += "过往经验教训：\n"
        for i, lesson in enumerate(lessons[:5], 1):
            ctx += f"  {i}. {lesson}\n"
    if skills:
        top_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)[:3]
        ctx += "核心技能积累：\n"
        for skill, points in top_skills:
            ctx += f"  - {skill}: +{points}\n"
    ctx += "请充分利用以上经验，避免重复犯错，高效完成任务。"
    return ctx


def get_company_experience_context(company: Company, task_type: TaskType) -> str:
    """获取公司知识库中的经验上下文（供公司所有成员使用）"""
    kb = company.knowledge_base
    if not kb:
        return ""
    
    # 筛选相关类型的任务反思
    task_ids_in_kb = [entry.get("task_id") for entry in kb if entry.get("reflection")]
    if not task_ids_in_kb:
        return ""
    
    # 从已完成任务中匹配类型
    tasks = get_tasks()
    company_tasks_done = [
        t for t in tasks 
        if t.id in task_ids_in_kb and t.task_type == task_type and t.status == TaskStatus.COMPLETED
    ]
    
    if not company_tasks_done:
        return ""
    
    ctx = f"\n[公司经验] {company.name} 知识库中有 {len(company_tasks_done)} 个相关任务的经验：\n"
    for i, t in enumerate(company_tasks_done[:5], 1):
        if t.reflection:
            ctx += f"  {i}. 《{t.title}》经验：\n"
            for lesson in t.reflection.lessons_learned[:3]:
                ctx += f"     - {lesson}\n"
    ctx += "请参考公司前辈的经验，站在巨人的肩膀上完成任务。"
    return ctx


def store_task_reflection_memory(character: Character, task: TaskItem, reflection: ReflectionReport, success: bool):
    """将任务反思存入角色记忆"""
    lessons_text = "; ".join(reflection.lessons_learned) if reflection.lessons_learned else "无"
    memory_content = f"任务《{task.title}》反思：{lessons_text}"
    
    # 如果有经验教训，同时记录详细版
    if reflection.what_went_wrong:
        memory_content += f"。不足：{'; '.join(reflection.what_went_wrong)}"
    if reflection.action_items:
        memory_content += f"。改进：{'; '.join(reflection.action_items)}"
    
    store_memory(
        character_id=character.id,
        content=memory_content,
        memory_type=MemoryType.REFLECTION,
        importance=0.9 if not success else 0.7,
        related_entities=[task.id],
        metadata={"reflection": reflection.model_dump()},
    )


def add_reflection_to_company_knowledge(company: Company, task: TaskItem, reflection: ReflectionReport):
    """将任务反思添加到公司知识库"""
    company.knowledge_base.insert(0, {
        "task_id": task.id,
        "task_type": task.task_type.value,
        "title": task.title,
        "reflection": reflection.model_dump(),
        "timestamp": int(time.time() * 1000),
    })
    # 限制知识库大小
    if len(company.knowledge_base) > 50:
        company.knowledge_base = company.knowledge_base[:50]


async def apply_reflection_after_task(task: TaskItem, approved: bool, review_notes: str):
    """任务审核后的反思应用：更新经验库、存储记忆、公司知识共享"""
    characters = get_characters()
    companies = get_companies()
    tasks = get_tasks()
    
    reflection = create_reflection_from_task(task, approved, review_notes)
    
    # 更新任务对象上的反思
    for i, t in enumerate(tasks):
        if t.id == task.id:
            t.reflection = reflection
            tasks[i] = t
    save_tasks(tasks)
    
    # 1) 个人反思：更新角色经验库
    if task.assignee_id:
        assignee = next((c for c in characters if c.id == task.assignee_id), None)
        if assignee:
            update_character_experience(assignee, task.task_type, reflection, approved)
            store_task_reflection_memory(assignee, task, reflection, approved)
            
            # 更新角色对象
            for i, c in enumerate(characters):
                if c.id == assignee.id:
                    characters[i] = assignee
                    break
            save_characters(characters)
            
            # 2) 公司反思：如果角色在公司，将经验共享到公司知识库
            if assignee.company_id:
                company = next((comp for comp in companies if comp.id == assignee.company_id), None)
                if company:
                    add_reflection_to_company_knowledge(company, task, reflection)
                    for i, c in enumerate(companies):
                        if c.id == company.id:
                            companies[i] = company
                            break
                    save_companies(companies)
                    add_log(company.name, "company_knowledge", f"新增任务《{task.title}》反思经验到公司知识库")
    
    return reflection


async def ai_auto_review_task(task: TaskItem, assignee: Character) -> Dict[str, Any]:
    """
    AI 自动审核任务：
    - 调用 LLM 根据任务描述和交付物进行评估
    - 返回审核结果（是否通过、评分、评审意见）
    - 触发反思系统更新经验
    """
    if not task.deliverable_text and not task.deliverable_code:
        # 交付物为空，自动拒绝
        return {
            "approved": False,
            "score": 30,
            "notes": "交付物不完整，请补充任务成果描述",
            "checklist": {"内容完整性": False, "质量达标": False, "按时提交": False},
        }
    
    # 检查角色经验，有经验的角色更容易通过
    exp_context = get_experience_context(assignee, task.task_type) if assignee else ""
    
    # 获取公司经验（如果角色在公司）
    company_context = ""
    if assignee and assignee.company_id:
        companies = get_companies()
        company = next((c for c in companies if c.id == assignee.company_id), None)
        if company:
            company_context = get_company_experience_context(company, task.task_type)
    
    # 构建审核 Prompt
    review_prompt = f"""你是一位专业的项目经理，请审核以下任务成果：

**任务信息**：
- 标题：{task.title}
- 类型：{task.task_type.value}
- 描述：{task.description}

**交付内容**：
{task.deliverable_text}
{task.deliverable_code if task.deliverable_code else ""}
{task.execution_notes}

{exp_context}
{company_context}

请评估：
1. 内容完整性（是/否）
2. 质量达标（是/否）
3. 按时提交（是/否）
4. 总体评分（0-100）
5. 审核意见（简短中文）
6. 是否通过审核（approved: true/false）

请严格按照以下 JSON 格式返回，不要包含其他内容：
{{"content_complete": true/false, "quality_ok": true/false, "on_time": true/false, "score": 0-100, "notes": "审核意见", "approved": true/false}}"""
    
    # 调用 LLM
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    
    if not llm_config:
        # 没有 LLM 时，使用简单规则审核
        return _simple_rule_based_review(task, assignee)
    
    try:
        import aiohttp
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": review_prompt}],
            "temperature": 0.3,
            "max_tokens": 300
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    record_llm_usage(result, llm_config, "ai_review_task", task.assignee_id)
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                    
                    # 解析 JSON 响应
                    import json
                    try:
                        # 尝试从响应中提取 JSON
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            review_data = json.loads(json_match.group())
                            return {
                                "approved": review_data.get("approved", False),
                                "score": review_data.get("score", 50),
                                "notes": review_data.get("notes", "AI 审核完成"),
                                "checklist": {
                                    "内容完整性": review_data.get("content_complete", False),
                                    "质量达标": review_data.get("quality_ok", False),
                                    "按时提交": review_data.get("on_time", True),
                                },
                            }
                    except (json.JSONDecodeError, KeyError):
                        pass
    
    except Exception as e:
        add_log("system", "ai_review_error", f"AI 审核异常：{str(e)[:200]}")
    
    # 失败时降级到规则审核
    return _simple_rule_based_review(task, assignee)


def _simple_rule_based_review(task: TaskItem, assignee: Optional[Character]) -> Dict[str, Any]:
    """简单规则审核：当 LLM 不可用时使用"""
    has_content = bool(task.deliverable_text or task.deliverable_code)
    has_notes = bool(task.execution_notes)
    
    # 基础评分
    score = 50
    if has_content:
        score += 20
    if has_notes:
        score += 10
    
    # 有经验加成
    if assignee and assignee.experience_skills.get(task.task_type.value, {}).get("count", 0) > 0:
        score += 15
    
    # 公司协作加成
    if task.collaborator_ids:
        score += 5
    
    score = min(95, max(40, score + random.randint(-5, 10)))
    
    return {
        "approved": score >= 60,
        "score": int(score),
        "notes": "AI 自动审核通过" if score >= 60 else "交付物质量有待提升",
        "checklist": {
            "内容完整性": has_content,
            "质量达标": score >= 60,
            "按时提交": True,
        },
    }


async def auto_review_pending_tasks(max_tasks: int = 3):
    """自动审核待审核任务，完成完整的任务流程"""
    try:
        tasks = get_tasks()
        characters = get_characters()
        
        pending_tasks = [t for t in tasks if t.status == TaskStatus.PENDING_REVIEW]
        reviewed_count = 0
        
        for task in pending_tasks[:max_tasks]:
            assignee = next((c for c in characters if c.id == task.assignee_id), None)
            
            # AI 审核
            review_result = await ai_auto_review_task(task, assignee)
            
            # 应用审核结果
            task.review_notes = review_result["notes"]
            task.review_round += 1
            task.review_history.append({
                "round": task.review_round,
                "approved": review_result["approved"],
                "notes": review_result["notes"],
                "score": review_result["score"],
                "checklist": review_result["checklist"],
                "timestamp": int(time.time() * 1000),
                "auto_review": True,  # 标记为自动审核
            })
            task.updated_at = int(time.time() * 1000)
            
            if review_result["approved"]:
                task.status = TaskStatus.COMPLETED
                task.completed_at = int(time.time() * 1000)
                
                # 发放奖励
                if task.assignee_type == TaskAssigneeType.PERSONAL and task.assignee_id:
                    for idx, char in enumerate(characters):
                        if char.id == task.assignee_id:
                            char.money += task.reward
                            char.updated_at = int(time.time() * 1000)
                            characters[idx] = char
                            break
                    save_characters(characters)
                
                # 公司奖励
                if task.assignee_type == TaskAssigneeType.COMPANY and task.company_id:
                    companies = get_companies()
                    cidx = next((idx for idx, comp in enumerate(companies) if comp.id == task.company_id), None)
                    if cidx is not None:
                        comp = companies[cidx]
                        comp.funds += task.reward
                        comp.updated_at = int(time.time() * 1000)
                        companies[cidx] = comp
                        apply_company_task_bonus_distribution(companies, cidx, task, characters)
                        save_companies(companies)
                        save_characters(characters)
                
                reviewed_count += 1
                add_log("system", "auto_review", f"任务《{task.title}》AI 审核通过（评分：{review_result['score']}）")
                
            else:
                task.status = TaskStatus.IN_PROGRESS if task.review_round < 3 else TaskStatus.FAILED
                reviewed_count += 1
                add_log("system", "auto_review", f"任务《{task.title}》AI 审核未通过（评分：{review_result['score']}）")
            
            # 更新任务
            for i, t in enumerate(tasks):
                if t.id == task.id:
                    tasks[i] = task
                    break
            
            # 触发反思
            await apply_reflection_after_task(task, review_result["approved"], review_result["notes"])
        
        save_tasks(tasks)
        
        if reviewed_count > 0:
            add_log("system", "auto_review", f"本轮自动审核 {reviewed_count} 个任务")
            
    except Exception as e:
        add_log("system", "auto_review_error", f"自动审核异常：{str(e)[:200]}")


async def run_character_heartbeat(character: Character, characters: List[Character]):
    """
    单角色心跳：
    - 优先处理 pending_intents (通过 Exec 协议预设的意图)
    - 逛朋友圈（按可见性挑选动态）
    - 点赞/评论（尊重约束：每动态每角色最多1条顶层评论）
    - 小概率发一条动态
    - 小概率接取一个 open 任务并推进到待审核
    """
    if not character.is_alive:
        return

    # 1) 优先执行预设意图
    if character.pending_intents:
        intent = character.pending_intents.pop(0)
        action = intent["action"]
        params = intent["params"]
        add_log(character.name, "执行意图", f"Action: {action}, Params: {params}")
        try:
            if action == "PostMoment":
                await generate_character_moment(character.id, GenerateMomentRequest(
                    trigger_type="ai_action",
                    event_text=params,
                    with_image=True
                ))
            elif action == "TakeTask":
                await auto_take_task(params, AutoTakeTaskRequest(preferred_character_id=character.id))
            elif action == "SubmitTask":
                try:
                    parts = [p.strip() for p in params.split(",", 1)]
                    t_id = parts[0]
                    notes = parts[1] if len(parts) > 1 else "AI 自主完成"
                    # 先获取任务信息，根据类型生成真实成果
                    task_obj = None
                    for t in get_tasks():
                        if t.id == t_id:
                            task_obj = t
                            break
                    if task_obj and task_obj.task_type == TaskType.IMAGE:
                        img_url = await _generate_task_image(task_obj, character)
                        await submit_task(t_id, SubmitTaskRequest(
                            submitter_id=character.id,
                            execution_notes=notes,
                            deliverable_text=f"{character.name} 完成了图像创作：「{task_obj.title}」",
                            deliverable_image_url=img_url
                        ))
                    elif task_obj and task_obj.task_type == TaskType.CODE:
                        code = await _generate_task_code(task_obj, character)
                        await submit_task(t_id, SubmitTaskRequest(
                            submitter_id=character.id,
                            execution_notes=notes,
                            deliverable_text=f"{character.name} 完成了代码实现：「{task_obj.title}」",
                            deliverable_code=code
                        ))
                    elif task_obj and task_obj.task_type == TaskType.RESEARCH:
                        report = await _generate_task_research(task_obj, character)
                        await submit_task(t_id, SubmitTaskRequest(
                            submitter_id=character.id,
                            execution_notes=notes,
                            deliverable_text=report
                        ))
                    else:
                        await submit_task(t_id, SubmitTaskRequest(
                            submitter_id=character.id,
                            execution_notes=notes,
                            deliverable_text=f"{character.name} 完成任务：「{task_obj.title if task_obj else t_id}」"
                        ))
                except Exception:
                    await auto_complete_task(params)
        except Exception as e:
            add_log(character.name, "意图执行失败", str(e))
        # 执行了意图后，本次心跳不再进行其他随机操作，模拟"专注工作"
        return

    stress = economic_stress_multiplier(character)
    social_scale = 1.0 / max(1.0, stress * 0.82)
    like_p = min(0.32, 0.25 * social_scale)
    comment_p = min(0.18, 0.12 * social_scale)
    # 优化朋友圈频率：结合经济压力和角色设定的频率
    freq_multiplier = get_moment_frequency_multiplier(character)
    moment_p = min(0.25, 0.05 * social_scale * freq_multiplier)
    task_base = 0.08 * stress
    task_p = min(0.42, task_base)

    # 1) 逛朋友圈
    moments = get_moments()
    moments.sort(key=lambda m: m.timestamp, reverse=True)
    visible = [m for m in moments[:60] if can_view_moment(character.id, m)]
    if visible:
        add_log(character.name, "heartbeat", f"浏览朋友圈 {min(len(visible), 20)} 条")
    for post in visible[:20]:
        if post.author_id == character.id:
            continue
        if character.id not in (post.liked_by or []) and random.random() < like_p:
            try:
                await like_moment(post.id, character.id)
                add_log(character.name, "heartbeat_like", f"点赞了 {post.author_name} 的朋友圈")
            except HTTPException:
                pass
        if not has_commented_moment(post, character.id) and random.random() < comment_p:
            try:
                await comment_moment(post.id, MomentCommentRequest(author_id=character.id, auto_generate=True))
                add_log(character.name, "heartbeat_comment", f"评论了 {post.author_name} 的朋友圈")
            except HTTPException:
                pass

    if random.random() < moment_p:
        try:
            await generate_character_moment(character.id, GenerateMomentRequest(trigger_type="random", with_image=True))
        except HTTPException:
            pass

    if random.random() < task_p:
        tasks = get_tasks()
        open_tasks = [t for t in tasks if t.status == TaskStatus.OPEN]
        if open_tasks:
            company_pool = [
                t for t in open_tasks
                if t.company_id and t.company_id == character.company_id and t.assignee_type == TaskAssigneeType.COMPANY
            ]
            if company_pool and random.random() < 0.5:
                pool = company_pool
            else:
                pool = open_tasks
            if character.money <= 0 or character.poverty_days >= 1:
                pool = sorted(pool, key=lambda t: t.reward, reverse=True)
                task = pool[0]
            else:
                task = random.choice(pool)
            try:
                await auto_take_task(task.id, AutoTakeTaskRequest(preferred_character_id=character.id))
                complete_p = 0.35 if stress > 1.2 else 0.5
                if random.random() < complete_p:
                    await auto_complete_task(task.id)
            except HTTPException:
                pass


async def run_heartbeat_tick(limit_characters: int = 30) -> Dict[str, Any]:
    characters = get_characters()
    alive = [c for c in characters if c.is_alive]
    if not alive:
        return {"characters": 0, "ticked": 0}
    # 采样避免一次性太重
    sampled = alive if len(alive) <= limit_characters else random.sample(alive, limit_characters)
    for char in sampled:
        await run_character_heartbeat(char, alive)
    
    # AI 自主管理公司（每3次心跳触发一次）
    if random.random() < 0.33:
        await run_ai_company_heartbeat()
    
    # 关键：心跳结束后必须保存状态（包括消耗的意图、更新的位置等）
    save_characters(characters)
    return {"characters": len(alive), "ticked": len(sampled)}


async def run_ai_company_heartbeat():
    """AI 自主管理公司：角色根据经济状况和社交关系自主创建公司、招募成员"""
    characters = get_characters()
    companies = get_companies()
    alive_chars = [c for c in characters if c.is_alive]
    if not alive_chars:
        return
    
    # 1) 没有公司但资金充裕的角色，小概率自主创业
    chars_without_company = [c for c in alive_chars if not c.company_id and c.money >= 1500 and c.age >= 18]
    if chars_without_company and random.random() < 0.2:
        founder = max(chars_without_company, key=lambda c: c.money)
        occupation = founder.occupation or "创业者"
        company_names = [
            f"{founder.name}的{occupation}工作室",
            f"云海{occupation}事务所",
            f"{founder.name}{occupation}公司",
            f"{occupation}创新坊",
        ]
        company_name = random.choice(company_names)
        
        # 扣除创业资金
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
        add_log(founder.name, "AI创业", f"自主创建公司「{company_name}」，投入500元启动资金，个人账户剩余{founder.money:.0f}元")
    
    # 2) 公司法人小概率招募新成员（优先招募有亲密度的角色）
    for company in companies[:]:  # copy to avoid modification during iteration
        if random.random() < 0.15:
            founder = next((c for c in alive_chars if c.id == company.legal_person_id), None)
            if not founder or founder.money < 300:
                continue
            # 从没公司的角色中挑选，优先有互动的
            candidates = [c for c in alive_chars if c.id not in company.member_ids and not c.company_id and c.age >= 16]
            if candidates:
                # 按亲密度和随机性综合排序
                from collections import defaultdict
                relationships = get_relationships()
                candidate_scores = []
                for cand in candidates:
                    rel = next((r for r in relationships if (r.from_id == founder.id and r.to_id == cand.id) or (r.from_id == cand.id and r.to_id == founder.id)), None)
                    intimacy = rel.intimacy if rel else 0
                    score = intimacy * 0.6 + random.random() * 40
                    candidate_scores.append((score, cand))
                candidate_scores.sort(key=lambda x: x[0], reverse=True)
                recruit = candidate_scores[0][1]
                
                recruit.company_id = company.id
                company.member_ids.append(recruit.id)
                save_companies(companies)
                save_characters(characters)
                add_log(company.name, "AI招募", f"法人 {founder.name} 自主招募 {recruit.name}（亲密度{intimacy:.0f}）加入公司")


def run_daily_economy(world_elapsed_ms: int):
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
        daily_cost = 5 * days
        char.money -= daily_cost
        detail_parts.append(f"日常消耗 -{daily_cost:.0f}（{days}天）")
        if char.money <= 0:
            char.poverty_days += days
        else:
            char.poverty_days = 0

        if char.poverty_days >= 3 and char.debt_balance <= 0:
            char.debt_balance += 100
            char.money += 100
            char.poverty_days = 0
            detail_parts.append("连续贫困触发贷款 +100")

        if char.debt_balance > 0:
            interest = round(char.debt_balance * 0.01 * days, 2)
            char.debt_balance += interest
            detail_parts.append(f"贷款利息 +{interest:.2f}")
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
        add_log(char.name, "economy", detail)
    if len(logs) > 400:
        logs = logs[:400]
    save_economy_logs(logs)
    save_characters(characters)


async def compress_context(character: Character, conversation_id: str, messages: List[Dict[str, str]]) -> str:
    """
    对历史对话进行压缩摘要，并存入角色记忆
    """
    if len(messages) < 5:
        return ""

    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return ""

    chat_history = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
    prompt = f"请对以下对话内容进行简要总结，提取关键信息和角色状态，用于长期记忆：\n\n{chat_history}"

    try:
        import aiohttp
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    record_llm_usage(result, llm_config, "compress_context", character.id)
                    summary = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                    if summary:
                        store_memory(
                            character_id=character.id,
                            content=f"【对话复盘】{summary}",
                            memory_type=MemoryType.REFLECTION,
                            importance=0.7,
                            related_entities=[conversation_id]
                        )
                        return summary
    except Exception as e:
        add_log("系统", "压缩错误", str(e))
    return ""

# ==================== AI 回复生成 ====================

async def generate_ai_reply(
    character: Character,
    user_input: str,
    *,
    peer: Optional[Character] = None,
    chat_with_character: bool = False,
    conversation_id: Optional[str] = None
) -> str:
    """根据角色人设生成回复（集成 Session 管理、上下文压缩与 Exec 协议）"""
    import aiohttp
    
    conv_id = conversation_id or (f"peer:{peer.id}" if peer else "user_default")
    
    # 1. 获取并维护 Session 上下文
    session_manager.add_message(conv_id, "user", user_input)
    history = session_manager.get_context(conv_id)
    
    # 2. 召回相关长期记忆
    recalled_memories = await recall_memories(character_id=character.id, query=user_input, top_k=3)
    memory_context = build_memory_context(recalled_memories)

    # 2.1 注入实时任务列表上下文（仅显示 OPEN 状态且匹配该角色的）
    all_tasks = get_tasks()
    available_tasks = [t for t in all_tasks if t.status == TaskStatus.OPEN]
    
    # 注入经验上下文到任务列表中
    task_context_parts = []
    for t in available_tasks[:5]:
        exp_context = get_experience_context(character, t.task_type)
        company_context = ""
        if character.company_id:
            companies = get_companies()
            company = next((c for c in companies if c.id == character.company_id), None)
            if company:
                company_context = get_company_experience_context(company, t.task_type)
        task_context_parts.append(f"- [TaskID: {t.id}] {t.title}: {t.reward}元{exp_context}{company_context}")
    
    task_context = "\n".join(task_context_parts)
    if not task_context: task_context = "当前暂无新任务"
    
    # 3. 构造增强 Prompt
    configs = get_api_configs()
    # 优先使用角色指定的LLM模型，否则使用全局配置
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    
    if not llm_config:
        return get_fallback_reply(character, user_input)

    # 确定使用的模型
    model_name = character.llm_model_id if character.llm_model_id else (llm_config.selected_model or "gpt-3.5-turbo")

    world_time = get_world_time_text()
    # 注入年龄性格修饰
    personality_with_age = get_age_personality_modifier(character.age, character.personality)
    # 注入 Exec 协议能力说明
    exec_hint = """
[EXEC Protocol Enabled]
You can execute world actions by appending instructions at the end of your reply:
- [EXEC:PostMoment(content)] 发送一条朋友圈
- [EXEC:MoveTo(location)] 移动到新地点 (办公室/餐厅/社交场所等)
- [EXEC:Transfer(amount, target_id)] 转账给某人
- [EXEC:TakeTask(task_id)] 接取一个任务
- [EXEC:SubmitTask(task_id, notes)] 提交并完成任务
- [EXEC:CreateCompany(name)] 创建公司（如果你有足够资金和商业头脑）
- [EXEC:RecruitMember(company_id, target_id)] 招募公司成员
Example: "好的，我现在就过去。[EXEC:MoveTo(餐厅)]"
"""

    system_prompt = f"""你是 {character.name}，{character.get_age_display()}，{character.gender}，{character.occupation}。
当前世界时间：{world_time}
你的性格：{personality_with_age}

【回复风格要求】
1. 用日常口语回复，像真人在微信聊天一样自然
2. 可以用"嗯""啊""哈哈""唉""嘛""呢"等语气词，但要适度
3. 可以有轻微口癖，如"说实话""我觉得""反正"等
4. 回复要简短自然，一般20-80字，偶尔可以长一点
5. 不要长篇大论，不要分段超过两段
6. 不要用"作为AI""我是一个模型"等打破第四面墙的话
7. 不要用过于书面化或学术化的表达
8. 可以有情绪波动：开心、无奈、兴奋、疲惫等，根据上下文决定
9. 可以用emoji但不要滥用，偶尔用一个就好
10. 如果是工作时间就别太热情，深夜就别太活跃
11. 遇到不懂的事情可以表现出困惑或好奇
12. 和朋友聊天可以随意一点，和陌生人或长辈要礼貌些

[EXEC Protocol Enabled]
你可以在回复末尾通过以下指令执行世界动作：
- [EXEC:PostMoment(content)] 发一条朋友圈
- [EXEC:MoveTo(地点)] 移动到某处 (办公室/餐厅/社交场所等)
- [EXEC:Transfer(金额, 目标ID)] 转账给某人
- [EXEC:TakeTask(任务ID)] 接取一个任务
- [EXEC:SubmitTask(任务ID, 备注)] 提交任务
示例："好的，我现在就过去。[EXEC:MoveTo(餐厅)]"

[相关长期记忆]
{memory_context}

[当前可接任务]
{task_context}

请用简体中文回复，保持自然口语化风格。注意当前世界时间和自己的作息。"""

    try:
        # 4. 调用 LLM (包含历史 Session)
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-6:]: # 取最近6轮对话
            messages.append({"role": msg["role"], "content": msg["content"]})

        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    res_json = await response.json()
                    record_llm_usage(res_json, llm_config, "ai_reply", character.id)
                    reply = res_json.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                    
                    # 5. 处理 Exec 协议指令
                    instructions = ExecProtocol.parse_instructions(reply)
                    for inst in instructions:
                        action = inst['action']
                        params = inst['params']
                        add_log(character.name, "识别指令", f"Action: {action}, Params: {params}")
                        
                        # 某些指令立即执行，某些指令存入意图队列待心跳触发
                        if action in ["Transfer", "MoveTo"]:
                            # 立即执行的物理/资金操作
                            try:
                                if action == "MoveTo":
                                    update_character_location(character, params, source="ai_action")
                                    add_log(character.name, "移动", f"AI 自主决定移动到 {params}")
                                elif action == "Transfer":
                                    # ... (保持原有转账逻辑)
                                    parts = [p.strip() for p in params.split(",")]
                                    if len(parts) >= 2:
                                        amount = float(parts[0])
                                        target_id = parts[1]
                                        chars = get_characters()
                                        sender = next((c for c in chars if c.id == character.id), None)
                                        receiver = next((c for c in chars if c.id == target_id), None)
                                        if sender and receiver and sender.money >= amount:
                                            sender.money -= amount
                                            receiver.money += amount
                                            sender.updated_at = int(time.time() * 1000)
                                            receiver.updated_at = int(time.time() * 1000)
                                            save_characters(chars)
                                            add_log(sender.name, "转账", f"向 {receiver.name} 转账 {amount:.2f}")
                                            add_log(receiver.name, "收款", f"收到来自 {sender.name} 的转账 {amount:.2f}")
                            except Exception as e:
                                add_log(character.name, "即时指令失败", str(e))
                        elif action == "CreateCompany":
                            # 创建公司 - 需要一定资金
                            try:
                                company_name = params.strip()
                                if len(company_name) > 50:
                                    company_name = company_name[:50]
                                if character.money < 1000:
                                    add_log(character.name, "创建公司失败", "资金不足（至少需要1000元）")
                                else:
                                    companies = get_companies()
                                    new_company = Company(
                                        name=company_name,
                                        legal_person_id=character.id,
                                        member_ids=[character.id],
                                        funds=500.0,  # 初始公司资金
                                        location_name=character.current_location_id or "办公室",
                                    )
                                    # 从个人资金中扣除
                                    character.money -= 1000
                                    character.company_id = new_company.id
                                    companies.append(new_company)
                                    save_companies(companies)
                                    save_characters(get_characters())
                                    add_log(character.name, "创建公司", f"成功创建公司「{company_name}」，投入500元启动资金")
                            except Exception as e:
                                add_log(character.name, "创建公司失败", str(e))
                        elif action == "RecruitMember":
                            # 招募公司成员
                            try:
                                parts = [p.strip() for p in params.split(",")]
                                if len(parts) >= 2:
                                    company_id = parts[0]
                                    target_id = parts[1]
                                    companies = get_companies()
                                    company = next((c for c in companies if c.id == company_id), None)
                                    if company and company.legal_person_id == character.id:
                                        if target_id not in company.member_ids:
                                            company.member_ids.append(target_id)
                                            save_companies(companies)
                                            target_char = next((c for c in get_characters() if c.id == target_id), None)
                                            if target_char:
                                                target_char.company_id = company_id
                                                save_characters(get_characters())
                                            add_log(character.name, "招募", f"成功招募 {target_char.name if target_char else target_id} 加入 {company.name}")
                                        else:
                                            add_log(character.name, "招募失败", f"{target_id} 已经是公司成员")
                                    else:
                                        add_log(character.name, "招募失败", "你不是该公司法人或公司不存在")
                            except Exception as e:
                                add_log(character.name, "招募失败", str(e))
                        else:
                            # 存入待办意图队列，由心跳系统在合适的"时机"执行
                            character.pending_intents.append({"action": action, "params": params, "created_at": int(time.time() * 1000)})
                            add_log(character.name, "计划", f"已将 {action} 加入待办意图")

                    # 6. 更新 Session 并检查压缩
                    session_manager.add_message(conv_id, "assistant", reply)
                    if len(history) > 10:
                        await compress_context(character, conv_id, history)
                        # 压缩后可以清理部分旧 Session
                        session_manager.sessions[conv_id] = history[-4:]

                    return reply
    except Exception as e:
        add_log("系统", "对话异常", str(e))
        return get_fallback_reply(character, user_input)


def get_fallback_reply(character: Character, user_input: str) -> str:
    """获取备用回复（当 LLM 不可用时）"""
    import random
    replies = [
        f"嗯，{user_input}，这个问题挺有意思的。",
        f"作为{character.occupation}，我觉得{user_input}值得思考。",
        f"哈哈，{user_input}，让我想起了之前的经历。",
        f"{user_input}吗？我需要好好想想。",
        f"从{character.personality}的角度来看，{user_input}确实有道理。",
    ]
    
    # 根据性格调整回复风格
    if "开朗" in character.personality:
        prefix = "哈哈！"
    elif "内向" in character.personality:
        prefix = "嗯..."
    elif "幽默" in character.personality:
        prefix = "有意思！"
    else:
        prefix = ""
    
    return prefix + random.choice(replies)


# ==================== 静态文件服务 ====================

# 挂载头像目录为静态文件
app.mount("/avatars", StaticFiles(directory=AVATARS_DIR), name="avatars")
# 挂载图片提示词目录为静态文件
app.mount("/image-prompts", StaticFiles(directory=IMAGE_PROMPTS_DIR), name="image-prompts")


# ==================== API 接口 ====================

@app.get("/")
async def root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "web", "index.html"))


@app.get("/api/characters")
async def list_characters(include_dead: bool = False):
    """Get characters"""
    characters = get_characters()
    settings = get_settings()
    normalized = False
    for character in characters:
        if ensure_character_defaults(character, settings):
            normalized = True
    if normalized:
        save_characters(characters)
    if not include_dead:
        characters = [char for char in characters if char.is_alive]
    return {"success": True, "data": [char.model_dump() for char in characters]}


@app.get("/api/characters/{character_id}")
async def get_character(character_id: str):
    """Get character detail"""
    characters = get_characters()
    settings = get_settings()
    for index, char in enumerate(characters):
        if char.id == character_id:
            if ensure_character_defaults(char, settings):
                characters[index] = char
                save_characters(characters)
            return {"success": True, "data": char.model_dump()}
    raise HTTPException(status_code=404, detail="Character not found")


@app.get("/api/characters/{character_id}/history")
async def get_character_history(character_id: str):
    """Get character lifecycle history"""
    return {"success": True, "data": [item.model_dump() for item in get_character_histories(character_id)]}


@app.post("/api/characters/{character_id}/history/{history_id}/restore")
async def restore_character_from_history(character_id: str, history_id: str):
    """Restore character state from a history snapshot"""
    history_entry = get_history_entry(character_id, history_id)
    if not history_entry:
        raise HTTPException(status_code=404, detail="History entry not found")

    characters = get_characters()
    settings = get_settings()
    all_character_ids = {item.id for item in characters}

    for index, char in enumerate(characters):
        if char.id != character_id:
            continue
        restored = Character(**history_entry.snapshot)
        restored.id = character_id
        restored.updated_at = int(time.time() * 1000)
        normalize_parent_ids(restored, all_character_ids)
        notes = ensure_character_defaults(restored, settings)
        characters[index] = restored
        save_characters(characters)
        add_log(restored.name, "history_restore", f"已回溯到历史节点：{history_entry.event_type}")
        for note in notes:
            add_log(restored.name, "lifecycle", note)
        record_character_history(
            restored,
            "restore",
            f"已从历史记录恢复到 {history_entry.event_type}",
            {"source_history_id": history_entry.id}
        )
        return {"success": True, "data": restored.model_dump()}

    raise HTTPException(status_code=404, detail="Character not found")


@app.post("/api/characters")
async def create_character(request: CreateCharacterRequest):
    """Create character"""
    characters = get_characters()
    settings = get_settings()
    now_ms = int(time.time() * 1000)
    min_lifespan = min(settings.min_lifespan, settings.max_lifespan)
    max_lifespan = max(settings.min_lifespan, settings.max_lifespan)

    character = Character(
        name=request.name,
        age=request.age,
        gender=request.gender,
        occupation=request.occupation,
        personality=request.personality,
        signature=request.signature or "暂无签名",
        avatar_url=request.avatar_url,
        parent_ids=request.parent_ids or [],
        stage_entered_at=now_ms,
        max_lifespan=random.randint(min_lifespan, max_lifespan)
    )

    normalize_parent_ids(character, {item.id for item in characters})
    if character.avatar_url:
        character.last_avatar_change_time = now_ms
        character.avatar_change_history = [now_ms]

    notes = ensure_character_defaults(character, settings)
    characters.append(character)
    save_characters(characters)

    add_log(character.name, "create", f"character created: {character.get_age_display()} / {character.occupation}")
    for note in notes:
        add_log(character.name, "lifecycle", note)
    record_character_history(character, "create", "character created")

    return {"success": True, "data": character.model_dump()}


@app.delete("/api/characters/{character_id}")
async def delete_character(character_id: str):
    """删除角色"""
    characters = get_characters()
    
    char_to_delete = None
    for char in characters:
        if char.id == character_id:
            char_to_delete = char
            break
    
    if not char_to_delete:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    characters.remove(char_to_delete)
    save_characters(characters)
    
    add_log(char_to_delete.name, "删除", f"角色\"{char_to_delete.name}\"被删除")
    
    return {"success": True}


@app.put("/api/characters/{character_id}")
async def update_character(character_id: str, request: CreateCharacterRequest):
    """Update character"""
    characters = get_characters()
    settings = get_settings()

    for index, char in enumerate(characters):
        if char.id == character_id:
            avatar_changed = request.avatar_url and request.avatar_url != char.avatar_url
            char.name = request.name
            char.age = request.age
            char.gender = request.gender
            char.occupation = request.occupation
            char.personality = request.personality
            char.signature = request.signature or char.signature or "暂无签名"
            char.parent_ids = request.parent_ids or []
            # 更新 AI 设置（仅当请求中明确提供时）
            if request.llm_model_id is not None:
                char.llm_model_id = request.llm_model_id if request.llm_model_id else None
            if request.moment_frequency:
                char.moment_frequency = request.moment_frequency
            normalize_parent_ids(char, {item.id for item in characters})
            if request.avatar_url:
                char.avatar_url = request.avatar_url
            if avatar_changed:
                now_ms = int(time.time() * 1000)
                char.last_avatar_change_time = now_ms
                trim_avatar_change_history(char, now_ms)
                char.avatar_change_history.append(now_ms)
            notes = ensure_character_defaults(char, settings)
            char.updated_at = int(time.time() * 1000)
            characters[index] = char
            save_characters(characters)
            add_log(char.name, "update", f"character updated: {char.get_age_display()} / {char.occupation}")
            for note in notes:
                add_log(char.name, "lifecycle", note)
            record_character_history(char, "update", "character updated")
            return {"success": True, "data": char.model_dump()}

    raise HTTPException(status_code=404, detail="Character not found")


class UpdateCharacterAISettingsRequest(BaseModel):
    """Partial update for character AI settings"""
    llm_model_id: Optional[str] = None
    moment_frequency: Optional[str] = None


@app.patch("/api/characters/{character_id}/ai-settings")
async def update_character_ai_settings(character_id: str, request: UpdateCharacterAISettingsRequest):
    """Update character AI settings (partial update)"""
    characters = get_characters()

    for index, char in enumerate(characters):
        if char.id == character_id:
            if request.llm_model_id is not None:
                char.llm_model_id = request.llm_model_id if request.llm_model_id else None
            if request.moment_frequency is not None:
                char.moment_frequency = request.moment_frequency
            char.updated_at = int(time.time() * 1000)
            characters[index] = char
            save_characters(characters)
            add_log(char.name, "ai_settings", f"AI settings updated: llm={char.llm_model_id or 'default'}, freq={char.moment_frequency}")
            return {"success": True, "data": char.model_dump()}

    raise HTTPException(status_code=404, detail="Character not found")


@app.get("/api/messages/{conversation_id}")
async def get_conversation_messages(conversation_id: str):
    """获取会话消息"""
    messages = get_messages()
    conv_messages = [msg for msg in messages if msg.conversation_id == conversation_id]
    conv_messages.sort(key=lambda x: x.timestamp)
    return {"success": True, "data": [msg.model_dump() for msg in conv_messages]}


@app.post("/api/groups/private/sync")
async def sync_private_groups_api():
    """同步私人群聊：亲密度>=21自动建群，失效自动解散"""
    summary = sync_private_groups()
    return {"success": True, "data": summary}


@app.get("/api/groups/private")
async def list_private_groups():
    """获取私人群聊列表（仅供查看，不可发送）"""
    sync_private_groups()
    groups = [g for g in get_private_groups() if g.is_active]
    groups.sort(key=lambda item: item.created_at, reverse=True)
    return {"success": True, "data": [g.model_dump() for g in groups]}


@app.get("/api/groups/private/{group_id}/messages")
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


@app.post("/api/groups/private/{group_id}/simulate")
async def simulate_private_group_chat(group_id: str, request: SimulatePrivateGroupChatRequest):
    """模拟私人群聊对话（系统生成，用户只读）"""
    groups = get_private_groups()
    group = next((g for g in groups if g.id == group_id and g.is_active), None)
    if not group:
        raise HTTPException(status_code=404, detail="Private group not found")

    characters = get_characters()
    char_map = {c.id: c for c in characters}
    if any(mid not in char_map for mid in group.member_ids):
        raise HTTPException(status_code=400, detail="Group members not found")

    await append_private_group_exchange(group, request.topic)
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



@app.post("/api/messages/{conversation_id}/read")
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


@app.get("/api/moments")
async def list_moments(viewer_id: Optional[str] = None, limit: int = 50):
    """朋友圈时间线（按时间倒序，按亲密度过滤可见性）"""
    moments = get_moments()
    moments.sort(key=lambda m: m.timestamp, reverse=True)
    visible = [m for m in moments if can_view_moment(viewer_id, m)]
    return {"success": True, "data": [m.model_dump() for m in visible[:max(1, min(limit, 200))]]}


@app.post("/api/characters/{character_id}/moments/generate")
async def generate_character_moment(character_id: str, request: GenerateMomentRequest):
    """角色自动发布朋友圈（可选自动生成图片）"""
    characters = get_characters()
    character = next((c for c in characters if c.id == character_id), None)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    content = await generate_moment_content(character, request)
    image_url = None
    if request.with_image:
        plan = await generate_moment_image_plan(character, request, content or "")
        kind = plan.get("image_kind") or "scene"
        avatar_prompt = plan.get("image_prompt") or ""
        if kind not in ("selfie", "scene", "portrait"):
            kind = "scene"
        generated = await generate_avatar(GenerateAvatarRequest(
            avatar_prompt=avatar_prompt,
            style="realistic",
            image_kind=kind,
        ))
        if generated.get("success"):
            image_url = generated.get("data", {}).get("image_url")
    if request.with_image and not image_url:
        image_url = fallback_moment_image_url(f"{character.id}:{content[:80]}")

    moments = get_moments()
    post = MomentPost(
        author_id=character.id,
        author_name=character.name,
        content=content,
        image_url=image_url,
        trigger_type=request.trigger_type,
        mood=request.mood,
    )
    moments.append(post)
    save_moments(moments)
    add_log(character.name, "moment_post", f"发布朋友圈：{content[:20]}")
    store_memory(
        character_id=character.id,
        content=f"我发布了一条朋友圈：{content}",
        memory_type=MemoryType.EVENT,
        importance=0.65,
        related_entities=["朋友圈", request.trigger_type],
    )
    return {"success": True, "data": post.model_dump()}


@app.post("/api/users/moments")
async def create_user_moment(request: UserCreateMomentRequest):
    """用户发布朋友圈"""
    content = (request.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    image_url = request.image_url
    prompt_file = None
    if request.generate_image:
        hint = (request.image_prompt or content).strip()[:600]
        gen = await generate_avatar(GenerateAvatarRequest(
            avatar_prompt=f"Lifestyle / scene photograph for social feed, visual idea: {hint}. High quality, no text, no watermark.",
            style="realistic",
            image_kind="scene",
        ))
        if gen.get("success"):
            image_url = gen.get("data", {}).get("image_url")
            prompt_file = gen.get("data", {}).get("prompt_file")
    if not image_url:
        image_url = fallback_moment_image_url(f"user:{content[:120]}")
    moments = get_moments()
    post = MomentPost(
        author_id="user",
        author_name="用户",
        content=content,
        image_url=image_url,
        image_prompt_file=prompt_file,
        trigger_type="user",
        mood="active",
        visible_min_intimacy=0,
    )
    moments.append(post)
    save_moments(moments)
    add_log("用户", "moment_post", f"发布朋友圈：{content[:20]}")
    return {"success": True, "data": post.model_dump()}


@app.post("/api/moments/{moment_id}/like")
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


@app.post("/api/moments/{moment_id}/comment")
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
            # 每个动态每个角色只允许一条顶层评论
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
                commenter=commenter,
                moment_author=moment_author,
                moment_content=post.content,
                parent_comment=parent_comment
            )
        if parent_comment and f"@{parent_comment.author_name}" not in content:
            content = f"@{parent_comment.author_name} {content}"
        comment = MomentComment(
            moment_id=post.id,
            author_id=commenter.id,
            author_name=commenter.name,
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


@app.post("/api/moments/auto-interactions/run")
async def run_moment_auto_interactions_api(limit: int = 30):
    """手动触发朋友圈自动互动批处理"""
    summary = await run_moment_auto_interactions(limit=limit)
    settings = get_settings()
    settings.auto_moment_last_run_time = int(time.time() * 1000)
    save_settings(settings)
    return {"success": True, "data": summary}


@app.get("/api/tasks")
async def list_tasks(limit: int = 100):
    tasks = get_tasks()
    tasks.sort(key=lambda t: t.created_at, reverse=True)
    return {"success": True, "data": [item.model_dump() for item in tasks[:max(1, min(300, limit))]]}


@app.get("/api/tasks/{task_id}")
async def get_task_detail(task_id: str):
    tasks = get_tasks()
    task = next((item for item in tasks if item.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "data": task.model_dump()}


@app.post("/api/tasks")
async def create_task(request: CreateTaskRequest):
    tasks = get_tasks()
    task = TaskItem(
        title=request.title,
        description=request.description,
        task_type=request.task_type,
        reward=max(1.0, float(request.reward)),
        assignee_type=request.assignee_type,
        assignee_id=request.assignee_id,
        company_id=request.company_id,
    )
    tasks.append(task)
    save_tasks(tasks)
    add_log("用户", "task_create", f"创建任务：{task.title}")
    return {"success": True, "data": task.model_dump()}


@app.post("/api/tasks/{task_id}/assign")
async def assign_task(task_id: str, request: AssignTaskRequest):
    tasks = get_tasks()
    for i, task in enumerate(tasks):
        if task.id != task_id:
            continue
        task.assignee_type = request.assignee_type
        task.assignee_id = request.assignee_id
        task.company_id = request.company_id
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = int(time.time() * 1000)
        tasks[i] = task
        save_tasks(tasks)
        add_log("system", "task_assign", f"{task.title} -> {request.assignee_id}")
        return {"success": True, "data": task.model_dump()}
    raise HTTPException(status_code=404, detail="Task not found")


@app.post("/api/tasks/{task_id}/auto-take")
async def auto_take_task(task_id: str, request: AutoTakeTaskRequest):
    tasks = get_tasks()
    characters = get_characters()
    companies = get_companies()
    for i, task in enumerate(tasks):
        if task.id != task_id:
            continue
        if task.assignee_type == TaskAssigneeType.COMPANY and task.company_id:
            company = next((c for c in companies if c.id == task.company_id), None)
            if not company:
                raise HTTPException(status_code=400, detail="Company not found for task")
            alive_ids = [
                mid for mid in company.member_ids
                if any(ch.id == mid and ch.is_alive for ch in characters)
            ]
            if not alive_ids:
                raise HTTPException(status_code=400, detail="No alive company member")
            preferred = request.preferred_character_id
            assignee = None
            if preferred and preferred in alive_ids:
                assignee = next((ch for ch in characters if ch.id == preferred), None)
            if not assignee and company.legal_person_id in alive_ids:
                assignee = next((ch for ch in characters if ch.id == company.legal_person_id), None)
            if not assignee:
                assignee = next((ch for ch in characters if ch.id == alive_ids[0]), None)
            others = [mid for mid in alive_ids if mid != assignee.id]
            random.shuffle(others)
            task.collaborator_ids = others[:2]
            task.assignee_id = assignee.id
            task.status = TaskStatus.IN_PROGRESS
            task.updated_at = int(time.time() * 1000)
            tasks[i] = task
            save_tasks(tasks)
            add_log(assignee.name, "task_take", f"代表公司接取协作任务：{task.title}")
            return {"success": True, "data": task.model_dump()}
        assignee = choose_task_assignee(task, characters, request.preferred_character_id)
        if not assignee:
            raise HTTPException(status_code=400, detail="No alive character available")
        task.collaborator_ids = []
        task.assignee_type = TaskAssigneeType.PERSONAL
        task.assignee_id = assignee.id
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = int(time.time() * 1000)
        tasks[i] = task
        save_tasks(tasks)
        add_log(assignee.name, "task_take", f"自行接取任务：{task.title}")
        return {"success": True, "data": task.model_dump()}
    raise HTTPException(status_code=404, detail="Task not found")


@app.post("/api/tasks/{task_id}/submit")
async def submit_task(task_id: str, request: SubmitTaskRequest):
    tasks = get_tasks()
    for i, task in enumerate(tasks):
        if task.id != task_id:
            continue
        task.submitter_id = request.submitter_id
        task.execution_notes = request.execution_notes.strip()
        task.deliverable_text = request.deliverable_text.strip()
        task.deliverable_image_url = request.deliverable_image_url
        task.deliverable_code = request.deliverable_code
        task.status = TaskStatus.PENDING_REVIEW
        task.updated_at = int(time.time() * 1000)
        tasks[i] = task
        save_tasks(tasks)
        add_log("system", "task_submit", f"{task.title} 已提交审核")
        return {"success": True, "data": task.model_dump()}
    raise HTTPException(status_code=404, detail="Task not found")


async def _generate_task_image(task: TaskItem, assignee: Optional[Character]) -> Optional[str]:
    """为图像任务生成实际图片"""
    import aiohttp
    configs = get_api_configs()
    image_config = None
    for config in configs:
        if config.api_type == 'image' and config.is_enabled:
            image_config = config
            break
    if not image_config:
        return None
    
    prompt = f"{task.title}: {task.description}, high quality, professional, detailed"
    provider = image_config.provider.lower()
    # 优先使用任务指定的绘画模型，否则使用全局配置
    model = task.image_model_id if task.image_model_id else (image_config.selected_model or "dall-e-3")
    api_url = image_config.api_url
    # 使用LLM根据任务自动选择图片大小（只有3种选项）
    image_size = await llm_choose_image_size(prompt, f"任务：{task.title}")
    if not image_size:
        settings = get_settings()
        image_size = settings.default_image_size or "1024x1024"
    headers = {"Authorization": f"Bearer {image_config.api_key}", "Content-Type": "application/json"}
    
    # 根据服务商构造请求
    if 'stability' in provider or 'sd' in provider:
        width, height = parse_image_size(image_size)
        request_data = {
            "text_prompts": [{"text": prompt, "weight": 1}],
            "cfg_scale": 7,
            "height": height,
            "width": width,
            "steps": 30,
            "samples": 1
        }
    elif 'midjourney' in provider:
        ar = get_aspect_ratio(image_size)
        request_data = {
            "prompt": prompt,
            "aspect_ratio": ar
        }
    elif 'siliconflow' in provider or 'silicon' in provider:
        if '/chat/completions' in api_url:
            api_url = api_url.replace('/chat/completions', '/images/generations')
        elif not '/images' in api_url:
            api_url = api_url.rstrip('/') + '/v1/images/generations'
        request_data = {
            "model": model,
            "prompt": prompt,
            "image_size": image_size,
            "batch_size": 1,
            "num_inference_steps": 20,
            "guidance_scale": 7.5
        }
    elif 'modelscope' in provider or 'modelscope' in api_url.lower():
        if not api_url.endswith('/v1/images/generations'):
            api_url = api_url.rstrip('/') + '/v1/images/generations'
        request_data = {
            "model": model,
            "prompt": prompt,
            "image_size": image_size
        }
    else:
        if '/chat/completions' in api_url:
            api_url = api_url.replace('/chat/completions', '/images/generations')
        elif api_url.endswith('/v1') or api_url.endswith('/v1/'):
            api_url = api_url.rstrip('/') + '/images/generations'
        elif not '/images' in api_url:
            api_url = api_url.rstrip('/') + '/v1/images/generations'
        request_data = {"model": model, "prompt": prompt, "n": 1, "size": image_size, "quality": "standard", "response_format": "url"}
    
    try:
        # 检查是否为异步任务型API
        if is_async_image_provider(provider, image_config.api_url):
            success, image_url_or_error, _ = await call_async_image_api(
                api_url, headers, request_data, headers
            )
            if success and image_url_or_error:
                record_image_usage(image_config, "task_image_generation", task.assignee_id, success=True)
                add_log("系统", "任务图像", f"为任务《{task.title}》生成图片成功，尺寸: {image_size}")
                # 保存提示词为MD文档
                task_title = task.title
                save_image_prompt_md(prompt, f"任务图像：{task_title}", image_url_or_error, task_title)
                return image_url_or_error
            else:
                record_image_usage(image_config, "task_image_generation", task.assignee_id, success=False, error_message=image_url_or_error)
                return None
        else:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
                async with session.post(api_url, headers=headers, json=request_data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        image_url = None
                        if 'data' in result and len(result['data']) > 0:
                            image_url = result['data'][0].get('url') or result['data'][0].get('b64_json')
                        elif 'images' in result and len(result['images']) > 0:
                            image_url = result['images'][0].get('url') or result['images'][0].get('b64_json')
                        elif 'url' in result:
                            image_url = result['url']
                        elif 'image_url' in result:
                            image_url = result['image_url']
                        
                        if image_url:
                            record_image_usage(image_config, "task_image_generation", task.assignee_id, success=True)
                            add_log("系统", "任务图像", f"为任务《{task.title}》生成图片成功，尺寸: {image_size}")
                            # 保存提示词为MD文档
                            task_title = task.title
                            save_image_prompt_md(prompt, f"任务图像：{task_title}", image_url, task_title)
                            return image_url
                        else:
                            record_image_usage(image_config, "task_image_generation", task.assignee_id, success=False, error_message="无法解析图像响应")
                    else:
                        record_image_usage(image_config, "task_image_generation", task.assignee_id, success=False, error_message=f"HTTP {resp.status}")
    except Exception as e:
        record_image_usage(image_config, "task_image_generation", task.assignee_id, success=False, error_message=str(e))
        add_log("系统", "警告", f"任务图像生成失败：{str(e)}")
    return None


async def _generate_task_code(task: TaskItem, assignee: Optional[Character]) -> str:
    """为代码任务生成有意义的代码"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return f"# {task.title}\nprint('Task completed')"
    model_name = (assignee.llm_model_id if assignee and assignee.llm_model_id else (llm_config.selected_model or "gpt-3.5-turbo"))
    # 注入经验教训
    exp_note = ""
    if assignee:
        exp = assignee.experience_skills.get("code", {})
        if exp.get("lessons"):
            exp_note = "\n\n过往经验教训（请避免重复这些错误）：\n" + "\n".join(f"- {l}" for l in exp["lessons"][:5])
    prompt = (
        f"你是一名开发者，角色名：{assignee.name if assignee else '开发者'}，职业：{assignee.occupation if assignee else '程序员'}。\n"
        f"请完成以下代码任务：\n"
        f"标题：{task.title}\n"
        f"需求描述：{task.description}\n"
        f"{exp_note}\n"
        f"请写一段完整的、可运行的Python代码来实现这个任务。要求：\n"
        f"1. 代码要有清晰的注释\n"
        f"2. 要有合理的函数拆分\n"
        f"3. 要处理基本的异常情况\n"
        f"4. 不要只写框架，要有实际功能的实现\n"
        f"5. 直接输出代码，不要解释"
    )
    try:
        import aiohttp
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {"model": model_name, "messages": [{"role": "user", "content": prompt}], "max_tokens": 3000, "temperature": 0.3}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                    import re
                    code_match = re.search(r'```python\s*([\s\S]*?)```', content, re.DOTALL)
                    if code_match:
                        return code_match.group(1).strip()
                    code_match = re.search(r'```\s*([\s\S]*?)```', content, re.DOTALL)
                    if code_match:
                        return code_match.group(1).strip()
                    return content
    except Exception:
        pass
    return f"# {task.title}\nprint('Task completed')"


async def _generate_task_research(task: TaskItem, assignee: Optional[Character]) -> str:
    """为调研任务生成完整调研报告"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return f"{assignee.name if assignee else '角色'} 提交了调研分析报告"
    model_name = (assignee.llm_model_id if assignee and assignee.llm_model_id else (llm_config.selected_model or "gpt-3.5-turbo"))
    # 注入经验教训和公司经验
    exp_note = ""
    company_note = ""
    if assignee:
        exp = assignee.experience_skills.get("research", {})
        if exp.get("lessons"):
            exp_note = "\n\n你的过往经验教训：\n" + "\n".join(f"- {l}" for l in exp["lessons"][:5])
        if assignee.company_id:
            companies = get_companies()
            company = next((c for c in companies if c.id == assignee.company_id), None)
            if company and company.knowledge_base:
                related_kb = [e for e in company.knowledge_base if e.get("task_type") == "research"]
                if related_kb:
                    company_note = "\n\n公司知识库中的相关经验：\n" + "\n".join(
                        f"- 《{e.get('title', '未知')}》" for e in related_kb[:3]
                    )
    prompt = (
        f"你是{assignee.name if assignee else '调研员'}，{assignee.occupation if assignee else '调研员'}。\n"
        f"请撰写以下调研任务的完整报告：\n"
        f"标题：{task.title}\n"
        f"需求：{task.description}\n"
        f"{exp_note}{company_note}\n"
        f"报告要求包含：一、背景分析 二、现状调研 三、竞争/对比分析 四、风险评估 五、机会洞察 六、结论与建议\n"
        f"要求：数据翔实、分析有逻辑、建议可落地，不要空话套话。"
    )
    try:
        import aiohttp
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {"model": model_name, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4000, "temperature": 0.5}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=90)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                    return content
    except Exception:
        pass
    return f"{assignee.name if assignee else '角色'} 提交了调研分析报告"


async def _generate_task_text(task: TaskItem, assignee: Optional[Character]) -> str:
    """为文本/设计任务生成完整文案"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return f"{assignee.name if assignee else '角色'} 已完成任务：{task.title}"
    model_name = (assignee.llm_model_id if assignee and assignee.llm_model_id else (llm_config.selected_model or "gpt-3.5-turbo"))
    # 注入经验教训
    exp_note = ""
    if assignee:
        exp_type = "text" if task.task_type == TaskType.TEXT else "design"
        exp = assignee.experience_skills.get(exp_type, {})
        if exp.get("lessons"):
            exp_note = "\n\n你的过往经验教训：\n" + "\n".join(f"- {l}" for l in exp["lessons"][:5])
    prompt = (
        f"你是{assignee.name if assignee else '创作者'}，{assignee.occupation if assignee else '创作者'}。\n"
        f"请完成以下创作任务：\n"
        f"标题：{task.title}\n"
        f"需求描述：{task.description}\n"
        f"{exp_note}\n"
        f"要求：\n"
        f"1. 输出完整的、可直接使用的成品\n"
        f"2. 内容要有质量和深度，不要敷衍\n"
        f"3. 如果是文案要有吸引力，如果是设计要有创意\n"
        f"4. 直接输出成果内容，不要解释过程"
    )
    try:
        import aiohttp
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {"model": model_name, "messages": [{"role": "user", "content": prompt}], "max_tokens": 3000, "temperature": 0.7}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                    return content
    except Exception:
        pass
    return f"{assignee.name if assignee else '角色'} 已完成任务：{task.title}"


@app.post("/api/tasks/{task_id}/auto-complete")
async def auto_complete_task(task_id: str):
    tasks = get_tasks()
    characters = get_characters()
    for i, task in enumerate(tasks):
        if task.id != task_id:
            continue
        if not task.assignee_id:
            raise HTTPException(status_code=400, detail="Task has no assignee")
        assignee = next((c for c in characters if c.id == task.assignee_id), None)
        assignee_name = assignee.name if assignee else "角色"
        collab_names = []
        for cid in task.collaborator_ids or []:
            cm = next((c for c in characters if c.id == cid), None)
            if cm:
                collab_names.append(cm.name)
        
        # 使用经验生成更优质的交付物
        experience_note = ""
        if assignee:
            exp = assignee.experience_skills.get(task.task_type.value, {})
            if exp.get("lessons"):
                experience_note = "（参考过往经验：" + "; ".join(exp["lessons"][:3]) + "）"
        
        task.submitter_id = task.assignee_id
        if task.assignee_type == TaskAssigneeType.COMPANY and collab_names:
            task.execution_notes = f"公司协作：主执行 {assignee_name}，协作 {', '.join(collab_names)}，已整合提交审核{experience_note}"
        else:
            task.execution_notes = f"角色已自主完成任务并提交审核{experience_note}"
        
        # 根据任务类型生成真实成果
        if task.task_type == TaskType.IMAGE:
            # 图像任务：尝试调用图像生成 API
            task.deliverable_image_url = await _generate_task_image(task, assignee)
            task.deliverable_text = f"{assignee_name} 完成了图像创作：「{task.title}」{experience_note}"
        elif task.task_type == TaskType.CODE:
            # 代码任务：生成有意义的代码
            task.deliverable_code = await _generate_task_code(task, assignee)
            task.deliverable_text = f"{assignee_name} 完成了代码实现：「{task.title}」{experience_note}"
        elif task.task_type == TaskType.RESEARCH:
            # 调研任务：生成完整报告
            task.deliverable_text = await _generate_task_research(task, assignee)
        else:
            # 文本/设计任务：生成完整文案
            if task.assignee_type == TaskAssigneeType.COMPANY and collab_names:
                task.deliverable_text = f"{assignee_name} 牵头，与 {', '.join(collab_names)} 协作产出：\n\n{await _generate_task_text(task, assignee)}"
            else:
                task.deliverable_text = f"{assignee_name} 完成任务：「{task.title}」\n\n{await _generate_task_text(task, assignee)}"
        
        task.status = TaskStatus.PENDING_REVIEW
        task.updated_at = int(time.time() * 1000)
        tasks[i] = task
        save_tasks(tasks)
        add_log("system", "task_submit", f"{task.title} 由角色自主完成并提交审核")
        return {"success": True, "data": task.model_dump()}
    raise HTTPException(status_code=404, detail="Task not found")


@app.post("/api/tasks/{task_id}/review")
async def review_task(task_id: str, request: ReviewTaskRequest):
    tasks = get_tasks()
    characters = get_characters()
    companies = get_companies()
    for i, task in enumerate(tasks):
        if task.id != task_id:
            continue
        task.review_notes = request.review_notes.strip()
        task.review_round += 1
        task.review_history.append({
            "round": task.review_round,
            "approved": request.approved,
            "notes": task.review_notes,
            "score": max(0, min(100, int(request.score))),
            "checklist": request.checklist,
            "timestamp": int(time.time() * 1000),
        })
        task.updated_at = int(time.time() * 1000)
        
        # 统一反思机制：使用 apply_reflection_after_task 处理所有反思逻辑
        if request.approved:
            task.status = TaskStatus.COMPLETED
            task.completed_at = int(time.time() * 1000)
            
            # 发放奖励
            if task.assignee_type == TaskAssigneeType.PERSONAL and task.assignee_id:
                for idx, char in enumerate(characters):
                    if char.id == task.assignee_id:
                        char.money += task.reward
                        char.updated_at = int(time.time() * 1000)
                        characters[idx] = char
                        add_log(char.name, "task_reward", f"任务奖励 +{task.reward:.0f}")
                        break
                save_characters(characters)
            
            if task.assignee_type == TaskAssigneeType.COMPANY and task.company_id:
                cidx = next((idx for idx, comp in enumerate(companies) if comp.id == task.company_id), None)
                if cidx is not None:
                    comp = companies[cidx]
                    comp.funds += task.reward
                    comp.updated_at = int(time.time() * 1000)
                    companies[cidx] = comp
                    add_log(comp.name, "company_income", f"任务入账 +{task.reward:.0f}")
                    apply_company_task_bonus_distribution(companies, cidx, task, characters)
                save_companies(companies)
                save_characters(characters)
        else:
            task.status = TaskStatus.IN_PROGRESS if task.review_round < 3 else TaskStatus.FAILED
        
        tasks[i] = task
        save_tasks(tasks)
        
        # 统一反思处理：更新经验库、记忆、公司知识共享
        await apply_reflection_after_task(task, request.approved, task.review_notes)
        
        return {"success": True, "data": task.model_dump()}
    raise HTTPException(status_code=404, detail="Task not found")


@app.get("/api/companies")
async def list_companies():
    companies = get_companies()
    return {"success": True, "data": [item.model_dump() for item in companies]}


@app.get("/api/companies/{company_id}")
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


@app.post("/api/companies")
async def create_company(request: CreateCompanyRequest):
    characters = get_characters()
    legal_person = next((c for c in characters if c.id == request.legal_person_id), None)
    if not legal_person:
        raise HTTPException(status_code=404, detail="法人角色不存在")
    if legal_person.money < 1000:
        raise HTTPException(status_code=400, detail="法人资金不足（至少需要1000元）")
    companies = get_companies()
    # 从法人资金中扣除
    legal_person.money -= 1000
    legal_person.company_id = None  # 会被下面的设置覆盖
    new_company = Company(
        name=request.name,
        legal_person_id=request.legal_person_id,
        member_ids=[request.legal_person_id] + request.member_ids,
        funds=500.0,
        location_name=legal_person.current_location_id or "办公室",
    )
    legal_person.company_id = new_company.id
    # 更新所有成员的公司ID
    for member_id in request.member_ids:
        member = next((c for c in characters if c.id == member_id), None)
        if member:
            member.company_id = new_company.id
    companies.append(new_company)
    save_companies(companies)
    save_characters(characters)
    add_log(legal_person.name, "创建公司", f"成功创建公司「{request.name}」，投入500元启动资金")
    for mid in request.member_ids:
        m = next((c for c in characters if c.id == mid), None)
        if m:
            add_log(m.name, "加入公司", f"成为 {request.name} 的创始成员")
    return {"success": True, "data": new_company.model_dump()}


@app.post("/api/companies/{company_id}/recruit")
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
    add_log(company.name, "招募", f"成功招募 {target.name} 加入公司")
    return {"success": True, "data": company.model_dump()}


@app.post("/api/companies/ai-manage")
async def ai_manage_companies():
    """AI 自主管理公司：有经济压力且有钱的角色可能创建公司，公司可能招募成员"""
    characters = get_characters()
    companies = get_companies()
    alive_chars = [c for c in characters if c.is_alive]
    
    # 1) 没有公司的角色且资金充足时，小概率创建公司
    chars_without_company = [c for c in alive_chars if not c.company_id and c.money >= 1500]
    if chars_without_company and random.random() < 0.15:
        founder = random.choice(chars_without_company)
        # 根据职业生成公司名
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
        add_log(founder.name, "AI创业", f"自主创建公司「{company_name}」，投入500元启动资金")
    
    # 2) 公司法人小概率招募其他角色
    for company in companies:
        if random.random() < 0.1:
            founder = next((c for c in alive_chars if c.id == company.legal_person_id), None)
            if founder and founder.money >= 500:
                # 从没公司的角色中挑选候选人
                candidates = [c for c in alive_chars if c.id not in company.member_ids and not c.company_id]
                if candidates:
                    # 根据职业匹配度排序
                    candidates.sort(key=lambda c: random.random(), reverse=True)
                    recruit = candidates[0]
                    recruit.company_id = company.id
                    company.member_ids.append(recruit.id)
                    save_companies(companies)
                    save_characters(characters)
                    add_log(company.name, "AI招募", f"自主招募 {recruit.name} 加入公司")
    
    return {"success": True}
    if not legal_person:
        raise HTTPException(status_code=404, detail="Legal person not found")
    companies = get_companies()
    member_ids = list(dict.fromkeys([request.legal_person_id] + request.member_ids))
    
    # 为公司自动生成地图位置
    meta = get_active_world_map()
    company_x = round(random.uniform(15, 85), 2)
    company_y = round(random.uniform(15, 85), 2)
    # 尝试放在已有的"公司"bind附近，或者随机生成地标
    company_location_name = f"{request.name}总部"
    
    company = Company(
        name=request.name, 
        legal_person_id=request.legal_person_id, 
        member_ids=member_ids,
        location_name=company_location_name,
        location_x=company_x,
        location_y=company_y,
    )
    companies.append(company)
    
    # 将公司作为地标添加到地图中
    landmark = {
        "name": company_location_name,
        "x": company_x,
        "y": company_y,
        "bind": WORLD_COMPANY_BIND,
        "type": "company",
        "company_id": company.id,
    }
    if "landmarks" not in meta:
        meta["landmarks"] = []
    meta["landmarks"].append(landmark)
    save_persisted_world_map(meta)
    
    save_companies(companies)
    for idx, char in enumerate(characters):
        if char.id in member_ids:
            char.company_id = company.id
            char.updated_at = int(time.time() * 1000)
            characters[idx] = char
    save_characters(characters)
    add_log(company.name, "company_create", f"公司创建，成员数 {len(member_ids)}，位置：({company_x}, {company_y})")
    return {"success": True, "data": company.model_dump()}


@app.post("/api/companies/{company_id}/members")
async def add_company_member(company_id: str, request: AddCompanyMemberRequest):
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


@app.post("/api/economy/distribute-bonus")
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
            add_log(char.name, "bonus", f"{request.reason} +{bonus:.0f}")
        save_companies(companies)
        save_characters(characters)
        return {"success": True, "data": {"distributed": total, "remaining_funds": company.funds}}
    raise HTTPException(status_code=404, detail="Company not found")


@app.post("/api/economy/daily-settle")
async def run_daily_settlement(days: int = 1):
    days = max(1, min(30, int(days)))
    run_daily_economy(days * MILLISECONDS_PER_DAY)
    return {"success": True, "data": {"days": days}}


@app.get("/api/economy/overview")
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


@app.get("/api/economy/logs")
async def list_economy_logs(limit: int = 100):
    logs = get_economy_logs()
    logs.sort(key=lambda x: x.timestamp, reverse=True)
    return {"success": True, "data": [item.model_dump() for item in logs[:max(1, min(limit, 500))]]}


@app.get("/api/schedules")
async def list_daily_schedules(day_index: Optional[int] = None):
    settings = get_settings()
    query_day = day_index if day_index is not None else int(settings.world_elapsed_ms // MILLISECONDS_PER_DAY)
    schedules = [item for item in get_schedules() if item.day_index == query_day]
    return {"success": True, "data": [item.model_dump() for item in schedules]}


@app.get("/api/map/meta")
async def get_world_map_meta():
    """虚拟城市地图：道路、地标、水系（与角色活动地点绑定）；来自持久化世界或默认模板。"""
    return {"success": True, "data": get_active_world_map()}


@app.get("/api/map/landmarks/{landmark_name}/detail")
async def get_landmark_detail(landmark_name: str):
    """获取地标详情及在此地的角色"""
    meta = get_active_world_map()
    landmark = None
    for lm in meta.get("landmarks") or []:
        if lm.get("name") == landmark_name or lm.get("bind") == landmark_name:
            landmark = lm
            break
    if not landmark:
        raise HTTPException(status_code=404, detail="地标未找到")

    # 获取在此地的角色
    settings = get_settings()
    drift_bucket = int(settings.world_elapsed_ms // WORLD_LOCATION_SLOT_MS)
    characters = [c for c in get_characters() if c.is_alive]
    characters_here = []
    for char in characters:
        loc = char.current_location_id or "城市"
        if loc == landmark_name or loc == landmark.get("bind"):
            x, y = resolve_location_coordinates(loc, char.id, drift_bucket=drift_bucket)
            characters_here.append({
                "id": char.id,
                "name": char.name,
                "occupation": char.occupation,
                "x": round(x, 2),
                "y": round(y, 2),
            })

    return {
        "success": True,
        "data": {
            "landmark": landmark,
            "characters_here": characters_here,
        }
    }


@app.get("/api/world/info")
async def world_info():
    """世界是否已持久化、城市名与氛围描述。"""
    persisted = load_persisted_world_map() is not None
    m = get_active_world_map()
    return {
        "success": True,
        "data": {
            "persisted": persisted,
            "city_name": m.get("city_name"),
            "lore": m.get("lore") or "",
        },
    }


class RegenerateWorldRequest(BaseModel):
    prompt: str = ""


@app.post("/api/world/regenerate")
async def regenerate_world(req: RegenerateWorldRequest):
    """按用户自然语言重塑城市（需可用 LLM）。会覆盖 world_map.json。"""
    prompt = (req.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    meta = await llm_generate_world_map(prompt)
    if not meta:
        raise HTTPException(status_code=400, detail="LLM 不可用或生成失败，请检查语言模型配置")
    save_persisted_world_map(meta)
    add_log("系统", "world_regen", f"城市已重塑：{meta.get('city_name', '')}")
    return {"success": True, "data": meta}


@app.get("/api/map/world")
async def get_world_map():
    settings = get_settings()
    drift_bucket = int(settings.world_elapsed_ms // WORLD_LOCATION_SLOT_MS)
    characters = [item for item in get_characters() if item.is_alive]
    points = []
    for char in characters:
        location = char.current_location_id or get_character_residence(char.id)
        x, y = resolve_location_coordinates(location, char.id, drift_bucket=drift_bucket)
        points.append({
            "character_id": char.id,
            "name": char.name,
            "location_name": location,
            "x": x,
            "y": y,
            "company_id": char.company_id,
            "money": char.money,
        })
    
    # 获取公司位置信息
    companies = get_companies()
    company_locations = []
    for comp in companies:
        if comp.location_name:
            company_locations.append({
                "company_id": comp.id,
                "name": comp.name,
                "location_name": comp.location_name,
                "x": comp.location_x,
                "y": comp.location_y,
                "member_count": len(comp.member_ids),
            })
    
    return {"success": True, "data": {"characters": points, "companies": company_locations}}


@app.get("/api/map/characters/{character_id}/history")
async def get_character_location_history(character_id: str, limit: int = 100):
    return {"success": True, "data": [item.model_dump() for item in get_location_history(character_id=character_id, limit=limit)]}


@app.post("/api/map/encounters/run")
async def run_encounters(window_minutes: int = 5):
    summary = detect_encounters(window_minutes=window_minutes)
    await process_encounter_followups(summary.get("items") or [])
    return {"success": True, "data": summary}


@app.post("/api/heartbeat/run")
async def run_heartbeat_api(limit_characters: int = 30):
    """手动触发一次心跳批处理"""
    summary = await run_heartbeat_tick(limit_characters=max(1, min(200, int(limit_characters))))
    settings = get_settings()
    settings.heartbeat_last_run_time = int(time.time() * 1000)
    save_settings(settings)
    return {"success": True, "data": summary}


@app.post("/api/schedules/generate")
async def generate_daily_schedules():
    settings = get_settings()
    day_index = int(settings.world_elapsed_ms // MILLISECONDS_PER_DAY)
    characters = get_characters()
    schedules = [item for item in get_schedules() if item.day_index != day_index]
    for char in characters:
        if not char.is_alive:
            continue
        schedules.append(generate_schedule_for_character(char, day_index))
    save_schedules(schedules)
    return {"success": True, "data": {"day_index": day_index, "count": len(schedules)}}


@app.get("/api/schedules/{character_id}")
async def get_character_schedule(character_id: str, day_index: Optional[int] = None):
    settings = get_settings()
    query_day = day_index if day_index is not None else int(settings.world_elapsed_ms // MILLISECONDS_PER_DAY)
    schedules = get_schedules()
    target = [item for item in schedules if item.character_id == character_id and item.day_index == query_day]
    if target:
        return {"success": True, "data": target[0].model_dump()}
    characters = get_characters()
    char = next((c for c in characters if c.id == character_id), None)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    generated = generate_schedule_for_character(char, query_day)
    schedules.append(generated)
    save_schedules(schedules)
    return {"success": True, "data": generated.model_dump()}


@app.get("/api/relationships/{from_id}/{to_id}")
async def get_relationship_snapshot(from_id: str, to_id: str):
    intimacy = get_relationship_intimacy(from_id, to_id)
    if intimacy <= 20:
        state = "陌生人"
    elif intimacy <= 40:
        state = "认识"
    elif intimacy <= 60:
        state = "熟人"
    elif intimacy <= 80:
        state = "好友"
    else:
        state = "密友"
    return {"success": True, "data": {"from_id": from_id, "to_id": to_id, "intimacy": intimacy, "state": state}}


@app.post("/api/relationships/interact")
async def relationship_interact(request: RelationshipInteractRequest):
    new_intimacy = apply_relationship_interaction(request.from_id, request.to_id, request.action)
    sync_private_groups()
    return {"success": True, "data": {"intimacy": new_intimacy}}


@app.post("/api/relationships/maintenance")
async def run_relationship_maintenance():
    decayed = apply_inactivity_decay()
    sync_summary = sync_private_groups()
    return {"success": True, "data": {"decayed_pairs": decayed, "groups": sync_summary}}

@app.post("/api/messages/send")
async def send_message(request: SendMessageRequest):
    """发送消息并获取 AI 回复"""
    messages = get_messages()
    characters = get_characters()
    
    # 查找角色
    character = None
    for char in characters:
        if char.id == request.conversation_id:
            character = char
            break
    
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 保存用户消息
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
    
    # 生成 AI 回复（异步调用）
    reply_prompt = user_text if user_text else ("用户发送了图片消息" if request.message_type == "image" else "用户发送了语音消息")
    reply_content = await generate_ai_reply(character, reply_prompt)
    
    # 保存 AI 回复
    ai_message = ChatMessage(
        conversation_id=request.conversation_id,
        sender_id=character.id,
        content=reply_content,
        is_from_user=False
    )
    messages.append(ai_message)
    save_messages(messages)
    
    # 关键：持久化角色状态（如通过 Exec 协议产生的新意图队列）
    save_characters(characters)
    
    # 记录日志
    add_log(character.name, "对话", f"回复：\"{reply_content[:30]}...\"")

    return {
        "success": True,
        "data": {
            "user_message": user_message.model_dump(),
            "ai_message": ai_message.model_dump()
        }
    }


@app.delete("/api/messages/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """清空会话消息"""
    messages = get_messages()
    messages = [msg for msg in messages if msg.conversation_id != conversation_id]
    save_messages(messages)
    return {"success": True}


@app.get("/api/logs")
async def get_recent_logs(limit: int = 50):
    """获取最近日志"""
    logs = get_logs()
    return {"success": True, "data": logs[:limit]}


@app.get("/api/logs/character/{character_id}")
async def get_character_logs(character_id: str, limit: int = 100):
    """获取角色相关日志"""
    characters = get_characters()
    char = next((c for c in characters if c.id == character_id), None)
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")
    logs = get_logs()
    char_logs = [log for log in logs if char.name in log.character_name or log.character_name == "系统"]
    char_logs.sort(key=lambda x: x.timestamp, reverse=True)
    return {"success": True, "data": char_logs[:limit]}


@app.get("/api/characters/{character_id}/life-experience")
async def get_character_life_experience(character_id: str):
    """获取角色人生经历摘要（经验技能库、任务历史、反思汇总等）"""
    characters = get_characters()
    char = next((c for c in characters if c.id == character_id), None)
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 经验技能库
    exp_skills = char.experience_skills or {}
    exp_summary = []
    for task_type, data in exp_skills.items():
        count = data.get("count", 0)
        success = data.get("success_count", 0)
        rate = (success / count * 100) if count > 0 else 0
        exp_summary.append({
            "task_type": task_type,
            "count": count,
            "success_count": success,
            "success_rate": round(rate, 1),
            "lessons": data.get("lessons", [])[:5],
            "skill_improvements": data.get("skill_improvements", {}),
        })
    
    # 任务历史
    tasks = get_tasks()
    char_tasks = [t for t in tasks if t.assignee_id == character_id]
    task_history = []
    for t in sorted(char_tasks, key=lambda x: x.updated_at, reverse=True)[:20]:
        task_history.append({
            "id": t.id,
            "title": t.title,
            "type": t.task_type.value,
            "status": t.status.value,
            "reward": t.reward,
            "reflection_summary": (t.reflection.lessons_learned[:3] if t.reflection else []),
            "completed_at": t.completed_at,
        })
    
    # 记忆中的反思
    memories = get_character_memories(character_id)
    reflections = [m for m in memories if m.memory_type == MemoryType.REFLECTION][:10]
    reflection_summary = [{
        "content": m.content[:100],
        "importance": m.importance,
        "timestamp": m.timestamp,
    } for m in reflections]
    
    # 关系网络
    relationships = get_relationships()
    my_relations = [r for r in relationships if r.from_id == character_id or r.to_id == character_id]
    relation_summary = []
    for r in sorted(my_relations, key=lambda x: x.intimacy, reverse=True)[:10]:
        other_id = r.to_id if r.from_id == character_id else r.from_id
        other_char = next((c for c in characters if c.id == other_id), None)
        if other_char:
            relation_summary.append({
                "name": other_char.name,
                "intimacy": round(r.intimacy, 1),
                "status": r.get_status,
            })
    
    return {
        "success": True,
        "data": {
            "character_id": character_id,
            "name": char.name,
            "age": char.age,
            "occupation": char.occupation,
            "experience_skills": exp_summary,
            "task_history": task_history,
            "reflections": reflection_summary,
            "relationships": relation_summary,
            "total_tasks": len(char_tasks),
            "completed_tasks": len([t for t in char_tasks if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in char_tasks if t.status == TaskStatus.FAILED]),
        }
    }


@app.delete("/api/logs")
async def clear_logs():
    """清空日志"""
    save_logs([])
    return {"success": True}


# ==================== 记忆系统接口 ====================

@app.get("/api/memories/{character_id}")
async def get_character_memories_api(character_id: str, limit: int = 20):
    """获取角色记忆列表"""
    memories = get_character_memories(character_id)
    # 按时间倒序排列
    memories.sort(key=lambda x: x.timestamp, reverse=True)
    return {"success": True, "data": memories[:limit]}


@app.post("/api/memories/recall")
async def recall_memories_api(request: RecallMemoriesRequest):
    """召回相关记忆"""
    memories = await recall_memories(
        character_id=request.character_id,
        query=request.query,
        top_k=request.top_k or 5
    )
    return {"success": True, "data": memories}


@app.post("/api/memories")
async def create_memory(request: CreateMemoryRequest):
    """手动创建记忆"""
    # 将字符串转换为 MemoryType 枚举
    try:
        mem_type = MemoryType(request.memory_type)
    except ValueError:
        mem_type = MemoryType.EVENT  # 默认值
    
    memory = store_memory(
        character_id=request.character_id,
        content=request.content,
        memory_type=mem_type,
        importance=request.importance,
        related_entities=request.related_entities
    )
    return {"success": True, "data": memory.model_dump()}


@app.delete("/api/memories/character/{character_id}")
async def clear_character_memories(character_id: str):
    """清空角色所有记忆"""
    memories = get_memories()
    original_count = len(memories)
    memories = [m for m in memories if m.character_id != character_id]
    save_memories(memories)
    deleted_count = original_count - len(memories)
    add_log("系统", "记忆", f"已清空角色 {character_id} 的 {deleted_count} 条记忆")
    return {"success": True, "message": f"已删除 {deleted_count} 条记忆"}


class RecallMemoriesRequest(BaseModel):
    character_id: str
    query: str
    top_k: Optional[int] = 5


class CreateMemoryRequest(BaseModel):
    character_id: str
    content: str
    memory_type: str = "event"  # 接受字符串，后续转换为枚举
    importance: float = 0.5
    related_entities: Optional[List[str]] = None


@app.get("/api/settings")
async def get_app_settings():
    """Get app settings"""
    settings = get_settings()
    return {"success": True, "data": settings.model_dump()}


@app.put("/api/settings")
async def update_app_settings(settings_data: Dict[str, Any]):
    """Update app settings"""
    current_settings = get_settings()
    merged = current_settings.model_dump()
    merged.update({key: value for key, value in settings_data.items() if value is not None})
    merged["time_speed"] = max(1, min(30, int(merged.get("time_speed", current_settings.time_speed))))
    merged["enable_auto_moment_interactions"] = bool(
        merged.get("enable_auto_moment_interactions", current_settings.enable_auto_moment_interactions)
    )
    merged["auto_moment_interval_minutes"] = max(
        1, min(120, int(merged.get("auto_moment_interval_minutes", current_settings.auto_moment_interval_minutes)))
    )
    merged["enable_heartbeat"] = bool(merged.get("enable_heartbeat", current_settings.enable_heartbeat))
    merged["heartbeat_interval_seconds"] = max(
        10, min(600, int(merged.get("heartbeat_interval_seconds", current_settings.heartbeat_interval_seconds)))
    )
    merged["min_lifespan"] = int(merged.get("min_lifespan", current_settings.min_lifespan))
    merged["max_lifespan"] = int(merged.get("max_lifespan", current_settings.max_lifespan))
    if merged["min_lifespan"] > merged["max_lifespan"]:
        merged["min_lifespan"], merged["max_lifespan"] = merged["max_lifespan"], merged["min_lifespan"]
    settings = Settings(**merged)
    save_settings(settings)
    add_log("system", "settings", f"time speed={settings.time_speed}x, lifespan={settings.min_lifespan}-{settings.max_lifespan}")
    return {"success": True, "data": settings.model_dump()}


@app.get("/api/api-configs")
async def list_api_configs():
    """获取所有 API 配置"""
    configs = get_api_configs()
    # 不返回 api_key 以保护敏感信息
    result = []
    for config in configs:
        config_dict = config.model_dump()
        config_dict['api_key'] = '***' + config.api_key[-4:] if len(config.api_key) > 4 else '***'
        result.append(config_dict)
    return {"success": True, "data": result}


@app.get("/api/api-configs/{config_id}")
async def get_api_config(config_id: str):
    """获取 API 配置详情"""
    config = get_api_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return {"success": True, "data": config.model_dump()}


@app.post("/api/api-configs")
async def create_api_config(request: CreateApiConfigRequest):
    """创建 API 配置"""
    configs = get_api_configs()

    config = ApiConfig(
        name=request.name,
        api_type=request.api_type,
        provider=request.provider,
        api_url=request.api_url,
        api_key=request.api_key,
        models=request.models,
        selected_model=request.selected_model,
        is_enabled=request.is_enabled,
        priority=request.priority
    )

    configs.append(config)
    save_api_configs(configs)

    add_log("系统", "API 配置", f"创建 API 配置\"{config.name}\" ({config.provider})")

    return {"success": True, "data": config.model_dump()}


@app.put("/api/api-configs/{config_id}")
async def update_api_config(config_id: str, request: CreateApiConfigRequest):
    """更新 API 配置"""
    configs = get_api_configs()

    for i, config in enumerate(configs):
        if config.id == config_id:
            config.name = request.name
            config.api_type = request.api_type
            config.provider = request.provider
            config.api_url = request.api_url
            # 只有在提供了新密钥时才更新（排除空值和脱敏格式）
            if request.api_key and not request.api_key.startswith('***'):
                config.api_key = request.api_key
            # 如果密钥为空或脱敏格式，保留原有密钥
            config.models = request.models
            config.selected_model = request.selected_model
            config.is_enabled = request.is_enabled
            config.priority = request.priority
            config.updated_at = int(time.time() * 1000)
            configs[i] = config
            save_api_configs(configs)

            add_log("系统", "API 配置", f"更新 API 配置\"{config.name}\"")

            return {"success": True, "data": config.model_dump()}

    raise HTTPException(status_code=404, detail="配置不存在")


@app.delete("/api/api-configs/{config_id}")
async def delete_api_config(config_id: str):
    """删除 API 配置"""
    configs = get_api_configs()

    config_to_delete = None
    for config in configs:
        if config.id == config_id:
            config_to_delete = config
            break

    if not config_to_delete:
        raise HTTPException(status_code=404, detail="配置不存在")

    configs.remove(config_to_delete)
    save_api_configs(configs)

    add_log("系统", "API 配置", f"删除 API 配置\"{config_to_delete.name}\"")

    return {"success": True}


@app.post("/api/api-configs/{config_id}/toggle")
async def toggle_api_config(config_id: str):
    """切换 API 配置启用状态"""
    configs = get_api_configs()

    for i, config in enumerate(configs):
        if config.id == config_id:
            config.is_enabled = not config.is_enabled
            config.updated_at = int(time.time() * 1000)
            configs[i] = config
            save_api_configs(configs)

            status = "启用" if config.is_enabled else "禁用"
            add_log("系统", "API 配置", f"{status} API 配置\"{config.name}\"")

            return {"success": True, "data": config.model_dump()}

    raise HTTPException(status_code=404, detail="配置不存在")


@app.post("/api/characters/{character_id}/maybe-refresh-avatar")
async def maybe_refresh_avatar(character_id: str, request: MaybeRefreshAvatarRequest):
    """根据心情/事件尝试刷新头像（含频率限制）"""
    characters = get_characters()
    for index, char in enumerate(characters):
        if char.id != character_id:
            continue

        now_ms = int(time.time() * 1000)
        if not request.forced and not can_refresh_avatar(char, now_ms):
            return {
                "success": False,
                "message": "头像刷新频率已达每周上限",
            }

        success, message = await refresh_character_avatar_for_stage(char, forced=True)
        if success:
            char.updated_at = now_ms
            trim_avatar_change_history(char, now_ms)
            char.avatar_change_history.append(now_ms)
            characters[index] = char
            save_characters(characters)
            reason = request.reason or "心情变化/重大事件"
            add_log(char.name, "avatar_refresh", f"{reason}，{message}")
            record_character_history(char, "avatar_refresh", f"{reason}触发头像更新")
        return {"success": success, "message": message}

    raise HTTPException(status_code=404, detail="Character not found")


@app.post("/api/api-configs/test")
async def test_api_config(request: TestApiConfigRequest):
    """测试 API 配置是否可用"""
    import aiohttp
    
    try:
        headers = {
            "Authorization": f"Bearer {request.api_key}",
            "Content-Type": "application/json"
        }
        
        # 根据 API 类型构造不同的测试请求
        if request.api_type == 'llm':
            test_data = {
                "model": request.selected_model or "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
        elif request.api_type == 'image':
            test_data = {
                "prompt": "test",
                "n": 1,
                "size": "256x256"
            }
        elif request.api_type == 'vector':
            test_data = {
                "model": request.selected_model or "text-embedding-ada-002",
                "input": ["test"]
            }
        elif request.api_type == 'rerank':
            test_data = {
                "query": "test",
                "documents": ["test document"],
                "top_n": 1
            }
        else:
            return {"success": False, "error": f"不支持的 API 类型：{request.api_type}"}
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(request.api_url, headers=headers, json=test_data) as response:
                # 尝试解析响应
                try:
                    result = await response.json()
                except Exception as e:
                    # 如果不是 JSON，获取文本
                    text = await response.text()
                    result = {"raw_response": text, "parse_error": str(e)}
                
                if response.status == 200:
                    return {
                        "success": True,
                        "message": "API 配置测试成功",
                        "data": {
                            "status": "ok",
                            "response_time": response.headers.get('X-Request-Id', 'N/A'),
                            "http_status": response.status
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API 测试失败 (HTTP {response.status})",
                        "details": result
                    }
    except aiohttp.ClientError as e:
        return {
            "success": False,
            "error": f"网络错误：{type(e).__name__}",
            "details": {
                "type": "network_error",
                "url": request.api_url,
                "message": str(e)
            }
        }
    except Exception as e:
        # 返回详细的异常信息
        import traceback
        return {
            "success": False,
            "error": f"测试失败：{type(e).__name__}",
            "details": {
                "type": "unknown_error",
                "exception": str(e),
                "traceback": traceback.format_exc()
            }
        }


@app.get("/api/api-configs/models")
async def get_available_models(
    api_url: str,
    api_key: str,
    api_type: str = "llm"
):
    """获取平台可用的所有模型列表"""
    import aiohttp
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 构造获取模型列表的 URL
        models_url = api_url.rsplit('/', 1)[0] + '/models' if '/chat/' in api_url or '/images/' in api_url or '/embeddings/' in api_url else api_url
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(models_url, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    models = result.get('data', [])
                    
                    # 根据 API 类型过滤模型
                    filtered_models = []
                    for model in models:
                        model_id = model.get('id', '') if isinstance(model, dict) else str(model)
                        
                        # 根据类型过滤
                        if api_type == 'llm':
                            if any(kw in model_id.lower() for kw in ['gpt', 'chat', 'completion', 'text']):
                                filtered_models.append(model)
                        elif api_type == 'image':
                            if any(kw in model_id.lower() for kw in ['image', 'dall', 'stable', 'diffusion']):
                                filtered_models.append(model)
                        elif api_type == 'vector':
                            if any(kw in model_id.lower() for kw in ['embedding', 'vector', 'ada']):
                                filtered_models.append(model)
                        else:
                            filtered_models.append(model)
                    
                    return {
                        "success": True,
                        "data": filtered_models,
                        "total": len(filtered_models)
                    }
                else:
                    # 如果无法获取模型列表，返回预设的常用模型
                    preset_models = get_preset_models(api_type)
                    return {
                        "success": True,
                        "data": preset_models,
                        "total": len(preset_models),
                        "note": "无法从 API 获取模型列表，返回预设模型"
                    }
    except Exception as e:
        # 返回预设模型
        preset_models = get_preset_models(api_type)
        return {
            "success": True,
            "data": preset_models,
            "total": len(preset_models),
            "note": f"获取失败：{str(e)}，返回预设模型"
        }


def get_preset_models(api_type: str) -> List[Dict]:
    """获取预设的常用模型列表"""
    presets = {
        'llm': [
            {'id': 'gpt-4', 'name': 'GPT-4'},
            {'id': 'gpt-4-turbo', 'name': 'GPT-4 Turbo'},
            {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo'},
            {'id': 'claude-3-opus', 'name': 'Claude 3 Opus'},
            {'id': 'claude-3-sonnet', 'name': 'Claude 3 Sonnet'},
        ],
        'image': [
            {'id': 'dall-e-3', 'name': 'DALL-E 3'},
            {'id': 'dall-e-2', 'name': 'DALL-E 2'},
            {'id': 'stable-diffusion-xl', 'name': 'Stable Diffusion XL'},
            {'id': 'midjourney', 'name': 'Midjourney'},
        ],
        'vector': [
            {'id': 'text-embedding-ada-002', 'name': 'Text Embedding Ada-002'},
            {'id': 'text-embedding-3-small', 'name': 'Text Embedding 3 Small'},
            {'id': 'text-embedding-3-large', 'name': 'Text Embedding 3 Large'},
        ],
        'rerank': [
            {'id': 'reranker-v1', 'name': 'Reranker V1'},
        ]
    }


@app.post("/api/characters/{character_id}/maybe-update-signature")
async def maybe_update_signature(character_id: str, request: MaybeUpdateSignatureRequest):
    """根据当前状态和近期经历自动生成新签名（含频率限制）"""
    characters = get_characters()
    for index, char in enumerate(characters):
        if char.id != character_id:
            continue

        now_ms = int(time.time() * 1000)
        if not can_refresh_signature(char, now_ms):
            return {
                "success": False,
                "message": "签名更新频率已达每周上限",
            }

        # 使用近期记忆构建上下文
        recent_memories = get_character_memories(character_id, limit=10)
        memory_context = build_memory_context(recent_memories, max_length=400)

        new_signature = await generate_new_signature(char, memory_context)
        if not new_signature:
            return {
                "success": False,
                "message": "签名生成失败，请检查 LLM 配置",
            }

        char.signature = new_signature
        char.last_signature_change_time = now_ms
        trim_signature_change_history(char, now_ms)
        char.signature_change_history.append(now_ms)
        char.updated_at = now_ms
        characters[index] = char
        save_characters(characters)

        reason = request.reason or "心情变化/近期经历"
        add_log(char.name, "signature_update", f"{reason}，新签名：{new_signature}")
        record_character_history(char, "signature_update", f"{reason}触发签名更新")

        return {"success": True, "data": {"signature": new_signature}}

    raise HTTPException(status_code=404, detail="Character not found")
    return presets.get(api_type, [])


@app.get("/api/stats")
async def get_statistics():
    """Get statistics"""
    characters = get_characters()
    messages = get_messages()
    settings = get_settings()

    alive_characters = [char for char in characters if char.is_alive]
    dead_characters = [char for char in characters if not char.is_alive]
    conversations = {}
    for msg in messages:
        conv_id = msg.conversation_id
        if conv_id not in conversations:
            conversations[conv_id] = 0
        conversations[conv_id] += 1

    return {
        "success": True,
        "data": {
            "character_count": len(alive_characters),
            "dead_character_count": len(dead_characters),
            "total_character_count": len(characters),
            "message_count": len(messages),
            "conversation_count": len(conversations),
            "world_elapsed_ms": settings.world_elapsed_ms,
            "world_elapsed_text": format_world_elapsed(settings.world_elapsed_ms)
        }
    }


@app.get("/api/memorials")
async def list_memorials():
    """List dead characters and memorial summaries"""
    characters = get_characters()
    memorials = [build_memorial_record(char) for char in characters if not char.is_alive]
    memorials.sort(key=lambda item: item.get("death_time") or 0, reverse=True)
    return {"success": True, "data": memorials}


@app.get("/api/memorials/{character_id}")
async def get_memorial_detail(character_id: str):
    """Get memorial detail for a dead character"""
    characters = get_characters()
    for char in characters:
        if char.id != character_id:
            continue
        if char.is_alive:
            raise HTTPException(status_code=400, detail="Character is still alive")
        data = build_memorial_record(char)
        data["histories"] = [item.model_dump() for item in get_character_histories(character_id)]
        data["memories"] = [item.model_dump() for item in get_character_memories(character_id, limit=30)]
        return {"success": True, "data": data}
    raise HTTPException(status_code=404, detail="Character not found")


class SuggestOccupationRequest(BaseModel):
    name: str = ""
    personality: str = ""


class SuggestPersonalityRequest(BaseModel):
    name: str = ""
    occupation: str = ""


class GenerateAvatarRequest(BaseModel):
    """统一文生图入参。`image_kind` 会与 `avatar_prompt` 拼接：`portrait` 头肩肖像；`selfie` 手机自拍；`scene` 环境/美食/静物等（如朋友圈非自拍配图）。"""
    avatar_prompt: str = ""
    style: str = "realistic"
    image_kind: str = "portrait"  # portrait | selfie | scene
    character_id: str = ""  # 可选，用于记录用量
    image_size: str = "1024x1024"  # 图片大小，如 1024x1024, 1024x768, 768x1024, 512x512 等


def parse_image_size(size_str: str) -> tuple[int, int]:
    """解析图片尺寸字符串，返回 (width, height)"""
    if 'x' in size_str:
        parts = size_str.lower().split('x')
        try:
            return int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            pass
    return 1024, 1024  # 默认


def get_aspect_ratio(size_str: str) -> str:
    """将尺寸字符串转换为宽高比字符串（如 "16:9"）用于 Midjourney 等"""
    w, h = parse_image_size(size_str)
    # 简化为常见比例
    if w == h:
        return "1:1"
    elif w > h:
        if w >= 1536:
            return "16:9"
        return "4:3"
    else:
        if h >= 1536:
            return "9:16"
        return "3:4"


def is_async_image_provider(provider: str, api_url: str) -> bool:
    """判断是否为异步任务型图像API（如魔搭社区）"""
    provider_lower = provider.lower()
    url_lower = api_url.lower()
    return 'modelscope' in provider_lower or 'modelscope' in url_lower


async def call_async_image_api(api_url: str, headers: dict, request_data: dict, common_headers: dict) -> tuple[bool, str, dict]:
    """调用异步图像API（如魔搭社区），返回 (success, image_url_or_error, response_data)"""
    import aiohttp
    
    # 第一步：提交任务
    submit_url = api_url
    submit_headers = {**common_headers, "X-ModelScope-Async-Mode": "true"}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(submit_url, headers=submit_headers, json=request_data) as resp:
            if resp.status != 200:
                return False, f"提交任务失败 HTTP {resp.status}", {}
            result = await resp.json()
            task_id = result.get("task_id")
            if not task_id:
                return False, "响应缺少 task_id", result
        
        # 第二步：轮询任务状态
        import asyncio
        task_url = api_url.replace('/images/generations', f'/tasks/{task_id}')
        task_headers = {**common_headers, "X-ModelScope-Task-Type": "image_generation"}
        
        for _ in range(60):  # 最多等待 5 分钟（60 * 5秒）
            await asyncio.sleep(5)
            async with session.get(task_url, headers=task_headers) as task_resp:
                if task_resp.status != 200:
                    continue
                task_data = await task_resp.json()
                status = task_data.get("task_status", "")
                
                if status == "SUCCEED":
                    output_images = task_data.get("output_images", [])
                    if output_images:
                        return True, output_images[0], task_data
                    return False, "成功但无图片", task_data
                elif status == "FAILED":
                    return False, "任务执行失败", task_data
                # 否则继续轮询
        
        return False, "任务超时", {}


@app.post("/api/characters/suggest-occupation")
async def suggest_occupation(request: SuggestOccupationRequest):
    """AI 推荐职业"""
    import aiohttp
    
    configs = get_api_configs()
    llm_config = None
    for config in configs:
        if config.api_type == 'llm' and config.is_enabled:
            llm_config = config
            break
    
    if not llm_config:
        # 没有配置 LLM 时返回默认职业
        default_occupations = ["程序员", "教师", "医生", "设计师", "作家", "厨师", "摄影师", "律师"]
        return {"success": True, "data": {"suggestions": default_occupations[:5]}}
    
    prompt = f"根据以下信息推荐3-5个适合的职业，只返回职业名称，用逗号分隔：\n"
    if request.name:
        prompt += f"名字：{request.name}\n"
    if request.personality:
        prompt += f"性格：{request.personality}\n"
    
    try:
        headers = {
            "Authorization": f"Bearer {llm_config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "suggest_occupation")
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    suggestions = [s.strip() for s in content.replace('，', ',').split(',') if s.strip()]
                    return {"success": True, "data": {"suggestions": suggestions[:5]}}
        
    except Exception as e:
        pass
    
    # 出错时返回默认职业
    default_occupations = ["程序员", "教师", "医生", "设计师", "作家"]
    return {"success": True, "data": {"suggestions": default_occupations}}


@app.post("/api/characters/suggest-personality")
async def suggest_personality(request: SuggestPersonalityRequest):
    """AI 生成性格描述"""
    import aiohttp
    
    configs = get_api_configs()
    llm_config = None
    for config in configs:
        if config.api_type == 'llm' and config.is_enabled:
            llm_config = config
            break
    
    if not llm_config:
        # 没有配置 LLM 时返回默认性格
        default_personalities = ["开朗活泼", "温柔内向", "幽默风趣", "认真严谨", "热情大方"]
        return {"success": True, "data": {"personality": default_personalities[0]}}
    
    prompt = f"为一个{request.occupation}生成合适的性格描述（2-4个词，用顿号分隔）：\n"
    if request.name:
        prompt = f"为名叫{request.name}的{request.occupation}生成合适的性格描述（2-4个词，用顿号分隔）：\n"
    
    try:
        headers = {
            "Authorization": f"Bearer {llm_config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 50
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "suggest_personality")
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                    return {"success": True, "data": {"personality": content}}
        
    except Exception as e:
        pass
    
    return {"success": True, "data": {"personality": "性格温和"}}


# ==================== AI 生成角色接口 ====================

class GenerateCharacterRequest(BaseModel):
    prompt: str
    age_range: str = "adult"  # child, teen, adult, elder


@app.post("/api/characters/generate")
async def generate_character(request: GenerateCharacterRequest):
    """AI 生成完整角色人设（包含背景故事和人生经历）"""
    import aiohttp
    import re
    
    # 获取 LLM API 配置
    configs = get_api_configs()
    llm_config = None
    for config in configs:
        if config.api_type == 'llm' and config.is_enabled:
            llm_config = config
            break
    
    if not llm_config:
        return {"success": False, "error": "未找到可用的语言模型配置"}
    
    # 年龄段映射
    age_ranges = {
        'child': (6, 12),
        'teen': (13, 17),
        'adult': (18, 40),
        'elder': (60, 80)
    }
    min_age, max_age = age_ranges.get(request.age_range, (18, 40))
    
    # 构建更详细的提示词
    system_prompt = f"""你是一个专业的角色设计师。根据用户的简单描述，创作一个有深度、有故事的角色。

请返回严格的 JSON 格式，包含以下字段：
{{
    "name": "角色名字（中文，2-4字）",
    "age": 年龄数字（{min_age}-{max_age}之间）,
    "gender": "性别（男/女）",
    "occupation": "职业",
    "personality": "性格描述（3-5个形容词，用逗号分隔）",
    "signature": "个性签名（体现角色特点，15字以内）",
    "background": "背景故事（200字以内的身世背景）",
    "life_experience": "人生经历（3个重要经历，数组格式）",
    "hobbies": "兴趣爱好（2-3个）",
    "avatar_description": "详细的外貌描述（中文，用于生成头像）",
    "avatar_prompt": "Avatar generation prompt in English, detailed description of appearance for AI image generation"
}}

注意：
1. 角色要有深度，背景故事要符合年龄段
2. 人生经历要与年龄匹配
3. avatar_prompt 需要详细的英文描述，包含：face, hair, eyes, clothing, expression, style
4. 只返回 JSON，不要任何其他文字"""

    user_prompt = f"请根据以下描述创建一个角色：{request.prompt}"
    
    try:
        headers = {
            "Authorization": f"Bearer {llm_config.api_key}",
            "Content-Type": "application/json"
        }
        
        request_data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 800
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "generate_character")
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    
                    # 解析 JSON 响应
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        character_data = json.loads(json_match.group())
                        
                        add_log("系统", "角色生成", f"AI生成角色：{character_data.get('name', '未知')}")
                        
                        return {"success": True, "data": character_data}
                    else:
                        return {"success": False, "error": "AI 返回格式不正确", "raw": content}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"AI 服务失败 (HTTP {response.status})"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON 解析失败：{str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"生成失败：{str(e)}"}


@app.post("/api/characters/generate-avatar")
async def generate_avatar(request: GenerateAvatarRequest):
    """AI 生成角色头像（支持多种图像API）"""
    import aiohttp
    import urllib.parse
    
    # 获取 Image API 配置
    configs = get_api_configs()
    image_config = None
    for config in configs:
        if config.api_type == 'image' and config.is_enabled:
            image_config = config
            break
    
    # 如果没有专门的图像配置，尝试使用支持图像的 LLM 配置
    if not image_config:
        for config in configs:
            if config.api_type == 'llm' and config.is_enabled:
                # 检查是否支持图像生成（如 OpenAI DALL-E）
                if 'openai' in config.provider.lower() or 'dall' in str(config.models).lower():
                    image_config = config
                    break
    
    if not image_config:
        return {"success": False, "error": "未找到可用的图像模型配置，请在设置中添加图像生成API"}
    
    try:
        # 构建完整的头像提示词
        style_prompts = {
            "realistic": "realistic photo, high quality, detailed",
            "anime": "anime style, vibrant colors, detailed",
            "cartoon": "cartoon style, colorful, friendly"
        }
        style_seg = style_prompts.get(request.style, style_prompts['realistic'])
        kind = (request.image_kind or "portrait").lower()
        if kind == "selfie":
            full_prompt = f"{request.avatar_prompt}, {style_seg}, smartphone selfie, front camera look, authentic casual photo, natural lighting"
        elif kind == "scene":
            full_prompt = f"{request.avatar_prompt}, {style_seg}, lifestyle or environmental photograph, suitable for social feed, no text or watermark"
        else:
            full_prompt = f"{request.avatar_prompt}, {style_seg}, portrait, upper body, neutral background"
        
        headers = {
            "Authorization": f"Bearer {image_config.api_key}",
            "Content-Type": "application/json"
        }
        
        # 根据服务商构造请求
        provider = image_config.provider.lower()
        model = image_config.selected_model or "dall-e-3"
        
        if 'stability' in provider or 'sd' in provider:
            # Stability AI / Stable Diffusion 格式
            api_url = image_config.api_url
            width, height = parse_image_size(request.image_size or settings.default_image_size or "1024x1024")
            request_data = {
                "text_prompts": [{"text": full_prompt, "weight": 1}],
                "cfg_scale": 7,
                "height": height,
                "width": width,
                "steps": 30,
                "samples": 1
            }
        elif 'midjourney' in provider:
            # Midjourney 格式（通常需要第三方服务）
            api_url = image_config.api_url
            ar = get_aspect_ratio(request.image_size or settings.default_image_size or "1024x1024")
            request_data = {
                "prompt": full_prompt,
                "aspect_ratio": ar
            }
        elif 'siliconflow' in provider or 'silicon' in provider:
            # 硅基流动格式
            api_url = image_config.api_url
            if '/chat/completions' in api_url:
                api_url = api_url.replace('/chat/completions', '/images/generations')
            elif not '/images' in api_url:
                api_url = api_url.rstrip('/') + '/v1/images/generations'
            # 让 LLM 选择图片大小
            chosen_size = await llm_choose_image_size(full_prompt, "avatar generation")
            request_data = {
                "model": model,
                "prompt": full_prompt,
                "image_size": chosen_size,
                "batch_size": 1,
                "num_inference_steps": 20,
                "guidance_scale": 7.5
            }
        elif 'modelscope' in provider or 'modelscope' in image_config.api_url.lower():
            # 魔搭社区格式（异步任务）
            api_url = image_config.api_url
            if not api_url.endswith('/'):
                api_url = api_url.rstrip('/') + '/'
            if not api_url.endswith('v1/'):
                api_url = api_url.rstrip('/') + '/v1/images/generations'
            # 让 LLM 选择图片大小
            chosen_size = await llm_choose_image_size(full_prompt, "avatar generation")
            request_data = {
                "model": model,
                "prompt": full_prompt,
                "image_size": chosen_size
            }
        else:
            # OpenAI DALL-E 格式（最通用）
            api_url = image_config.api_url
            # 自动修正 API URL
            if '/chat/completions' in api_url:
                api_url = api_url.replace('/chat/completions', '/images/generations')
            elif api_url.endswith('/v1') or api_url.endswith('/v1/'):
                api_url = api_url.rstrip('/') + '/images/generations'
            elif not '/images' in api_url:
                api_url = api_url.rstrip('/') + '/v1/images/generations'
            
            # 让 LLM 选择图片大小
            chosen_size = await llm_choose_image_size(full_prompt, "avatar generation")
            request_data = {
                "model": model,
                "prompt": full_prompt,
                "n": 1,
                "size": chosen_size,
                "quality": "standard",
                "response_format": "url"
            }
        
        add_log("系统", "头像生成", f"正在生成头像: {full_prompt[:50]}...")
        
        # 检查是否为异步任务型API（如魔搭社区）
        if is_async_image_provider(provider, image_config.api_url):
            success, image_url_or_error, response_data = await call_async_image_api(
                api_url, headers, request_data, {
                    "Authorization": f"Bearer {image_config.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if success and image_url_or_error:
                record_image_usage(image_config, "avatar_generation", request.character_id, success=True)
                # 下载图片并保存到本地
                local_avatar_path = None
                try:
                    import base64
                    avatar_filename = f"{uuid.uuid4().hex}.png"
                    avatar_filepath = os.path.join(AVATARS_DIR, avatar_filename)
                    async with aiohttp.ClientSession() as download_session:
                        async with download_session.get(image_url_or_error, timeout=aiohttp.ClientTimeout(total=30)) as download_resp:
                            if download_resp.status == 200:
                                image_data = await download_resp.read()
                                with open(avatar_filepath, 'wb') as f:
                                    f.write(image_data)
                                local_avatar_path = f"/avatars/{avatar_filename}"
                                add_log("系统", "头像保存", f"头像已保存到本地: {avatar_filename}")
                except Exception as save_error:
                    add_log("系统", "警告", f"头像保存失败，使用远程URL: {str(save_error)}")
                    local_avatar_path = None
                
                add_log("系统", "头像生成", "头像生成成功（异步任务）")
                # 保存提示词为MD文档
                prompt_file = save_image_prompt_md(full_prompt, "头像生成", image_url_or_error, character_title)
                return {
                    "success": True,
                    "data": {
                        "image_url": local_avatar_path or image_url_or_error,
                        "remote_url": image_url_or_error,
                        "local_path": local_avatar_path,
                        "prompt": full_prompt,
                        "prompt_file": prompt_file
                    }
                }
            else:
                record_image_usage(image_config, "avatar_generation", request.character_id, success=False, error_message=image_url_or_error)
                return {"success": False, "error": f"异步任务失败：{image_url_or_error}"}
        else:
            # 同步API调用
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
                async with session.post(api_url, headers=headers, json=request_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # 解析不同格式的响应
                        image_url = None
                        
                        # OpenAI 格式
                        if 'data' in result and len(result['data']) > 0:
                            image_url = result['data'][0].get('url') or result['data'][0].get('b64_json')
                        
                        # Stability AI 格式
                        elif 'artifacts' in result and len(result['artifacts']) > 0:
                            image_url = result['artifacts'][0].get('url')
                            if result['artifacts'][0].get('finishReason') == 'ERROR':
                                return {"success": False, "error": "图像生成被内容审核拒绝"}
                        
                        # 硅基流动格式
                        elif 'images' in result and len(result['images']) > 0:
                            image_url = result['images'][0].get('url') or result['images'][0].get('b64_json')
                        
                        # 其他格式
                        elif 'url' in result:
                            image_url = result['url']
                        elif 'image_url' in result:
                            image_url = result['image_url']
                        
                        if image_url:
                            # 记录成功
                            record_image_usage(image_config, "avatar_generation", request.character_id, success=True)
                            # 下载图片并保存到本地
                            local_avatar_path = None
                            try:
                                import aiohttp
                                import base64
                                
                                # 生成唯一文件名
                                avatar_filename = f"{uuid.uuid4().hex}.png"
                                avatar_filepath = os.path.join(AVATARS_DIR, avatar_filename)
                                
                                # 如果是 base64 数据
                                if image_url.startswith('data:image'):
                                    # 解析 base64 数据
                                    base64_data = image_url.split(',')[1]
                                    image_data = base64.b64decode(base64_data)
                                    with open(avatar_filepath, 'wb') as f:
                                        f.write(image_data)
                                    local_avatar_path = f"/avatars/{avatar_filename}"
                                else:
                                    # 下载远程图片
                                    async with aiohttp.ClientSession() as download_session:
                                        async with download_session.get(image_url, timeout=aiohttp.ClientTimeout(total=30)) as download_resp:
                                            if download_resp.status == 200:
                                                image_data = await download_resp.read()
                                                with open(avatar_filepath, 'wb') as f:
                                                    f.write(image_data)
                                                local_avatar_path = f"/avatars/{avatar_filename}"
                                                add_log("系统", "头像保存", f"头像已保存到本地: {avatar_filename}")
                            except Exception as save_error:
                                add_log("系统", "警告", f"头像保存失败，使用远程URL: {str(save_error)}")
                                local_avatar_path = None
                            
                            add_log("系统", "头像生成", "头像生成成功")
                            # 保存提示词为MD文档
                            prompt_file = save_image_prompt_md(full_prompt, "头像生成", image_url, character_title)
                            return {
                                "success": True,
                                "data": {
                                    "image_url": local_avatar_path or image_url,
                                    "remote_url": image_url,
                                    "local_path": local_avatar_path,
                                    "prompt": full_prompt,
                                    "prompt_file": prompt_file
                                }
                            }
                        else:
                            record_image_usage(image_config, "avatar_generation", request.character_id, success=False, error_message="无法解析图像响应")
                            return {"success": False, "error": "无法解析图像响应", "response": result}
                    else:
                        error_data = await response.json() if 'json' in response.headers.get('content-type', '') else await response.text()
                        record_image_usage(image_config, "avatar_generation", request.character_id, success=False, error_message=f"HTTP {response.status}")
                        return {"success": False, "error": f"图像生成失败 (HTTP {response.status})", "details": error_data}
                    
    except aiohttp.ClientError as e:
        record_image_usage(image_config, "avatar_generation", request.character_id, success=False, error_message=str(e))
        return {"success": False, "error": f"网络错误：{str(e)}"}
    except Exception as e:
        record_image_usage(image_config, "avatar_generation", request.character_id, success=False, error_message=str(e))
        add_log("系统", "错误", f"头像生成异常: {str(e)}")
        return {"success": False, "error": f"生成失败：{str(e)}"}


# ==================== LLM 用量统计接口 ====================

@app.get("/api/llm-usage/stats")
async def get_llm_usage_stats():
    """获取 LLM 用量统计信息"""
    stats = compute_llm_usage_stats()
    return {"success": True, "data": stats.model_dump()}


@app.get("/api/llm-usage/history")
async def get_llm_usage_history(limit: int = 100, endpoint: str = "", model: str = ""):
    """获取 LLM 用量历史记录"""
    records = get_llm_usage_records(limit=limit)
    if endpoint:
        records = [r for r in records if r.endpoint == endpoint]
    if model:
        records = [r for r in records if model.lower() in (r.model_name or "").lower()]
    return {"success": True, "data": [r.model_dump() for r in records]}


@app.get("/api/llm-usage/models")
async def get_llm_usage_by_model():
    """按模型分组获取用量统计"""
    stats = compute_llm_usage_stats()
    return {"success": True, "data": {"by_model": stats.by_model, "by_endpoint": stats.by_endpoint, "by_config": stats.by_config}}


# ==================== 调度器接口（提醒 + 主动对话）V3.3 新增 ====================

class AddReminderRequest(BaseModel):
    character_id: str
    reminder_type: str = "reminder"  # reminder/greeting/task_reminder
    trigger_time_ms: int  # 触发时间（毫秒时间戳）
    content: str
    repeat: str = "none"  # none/daily/weekly


@app.get("/api/scheduler/reminders")
async def list_reminders(character_id: Optional[str] = None):
    """获取提醒列表"""
    if character_id:
        reminders = get_character_reminders(character_id)
    else:
        reminders = get_reminders()
    return {"success": True, "data": reminders}


@app.post("/api/scheduler/reminders")
async def create_reminder(request: AddReminderRequest):
    """创建提醒"""
    reminder = add_reminder(
        character_id=request.character_id,
        reminder_type=request.reminder_type,
        trigger_time_ms=request.trigger_time_ms,
        content=request.content,
        repeat=request.repeat,
    )
    add_log("system", "reminder_create", f"为角色 {request.character_id} 创建提醒：{request.content[:50]}...")
    return {"success": True, "data": reminder}


@app.delete("/api/scheduler/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str):
    """删除提醒"""
    success = remove_reminder(reminder_id)
    if success:
        add_log("system", "reminder_delete", f"删除提醒 {reminder_id}")
    return {"success": success}


@app.post("/api/scheduler/run")
async def run_scheduler_api():
    """手动触发调度器（检查到期提醒、主动对话、节日问候等）"""
    characters = [c for c in get_characters() if c.is_alive]
    results = await run_scheduler_tick(
        characters=characters,
        get_ai_reply_func=generate_ai_reply,
        save_messages_func=save_messages,
        get_messages_func=get_messages,
        add_log_func=add_log,
    )
    return {"success": True, "data": results}


@app.post("/api/characters/{character_id}/proactive-message")
async def trigger_proactive_message(character_id: str, context: str = "default"):
    """触发角色主动发消息给用户"""
    characters = get_characters()
    char = next((c for c in characters if c.id == character_id), None)
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")
    if not char.is_alive:
        raise HTTPException(status_code=400, detail="角色已不在世")

    message = generate_proactive_message(char, context)
    msg = ChatMessage(
        conversation_id=char.id,
        sender_id=char.id,
        content=message,
        is_from_user=False,
    )
    messages = get_messages()
    messages.append(msg)
    save_messages(messages)
    record_proactive_message(char.id)
    add_log(char.name, "主动联系", f"触发主动消息：{message[:30]}...")
    return {"success": True, "data": msg.model_dump()}


# 启动后台任务：年龄增长
@app.on_event("startup")
async def startup_event():
    """Init background tasks"""
    import asyncio
    init_memory_db()
    migrate_legacy_memories_if_needed()
    await ensure_world_map_initialized()
    sync_private_groups()
    last_schedule_day = -1

    async def age_growth_task():
        nonlocal last_schedule_day
        while True:
            await asyncio.sleep(60)
            now_ms = int(time.time() * 1000)
            settings = get_settings()
            real_elapsed_ms = max(0, now_ms - settings.last_world_update_time)
            settings.last_world_update_time = now_ms

            if real_elapsed_ms <= 0:
                save_settings(settings)
                continue

            world_elapsed_ms = real_elapsed_ms * settings.time_speed
            settings.world_elapsed_ms += world_elapsed_ms
            run_daily_economy(world_elapsed_ms)
            current_day = int(settings.world_elapsed_ms // MILLISECONDS_PER_DAY)
            if current_day != last_schedule_day:
                alive_characters = [c for c in get_characters() if c.is_alive]
                schedules = [item for item in get_schedules() if item.day_index != current_day]
                for char in alive_characters:
                    schedules.append(generate_schedule_for_character(char, current_day))
                save_schedules(schedules)
                last_schedule_day = current_day

            characters = get_characters()
            updated = False

            for index, char in enumerate(characters):
                notes = ensure_character_defaults(char, settings)
                for note in notes:
                    add_log(char.name, "lifecycle", note)
                    updated = True

                if not char.is_alive:
                    characters[index] = char
                    continue

                char.growth_progress_ms += world_elapsed_ms
                month_steps = char.growth_progress_ms // WORLD_MONTH_MS
                char.growth_progress_ms = char.growth_progress_ms % WORLD_MONTH_MS

                if month_steps <= 0:
                    characters[index] = char
                    continue

                stage_changed = False
                total_support = 0.0

                for _ in range(int(month_steps)):
                    previous_stage = char.get_age_stage()
                    previous_age = char.age

                    char.age_months += 1
                    if char.age_months >= MONTHS_PER_YEAR:
                        char.age += 1
                        char.age_months = 0

                    current_stage = char.get_age_stage()
                    total_support += apply_parental_support(char, characters, current_stage)

                    for note in apply_age_stage_constraints(char):
                        add_log(char.name, "lifecycle", note)

                    if current_stage != previous_stage:
                        stage_changed = True
                        char.stage_entered_at = now_ms
                        add_log(char.name, "stage", f"entered stage: {current_stage}")
                        record_character_history(char, "stage_change", f"entered stage {current_stage}")

                    if char.age != previous_age:
                        add_log(char.name, "growth", f"age -> {char.age}")
                        record_character_history(char, "birthday", f"grew to age {char.age}")

                    if settings.enable_death_mechanism and char.age >= char.max_lifespan:
                        if mark_character_deceased(char, f"Natural death at lifespan limit {char.max_lifespan}", now_ms):
                            stage_changed = False
                            break

                    if settings.enable_death_mechanism and settings.enable_accidental_death and char.is_alive:
                        cause = maybe_get_accidental_death_cause(char)
                        if cause and mark_character_deceased(char, cause, now_ms):
                            stage_changed = False
                            break

                if total_support > 0 and char.is_alive:
                    char.money += total_support
                    add_log(char.name, "family_support", f"monthly support +{total_support:.0f}")

                if char.is_alive:
                    loc, act = pick_schedule_location_for_world_time(char, settings.world_elapsed_ms)
                    update_character_location(
                        char,
                        loc,
                        source=f"schedule:{act}",
                        world_elapsed_ms=settings.world_elapsed_ms,
                    )

                if stage_changed and char.is_alive and settings.enable_auto_avatar_update:
                    success, message = await refresh_character_avatar_for_stage(char, forced=True)
                    add_log(char.name, "avatar_refresh", message)

                char.updated_at = now_ms
                characters[index] = char
                updated = True

            save_settings(settings)
            if updated:
                save_characters(characters)

    async def social_autorun_task():
        while True:
            await asyncio.sleep(60)
            settings = get_settings()
            if not settings.enable_auto_moment_interactions:
                continue
            interval_min = max(1, int(settings.auto_moment_interval_minutes))
            now_ms = int(time.time() * 1000)
            if now_ms - int(settings.auto_moment_last_run_time or 0) < interval_min * 60 * 1000:
                continue
            await run_moment_auto_interactions(limit=50)
            apply_inactivity_decay()
            sync_private_groups()
            enc = detect_encounters(window_minutes=10)
            await process_encounter_followups(enc.get("items") or [])
            settings.auto_moment_last_run_time = now_ms
            save_settings(settings)

    async def heartbeat_task():
        while True:
            settings = get_settings()
            interval = max(10, int(settings.heartbeat_interval_seconds or 60))
            await asyncio.sleep(interval)
            settings = get_settings()
            if not settings.enable_heartbeat:
                continue
            now_ms = int(time.time() * 1000)
            if now_ms - int(settings.heartbeat_last_run_time or 0) < interval * 1000:
                continue
            try:
                summary = await run_heartbeat_tick(limit_characters=40)
                add_log("system", "heartbeat", f"tick={summary.get('ticked')} alive={summary.get('characters')}")
                settings.heartbeat_last_run_time = now_ms
                save_settings(settings)
            except Exception as e:
                add_log("system", "heartbeat_error", str(e)[:120])

    async def task_engine_task():
        """后台任务引擎：定期驱动角色/公司自动接取和完成任务"""
        while True:
            await asyncio.sleep(30)  # 每 30 秒运行一次
            settings = get_settings()
            if not getattr(settings, 'enable_task_engine', True):
                continue
            try:
                await run_task_engine(max_tasks_per_tick=5)
            except Exception as e:
                add_log("system", "task_engine_error", str(e)[:120])

    async def scheduler_task():
        """V3.3 新增：调度器任务 - 提醒触发、角色主动对话、节日问候"""
        while True:
            await asyncio.sleep(45)  # 每 45 秒检查一次
            settings = get_settings()
            if not getattr(settings, 'enable_scheduler', True):
                continue
            try:
                characters = [c for c in get_characters() if c.is_alive]
                results = await run_scheduler_tick(
                    characters=characters,
                    get_ai_reply_func=generate_ai_reply,
                    save_messages_func=save_messages,
                    get_messages_func=get_messages,
                    add_log_func=add_log,
                )
                if results["reminders_triggered"] > 0:
                    add_log("system", "scheduler", f"触发 {results['reminders_triggered']} 个提醒")
                if results["proactive_messages"] > 0:
                    add_log("system", "scheduler", f"角色主动发消息 {results['proactive_messages']} 次")
            except Exception as e:
                add_log("system", "scheduler_error", str(e)[:120])

    settings = get_settings()
    if settings.last_world_update_time <= 0:
        settings.last_world_update_time = int(time.time() * 1000)
        save_settings(settings)

    asyncio.create_task(age_growth_task())
    asyncio.create_task(social_autorun_task())
    asyncio.create_task(heartbeat_task())
    asyncio.create_task(task_engine_task())
    asyncio.create_task(scheduler_task())  # V3.3 新增：调度器任务


if __name__ == "__main__":
    import uvicorn
    # 禁用彩色日志输出
    uvicorn.run(app, host="0.0.0.0", port=8080, log_config={
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(levelname)s - %(message)s",
                "use_colors": False
            },
            "access": {
                "format": "%(asctime)s - %(levelname)s - %(message)s",
                "use_colors": False
            }
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout"
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout"
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["default"]
        },
        "loggers": {
            "uvicorn": {
                "level": "INFO",
                "handlers": ["default"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["access"],
                "propagate": False
            }
        }
    })

