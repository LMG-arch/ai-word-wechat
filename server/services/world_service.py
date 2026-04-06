"""
AIWeChat 世界地图与位置服务模块
世界地图加载/生成、角色位置管理、相遇检测、日程生成。
"""

from __future__ import annotations

import json
import os
import time
import random
from typing import Optional, List, Dict, Any

from config import (
    DATA_DIR, WORLD_LOCATION_SLOT_MS, MILLISECONDS_PER_DAY
)


def _deep_copy_world_template() -> Dict[str, Any]:
    """深拷贝世界地图模板"""
    from config import DEFAULT_WORLD_MAP
    return json.loads(json.dumps(DEFAULT_WORLD_MAP))


def load_persisted_world_map() -> Optional[Dict[str, Any]]:
    """加载持久化的世界地图"""
    from storage import load_json
    data = load_json(os.path.join(DATA_DIR, "world_map.json"), None)
    if isinstance(data, dict) and data.get("city_name"):
        return data
    return None


def save_persisted_world_map(meta: Dict[str, Any]):
    """保存世界地图"""
    from storage import save_json
    save_json(os.path.join(DATA_DIR, "world_map.json"), meta)


def get_active_world_map() -> Dict[str, Any]:
    """获取当前活跃的世界地图"""
    p = load_persisted_world_map()
    if p:
        return p
    return _deep_copy_world_template()


def randomized_default_world_map() -> Dict[str, Any]:
    """生成随机化的默认世界地图"""
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
    """钳位地图坐标"""
    try:
        xf = float(x)
        yf = float(y)
    except (TypeError, ValueError):
        xf, yf = 50.0, 50.0
    return max(lo, min(hi, xf)), max(lo, min(hi, yf))


def normalize_world_map_payload(obj: Any) -> Optional[Dict[str, Any]]:
    """标准化世界地图载荷"""
    from config import DEFAULT_WORLD_MAP
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
    for key in ["办公室", "工作室", "学校", "医院", "书房", "餐厅", "社交场所", "城市"]:
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


async def ensure_world_map_initialized():
    """确保世界地图已初始化"""
    existing = load_persisted_world_map()
    if not existing:
        save_persisted_world_map(_deep_copy_world_template())


def resolve_location_base(location_name: str) -> tuple[float, float]:
    """解析地点基础坐标"""
    meta = get_active_world_map()
    for lm in (meta.get("landmarks") or []):
        if lm.get("name") == location_name:
            return float(lm.get("x", 50)), float(lm.get("y", 50))
    return 50.0, 50.0


def resolve_location_coordinates(
    location_name: str,
    drift: bool = True
) -> tuple[float, float]:
    """解析地点坐标（可加入随机漂移）"""
    x, y = resolve_location_base(location_name)
    if drift:
        x += random.uniform(-2, 2)
        y += random.uniform(-2, 2)
    return round(max(0, min(100, x)), 2), round(max(0, min(100, y)), 2)


def world_hour_of_day(world_elapsed_ms: int) -> float:
    """计算世界时间的小时"""
    total_hours = world_elapsed_ms / (60 * 60 * 1000)
    return total_hours % 24


def pick_schedule_location_for_world_time(character, world_elapsed_ms: int) -> tuple[str, str]:
    """根据世界时间选择日程位置"""
    hour = world_hour_of_day(world_elapsed_ms)
    loc_map = {
        (6, 9): ("home", "家中"),
        (9, 12): ("work", "办公室"),
        (12, 14): ("lunch", "餐厅"),
        (14, 18): ("work", "办公室"),
        (18, 22): ("leisure", "社交场所"),
        (22, 24): ("home", "家中"),
        (0, 6): ("home", "家中"),
    }
    for (start, end), (loc_id, loc_name) in loc_map.items():
        if start <= hour < end:
            return loc_id, loc_name
    return "home", "家中"


def update_character_location(
    character,
    location: str,
    source: str = "manual",
):
    """更新角色位置"""
    from storage import get_characters, save_characters
    
    character.current_location_id = location
    character.updated_at = int(time.time() * 1000)
    
    characters = get_characters()
    for i, c in enumerate(characters):
        if c.id == character.id:
            characters[i] = character
            break
    save_characters(characters)


def detect_encounters(window_minutes: int = 5) -> Dict[str, Any]:
    """检测角色相遇"""
    from storage import get_characters
    
    characters = [c for c in get_characters() if c.is_alive]
    encounters = []
    
    # 按位置分组
    location_groups: Dict[str, List] = {}
    for char in characters:
        loc = char.current_location_id or "未知"
        if loc not in location_groups:
            location_groups[loc] = []
        location_groups[loc].append(char)
    
    # 检测同一地点的多角色
    for loc, chars in location_groups.items():
        if len(chars) >= 2:
            encounters.append({
                "location": loc,
                "characters": [c.name for c in chars],
                "character_ids": [c.id for c in chars],
            })
    
    return {
        "encounters": encounters,
        "total": len(encounters),
    }


async def generate_schedule_for_character(character, day_index: int) -> Any:
    """为角色生成日程"""
    from storage import get_schedules, save_schedules
    from models import CharacterSchedule, ScheduleEvent
    
    settings = get_settings()
    world_time = settings.world_elapsed_ms
    
    events = []
    # 根据角色职业和时间生成日程
    hour = world_hour_of_day(world_time)
    
    schedule_patterns = {
        "程序员": [
            (9, 12, "work", "办公室", "写代码"),
            (12, 14, "lunch", "餐厅", "午餐休息"),
            (14, 18, "work", "办公室", "继续编码"),
            (18, 20, "leisure", "社交场所", "放松时间"),
        ],
        "教师": [
            (8, 12, "work", "学校", "上课"),
            (12, 14, "lunch", "餐厅", "午餐"),
            (14, 17, "work", "学校", "备课/批改作业"),
            (17, 19, "leisure", "家中", "休息"),
        ],
    }
    
    occupation = character.occupation
    patterns = schedule_patterns.get(occupation, [
        (9, 12, "work", "办公室", "工作"),
        (12, 14, "lunch", "餐厅", "午餐"),
        (14, 18, "work", "办公室", "工作"),
        (18, 20, "leisure", "社交场所", "休闲"),
    ])
    
    for start_h, end_h, event_type, location, description in patterns:
        events.append(ScheduleEvent(
            start_hour=start_h,
            end_hour=end_h,
            event_type=event_type,
            location=location,
            description=description,
        ))
    
    schedule = CharacterSchedule(
        character_id=character.id,
        character_name=character.name,
        day_index=day_index,
        events=events,
        generated_at=int(time.time() * 1000),
    )
    
    schedules = get_schedules()
    # 移除旧的
    schedules = [s for s in schedules if not (s.character_id == character.id and s.day_index == day_index)]
    schedules.append(schedule)
    save_schedules(schedules)
    
    return schedule
