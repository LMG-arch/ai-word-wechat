"""
AI 社交世界 - 后端服务
提供 RESTful API 接口，数据存储在本地 JSON 文件
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import os
import uuid
import time

app = FastAPI(title="AI 社交世界 API")

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

# 数据文件路径
CHARACTERS_FILE = os.path.join(DATA_DIR, "characters.json")
MESSAGES_FILE = os.path.join(DATA_DIR, "messages.json")
LOGS_FILE = os.path.join(DATA_DIR, "logs.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
API_CONFIGS_FILE = os.path.join(DATA_DIR, "api_configs.json")


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
    created_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    last_avatar_change_time: int = 0
    last_signature_change_time: int = 0
    is_alive: bool = True
    death_time: Optional[int] = None

    def get_age_stage(self) -> str:
        if self.age <= 12:
            return "儿童"
        elif self.age <= 17:
            return "青少年"
        elif self.age <= 40:
            return "青年"
        elif self.age <= 60:
            return "中年"
        return "老年"

    def get_avatar_initials(self) -> str:
        return self.name[0] if self.name else "?"


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    sender_id: str
    content: str
    message_type: str = "text"  # text, image, voice
    image_url: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    is_read: bool = False
    is_from_user: bool = True


class LogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str
    character_name: str
    action_type: str
    description: str


class Settings(BaseModel):
    time_speed: int = 30
    enable_death_mechanism: bool = False
    api_configs: dict = {}


class CreateCharacterRequest(BaseModel):
    name: str
    age: int = 25
    gender: str = "男"
    occupation: str
    personality: str


class SendMessageRequest(BaseModel):
    conversation_id: str
    content: str


class ChatResponse(BaseModel):
    content: str
    character_id: str
    timestamp: int


class ApiConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    api_type: str  # llm, image, vector, rerank
    provider: str  # openai, azure, baidu, etc.
    api_url: str
    api_key: str
    model_name: str
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
    model_name: str
    is_enabled: bool = True
    priority: int = 0


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


def get_logs() -> List[LogEntry]:
    data = load_json(LOGS_FILE, [])
    return [LogEntry(**log) for log in data]


def save_logs(logs: List[LogEntry]):
    save_json(LOGS_FILE, [log.model_dump() for log in logs])


def get_settings() -> Settings:
    data = load_json(SETTINGS_FILE, {"time_speed": 30})
    return Settings(**data) if isinstance(data, dict) else Settings()


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


def add_log(character_name: str, action_type: str, description: str):
    logs = get_logs()
    now = datetime.now().strftime("%H:%M:%S")
    log = LogEntry(
        timestamp=now,
        character_name=character_name,
        action_type=action_type,
        description=description
    )
    logs.insert(0, log)
    if len(logs) > 100:
        logs = logs[:100]
    save_logs(logs)
    return log


# ==================== AI 回复生成 ====================

def generate_ai_reply(character: Character, user_input: str) -> str:
    """根据角色人设生成回复"""
    replies = [
        f"嗯，{user_input}，这个问题挺有意思的。",
        f"作为{character.occupation}，我觉得{user_input}值得思考。",
        f"哈哈，{user_input}，让我想起了之前的经历。",
        f"{user_input}吗？我需要好好想想。",
        f"从{character.personality}的角度来看，{user_input}确实有道理。",
        f"我{character.age}岁了，遇到过类似的情况。{user_input}...让我想想。",
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
    
    import random
    return prefix + random.choice(replies)


# ==================== API 接口 ====================

@app.get("/")
async def root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "web", "index.html"))


@app.get("/api/characters")
async def list_characters():
    """获取所有角色列表"""
    characters = get_characters()
    return {"success": True, "data": [char.model_dump() for char in characters]}


@app.get("/api/characters/{character_id}")
async def get_character(character_id: str):
    """获取角色详情"""
    characters = get_characters()
    for char in characters:
        if char.id == character_id:
            return {"success": True, "data": char.model_dump()}
    raise HTTPException(status_code=404, detail="角色不存在")


@app.post("/api/characters")
async def create_character(request: CreateCharacterRequest):
    """创建新角色"""
    characters = get_characters()

    character = Character(
        name=request.name,
        age=request.age,
        gender=request.gender,
        occupation=request.occupation,
        personality=request.personality
    )

    characters.append(character)
    save_characters(characters)

    add_log(character.name, "创建", f"角色\"{character.name}\"被创建，{character.age}岁，{character.occupation}")

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
    """更新角色信息"""
    characters = get_characters()
    
    for i, char in enumerate(characters):
        if char.id == character_id:
            char.name = request.name
            char.age = request.age
            char.gender = request.gender
            char.occupation = request.occupation
            char.personality = request.personality
            char.updated_at = int(time.time() * 1000)
            characters[i] = char
            save_characters(characters)
            
            add_log(char.name, "更新", f"角色信息已更新")

            return {"success": True, "data": char.model_dump()}

    raise HTTPException(status_code=404, detail="角色不存在")


@app.get("/api/messages/{conversation_id}")
async def get_conversation_messages(conversation_id: str):
    """获取会话消息"""
    messages = get_messages()
    conv_messages = [msg for msg in messages if msg.conversation_id == conversation_id]
    conv_messages.sort(key=lambda x: x.timestamp)
    return {"success": True, "data": [msg.model_dump() for msg in conv_messages]}


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
    user_message = ChatMessage(
        conversation_id=request.conversation_id,
        sender_id="user",
        content=request.content,
        is_from_user=True
    )
    messages.append(user_message)
    save_messages(messages)
    
    # 生成 AI 回复
    reply_content = generate_ai_reply(character, request.content)
    
    # 保存 AI 回复
    ai_message = ChatMessage(
        conversation_id=request.conversation_id,
        sender_id=character.id,
        content=reply_content,
        is_from_user=False
    )
    messages.append(ai_message)
    save_messages(messages)
    
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


@app.delete("/api/logs")
async def clear_logs():
    """清空日志"""
    save_logs([])
    return {"success": True}


@app.get("/api/settings")
async def get_app_settings():
    """获取应用设置"""
    settings = get_settings()
    return {"success": True, "data": settings.model_dump()}


@app.put("/api/settings")
async def update_app_settings(settings: Settings):
    """更新应用设置"""
    save_settings(settings)
    add_log("系统", "设置", f"时间倍速调整为{settings.time_speed}x")
    return {"success": True, "data": settings.model_dump()}


# ==================== API 配置接口 ====================

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
        model_name=request.model_name,
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
            if request.api_key and request.api_key != '***':
                config.api_key = request.api_key
            config.model_name = request.model_name
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


@app.get("/api/stats")
async def get_statistics():
    """获取统计信息"""
    characters = get_characters()
    messages = get_messages()
    
    # 按会话统计消息
    conversations = {}
    for msg in messages:
        conv_id = msg.conversation_id
        if conv_id not in conversations:
            conversations[conv_id] = 0
        conversations[conv_id] += 1
    
    return {
        "success": True,
        "data": {
            "character_count": len(characters),
            "message_count": len(messages),
            "conversation_count": len(conversations)
        }
    }


# 启动后台任务：年龄增长
@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    import asyncio
    
    async def age_growth_task():
        while True:
            await asyncio.sleep(60)  # 每分钟检查一次
            settings = get_settings()
            characters = get_characters()
            
            # 根据时间倍速计算年龄增长
            # 30 倍速：现实 1 分钟 = 角色增长 0.5 岁
            age_increase = (settings.time_speed / 60) * (1 / 60)
            
            updated = False
            for char in characters:
                if char.is_alive:
                    # 随机触发年龄增长
                    import random
                    if random.random() < 0.1:
                        char.age += 1
                        char.updated_at = int(time.time() * 1000)
                        add_log(char.name, "成长", f"年龄增长到{char.age}岁")
                        updated = True
            
            if updated:
                save_characters(characters)
    
    # 启动后台任务
    import asyncio
    asyncio.create_task(age_growth_task())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
