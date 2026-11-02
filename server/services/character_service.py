"""
AIWeChat 角色服务模块
角色管理、生命周期、头像/签名、年龄阶段等逻辑。
"""

from __future__ import annotations

import time
import random
from typing import Optional, List, Dict, Any

# 类型别名
AgeStage = str
ResidenceName = str
WorldTimeMs = int

# 使用相对导入
from models import (
    Character, CharacterHistoryEntry, Settings,
    SuggestOccupationRequest, SuggestPersonalityRequest,
)
from storage import (
    load_json, save_json, get_characters, save_characters,
    get_settings, save_settings
)
from config import (
    CHARACTER_HISTORY_FILE, MILLISECONDS_PER_DAY
)

# =====================================================================
#  住宅/住处相关
# =====================================================================

def get_residential_landmarks() -> List[Dict[str, Any]]:
    """获取所有住宅类地标，用于随机分配角色住处"""
    from storage import get_active_world_map
    meta = get_active_world_map()
    return [lm for lm in (meta.get("landmarks") or []) if lm.get("type") == "residential"]


def assign_random_residence(character_id: str) -> str:
    """为角色随机分配一个住宅地标作为住处"""
    residential = get_residential_landmarks()
    if not residential:
        return "城市"
    lm = random.choice(residential)
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
    return assign_random_residence(character_id)


# =====================================================================
#  年龄阶段相关
# =====================================================================

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


def get_age_personality_modifier(age: int, base_personality: str) -> str:
    """根据年龄调整性格描述"""
    modifiers = {
        "儿童": "天真活泼",
        "青少年": "叛逆好奇",
        "青年": "精力充沛",
        "中年": "沉稳务实",
        "老年": "慈祥睿智",
    }
    stage = get_age_stage_from_age(age)
    return f"{modifiers.get(stage, '')}，{base_personality}"


def get_moment_frequency_multiplier(character: Character) -> float:
    """获取朋友圈频率乘数"""
    freq = getattr(character, 'moment_frequency', 'normal')
    multipliers = {"low": 0.5, "normal": 1.0, "high": 1.5}
    return multipliers.get(freq, 1.0)


def normalize_parent_ids(character: Character, all_character_ids: Optional[set[str]] = None) -> List[str]:
    """规范化父母 ID：去重、剔除自身、剔除不存在的角色，并同步写回。

    返回清理后的父 ID 列表（副作用：更新 character.parent_ids）。
    旧实现漏了「去重」与「剔除自身」，可能留下脏数据（如自己当自己的父母、重复 ID）。
    """
    cleaned: List[str] = []
    seen: set[str] = set()
    for pid in (character.parent_ids or []):
        if not pid or pid == character.id or pid in seen:
            continue
        if all_character_ids is not None and pid not in all_character_ids:
            continue
        cleaned.append(pid)
        seen.add(pid)
    character.parent_ids = cleaned
    return cleaned


def get_dialogue_style_hint(character: Character) -> str:
    """获取对话风格提示"""
    age = character.age
    if age < 13:
        return "说话简短天真，多用感叹号和emoji"
    if age < 18:
        return "说话带点叛逆，喜欢用网络流行语"
    if age < 40:
        return "说话自然流畅，像普通成年人"
    if age < 60:
        return "说话稳重，偶尔给建议"
    return "说话慈祥，喜欢分享经验"


def get_occupation_hint(character: Character) -> str:
    """获取职业相关提示"""
    occ = character.occupation
    hints = {
        "程序员": "可以聊技术，偶尔抱怨bug",
        "设计师": "对美感有追求，喜欢分享创意",
        "教师": "喜欢教育话题，耐心温和",
        "医生": "关注健康，说话专业但亲切",
    }
    return hints.get(occ, f"以{occ}的视角思考")


def format_world_elapsed(world_elapsed_ms: int) -> str:
    """格式化世界已运行时长，输出「N年N个月N天」（30 天/月、12 月/年）。

    与前端 `formatWorldTime()` 保持一致，避免同一界面出现两套时间文案。
    例：0 → "0天"；30 天 → "1个月"；395 天 → "1年1个月5天"。
    """
    days_per_month = 30
    months_per_year = 12
    total_days = max(0, int(world_elapsed_ms)) // MILLISECONDS_PER_DAY
    years = total_days // (days_per_month * months_per_year)
    remain_days = total_days % (days_per_month * months_per_year)
    months = remain_days // days_per_month
    days = remain_days % days_per_month
    parts = []
    if years:
        parts.append(f"{years}年")
    if months:
        parts.append(f"{months}个月")
    if days or not parts:
        parts.append(f"{days}天")
    return "".join(parts)


# =====================================================================
#  头像/签名变更历史
# =====================================================================

