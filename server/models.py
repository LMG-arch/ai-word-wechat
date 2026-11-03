"""
AIWeChat 数据模型模块
所有 Pydantic 模型、枚举类型、会话管理器等。
从 main.py 提取，保持向后兼容。
"""

from __future__ import annotations

import json
import math
import re
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator

import sqlite3

from config import (
    MEMORY_DB_FILE, MEMORIES_FILE, MILLISECONDS_PER_DAY,
    MEMORY_TYPE_EVENT, MEMORY_TYPE_REFLECTION
)


# ==================== 枚举类型 ====================

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


class MemoryType(str, Enum):
    CONVERSATION = "conversation"
    EVENT = "event"
    TASK = "task"
    RELATIONSHIP = "relationship"
    REFLECTION = "reflection"


# ==================== 核心数据模型 ====================

def get_age_stage_from_age(age: int) -> str:
    """根据年龄返回年龄阶段"""
    if age <= 12:
        return "儿童"
    if age <= 17:
        return "青少年"
    if age <= 40:
        return "青年"
    if age <= 60:
        return "中年"
    return "老年"


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
    experience_skills: Dict[str, Any] = Field(default_factory=dict)
    llm_model_id: Optional[str] = None
    moment_frequency: str = "normal"
    # V4.0：当前心境（happy/sad/angry/anxious/excited/calm/tired）
    mood: str = "calm"
    # V4.0 包B1：关系阶段与家庭
    relationship_stage: str = "stranger"   # stranger/friend/close/lover/spouse
    partner_id: Optional[str] = None
    spouse_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)
    # V4.0 包B2：职业等级（1 最低）
    career_level: int = 1
    career_title: str = ""
    career_exp: int = 0
    tasks_completed: int = 0

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
    message_type: str = "text"
    image_url: Optional[str] = None
    voice_url: Optional[str] = None
    red_packet_id: Optional[str] = None
    transfer_amount: Optional[float] = None
    transfer_note: Optional[str] = None
    transfer_status: Optional[str] = None  # accepted / rejected / pending
    # V4.0 包A5：语音条转写与时长、表情贴纸 id
    voice_duration: Optional[int] = None
    voice_text: Optional[str] = None
    sticker_id: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    is_read: bool = False
    is_from_user: bool = True


class RedPacketClaim(BaseModel):
    """红包领取记录。"""
    actor_id: str           # "user" 或 角色 id
    actor_name: str
    amount: float
    claimed_at: int = Field(default_factory=lambda: int(time.time() * 1000))


class RedPacket(BaseModel):
    """红包（拼手气）。"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    sender_id: str
    sender_name: str
    blessing: str = "恭喜发财，大吉大利"
    total_amount: float
    count: int
    claims: List[RedPacketClaim] = Field(default_factory=list)
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))

    @property
    def remaining(self) -> float:
        return round(self.total_amount - sum(c.amount for c in self.claims), 2)

    @property
    def is_finished(self) -> bool:
        return len(self.claims) >= self.count


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
    image_prompt_file: Optional[str] = None
    # public: 所有人可见；private: 仅作者可见；friends: 按亲密度阈值控制
    visibility: str = "friends"
    trigger_type: str = "random"
    mood: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    visible_min_intimacy: int = 21
    liked_by: List[str] = Field(default_factory=list)
    comments: List[MomentComment] = Field(default_factory=list)
    # V4.0 包A4：话题标签、位置签到、被@的角色
    topics: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    mentioned_ids: List[str] = Field(default_factory=list)


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
    review_notes: Optional[str] = None
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
    image_model_id: Optional[str] = None


class Company(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    legal_person_id: str
    member_ids: List[str] = Field(default_factory=list)
    funds: float = 0.0
    knowledge_base: List[Dict[str, Any]] = Field(default_factory=list)
    location_name: Optional[str] = None
    location_x: float = 0.0
    location_y: float = 0.0
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


class Memory(BaseModel):
    """记忆条目 - 每个角色独立存储"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    character_id: str
    memory_type: MemoryType
    content: str
    importance: float = 0.5
    emotion: Optional[str] = None
    related_entities: List[str] = Field(default_factory=list)
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    valid_from: int = Field(default_factory=lambda: int(time.time() * 1000))
    valid_to: Optional[int] = None
    embedding: Optional[List[float]] = None
    access_count: int = 0
    last_accessed: Optional[int] = None
    metadata: dict = Field(default_factory=dict)


