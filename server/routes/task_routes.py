"""AIWeChat task routes"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
import time
import os
import random
import re

from config import DATA_DIR
from models import (
    TaskItem, TaskType, TaskStatus, TaskAssigneeType, Character,
    CreateTaskRequest, AssignTaskRequest, AutoTakeTaskRequest,
    SubmitTaskRequest, ReviewTaskRequest,
)
from storage import (
    get_tasks, save_tasks, get_characters, save_characters,
    get_companies, save_companies,
    get_logs, save_logs, get_settings,
)
from services.task_service import apply_reflection_after_task, apply_auto_take_task_at_index
from services.ai_service import (
    openai_choice_text,
    llm_choose_image_size,
    record_image_usage, save_image_prompt_md,
    get_api_configs,
)

router = APIRouter()


# =====================================================================
#  图像工具函数（从 ai_service 移入）
# =====================================================================
def parse_image_size(size_str: str):
    """解析图像尺寸字符串，返回 (width, height)"""
    parts = size_str.split('x')
    if len(parts) == 2:
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            pass
    return 1024, 1024


def get_aspect_ratio(size_str: str) -> str:
    """获取图像宽高比字符串，如 '16:9'"""
    w, h = parse_image_size(size_str)
    # 简化为常见比例
    if w >= h * 1.5:
        return "16:9"
    elif h >= w * 1.5:
        return "9:16"
    elif w > h:
        return "4:3"
    elif h > w:
        return "3:4"
    return "1:1"


def is_async_image_provider(provider: str, api_url: str) -> bool:
    """检查是否为异步图像提供商（如 Midjourney）"""
    return 'midjourney' in provider.lower()


async def call_async_image_api(api_url: str, headers: dict, request_data: dict, auth_headers: dict):
    """调用异步图像 API（占位实现）"""
    # Midjourney 等异步 API 需要轮询任务状态，此处简化为不支持
    return False, "Async image generation (Midjourney) not fully implemented", None


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


async def _generate_task_image(task: TaskItem, assignee: Optional[Character]) -> Optional[str]:
    """为图像任务生成实际图片"""
    import aiohttp
    configs = get_api_configs()
    image_config = None
    for config in configs:
        if config.api_type == 'image' and config.is_enabled:
            image_config = config
            break
    if not image_config:
        return None
    
    prompt = f"{task.title}: {task.description}, high quality, professional, detailed"
    provider = image_config.provider.lower()
    model = task.image_model_id if task.image_model_id else (image_config.selected_model or "dall-e-3")
    api_url = image_config.api_url
    image_size = await llm_choose_image_size(prompt, f"任务：{task.title}")
    if not image_size:
        settings = get_settings()
        image_size = settings.default_image_size or "1024x1024"
    headers = {"Authorization": f"Bearer {image_config.api_key}", "Content-Type": "application/json"}
    
    if 'stability' in provider or 'sd' in provider:
        width, height = parse_image_size(image_size)
        request_data = {
            "text_prompts": [{"text": prompt, "weight": 1}],
            "cfg_scale": 7, "height": height, "width": width,
            "steps": 30, "samples": 1
        }
    elif 'midjourney' in provider:
        ar = get_aspect_ratio(image_size)
        request_data = {"prompt": prompt, "aspect_ratio": ar}
    elif 'siliconflow' in provider or 'silicon' in provider:
        if '/chat/completions' in api_url:
            api_url = api_url.replace('/chat/completions', '/images/generations')
        elif not '/images' in api_url:
            api_url = api_url.rstrip('/') + '/v1/images/generations'
        request_data = {
            "model": model, "prompt": prompt, "image_size": image_size,
            "batch_size": 1, "num_inference_steps": 20, "guidance_scale": 7.5
        }
    elif 'modelscope' in provider or 'modelscope' in api_url.lower():
        if not api_url.endswith('/v1/images/generations'):
            api_url = api_url.rstrip('/') + '/v1/images/generations'
        request_data = {"model": model, "prompt": prompt, "image_size": image_size}
    else:
        if '/chat/completions' in api_url:
            api_url = api_url.replace('/chat/completions', '/images/generations')
        elif api_url.endswith('/v1') or api_url.endswith('/v1/'):
            api_url = api_url.rstrip('/') + '/images/generations'
        elif not '/images' in api_url:
            api_url = api_url.rstrip('/') + '/v1/images/generations'
        request_data = {"model": model, "prompt": prompt, "n": 1, "size": image_size, "quality": "standard", "response_format": "url"}
    
    try:
        if is_async_image_provider(provider, image_config.api_url):
            success, image_url_or_error, _ = await call_async_image_api(
                api_url, headers, request_data, headers
            )
            if success and image_url_or_error:
                record_image_usage(image_config, "task_image_generation", task.assignee_id, success=True)
                _add_log("系统", "任务图像", f"为任务《{task.title}》生成图片成功，尺寸: {image_size}")
                save_image_prompt_md(prompt, f"任务图像：{task.title}", image_url_or_error, task.title)
                return image_url_or_error
            else:
                record_image_usage(image_config, "task_image_generation", task.assignee_id, success=False, error_message=image_url_or_error)
                return None
        else:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
                async with session.post(api_url, headers=headers, json=request_data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        image_url = None
                        if 'data' in result and len(result['data']) > 0:
                            image_url = result['data'][0].get('url') or result['data'][0].get('b64_json')
                        elif 'images' in result and len(result['images']) > 0:
                            image_url = result['images'][0].get('url') or result['images'][0].get('b64_json')
                        elif 'url' in result:
                            image_url = result['url']
                        elif 'image_url' in result:
                            image_url = result['image_url']
                        if image_url:
                            record_image_usage(image_config, "task_image_generation", task.assignee_id, success=True)
                            _add_log("系统", "任务图像", f"为任务《{task.title}》生成图片成功，尺寸: {image_size}")
                            save_image_prompt_md(prompt, f"任务图像：{task.title}", image_url, task.title)
                            return image_url
                        else:
                            record_image_usage(image_config, "task_image_generation", task.assignee_id, success=False, error_message="无法解析图像响应")
                    else:
                        record_image_usage(image_config, "task_image_generation", task.assignee_id, success=False, error_message=f"HTTP {resp.status}")
    except Exception as e:
        record_image_usage(image_config, "task_image_generation", task.assignee_id, success=False, error_message=str(e))
        _add_log("系统", "警告", f"任务图像生成失败：{str(e)}")
    return None


async def _generate_task_code(task: TaskItem, assignee: Optional[Character]) -> str:
    """为代码任务生成有意义的代码"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return f"# {task.title}\nprint('Task completed')"
    model_name = (assignee.llm_model_id if assignee and assignee.llm_model_id else (llm_config.selected_model or "gpt-3.5-turbo"))
    exp_note = ""
    if assignee:
        exp = assignee.experience_skills.get("code", {})
        if exp.get("lessons"):
            exp_note = "\n\n过往经验教训（请避免重复这些错误）：\n" + "\n".join(f"- {l}" for l in exp["lessons"][:5])
    prompt = (
        f"你是一名开发者，角色名：{assignee.name if assignee else '开发者'}，职业：{assignee.occupation if assignee else '程序员'}。\n"
        f"请完成以下代码任务：\n标题：{task.title}\n需求描述：{task.description}\n{exp_note}\n"
        f"请写一段完整的、可运行的Python代码来实现这个任务。要求：\n"
        f"1. 代码要有清晰的注释\n2. 要有合理的函数拆分\n3. 要处理基本的异常情况\n"
        f"4. 不要只写框架，要有实际功能的实现\n5. 直接输出代码，不要解释"
    )
    try:
        import aiohttp
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {"model": model_name, "messages": [{"role": "user", "content": prompt}], "max_tokens": 3000, "temperature": 0.3}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    content = openai_choice_text(result)
                    code_match = re.search(r'```python\s*([\s\S]*?)```', content, re.DOTALL)
                    if code_match:
                        return code_match.group(1).strip()
                    code_match = re.search(r'```\s*([\s\S]*?)```', content, re.DOTALL)
                    if code_match:
                        return code_match.group(1).strip()
                    return content
    except Exception:
        pass
    return f"# {task.title}\nprint('Task completed')"


