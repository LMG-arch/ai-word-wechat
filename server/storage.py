"""
AIWeChat 数据存储模块
JSON 文件加载/保存函数，数据访问层。
从 main.py 提取，保持向后兼容。
"""

from __future__ import annotations

import json
import os
import random
from datetime import datetime
from typing import Optional, List, Dict, Any

from models import (
    Character, ChatMessage, MomentPost, TaskItem, Company, EconomyLog,
    CharacterSchedule, LocationRecord, LogEntry, Settings, ApiConfig, UserProfile,
    Memory, PrivateGroupChat, CharacterHistoryEntry, MemoryType,
    LlmUsageRecord, ImageUsageRecord, SuggestOccupationRequest, SuggestPersonalityRequest
)
from config import (
    DATA_DIR, AVATARS_DIR,
    CHARACTERS_FILE, MESSAGES_FILE, MOMENTS_FILE, SCHEDULES_FILE,
    SETTINGS_FILE, LOGS_FILE, TASKS_FILE, COMPANIES_FILE,
    ECONOMY_LOGS_FILE, LOCATION_HISTORY_FILE, CHARACTER_HISTORY_FILE,
    API_CONFIGS_FILE, LLM_USAGE_FILE, WORLD_MAP_FILE, MEMORIES_FILE,
    MEMORY_DB_FILE, PRIVATE_GROUPS_FILE, WORLD_BIND_KEYS,
    DEFAULT_WORLD_MAP, AVATAR_REFRESH_INTERVAL_MS, SIGNATURE_REFRESH_INTERVAL_MS,
    MILLISECONDS_PER_DAY, WORLD_MONTH_MS
)

# ==================== 基础 JSON 读写 ====================

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


# ==================== 世界地图 ====================

def _deep_copy_world_template() -> Dict[str, Any]:
    return json.loads(json.dumps(DEFAULT_WORLD_MAP))


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
        roads_out = json.loads(json.dumps(DEFAULT_WORLD_MAP.get("roads") or []))

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

    bind_tpl = {x.get("bind"): x for x in DEFAULT_WORLD_MAP.get("landmarks") or [] if x.get("bind")}
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
        w0 = DEFAULT_WORLD_MAP.get("water")
        if isinstance(w0, dict):
            water_out = json.loads(json.dumps(w0))

    return {
        "city_name": city,
        "lore": lore,
        "roads": roads_out[:18],
        "landmarks": landmarks_out[:28],
        "water": water_out,
    }


# ==================== 角色存储 ====================

def get_characters() -> List[Character]:
    data = load_json(CHARACTERS_FILE, [])
    return [Character(**char) for char in data]


def save_characters(characters: List[Character]):
    save_json(CHARACTERS_FILE, [char.model_dump() for char in characters])


def repair_broken_local_avatar_urls() -> int:
    """
    avatar_url 若为 /avatars/<file> 但 web/data 下均无该文件，则清空引用，避免反复 404。
    启动时在 sync_legacy 之后调用。
    """
    legacy_av = os.path.join(DATA_DIR, "avatars")
    chars = get_characters()
    fixed = 0
    for c in chars:
        u = c.avatar_url
        if not u or not isinstance(u, str):
            continue
        if not u.startswith("/avatars/"):
            continue
        fn = u[len("/avatars/"):].strip()
        if not fn or ".." in fn or "/" in fn or "\\" in fn:
            continue
        primary = os.path.join(AVATARS_DIR, fn)
        legacy = os.path.join(legacy_av, fn)
        if not os.path.isfile(primary) and not os.path.isfile(legacy):
            c.avatar_url = None
            fixed += 1
    if fixed:
        save_characters(chars)
    return fixed


# ==================== 消息存储 ====================

def get_messages() -> List[ChatMessage]:
    data = load_json(MESSAGES_FILE, [])
    return [ChatMessage(**msg) for msg in data]


def save_messages(messages: List[ChatMessage]):
    save_json(MESSAGES_FILE, [msg.model_dump() for msg in messages])


# ==================== 私聊群组 ====================

def get_private_groups() -> List[PrivateGroupChat]:
    data = load_json(PRIVATE_GROUPS_FILE, [])
    return [PrivateGroupChat(**item) for item in data]


def save_private_groups(groups: List[PrivateGroupChat]):
    save_json(PRIVATE_GROUPS_FILE, [item.model_dump() for item in groups])


# ==================== 朋友圈 ====================

def get_moments() -> List[MomentPost]:
    data = load_json(MOMENTS_FILE, [])
    return [MomentPost(**item) for item in data]


def save_moments(moments: List[MomentPost]):
    save_json(MOMENTS_FILE, [item.model_dump() for item in moments])


# ==================== 任务 ====================

def get_tasks() -> List[TaskItem]:
    data = load_json(TASKS_FILE, [])
    return [TaskItem(**item) for item in data]


