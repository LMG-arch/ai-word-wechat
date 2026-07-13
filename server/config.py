"""
AIWeChat 配置模块
集中管理常量、路径、环境变量等配置信息。
从 main.py 提取的配置常量，保持向后兼容。
"""

import os
import sys

# === 修复 Windows 编码 ===
# 仅在非测试环境下包装 stdout，避免干扰 pytest 等工具
if sys.platform == "win32" and not os.environ.get("PYTEST_CURRENT_TEST"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# === 路径配置 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
AVATARS_DIR = os.path.join(BASE_DIR, "web", "avatars")
IMAGE_PROMPTS_DIR = os.path.join(BASE_DIR, "web", "image_prompts")

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(AVATARS_DIR, exist_ok=True)
os.makedirs(IMAGE_PROMPTS_DIR, exist_ok=True)


def sync_legacy_asset_directories() -> None:
    """
    将历史上保存到 data/avatars、data/image_prompts 的文件复制到当前静态目录（web/avatars 等），
    避免旧数据在更换挂载路径后出现 404。
    """
    import shutil

    legacy_av = os.path.join(DATA_DIR, "avatars")
    if os.path.isdir(legacy_av) and os.path.normpath(legacy_av) != os.path.normpath(AVATARS_DIR):
        try:
            for name in os.listdir(legacy_av):
                src = os.path.join(legacy_av, name)
                dst = os.path.join(AVATARS_DIR, name)
                if os.path.isfile(src) and not os.path.exists(dst):
                    shutil.copy2(src, dst)
        except OSError:
            pass

    legacy_ip = os.path.join(DATA_DIR, "image_prompts")
    if os.path.isdir(legacy_ip) and os.path.normpath(legacy_ip) != os.path.normpath(IMAGE_PROMPTS_DIR):
        try:
            for name in os.listdir(legacy_ip):
                src = os.path.join(legacy_ip, name)
                dst = os.path.join(IMAGE_PROMPTS_DIR, name)
                if os.path.isfile(src) and not os.path.exists(dst):
                    shutil.copy2(src, dst)
        except OSError:
            pass


# === 数据文件路径 ===
DATA_FILES = {
    "characters": os.path.join(DATA_DIR, "characters.json"),
    "messages": os.path.join(DATA_DIR, "messages.json"),
    "moments": os.path.join(DATA_DIR, "moments.json"),
    "schedules": os.path.join(DATA_DIR, "schedules.json"),
    "settings": os.path.join(DATA_DIR, "settings.json"),
    "logs": os.path.join(DATA_DIR, "logs.json"),
    "tasks": os.path.join(DATA_DIR, "tasks.json"),
    "companies": os.path.join(DATA_DIR, "companies.json"),
    "economy_logs": os.path.join(DATA_DIR, "economy_logs.json"),
    "relationships": os.path.join(DATA_DIR, "relationships.json"),
    "location_history": os.path.join(DATA_DIR, "location_history.json"),
    "character_histories": os.path.join(DATA_DIR, "character_history.json"),
    "memories": os.path.join(DATA_DIR, "memories.json"),
    "api_configs": os.path.join(DATA_DIR, "api_configs.json"),
    "llm_usage": os.path.join(DATA_DIR, "llm_usage.json"),
    "image_prompt_index": os.path.join(DATA_DIR, "image_prompts", "index.json"),
    "world_map": os.path.join(DATA_DIR, "world_map.json"),
}

# SQLite 记忆数据库路径
MEMORY_DB_PATH = os.path.join(DATA_DIR, "memory.db")
MEMORY_DB_FILE = MEMORY_DB_PATH  # 向后兼容别名

# === 向后兼容：独立的文件路径常量 ===
# 这些常量被 models.py 和其他模块直接导入
CHARACTERS_FILE = DATA_FILES["characters"]
MESSAGES_FILE = DATA_FILES["messages"]
LOGS_FILE = DATA_FILES["logs"]
SETTINGS_FILE = DATA_FILES["settings"]
API_CONFIGS_FILE = DATA_FILES["api_configs"]
MEMORIES_FILE = DATA_FILES["memories"]
MOMENTS_FILE = DATA_FILES["moments"]
TASKS_FILE = DATA_FILES["tasks"]
COMPANIES_FILE = DATA_FILES["companies"]
SCHEDULES_FILE = DATA_FILES["schedules"]
ECONOMY_LOGS_FILE = DATA_FILES["economy_logs"]
LOCATION_HISTORY_FILE = DATA_FILES["location_history"]
LLM_USAGE_FILE = DATA_FILES["llm_usage"]
WORLD_MAP_FILE = DATA_FILES["world_map"]
PRIVATE_GROUPS_FILE = os.path.join(DATA_DIR, "private_groups.json")
CHARACTER_HISTORY_FILE = DATA_FILES["character_histories"]

# === 时间常量 ===
MILLISECONDS_PER_SECOND = 1000
MILLISECONDS_PER_MINUTE = 60 * MILLISECONDS_PER_SECOND
MILLISECONDS_PER_HOUR = 60 * MILLISECONDS_PER_MINUTE
MILLISECONDS_PER_DAY = 24 * MILLISECONDS_PER_HOUR
WORLD_MONTH_MS = 30 * MILLISECONDS_PER_DAY
MONTHS_PER_YEAR = 12

# === 世界时间常量 ===
WORLD_LOCATION_SLOT_MS = 2 * MILLISECONDS_PER_HOUR  # 角色位置刷新间隔
WORLD_COMPANY_BIND = "公司"  # 公司地标绑定名称

# === 世界地图绑定键 ===
# 地标类型绑定，用于 resolve_location_coordinates 等函数
WORLD_BIND_KEYS = ("办公室", "工作室", "学校", "医院", "书房", "餐厅", "社交场所", "城市")
WORLD_RESIDENTIAL_BIND = "住宅"

# === 默认世界地图模板 ===
DEFAULT_WORLD_MAP = {
    "city_name": "云海市",
    "lore": "一座依山傍海的现代都市，生活节奏适中，充满人情味。",
    "landmarks": [
        {"name": "市民广场", "x": 50, "y": 50, "bind": "广场", "type": "public"},
        {"name": "中央公园", "x": 30, "y": 40, "bind": "公园", "type": "park"},
        {"name": "商业街", "x": 60, "y": 30, "bind": "商业区", "type": "commercial"},
        {"name": "图书馆", "x": 40, "y": 60, "bind": "图书馆", "type": "education"},
        {"name": "医院", "x": 70, "y": 60, "bind": "医院", "type": "medical"},
        {"name": "大学城", "x": 20, "y": 70, "bind": "学校", "type": "education"},
        {"name": "科技园", "x": 80, "y": 40, "bind": "办公室", "type": "company"},
        {"name": "海滨大道", "x": 90, "y": 80, "bind": "海边", "type": "scenic"},
        {"name": "老街区", "x": 15, "y": 25, "bind": "住宅区", "type": "residential"},
        {"name": "美食街", "x": 55, "y": 70, "bind": "餐厅", "type": "commercial"},
    ],
    "roads": [],
    "water": [],
}

# === 头像刷新限制 ===
AVATAR_REFRESH_INTERVAL_MS = 7 * MILLISECONDS_PER_DAY  # 每周最多刷新一次
SIGNATURE_REFRESH_INTERVAL_MS = 7 * MILLISECONDS_PER_DAY  # 每周最多刷新一次
MAX_AVATAR_CHANGES = 10  # 最多保留头像变更历史
MAX_SIGNATURE_CHANGES = 10  # 最多保留签名变更历史

# === 图像尺寸配置 ===
VALID_IMAGE_SIZES = ["256x256", "512x512", "1024x1024"]

# === 记忆类型 ===
MEMORY_TYPE_EVENT = "event"
MEMORY_TYPE_SEMANTIC = "semantic"
MEMORY_TYPE_PROCEDURAL = "procedural"
MEMORY_TYPE_REFLECTION = "reflection"

# === 任务类型 ===
TASK_TYPE_TEXT = "text"
TASK_TYPE_CODE = "code"
TASK_TYPE_RESEARCH = "research"
TASK_TYPE_DESIGN = "design"

# === 任务状态 ===
TASK_STATUS_PENDING = "pending"
TASK_STATUS_IN_PROGRESS = "in_progress"
TASK_STATUS_PENDING_REVIEW = "pending_review"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"

# === 关系状态阈值 ===
RELATIONSHIP_STRANGER = 20
RELATIONSHIP_ACQUAINTANCE = 40
RELATIONSHIP_FAMILIAR = 60
RELATIONSHIP_FRIEND = 80

# === 经济常量 ===
DEFAULT_INITIAL_MONEY = 500.0
DEFAULT_COMPANY_FUNDS = 500.0
COMPANY_CREATION_COST = 1000.0
MIN_MONEY_FOR_COMPANY_CREATION = 1500.0
MIN_MONEY_FOR_COMPANY_RECRUIT = 500.0

# === 心跳常量 ===
HEARTBEAT_DEFAULT_INTERVAL = 60  # 秒
HEARTBEAT_MIN_INTERVAL = 10
HEARTBEAT_MAX_INTERVAL = 600
HEARTBEAT_MAX_CHARACTERS = 200

# === 任务引擎常量 ===
TASK_ENGINE_DEFAULT_INTERVAL = 30  # 秒
TASK_ENGINE_MAX_TASKS_PER_TICK = 5

# === 社交自动运行常量 ===
SOCIAL_AUTORUN_DEFAULT_INTERVAL = 15  # 分钟
SOCIAL_AUTORUN_MIN_INTERVAL = 1
SOCIAL_AUTORUN_MAX_INTERVAL = 120

# === LLM 调用常量 ===
LLM_REQUEST_TIMEOUT = 60  # 秒
LLM_TEMP_CHARACTER_GENERATION = 0.8
LLM_MAX_TOKENS_CHARACTER_GENERATION = 800

# === 图像 API 常量 ===
IMAGE_REQUEST_TIMEOUT = 120  # 秒
IMAGE_DOWNLOAD_TIMEOUT = 30  # 秒
IMAGE_MAX_POLL_ATTEMPTS = 60  # 异步任务最大轮询次数
IMAGE_POLL_INTERVAL = 5  # 异步任务轮询间隔（秒）

# === 设置默认值 ===
# 注意：运行时实际默认值由 models.Settings 与 storage.get_settings() 统一提供，
# 此处不再保留一份易与前者冲突的 DEFAULT_SETTINGS（详见重构说明）。