AVATAR_LIMIT_WINDOW_MS = 7 * MILLISECONDS_PER_DAY
AVATAR_LIMIT_MAX_CHANGES = 2
SIGNATURE_LIMIT_WINDOW_MS = 7 * MILLISECONDS_PER_DAY
SIGNATURE_LIMIT_MAX_CHANGES = 2


def trim_avatar_change_history(character: Character, now_ms: Optional[int] = None) -> List[int]:
    """裁剪头像变更历史"""
    now = now_ms or int(time.time() * 1000)
    cutoff = now - AVATAR_LIMIT_WINDOW_MS
    character.avatar_change_history = [t for t in character.avatar_change_history if t > cutoff]
    return character.avatar_change_history


def trim_signature_change_history(character: Character, now_ms: Optional[int] = None) -> List[int]:
    """裁剪签名变更历史"""
    now = now_ms or int(time.time() * 1000)
    cutoff = now - SIGNATURE_LIMIT_WINDOW_MS
    character.signature_change_history = [t for t in character.signature_change_history if t > cutoff]
    return character.signature_change_history


def can_refresh_avatar(character: Character, now_ms: Optional[int] = None) -> bool:
    """检查是否可以刷新头像"""
    now = now_ms or int(time.time() * 1000)
    changes = len([t for t in character.avatar_change_history if t > now - AVATAR_LIMIT_WINDOW_MS])
    return changes < AVATAR_LIMIT_MAX_CHANGES


def can_refresh_signature(character: Character, now_ms: Optional[int] = None) -> bool:
    """检查是否可以刷新签名"""
    now = now_ms or int(time.time() * 1000)
    changes = len([t for t in character.signature_change_history if t > now - SIGNATURE_LIMIT_WINDOW_MS])
    return changes < SIGNATURE_LIMIT_MAX_CHANGES


# =====================================================================
#  角色默认值/约束
# =====================================================================

def apply_age_stage_constraints(character: Character) -> List[str]:
    """按年龄阶段修正职业与零花钱上限。

    合并了原 storage 版（老年退休、空职业补学生）与本模块版（零花钱封顶）的逻辑，
    两者此前各自只做一半，导致「老人不变退休」「空职业青少年不补学生」等遗漏。
    """
    notes: List[str] = []
    stage = get_age_stage_from_age(character.age)

    if stage == "儿童":
        if character.money > 100:
            character.money = 50
            notes.append("儿童零花钱已调整")
        if character.occupation != "学生":
            character.occupation = "学生"
            notes.append('年龄阶段调整，职业已修正为"学生"')
    elif stage == "青少年":
        if character.money > 200:
            character.money = 100
            notes.append("青少年零花钱已调整")
        if character.occupation != "学生":
            character.occupation = "学生"
            notes.append('青少年阶段职业已修正为"学生"')
    elif stage == "老年" and character.age >= 65 and character.occupation in ["", "无业", "待定"]:
        character.occupation = "退休"
        notes.append('老年阶段职业已设置为"退休"')

    return notes


def ensure_character_defaults(character: Character, settings: Optional[Settings] = None) -> List[str]:
    """确保角色有默认值"""
    notes = []
    
    if not character.personality:
        personalities = ["开朗", "内向", "幽默", "沉稳", "活泼", "温柔"]
        character.personality = random.choice(personalities)
        notes.append(f"已设置默认性格：{character.personality}")
    
    if not character.occupation:
        character.occupation = "自由职业者"
        notes.append("已设置默认职业")
    
    if not character.signature:
        character.signature = "暂无签名"
    
    if character.money < 0:
        character.money = 0
    
    age_notes = apply_age_stage_constraints(character)
    notes.extend(age_notes)
    
    return notes


# =====================================================================
#  角色历史记录
# =====================================================================

def get_character_histories(character_id: Optional[str] = None) -> List[CharacterHistoryEntry]:
    """获取角色历史记录"""
    data = load_json(CHARACTER_HISTORY_FILE, [])
    histories = [CharacterHistoryEntry(**item) for item in data]
    if character_id:
        histories = [h for h in histories if h.character_id == character_id]
    histories.sort(key=lambda x: x.real_timestamp_ms, reverse=True)
    return histories


def get_history_entry(character_id: str, history_id: str) -> Optional[CharacterHistoryEntry]:
    """获取单条历史记录"""
    histories = get_character_histories(character_id)
    return next((h for h in histories if h.id == history_id), None)


def save_character_histories(histories: List[CharacterHistoryEntry]):
    """保存角色历史记录"""
    save_json(CHARACTER_HISTORY_FILE, [h.model_dump() for h in histories])


def get_world_time_ms(settings: Optional[Settings] = None) -> int:
    """获取世界时间（毫秒）"""
    if not settings:
        settings = get_settings()
    return settings.world_elapsed_ms