def save_tasks(tasks: List[TaskItem]):
    save_json(TASKS_FILE, [item.model_dump() for item in tasks])


# ==================== 公司 ====================

def get_companies() -> List[Company]:
    data = load_json(COMPANIES_FILE, [])
    return [Company(**item) for item in data]


def save_companies(companies: List[Company]):
    save_json(COMPANIES_FILE, [item.model_dump() for item in companies])


# ==================== 日程 ====================

def get_schedules() -> List[CharacterSchedule]:
    data = load_json(SCHEDULES_FILE, [])
    return [CharacterSchedule(**item) for item in data]


def save_schedules(schedules: List[CharacterSchedule]):
    save_json(SCHEDULES_FILE, [item.model_dump() for item in schedules])


# ==================== 经济日志 ====================

def get_economy_logs() -> List[EconomyLog]:
    data = load_json(ECONOMY_LOGS_FILE, [])
    return [EconomyLog(**item) for item in data]


def save_economy_logs(logs: List[EconomyLog]):
    save_json(ECONOMY_LOGS_FILE, [item.model_dump() for item in logs])


# ==================== 位置历史 ====================

def get_location_history(character_id: Optional[str] = None, limit: int = 500) -> List[LocationRecord]:
    data = load_json(LOCATION_HISTORY_FILE, [])
    items = [LocationRecord(**item) for item in data]
    if character_id:
        items = [item for item in items if item.character_id == character_id]
    items.sort(key=lambda x: x.timestamp, reverse=True)
    return items[:max(1, min(limit, 5000))]


def save_location_history(records: List[LocationRecord]):
    save_json(LOCATION_HISTORY_FILE, [item.model_dump() for item in records])


# ==================== 日志 ====================

def get_logs() -> List[LogEntry]:
    data = load_json(LOGS_FILE, [])
    return [LogEntry(**log) for log in data]


def save_logs(logs: List[LogEntry]):
    save_json(LOGS_FILE, [log.model_dump() for log in logs])


def add_log(character_name: str, action_type: str, description: str):
    """添加一条日志"""
    logs = get_logs()
    entry = LogEntry(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        character_name=character_name,
        action_type=action_type,
        description=description,
    )
    logs.insert(0, entry)
    if len(logs) > 2000:
        logs = logs[:2000]
    save_logs(logs)
    return entry


# ==================== 设置 ====================

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
            "user_profile": UserProfile().model_dump(),
        }
    )
    if isinstance(data, dict) and not data.get("user_profile"):
        data["user_profile"] = UserProfile().model_dump()
    settings = Settings(**data) if isinstance(data, dict) else Settings()
    settings.time_speed = max(1, min(30, int(settings.time_speed)))
    settings.auto_moment_interval_minutes = max(1, min(120, int(settings.auto_moment_interval_minutes)))
    settings.heartbeat_interval_seconds = max(10, min(600, int(getattr(settings, "heartbeat_interval_seconds", 60) or 60)))
    if settings.min_lifespan > settings.max_lifespan:
        settings.min_lifespan, settings.max_lifespan = settings.max_lifespan, settings.min_lifespan
    return settings


def save_settings(settings: Settings):
    save_json(SETTINGS_FILE, settings.model_dump())


# ==================== API 配置 ====================

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


def pick_enabled_llm_config(configs: List[ApiConfig], character_llm_id: Optional[str] = None) -> Optional[ApiConfig]:
    """在已启用的 API 配置中选 LLM：角色可绑定 llm_model_id，否则取 priority 最高（同优先级取 updated_at 较新）。"""
    if character_llm_id:
        c = next((x for x in configs if x.id == character_llm_id), None)
        if c and c.api_type == "llm" and c.is_enabled:
            return c
    llms = [c for c in configs if c.api_type == "llm" and c.is_enabled]
    if not llms:
        return None
    llms.sort(key=lambda x: (getattr(x, "priority", 0), getattr(x, "updated_at", 0)), reverse=True)
    return llms[0]


def pick_enabled_vector_config(configs: List[ApiConfig]) -> Optional[ApiConfig]:
    """已启用的向量嵌入配置，按 priority / updated_at 选用。"""
    vecs = [c for c in configs if c.api_type == "vector" and c.is_enabled]
    if not vecs:
        return None
    vecs.sort(key=lambda x: (getattr(x, "priority", 0), getattr(x, "updated_at", 0)), reverse=True)
    return vecs[0]


def pick_enabled_rerank_config(configs: List[ApiConfig]) -> Optional[ApiConfig]:
    """已启用的重排模型配置，按 priority / updated_at 选用。"""
    rrs = [c for c in configs if c.api_type == "rerank" and c.is_enabled]
    if not rrs:
        return None
    rrs.sort(key=lambda x: (getattr(x, "priority", 0), getattr(x, "updated_at", 0)), reverse=True)
    return rrs[0]


