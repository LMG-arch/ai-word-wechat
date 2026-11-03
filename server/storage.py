"""
AIWeChat 数据存储模块
JSON 文件加载/保存函数，数据访问层。
从 main.py 提取，保持向后兼容。
"""

from __future__ import annotations

import json
import os
import random
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

from models import (
    Character, ChatMessage, MomentPost, TaskItem, Company, EconomyLog,
    CharacterSchedule, LocationRecord, LogEntry, Settings, ApiConfig, UserProfile,
    PrivateGroupChat, CharacterHistoryEntry,
    LlmUsageRecord, ImageUsageRecord, RedPacket,
)
from config import (
    DATA_DIR, AVATARS_DIR,
    CHARACTERS_FILE, MESSAGES_FILE, MOMENTS_FILE, SCHEDULES_FILE,
    SETTINGS_FILE, LOGS_FILE, TASKS_FILE, COMPANIES_FILE,
    ECONOMY_LOGS_FILE, LOCATION_HISTORY_FILE, CHARACTER_HISTORY_FILE,
    API_CONFIGS_FILE, LLM_USAGE_FILE, WORLD_MAP_FILE,
    PRIVATE_GROUPS_FILE, RED_PACKETS_FILE, WORLD_BIND_KEYS,
    DEFAULT_WORLD_MAP, AVATAR_REFRESH_INTERVAL_MS, SIGNATURE_REFRESH_INTERVAL_MS
)

# ==================== 基础 JSON 读写 ====================

# 同一文件路径的写入锁：避免多请求 / 后台任务并发写造成内容交错
_FILE_LOCKS: Dict[str, threading.Lock] = {}
_FILE_LOCKS_GUARD = threading.Lock()


def _lock_for(filename: str) -> threading.Lock:
    """为每个文件路径分配一把独立的锁（懒创建）。"""
    key = os.path.abspath(filename)
    lock = _FILE_LOCKS.get(key)
    if lock is None:
        with _FILE_LOCKS_GUARD:
            lock = _FILE_LOCKS.get(key)
            if lock is None:
                lock = threading.Lock()
                _FILE_LOCKS[key] = lock
    return lock


def load_json(filename: str, default=None):
    if default is None:
        default = []
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except json.JSONDecodeError as e:
        # 文件已损坏（多半是历史「非原子写」在中断时留下的半截 JSON）。
        # 保留现场并改名备份，避免随后被一次正常 save 彻底覆盖、无处追查。
        try:
            backup = f"{filename}.corrupt.{int(time.time())}"
            os.replace(filename, backup)
            print(f"[storage] 检测到损坏 JSON：{filename}（{e}）；已备份至 {backup}，本次按默认值处理")
        except Exception as move_err:
            print(f"[storage] 损坏文件备份失败：{move_err}")
    except Exception as e:
        print(f"Error loading {filename}: {e}")
    return default


def save_json(filename: str, data) -> bool:
    """原子写入 JSON。

    先写同目录临时文件 → flush + fsync → os.replace 原子替换。
    这样即使写盘过程中进程被 kill / 磁盘写满，也不会留下半截文件把原有数据毁掉
    （旧实现直接 open(...,'w') 会先截断原文件，中途失败即全丢）。

    返回 True 表示成功，False 表示失败（调用方可据此提示，而非静默继续）。
    """
    lock = _lock_for(filename)
    tmp = f"{filename}.{os.getpid()}.tmp"
    with lock:
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, filename)
            return True
        except Exception as e:
            print(f"Error saving {filename}: {e}")
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            return False


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


# ==================== 红包 ====================

def get_red_packets() -> List[RedPacket]:
    data = load_json(RED_PACKETS_FILE, [])
    return [RedPacket(**item) for item in data]


def save_red_packets(packets: List[RedPacket]):
    save_json(RED_PACKETS_FILE, [item.model_dump() for item in packets])


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


def store_memorial_memory(character: Character, cause: str):
    import asyncio
    from models import MemoryType
    from services.memory_service import store_memory
    try:
        coro = store_memory(
            character_id=character.id,
            content=f"角色 {character.name} 于 {character.age} 岁离世，原因：{cause}。",
            memory_type=MemoryType.EVENT,
            importance=1.0,
            related_entities=["死亡", "人生终点"]
        )
        # store_memory 为异步函数：在运行中的事件循环内则调度任务，
        # 否则同步运行；两种上下文都能落库且不阻塞（纪念记忆为 best-effort）。
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            asyncio.run(coro)
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


