from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import time
import aiohttp

from config import DATA_DIR
from models import ApiConfig, CreateApiConfigRequest
from storage import (
    get_settings, save_settings, get_api_configs, get_api_config_by_id,
    save_api_configs, get_logs, save_logs,
)
from services.ai_service import record_llm_usage


router = APIRouter()


def get_preset_models(api_type: str) -> list:
    """获取预设模型列表"""
    if api_type == 'llm':
        return ['gpt-3.5-turbo', 'gpt-4', 'gpt-4o', 'claude-3-haiku', 'claude-3-sonnet']
    elif api_type == 'image':
        return ['dall-e-3', 'dall-e-2', 'stable-diffusion']
    return []

def _add_log(character_name: str, action_type: str, description: str):
    try:
        from models import LogEntry
        from datetime import datetime
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


class TestApiConfigRequest(BaseModel):
    """测试 API 配置请求"""
    api_url: str
    api_key: str
    api_type: str = "llm"
    selected_model: str = ""


@router.get("/api/settings")
async def get_app_settings():
    """Get app settings"""
    settings = get_settings()
    return {"success": True, "data": settings.model_dump()}


@router.put("/api/settings")
async def update_app_settings(settings_data: Dict[str, Any]):
    """Update app settings"""
    from models import Settings
    current_settings = get_settings()
    merged = current_settings.model_dump()
    incoming = {key: value for key, value in settings_data.items() if value is not None}
    up_in = incoming.pop("user_profile", None)
    merged.update(incoming)
    if up_in is not None and isinstance(up_in, dict):
        cur_up = merged.get("user_profile") or {}
        if isinstance(cur_up, dict):
            merged["user_profile"] = {**cur_up, **up_in}
        else:
            merged["user_profile"] = up_in
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
    merged["chat_use_llm"] = bool(merged.get("chat_use_llm", current_settings.chat_use_llm))
    merged["memory_use_embedding"] = bool(merged.get("memory_use_embedding", current_settings.memory_use_embedding))
    merged["min_lifespan"] = int(merged.get("min_lifespan", current_settings.min_lifespan))
    merged["max_lifespan"] = int(merged.get("max_lifespan", current_settings.max_lifespan))
    if merged["min_lifespan"] > merged["max_lifespan"]:
        merged["min_lifespan"], merged["max_lifespan"] = merged["max_lifespan"], merged["min_lifespan"]
    settings = Settings(**merged)
    save_settings(settings)
    _add_log("system", "settings", f"time speed={settings.time_speed}x, lifespan={settings.min_lifespan}-{settings.max_lifespan}")
    return {"success": True, "data": settings.model_dump()}


@router.get("/api/api-configs")
async def list_api_configs():
    """获取所有 API 配置"""
    configs = get_api_configs()
    result = []
    for config in configs:
        config_dict = config.model_dump()
        config_dict['api_key'] = '***' + config.api_key[-4:] if len(config.api_key) > 4 else '***'
        result.append(config_dict)
    return {"success": True, "data": result}


@router.get("/api/api-configs/{config_id}")
async def get_api_config(config_id: str):
    """获取 API 配置详情"""
    config = get_api_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return {"success": True, "data": config.model_dump()}


@router.post("/api/api-configs")
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

    _add_log("系统", "API 配置", f"创建 API 配置\"{config.name}\" ({config.provider})")

    return {"success": True, "data": config.model_dump()}


@router.put("/api/api-configs/{config_id}")
async def update_api_config(config_id: str, request: CreateApiConfigRequest):
    """更新 API 配置"""
    configs = get_api_configs()

    for i, config in enumerate(configs):
        if config.id == config_id:
            config.name = request.name
            config.api_type = request.api_type
            config.provider = request.provider
            config.api_url = request.api_url
            if request.api_key and not request.api_key.startswith('***'):
                config.api_key = request.api_key
            config.models = request.models
            config.selected_model = request.selected_model
            config.is_enabled = request.is_enabled
            config.priority = request.priority
            config.updated_at = int(time.time() * 1000)
            configs[i] = config
            save_api_configs(configs)

            _add_log("系统", "API 配置", f"更新 API 配置\"{config.name}\"")

            return {"success": True, "data": config.model_dump()}

    raise HTTPException(status_code=404, detail="配置不存在")


@router.delete("/api/api-configs/{config_id}")
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

    _add_log("系统", "API 配置", f"删除 API 配置\"{config_to_delete.name}\"")

    return {"success": True}


@router.post("/api/api-configs/{config_id}/toggle")
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
            _add_log("系统", "API 配置", f"{status} API 配置\"{config.name}\"")

            return {"success": True, "data": config.model_dump()}

    raise HTTPException(status_code=404, detail="配置不存在")


@router.post("/api/api-configs/test")
async def test_api_config(request: TestApiConfigRequest):
    """测试 API 配置是否可用"""
    try:
        headers = {
            "Authorization": f"Bearer {request.api_key}",
            "Content-Type": "application/json"
        }
        
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
                try:
                    result = await response.json()
                except Exception as e:
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


@router.get("/api/api-configs/models")
async def get_available_models(
    api_url: str,
    api_key: str,
    api_type: str = "llm"
):
    """获取平台可用的所有模型列表"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        models_url = api_url.rsplit('/', 1)[0] + '/models' if '/chat/' in api_url or '/images/' in api_url or '/embeddings/' in api_url else api_url
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(models_url, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    models = result.get('data', [])
                    
                    filtered_models = []
                    for model in models:
                        model_id = model.get('id', '') if isinstance(model, dict) else str(model)
                        
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
                    preset_models = get_preset_models(api_type)
                    return {
                        "success": True,
                        "data": preset_models,
                        "total": len(preset_models),
                        "note": "无法从 API 获取模型列表，返回预设模型"
                    }
    except Exception as e:
        preset_models = get_preset_models(api_type)
        return {
            "success": True,
            "data": preset_models,
            "total": len(preset_models),
            "note": f"获取失败：{str(e)}，返回预设模型"
        }