# ==================== 角色历史 ====================

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


def record_character_history(character: Character, event_type: str, description: str, metadata: Optional[Dict[str, Any]] = None):
    from models import CharacterHistoryEntry
    from storage import get_world_time_ms
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


# ==================== LLM 用量记录 ====================

def get_llm_usage_records(limit: int = 200) -> List[Any]:
    """llm_usage.json 混存文本 LLM 记录与图像 API 记录，需按字段区分。"""
    data = load_json(LLM_USAGE_FILE, [])
    records: List[Any] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            if "prompt_tokens" in item:
                records.append(LlmUsageRecord(**item))
            elif "success" in item:
                records.append(ImageUsageRecord(**item))
            else:
                records.append(LlmUsageRecord(**item))
        except Exception:
            continue
    records.sort(key=lambda x: x.timestamp, reverse=True)
    return records[:limit]


def save_llm_usage_record(record: LlmUsageRecord):
    data = load_json(LLM_USAGE_FILE, [])
    data.append(record.model_dump())
    if len(data) > 2000:
        data = data[-2000:]
    save_json(LLM_USAGE_FILE, data)


def record_llm_usage(response_json: dict, config, endpoint: str = "", character_id: Optional[str] = None):
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
        pass


def record_image_usage(config, endpoint: str = "", character_id: Optional[str] = None, success: bool = True, error_message: Optional[str] = None):
    """记录图像API调用"""
    from models import ImageUsageRecord
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
        data = load_json(LLM_USAGE_FILE, [])
        data.append(record.model_dump())
        if len(data) > 2000:
            data = data[-2000:]
        save_json(LLM_USAGE_FILE, data)
    except Exception:
        pass


# ==================== 工具函数 ====================

def get_world_time_ms(settings: Optional[Settings] = None) -> int:
    settings = settings or get_settings()
    return max(0, int(settings.world_elapsed_ms))


def get_world_time_text(settings: Optional[Settings] = None) -> str:
    settings = settings or get_settings()
    return format_world_elapsed(settings.world_elapsed_ms)


def format_world_elapsed(world_elapsed_ms: int) -> str:
    WORLD_DAYS_PER_MONTH = 30
    MONTHS_PER_YEAR = 12
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
    """根据年龄段生成性格修饰词"""
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
    age = character.age
    if age <= 12:
        age_factor = 0.3
    elif age <= 17:
        age_factor = 1.5
    elif age <= 30:
        age_factor = 1.3
    elif age <= 40:
        age_factor = 1.0
    elif age <= 60:
        age_factor = 0.6
    else:
        age_factor = 0.3
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


def trim_avatar_change_history(character: Character, now_ms: Optional[int] = None) -> List[int]:
    if now_ms is None:
        now_ms = int(time.time() * 1000)
    character.avatar_change_history = [
        ts for ts in (character.avatar_change_history or [])
        if now_ms - ts <= AVATAR_REFRESH_INTERVAL_MS
    ]
    return character.avatar_change_history


def trim_signature_change_history(character: Character, now_ms: Optional[int] = None) -> List[int]:
    if now_ms is None:
        now_ms = int(time.time() * 1000)
    character.signature_change_history = [
        ts for ts in (character.signature_change_history or [])
        if now_ms - ts <= SIGNATURE_REFRESH_INTERVAL_MS
    ]
    return character.signature_change_history


def can_refresh_avatar(character: Character, now_ms: Optional[int] = None) -> bool:
    recent_changes = trim_avatar_change_history(character, now_ms)
    return len(recent_changes) < 10


def can_refresh_signature(character: Character, now_ms: Optional[int] = None) -> bool:
    recent_changes = trim_signature_change_history(character, now_ms)
    return len(recent_changes) < 10


def apply_age_stage_constraints(character: Character) -> List[str]:
    notes = []
    stage = character.get_age_stage()
    if stage == "儿童":
        if character.occupation != "学生":
            old_occupation = character.occupation or "?"
            character.occupation = "学生"
            notes.append(f'年龄阶段调整，职业已从"{old_occupation}"修正为"学生"')
    elif stage == "青少年":
        if not character.occupation:
            character.occupation = "学生"
            notes.append('青少年阶段默认职业已设置为"学生"')
    elif stage == "老年" and character.age >= 65 and character.occupation in ["", "无业", "待定"]:
        character.occupation = "退休"
        notes.append('老年阶段默认职业已设置为"退休"')
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


def build_memorial_record(character: Character) -> Dict[str, Any]:
    histories = get_character_histories(character.id)
    # Import here to avoid circular dependency
    from services.memory_system import get_character_memories
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
    from services.memory_system import store_memory
    from models import MemoryType
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
