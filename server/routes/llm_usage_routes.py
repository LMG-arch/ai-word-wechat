from fastapi import APIRouter

from config import DATA_DIR
from storage import get_llm_usage_records
from models import LlmUsageStats, LlmUsageRecord, ImageUsageRecord


router = APIRouter()


def compute_llm_usage_stats() -> LlmUsageStats:
    """计算 LLM 用量统计"""
    records = get_llm_usage_records()
    stats = LlmUsageStats()
    
    for r in records:
        if isinstance(r, ImageUsageRecord):
            stats.image_total_calls += 1
            if r.success:
                stats.image_success_calls += 1
            else:
                stats.image_failed_calls += 1
            config_key = f"{r.config_id or 'unknown'}"
            if config_key not in stats.image_by_config:
                stats.image_by_config[config_key] = {"total": 0, "success": 0, "failed": 0}
            stats.image_by_config[config_key]["total"] += 1
            if r.success:
                stats.image_by_config[config_key]["success"] += 1
            else:
                stats.image_by_config[config_key]["failed"] += 1
            model_key = r.model_name or "unknown"
            if model_key not in stats.by_model:
                stats.by_model[model_key] = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            stats.by_model[model_key]["calls"] += 1
            ep_key = r.endpoint or "unknown"
            if ep_key not in stats.by_endpoint:
                stats.by_endpoint[ep_key] = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            stats.by_endpoint[ep_key]["calls"] += 1
            cfg_key = f"{r.config_id or 'unknown'}"
            if cfg_key not in stats.by_config:
                stats.by_config[cfg_key] = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            stats.by_config[cfg_key]["calls"] += 1
            continue

        if not isinstance(r, LlmUsageRecord):
            continue
        stats.total_calls += 1
        stats.total_prompt_tokens += r.prompt_tokens or 0
        stats.total_completion_tokens += r.completion_tokens or 0
        stats.total_tokens += (r.prompt_tokens or 0) + (r.completion_tokens or 0)

        model_key = r.model_name or "unknown"
        if model_key not in stats.by_model:
            stats.by_model[model_key] = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        stats.by_model[model_key]["calls"] += 1
        stats.by_model[model_key]["prompt_tokens"] += r.prompt_tokens or 0
        stats.by_model[model_key]["completion_tokens"] += r.completion_tokens or 0
        stats.by_model[model_key]["total_tokens"] += (r.prompt_tokens or 0) + (r.completion_tokens or 0)

        ep_key = r.endpoint or "unknown"
        if ep_key not in stats.by_endpoint:
            stats.by_endpoint[ep_key] = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        stats.by_endpoint[ep_key]["calls"] += 1
        stats.by_endpoint[ep_key]["prompt_tokens"] += r.prompt_tokens or 0
        stats.by_endpoint[ep_key]["completion_tokens"] += r.completion_tokens or 0
        stats.by_endpoint[ep_key]["total_tokens"] += (r.prompt_tokens or 0) + (r.completion_tokens or 0)

        cfg_key = f"{r.config_id or 'unknown'}"
        if cfg_key not in stats.by_config:
            stats.by_config[cfg_key] = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        stats.by_config[cfg_key]["calls"] += 1
        stats.by_config[cfg_key]["prompt_tokens"] += r.prompt_tokens or 0
        stats.by_config[cfg_key]["completion_tokens"] += r.completion_tokens or 0
        stats.by_config[cfg_key]["total_tokens"] += (r.prompt_tokens or 0) + (r.completion_tokens or 0)

    return stats


@router.get("/api/llm-usage/stats")
async def get_llm_usage_stats():
    """获取 LLM 用量统计信息"""
    stats = compute_llm_usage_stats()
    return {"success": True, "data": stats.model_dump()}


@router.get("/api/llm-usage/history")
async def get_llm_usage_history(limit: int = 100, endpoint: str = "", model: str = ""):
    """获取 LLM 用量历史记录"""
    records = get_llm_usage_records(limit=limit)
    if endpoint:
        records = [r for r in records if r.endpoint == endpoint]
    if model:
        records = [r for r in records if model.lower() in (r.model_name or "").lower()]
    return {"success": True, "data": [r.model_dump() for r in records]}


@router.get("/api/llm-usage/models")
async def get_llm_usage_by_model():
    """按模型分组获取用量统计"""
    stats = compute_llm_usage_stats()
    return {"success": True, "data": {"by_model": stats.by_model, "by_endpoint": stats.by_endpoint, "by_config": stats.by_config}}
