"""
AI 社交世界 - 后端服务（精简入口）
提供 FastAPI 应用实例、中间件、静态文件挂载与后台任务启动。
所有路由已拆分至 routes/ 目录下的独立模块。
"""

from __future__ import annotations

import sys
import io
import os

# 修复 Windows CMD 编码和颜色问题（测试环境下跳过）
if sys.platform == 'win32' and not os.environ.get('PYTEST_CURRENT_TEST'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    os.environ['LOGURU_COLORIZE'] = 'False'

import asyncio
import time
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from contextlib import asynccontextmanager

# ==================== 应用创建 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动和关闭"""
    await startup_event()
    yield


app = FastAPI(title="AI 社交世界 API", lifespan=lifespan)

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ==================== 中间件 ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 路径常量 ====================
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

AVATARS_DIR = os.path.join(os.path.dirname(__file__), "data", "avatars")
os.makedirs(AVATARS_DIR, exist_ok=True)

IMAGE_PROMPTS_DIR = os.path.join(DATA_DIR, "image_prompts")
os.makedirs(IMAGE_PROMPTS_DIR, exist_ok=True)

# ==================== 静态文件挂载 ====================
app.mount("/avatars", StaticFiles(directory=AVATARS_DIR), name="avatars")
app.mount("/image-prompts", StaticFiles(directory=IMAGE_PROMPTS_DIR), name="image-prompts")

# ==================== 根路由 ====================
@app.get("/")
async def root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "web", "index.html"))

# ==================== 路由注册 ====================
from routes.character_routes import router as character_router
from routes.chat_routes import router as chat_router
from routes.moment_routes import router as moment_router
from routes.task_routes import router as task_router
from routes.company_routes import router as company_router
from routes.economy_routes import router as economy_router
from routes.map_routes import router as map_router
from routes.schedule_routes import router as schedule_router
from routes.relationship_routes import router as relationship_router
from routes.memory_routes import router as memory_router
from routes.settings_routes import router as settings_router
from routes.stats_routes import router as stats_router
from routes.scheduler_routes import router as scheduler_router
from routes.llm_usage_routes import router as llm_usage_router

app.include_router(character_router)
app.include_router(chat_router)
app.include_router(moment_router)
app.include_router(task_router)
app.include_router(company_router)
app.include_router(economy_router)
app.include_router(map_router)
app.include_router(schedule_router)
app.include_router(relationship_router)
app.include_router(memory_router)
app.include_router(settings_router)
app.include_router(stats_router)
app.include_router(scheduler_router)
app.include_router(llm_usage_router)

# ==================== 生命周期管理 ====================
async def startup_event():
    """启动后台心跳任务"""
    from storage import get_settings, save_settings
    from services.heartbeat_service import run_heartbeat_tick, process_encounter_followups
    from services.task_service import run_task_engine
    from services.scheduler import run_scheduler_tick
    from services.memory_service import sync_private_groups
    from services.world_service import detect_encounters
    from services.memory_service import apply_inactivity_decay
    from services.ai_service import generate_ai_reply
    from storage import get_characters, save_characters, get_messages, save_messages, get_logs
    from datetime import datetime

    # 年龄增长和社交自动运行的内联实现
    async def process_age_growth():
        """处理角色年龄增长"""
        from services.character_service import get_world_time_ms, get_age_stage_from_age
        settings = get_settings()
        now_ms = int(time.time() * 1000)
        last = getattr(settings, 'last_age_growth_time', 0)
        if now_ms - last < 24 * 3600 * 1000:  # 每天一次
            return
        characters = get_characters()
        for char in characters:
            if char.is_alive:
                char.age += 1
                new_stage = get_age_stage_from_age(char.age)
                if char.age_stage != new_stage:
                    char.age_stage = new_stage
                    add_log(char.name, "age_growth", f"进入{new_stage}阶段，年龄: {char.age}")
        save_characters(characters)
        settings.last_age_growth_time = now_ms
        save_settings(settings)

    async def process_social_autorun():
        """社交自动运行 - 角色自动互动"""
        from services.moment_service import run_moment_auto_interactions
        settings = get_settings()
        now_ms = int(time.time() * 1000)
        last = getattr(settings, 'auto_moment_last_run_time', 0)
        if now_ms - last < 300000:  # 5分钟一次
            return
        await run_moment_auto_interactions(limit=30)
        settings.auto_moment_last_run_time = now_ms
        save_settings(settings)

    def add_log(character_name: str, action_type: str, description: str):
        try:
            from models import LogEntry
            from storage import save_logs
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

    # 初始化世界时间
    settings = get_settings()
    if settings.last_world_update_time <= 0:
        settings.last_world_update_time = int(time.time() * 1000)
        save_settings(settings)

    async def age_growth_task():
        while True:
            await asyncio.sleep(300)
            try:
                await process_age_growth()
            except Exception as e:
                add_log("system", "age_growth_error", str(e)[:120])

    async def social_autorun_task():
        while True:
            await asyncio.sleep(60)
            settings = get_settings()
            if not getattr(settings, 'enable_social_autorun', True):
                continue
            try:
                await process_social_autorun()
                settings = get_settings()
                now_ms = int(time.time() * 1000)
                enc = detect_encounters()
                await process_encounter_followups(enc.get("items") or [])
                sync_private_groups()
                apply_inactivity_decay()
                settings.auto_moment_last_run_time = now_ms
                save_settings(settings)
            except Exception as e:
                add_log("system", "social_autorun_error", str(e)[:120])

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
            await asyncio.sleep(30)
            settings = get_settings()
            if not getattr(settings, 'enable_task_engine', True):
                continue
            try:
                await run_task_engine(max_tasks_per_tick=5)
            except Exception as e:
                add_log("system", "task_engine_error", str(e)[:120])

    async def scheduler_task():
        """调度器任务 - 提醒触发、角色主动对话、节日问候"""
        while True:
            await asyncio.sleep(45)
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

    # 启动所有后台任务
    asyncio.create_task(age_growth_task())
    asyncio.create_task(social_autorun_task())
    asyncio.create_task(heartbeat_task())
    asyncio.create_task(task_engine_task())
    asyncio.create_task(scheduler_task())


if __name__ == "__main__":
    import uvicorn
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