class UserProfile(BaseModel):
    """真实用户（操作者）资料，与 AI 角色区分；朋友圈点赞/评论使用 author_id=\"user\" 与此处昵称、头像一致。"""
    nickname: str = "用户"
    avatar_url: Optional[str] = None
    signature: str = ""
    experience: str = ""


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
    enable_task_engine: bool = True
    last_world_update_time: int = Field(default_factory=lambda: int(time.time() * 1000))
    world_elapsed_ms: int = 0
    api_configs: Dict[str, Any] = Field(default_factory=dict)
    character_residences: Dict[str, str] = Field(default_factory=dict)
    default_image_size: str = "1024x1024"
    user_profile: UserProfile = Field(default_factory=UserProfile)


class ApiConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    api_type: str
    provider: str
    api_url: str
    api_key: str
    models: List[str] = Field(default_factory=list)
    selected_model: str = ""
    is_enabled: bool = True
    priority: int = 0
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = Field(default_factory=lambda: int(time.time() * 1000))


# ==================== LLM 用量统计模型 ====================

class LlmUsageRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config_id: str = ""
    config_name: str = ""
    model_name: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    endpoint: str = ""
    character_id: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))


class LlmUsageStats(BaseModel):
    total_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    image_total_calls: int = 0
    image_success_calls: int = 0
    image_failed_calls: int = 0
    by_model: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    by_endpoint: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    by_config: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    image_by_config: Dict[str, Dict[str, int]] = Field(default_factory=dict)


class ImageUsageRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config_id: str = ""
    config_name: str = ""
    model_name: str = ""
    images_generated: int = 1
    endpoint: str = ""
    character_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))


class ImageUsageStats(BaseModel):
    total_calls: int = 0
    total_images: int = 0
    success_calls: int = 0
    failed_calls: int = 0


# ==================== 请求/响应模型 ====================

class CreateCharacterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=30)
    age: int = Field(default=25, ge=0, le=200)
    gender: str = Field(default="男", max_length=10)
    occupation: str = Field(min_length=1, max_length=50)
    personality: str = Field(default="", max_length=500)
    signature: str = Field(default="", max_length=200)
    avatar_url: Optional[str] = Field(default=None, max_length=2000)
    parent_ids: Optional[List[str]] = None
    llm_model_id: Optional[str] = None
    moment_frequency: str = Field(default="normal", max_length=20)

    @field_validator("name", "occupation")
    @classmethod
    def _strip_not_blank(cls, value: str) -> str:
        """去除首尾空白，并拒绝空串 / 纯空白（前端校验可被绕过，后端必须兜底）。"""
        value = (value or "").strip()
        if not value:
            raise ValueError("不能为空或仅包含空白字符")
        return value


class SendMessageRequest(BaseModel):
    conversation_id: str = Field(min_length=1, max_length=100)
    content: str = Field(max_length=5000)
    message_type: str = Field(default="text", max_length=20)
    image_url: Optional[str] = Field(default=None, max_length=2000)
    voice_url: Optional[str] = Field(default=None, max_length=2000)


class ChatResponse(BaseModel):
    content: str
    character_id: str
    timestamp: int


class CreateApiConfigRequest(BaseModel):
    name: str
    api_type: str
    provider: str
    api_url: str
    api_key: str
    models: List[str] = Field(default_factory=list)
    selected_model: str = ""
    is_enabled: bool = True
    priority: int = 0


class MaybeRefreshAvatarRequest(BaseModel):
    reason: Optional[str] = None
    forced: bool = False


class MaybeUpdateSignatureRequest(BaseModel):
    reason: Optional[str] = None