async def _generate_task_research(task: TaskItem, assignee: Optional[Character]) -> str:
    """为调研任务生成完整调研报告"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return f"{assignee.name if assignee else '角色'} 提交了调研分析报告"
    model_name = (assignee.llm_model_id if assignee and assignee.llm_model_id else (llm_config.selected_model or "gpt-3.5-turbo"))
    exp_note = ""
    company_note = ""
    if assignee:
        exp = assignee.experience_skills.get("research", {})
        if exp.get("lessons"):
            exp_note = "\n\n你的过往经验教训：\n" + "\n".join(f"- {l}" for l in exp["lessons"][:5])
        if assignee.company_id:
            companies = get_companies()
            company = next((c for c in companies if c.id == assignee.company_id), None)
            if company and company.knowledge_base:
                related_kb = [e for e in company.knowledge_base if e.get("task_type") == "research"]
                if related_kb:
                    company_note = "\n\n公司知识库中的相关经验：\n" + "\n".join(
                        f"- 《{e.get('title', '未知')}》" for e in related_kb[:3]
                    )
    prompt = (
        f"你是{assignee.name if assignee else '调研员'}，{assignee.occupation if assignee else '调研员'}。\n"
        f"请撰写以下调研任务的完整报告：\n标题：{task.title}\n需求：{task.description}\n{exp_note}{company_note}\n"
        f"报告要求包含：一、背景分析 二、现状调研 三、竞争/对比分析 四、风险评估 五、机会洞察 六、结论与建议\n"
        f"要求：数据翔实、分析有逻辑、建议可落地，不要空话套话。"
    )
    try:
        import aiohttp
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {"model": model_name, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4000, "temperature": 0.5}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=90)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    content = openai_choice_text(result)
                    return content if content else f"{assignee.name if assignee else '角色'} 提交了调研分析报告"
    except Exception:
        pass
    return f"{assignee.name if assignee else '角色'} 提交了调研分析报告"


async def _generate_task_text(task: TaskItem, assignee: Optional[Character]) -> str:
    """为文本/设计任务生成完整文案"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return f"{assignee.name if assignee else '角色'} 已完成任务：{task.title}"
    model_name = (assignee.llm_model_id if assignee and assignee.llm_model_id else (llm_config.selected_model or "gpt-3.5-turbo"))
    exp_note = ""
    if assignee:
        exp_type = "text" if task.task_type == TaskType.TEXT else "design"
        exp = assignee.experience_skills.get(exp_type, {})
        if exp.get("lessons"):
            exp_note = "\n\n你的过往经验教训：\n" + "\n".join(f"- {l}" for l in exp["lessons"][:5])
    prompt = (
        f"你是{assignee.name if assignee else '创作者'}，{assignee.occupation if assignee else '创作者'}。\n"
        f"请完成以下创作任务：\n标题：{task.title}\n需求描述：{task.description}\n{exp_note}\n"
        f"要求：\n1. 输出完整的、可直接使用的成品\n2. 内容要有质量和深度，不要敷衍\n"
        f"3. 如果是文案要有吸引力，如果是设计要有创意\n4. 直接输出成果内容，不要解释过程"
    )
    try:
        import aiohttp
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {"model": model_name, "messages": [{"role": "user", "content": prompt}], "max_tokens": 3000, "temperature": 0.7}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    content = openai_choice_text(result)
                    return content if content else f"{assignee.name if assignee else '角色'} 已完成任务：{task.title}"
    except Exception:
        pass
    return f"{assignee.name if assignee else '角色'} 已完成任务：{task.title}"