def get_world_time_text(settings: Optional[Settings] = None) -> str:
    """获取世界时间文本"""
    elapsed = get_world_time_ms(settings)
    return format_world_elapsed(elapsed)


def record_character_history(character: Character, event_type: str, description: str, metadata: Optional[Dict[str, Any]] = None):
    """记录角色历史"""
    histories = get_character_histories()
    entry = CharacterHistoryEntry(
        character_id=character.id,
        event_type=event_type,
        description=description,
        real_timestamp_ms=int(time.time() * 1000),
        world_timestamp_ms=get_world_time_ms(),
        snapshot=character.model_dump(),
        metadata=metadata or {},
    )
    histories.append(entry)
    save_character_histories(histories)


# =====================================================================
#  角色死亡/纪念
# =====================================================================

def build_memorial_record(character: Character) -> Dict[str, Any]:
    """构建纪念记录"""
    return {
        "id": character.id,
        "name": character.name,
        "age": character.age,
        "gender": character.gender,
        "occupation": character.occupation,
        "personality": character.personality,
        "death_time": character.death_time,
        "death_cause": character.death_cause,
        "lifespan": character.age,
        "memories": getattr(character, 'experience_skills', {}),
    }


def store_memorial_memory(character: Character, cause: str):
    """存储纪念记忆"""
    from models import MemoryType
    from services.memory_service import store_memory
    
    content = f"{character.name}（{character.age}岁，{character.occupation}）因{cause}去世。"
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(store_memory(
                character_id=character.id,
                memory_type=MemoryType.EVENT,
                content=content,
                importance=1.0,
                emotion="悲伤",
                related_entities=[character.name],
            ))
        else:
            loop.run_until_complete(store_memory(
                character_id=character.id,
                memory_type=MemoryType.EVENT,
                content=content,
                importance=1.0,
                emotion="悲伤",
                related_entities=[character.name],
            ))
    except Exception:
        pass


def mark_character_deceased(character: Character, cause: str, now_ms: Optional[int] = None):
    """标记角色死亡"""
    character.is_alive = False
    character.death_time = now_ms or int(time.time() * 1000)
    character.death_cause = cause
    store_memorial_memory(character, cause)


def apply_parental_support(character: Character, characters: List[Character], stage: str) -> float:
    """应用父母支持（经济）"""
    if stage not in ["儿童", "青少年"]:
        return 0.0
    
    parents = [c for c in characters if c.id in (character.parent_ids or []) and c.is_alive]
    if not parents:
        return 0.0
    
    total_support = 0
    for parent in parents:
        support = max(0, parent.money * 0.1)
        parent.money -= support
        character.money += support
        total_support += support
    
    return total_support


def maybe_get_accidental_death_cause(character: Character) -> Optional[str]:
    """随机获取意外死亡原因"""
    if character.age < 5:
        return None
    
    causes = [
        "意外事故", "突发疾病", "自然灾害", "交通事故",
    ]
    probability = 0.001  # 0.1% 概率
    if character.age > 70:
        probability = 0.005
    if character.money < 0:
        probability = 0.003
    
    if random.random() < probability:
        return random.choice(causes)
    return None


# =====================================================================
#  头像/签名刷新
# =====================================================================

async def refresh_character_avatar_for_stage(character: Character, forced: bool = False):
    """刷新角色头像"""
    from services.ai_service import generate_avatar
    
    now_ms = int(time.time() * 1000)
    if not forced and not can_refresh_avatar(character, now_ms):
        return
    
    new_avatar = await generate_avatar(character)
    if new_avatar:
        character.avatar_url = new_avatar
        character.last_avatar_change_time = now_ms
        if not character.avatar_change_history:
            character.avatar_change_history = []
        character.avatar_change_history.append(now_ms)


async def generate_new_signature(character: Character, memory_context: str = "") -> Optional[str]:
    """生成新签名"""
    from services.ai_service import generate_new_signature as ai_gen_sig
    return await ai_gen_sig(character, memory_context)


# =====================================================================
#  AI 建议
# =====================================================================

async def suggest_occupation_for_character(request: SuggestOccupationRequest) -> str:
    """AI 建议职业"""
    from services.ai_service import suggest_occupation_for_character as ai_suggest_occ
    return await ai_suggest_occ(request)


async def suggest_personality_for_character(request: SuggestPersonalityRequest) -> str:
    """AI 建议性格"""
    from services.ai_service import suggest_personality_for_character as ai_suggest_pers
    return await ai_suggest_pers(request)


# =====================================================================
#  位置更新
# =====================================================================

def update_character_location(
    character: Character,
    location: str,
    source: str = "manual",
):
    """更新角色位置"""
    character.current_location_id = location
    character.updated_at = int(time.time() * 1000)
    
    # 保存更新
    characters = get_characters()
    for i, c in enumerate(characters):
        if c.id == character.id:
            characters[i] = character
            break
    save_characters(characters)