class GenerateMomentRequest(BaseModel):
    trigger_type: str = "random"
    mood: Optional[str] = None
    event_text: Optional[str] = None
    with_image: bool = True


class MomentCommentRequest(BaseModel):
    author_id: str
    content: Optional[str] = None
    auto_generate: bool = False
    reply_to_comment_id: Optional[str] = None


class UserCreateMomentRequest(BaseModel):
    content: str
    image_url: Optional[str] = None
    generate_image: bool = False
    image_prompt: Optional[str] = None
    # V4.0 包A4
    visibility: str = "friends"          # public / friends / private
    location: Optional[str] = None
    mention_names: List[str] = Field(default_factory=list)


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
    approved: bool
    review_notes: str = ""
    score: float = 50.0
    checklist: Optional[Dict[str, Any]] = None


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
    topic: Optional[str] = None


class SendPrivateGroupMessageRequest(BaseModel):
    """用户在私人群聊里发言。content 支持 @角色名 点名。"""
    content: str = Field(min_length=1, max_length=1000)
    message_type: str = Field(default="text", max_length=20)


class SendRedPacketRequest(BaseModel):
    """发红包请求。"""
    conversation_id: str
    total_amount: float = Field(gt=0, le=100000)
    count: int = Field(ge=1, le=100)
    blessing: str = Field(default="恭喜发财，大吉大利", max_length=50)


class ClaimRedPacketRequest(BaseModel):
    """抢红包请求。actor_id 为 "user" 或角色 id（默认用户本人）。"""
    actor_id: str = "user"
    actor_name: str = "我"


class SendTransferRequest(BaseModel):
    """用户向角色转账。"""
    conversation_id: str
    amount: float = Field(gt=0, le=100000)
    note: str = Field(default="", max_length=50)


class RelationshipInteractRequest(BaseModel):
    from_id: str
    to_id: str
    action: str


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
    selected_model: str = ""


class GenerateCharacterRequest(BaseModel):
    prompt: str
    age_range: str = "adult"


class GenerateAvatarRequest(BaseModel):
    avatar_prompt: str = ""
    style: str = "realistic"
    image_kind: str = "portrait"
    character_id: str = ""
    image_size: str = "1024x1024"


class RegenerateWorldRequest(BaseModel):
    prompt: str = ""


class SuggestOccupationRequest(BaseModel):
    name: str = ""
    personality: str = ""


class SuggestPersonalityRequest(BaseModel):
    name: str = ""
    occupation: str = ""


# ==================== 会话管理器 ====================

class SessionManager:
    """管理对话 Session，负责短期上下文维护与长文本压缩"""
    def __init__(self, max_context_len: int = 10):
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.max_context_len = max_context_len

    def get_context(self, conversation_id: str) -> List[Dict[str, str]]:
        return self.sessions.get(conversation_id, [])

    def add_message(self, conversation_id: str, role: str, content: str):
        if conversation_id not in self.sessions:
            self.sessions[conversation_id] = []
        safe = content if isinstance(content, str) else ("" if content is None else str(content))
        self.sessions[conversation_id].append({"role": role, "content": safe})
        if len(self.sessions[conversation_id]) > self.max_context_len * 3:
            self.sessions[conversation_id] = self.sessions[conversation_id][-(self.max_context_len * 2):]

    def clear_session(self, conversation_id: str):
        if conversation_id in self.sessions:
            del self.sessions[conversation_id]


# ==================== 执行协议 ====================

class ExecProtocol:
    """
    定义 AI 执行协议，允许 AI 在输出中包含特定指令
    格式：[EXEC:ActionName(args)]
    """
    @staticmethod
    def parse_instructions(content: str) -> List[Dict[str, Any]]:
        instructions = []
        pattern = r"\[EXEC:(\w+)\((.*?)\)\]"
        matches = re.finditer(pattern, content)
        for match in matches:
            action = match.group(1)
            params_raw = match.group(2)
            instructions.append({"action": action, "params": params_raw})
        return instructions


# ==================== 全局实例 ====================

session_manager = SessionManager()
exec_protocol = ExecProtocol()