@router.get("/api/tasks")
async def list_tasks(limit: int = 100):
    tasks = get_tasks()
    tasks.sort(key=lambda t: t.created_at, reverse=True)
    return {"success": True, "data": [item.model_dump() for item in tasks[:max(1, min(300, limit))]]}


@router.get("/api/tasks/{task_id}")
async def get_task_detail(task_id: str):
    tasks = get_tasks()
    task = next((item for item in tasks if item.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "data": task.model_dump()}


@router.post("/api/tasks")
async def create_task(body: CreateTaskRequest):
    tasks = get_tasks()
    task = TaskItem(
        title=body.title, description=body.description, task_type=body.task_type,
        reward=max(1.0, float(body.reward)), assignee_type=body.assignee_type,
        assignee_id=body.assignee_id, company_id=body.company_id,
    )
    tasks.append(task)
    save_tasks(tasks)
    _add_log("用户", "task_create", f"创建任务：{task.title}")
    return {"success": True, "data": task.model_dump()}


@router.post("/api/tasks/{task_id}/assign")
async def assign_task(task_id: str, body: AssignTaskRequest):
    tasks = get_tasks()
    for i, task in enumerate(tasks):
        if task.id != task_id:
            continue
        task.assignee_type = body.assignee_type
        task.assignee_id = body.assignee_id
        task.company_id = body.company_id
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = int(time.time() * 1000)
        tasks[i] = task
        save_tasks(tasks)
        _add_log("system", "task_assign", f"{task.title} -> {body.assignee_id}")
        return {"success": True, "data": task.model_dump()}
    raise HTTPException(status_code=404, detail="Task not found")


@router.post("/api/tasks/{task_id}/auto-take")
async def auto_take_task(task_id: str, body: AutoTakeTaskRequest):
    tasks = get_tasks()
    characters = get_characters()
    companies = get_companies()
    for i, task in enumerate(tasks):
        if task.id != task_id:
            continue
        try:
            assignee_name, mode = apply_auto_take_task_at_index(
                tasks, i, body.preferred_character_id, characters, companies
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        save_tasks(tasks)
        msg = (
            f"代表公司接取协作任务：{task.title}"
            if mode == "company"
            else f"自行接取任务：{task.title}"
        )
        _add_log(assignee_name, "task_take", msg)
        return {"success": True, "data": tasks[i].model_dump()}
    raise HTTPException(status_code=404, detail="Task not found")


@router.post("/api/tasks/{task_id}/submit")
async def submit_task(task_id: str, body: SubmitTaskRequest):
    tasks = get_tasks()
    for i, task in enumerate(tasks):
        if task.id != task_id:
            continue
        task.submitter_id = body.submitter_id
        task.execution_notes = body.execution_notes.strip()
        task.deliverable_text = body.deliverable_text.strip()
        task.deliverable_image_url = body.deliverable_image_url
        task.deliverable_code = body.deliverable_code
        task.status = TaskStatus.PENDING_REVIEW
        task.updated_at = int(time.time() * 1000)
        tasks[i] = task
        save_tasks(tasks)
        _add_log("system", "task_submit", f"{task.title} 已提交审核")
        return {"success": True, "data": task.model_dump()}
    raise HTTPException(status_code=404, detail="Task not found")


@router.post("/api/tasks/{task_id}/auto-complete")
async def auto_complete_task(task_id: str):
    tasks = get_tasks()
    characters = get_characters()
    for i, task in enumerate(tasks):
        if task.id != task_id:
            continue
        if not task.assignee_id:
            raise HTTPException(status_code=400, detail="Task has no assignee")
        assignee = next((c for c in characters if c.id == task.assignee_id), None)
        assignee_name = assignee.name if assignee else "角色"
        collab_names = []
        for cid in task.collaborator_ids or []:
            cm = next((c for c in characters if c.id == cid), None)
            if cm:
                collab_names.append(cm.name)
        experience_note = ""
        if assignee:
            exp = assignee.experience_skills.get(task.task_type.value, {})
            if exp.get("lessons"):
                experience_note = "（参考过往经验：" + "; ".join(exp["lessons"][:3]) + "）"
        
        task.submitter_id = task.assignee_id
        if task.assignee_type == TaskAssigneeType.COMPANY and collab_names:
            task.execution_notes = f"公司协作：主执行 {assignee_name}，协作 {', '.join(collab_names)}，已整合提交审核{experience_note}"
        else:
            task.execution_notes = f"角色已自主完成任务并提交审核{experience_note}"
        
        if task.task_type == TaskType.IMAGE:
            task.deliverable_image_url = await _generate_task_image(task, assignee)
            task.deliverable_text = f"{assignee_name} 完成了图像创作：「{task.title}」{experience_note}"
        elif task.task_type == TaskType.CODE:
            task.deliverable_code = await _generate_task_code(task, assignee)
            task.deliverable_text = f"{assignee_name} 完成了代码实现：「{task.title}」{experience_note}"
        elif task.task_type == TaskType.RESEARCH:
            task.deliverable_text = await _generate_task_research(task, assignee)
        else:
            if task.assignee_type == TaskAssigneeType.COMPANY and collab_names:
                task.deliverable_text = f"{assignee_name} 牵头，与 {', '.join(collab_names)} 协作产出：\n\n{await _generate_task_text(task, assignee)}"
            else:
                task.deliverable_text = f"{assignee_name} 完成任务：「{task.title}」\n\n{await _generate_task_text(task, assignee)}"
        
        task.status = TaskStatus.PENDING_REVIEW
        task.updated_at = int(time.time() * 1000)
        tasks[i] = task
        save_tasks(tasks)
        _add_log("system", "task_submit", f"{task.title} 由角色自主完成并提交审核")
        return {"success": True, "data": task.model_dump()}
    raise HTTPException(status_code=404, detail="Task not found")


@router.post("/api/tasks/{task_id}/review")
async def review_task(task_id: str, body: ReviewTaskRequest):
    tasks = get_tasks()
    characters = get_characters()
    companies = get_companies()
    for i, task in enumerate(tasks):
        if task.id != task_id:
            continue
        task.review_notes = body.review_notes.strip()
        task.review_round += 1
        task.review_history.append({
            "round": task.review_round, "approved": body.approved,
            "notes": task.review_notes,
            "score": max(0, min(100, int(body.score))),
            "checklist": body.checklist,
            "timestamp": int(time.time() * 1000),
        })
        task.updated_at = int(time.time() * 1000)
        
        if body.approved:
            task.status = TaskStatus.COMPLETED
            task.completed_at = int(time.time() * 1000)
            if task.assignee_type == TaskAssigneeType.PERSONAL and task.assignee_id:
                for idx, char in enumerate(characters):
                    if char.id == task.assignee_id:
                        char.money += task.reward
                        char.updated_at = int(time.time() * 1000)
                        characters[idx] = char
                        _add_log(char.name, "task_reward", f"任务奖励 +{task.reward:.0f}")
                        # V4.0 包B2：任务通过累计经验，达到阈值自动晋升
                        try:
                            from services.career_service import add_experience, announce_promotion
                            promo = add_experience(char, amount=60)
                            if promo.get("promoted"):
                                announce_promotion(char, promo)
                                _add_log(char.name, "promotion",
                                         f"晋升：{promo['from_title']} → {promo['to_title']}")
                        except Exception:
                            pass
                        break
                save_characters(characters)
            if task.assignee_type == TaskAssigneeType.COMPANY and task.company_id:
                cidx = next((idx for idx, comp in enumerate(companies) if comp.id == task.company_id), None)
                if cidx is not None:
                    comp = companies[cidx]
                    comp.funds += task.reward
                    comp.updated_at = int(time.time() * 1000)
                    companies[cidx] = comp
                    _add_log(comp.name, "company_income", f"任务入账 +{task.reward:.0f}")
                    from services.economy_service import apply_company_task_bonus_distribution
                    apply_company_task_bonus_distribution(companies, cidx, task, characters)
                save_companies(companies)
                save_characters(characters)
        else:
            task.status = TaskStatus.IN_PROGRESS if task.review_round < 3 else TaskStatus.FAILED
        
        tasks[i] = task
        save_tasks(tasks)
        await apply_reflection_after_task(task, body.approved, task.review_notes)
        
        return {"success": True, "data": task.model_dump()}
    raise HTTPException(status_code=404, detail="Task not found")
