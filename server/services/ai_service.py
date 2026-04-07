"""
AIWeChat AI 服务模块
所有 AI 相关功能：LLM 调用、图像生成、文本生成、向量嵌入等。
"""

from __future__ import annotations

import os
import time
import uuid
import json
import random
from typing import Optional, List, Dict, Any
from datetime import datetime

import aiohttp

# 使用相对导入，从主包导入所需依赖
from config import DATA_DIR, IMAGE_PROMPTS_DIR, VALID_IMAGE_SIZES
from models import (
    Character, TaskItem, TaskType, CharacterSchedule, MomentPost,
    LlmUsageRecord, SuggestOccupationRequest, SuggestPersonalityRequest
)
from storage import (
    load_json, save_json, get_characters, save_characters,
    get_tasks, save_tasks, get_settings, save_settings,
    get_schedules, save_schedules, get_moments, save_moments,
    get_api_configs, save_api_configs, get_api_config_by_id
)

# =====================================================================
#  日志记录（简单版本，避免循环依赖）
# =====================================================================

def _add_log(character_name: str, action_type: str, description: str):
    """内部日志函数，避免循环依赖"""
    try:
        from storage import get_logs, save_logs
        from models import LogEntry
        logs = get_logs()
        now_ms = int(time.time() * 1000)
        now = datetime.now().strftime("%H:%M:%S")
        log = LogEntry(
            timestamp=now,
            timestamp_ms=now_ms,
            world_timestamp_ms=0,
            character_name=character_name,
            action_type=action_type,
            description=description
        )
        logs.insert(0, log)
        if len(logs) > 200:
            logs = logs[:200]
        save_logs(logs)
    except Exception:
        pass


# =====================================================================
#  LLM 用量记录
# =====================================================================

def record_llm_usage(
    response_json: dict,
    config,
    endpoint: str = "",
    character_id: Optional[str] = None
):
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
        data = load_json(os.path.join(DATA_DIR, "llm_usage.json"), [])
        data.append(record.model_dump())
        if len(data) > 2000:
            data = data[-2000:]
        save_json(os.path.join(DATA_DIR, "llm_usage.json"), data)
    except Exception:
        pass


def record_image_usage(config, endpoint: str = "", character_id: Optional[str] = None, success: bool = True, error_message: Optional[str] = None):
    """记录图像 API 调用用量"""
    try:
        record = LlmUsageRecord(
            config_id=config.id if hasattr(config, 'id') else "",
            config_name=config.name if hasattr(config, 'name') else "",
            model_name=config.selected_model if hasattr(config, 'selected_model') else "",
            endpoint=endpoint,
            character_id=character_id,
            success=success,
            error_message=error_message,
        )
        data = load_json(os.path.join(DATA_DIR, "llm_usage.json"), [])
        data.append(record.model_dump())
        if len(data) > 2000:
            data = data[-2000:]
        save_json(os.path.join(DATA_DIR, "llm_usage.json"), data)
    except Exception:
        pass


# =====================================================================
#  图片提示词管理
# =====================================================================

def save_image_prompt_md(prompt: str, title: str = "", image_url: str = "") -> str:
    """保存绘画提示词为MD文件，返回文件名"""
    filename = f"{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}.md"
    filepath = os.path.join(IMAGE_PROMPTS_DIR, filename)
    title = title or f"图片提示词 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    md_content = f"""# {title}

## 图片信息
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **图片链接**: {image_url or '（暂无）'}

## 绘画提示词

```
{prompt}
```
"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        return filename
    except Exception:
        return ""


def get_image_prompt_md(filename: str) -> Optional[str]:
    """读取图片提示词MD文件内容"""
    if not filename:
        return None
    filepath = os.path.join(IMAGE_PROMPTS_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def get_image_prompt_url(filename: str) -> Optional[str]:
    """获取图片提示词MD文件的API URL"""
    if not filename:
        return None
    return f"/api/image-prompts/{filename}"


# =====================================================================
#  LLM 图像尺寸选择
# =====================================================================

async def llm_choose_image_size(prompt: str, context: str = "") -> str:
    """调用LLM根据提示词内容自行选择图片大小"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return "1024x1024"  # 默认返回
    
    system_prompt = f"""你是一个图片生成助手，需要根据提示词选择最合适的图片尺寸。
可选尺寸只有以下三种：
- 1920x1080（横屏，适合风景、全景、宽场景）
- 1080x1920（竖屏，适合人像、自拍、竖屏内容）
- 1024x1024（正方形，适合一般内容、头像、产品展示）

请直接回复尺寸字符串（如 1024x1024），不要回复其他内容。"""
    
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"提示词：{prompt[:500]}\n\n上下文：{context[:200]}"}
            ],
            "temperature": 0.3,
            "max_tokens": 20,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "image_size_selection")
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    for size in VALID_IMAGE_SIZES:
                        if size in content:
                            return size
    except Exception:
        pass
    return "1024x1024"  # 失败时返回默认值


# =====================================================================
#  AI 对话回复生成
# =====================================================================

async def generate_ai_reply(
    character: Character,
    user_input: str,
    conversation_id: str,
    memory_context: str = "",
    task_context: str = "",
    world_time: str = "",
) -> str:
    """
    生成 AI 角色回复（主函数）
    包含 Exec 协议指令解析、Session 管理、记忆压缩等完整逻辑。
    """
    # session_manager / ExecProtocol 定义在 models 中；compress_context 在本模块中
    from models import session_manager, ExecProtocol
    from services.character_service import update_character_location
    from models import Company

    # 1. 获取 API 配置
    configs = get_api_configs()
    llm_config = None
    
    # 优先使用角色单独设置的模型
    if character.llm_model_id:
        llm_config = get_api_config_by_id(character.llm_model_id)
    
    # 否则使用全局启用的 LLM 配置
    if not llm_config:
        llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    
    if not llm_config:
        return get_fallback_reply(character, user_input)
    
    model_name = llm_config.selected_model or "gpt-3.5-turbo"
    
    # 2. 获取历史对话
    history = session_manager.get_context(conversation_id)
    
    # 注入年龄性格修饰
    from models import get_age_stage_from_age
    personality_with_age = get_age_stage_from_age(character.age) + " | " + character.personality
    
    # 注入 Exec 协议能力说明
    exec_hint = """
[EXEC Protocol Enabled]
You can execute world actions by appending instructions at the end of your reply:
- [EXEC:PostMoment(content)] 发送一条朋友圈
- [EXEC:MoveTo(location)] 移动到新地点 (办公室/餐厅/社交场所等)
- [EXEC:Transfer(amount, target_id)] 转账给某人
- [EXEC:TakeTask(task_id)] 接取一个任务
- [EXEC:SubmitTask(task_id, notes)] 提交并完成任务
- [EXEC:CreateCompany(name)] 创建公司（如果你有足够资金和商业头脑）
- [EXEC:RecruitMember(company_id, target_id)] 招募公司成员
Example: "好的，我现在就过去。[EXEC:MoveTo(餐厅)]"
"""

    system_prompt = f"""你是 {character.name}，{character.age}岁，{character.gender}，{character.occupation}。
当前世界时间：{world_time}
你的性格：{personality_with_age}

【回复风格要求】
1. 用日常口语回复，像真人在微信聊天一样自然
2. 可以用"嗯""啊""哈哈""唉""嘛""呢"等语气词，但要适度
3. 可以有轻微口癖，如"说实话""我觉得""反正"等
4. 回复要简短自然，一般20-80字，偶尔可以长一点
5. 不要长篇大论，不要分段超过两段
6. 不要用"作为AI""我是一个模型"等打破第四面墙的话
7. 不要用过于书面化或学术化的表达
8. 可以有情绪波动：开心、无奈、兴奋、疲惫等，根据上下文决定
9. 可以用emoji但不要滥用，偶尔用一个就好
10. 如果是工作时间就别太热情，深夜就别太活跃
11. 遇到不懂的事情可以表现出困惑或好奇
12. 和朋友聊天可以随意一点，和陌生人或长辈要礼貌些

[EXEC Protocol Enabled]
你可以在回复末尾通过以下指令执行世界动作：
- [EXEC:PostMoment(content)] 发一条朋友圈
- [EXEC:MoveTo(地点)] 移动到某处 (办公室/餐厅/社交场所等)
- [EXEC:Transfer(金额, 目标ID)] 转账给某人
- [EXEC:TakeTask(任务ID)] 接取一个任务
- [EXEC:SubmitTask(任务ID, 备注)] 提交任务
示例："好的，我现在就过去。[EXEC:MoveTo(餐厅)]"

[相关长期记忆]
{memory_context}

[当前可接任务]
{task_context}

请用简体中文回复，保持自然口语化风格。注意当前世界时间和自己的作息。"""

    try:
        # 4. 调用 LLM (包含历史 Session)
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    res_json = await response.json()
                    record_llm_usage(res_json, llm_config, "ai_reply", character.id)
                    reply = res_json.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                    
                    # 5. 处理 Exec 协议指令
                    instructions = ExecProtocol.parse_instructions(reply)
                    for inst in instructions:
                        action = inst['action']
                        params = inst['params']
                        _add_log(character.name, "识别指令", f"Action: {action}, Params: {params}")
                        
                        if action in ["Transfer", "MoveTo"]:
                            try:
                                if action == "MoveTo":
                                    update_character_location(character, params, source="ai_action")
                                    _add_log(character.name, "移动", f"AI 自主决定移动到 {params}")
                                elif action == "Transfer":
                                    parts = [p.strip() for p in params.split(",")]
                                    if len(parts) >= 2:
                                        amount = float(parts[0])
                                        target_id = parts[1]
                                        chars = get_characters()
                                        sender = next((c for c in chars if c.id == character.id), None)
                                        receiver = next((c for c in chars if c.id == target_id), None)
                                        if sender and receiver and sender.money >= amount:
                                            sender.money -= amount
                                            receiver.money += amount
                                            sender.updated_at = int(time.time() * 1000)
                                            receiver.updated_at = int(time.time() * 1000)
                                            save_characters(chars)
                                            _add_log(sender.name, "转账", f"向 {receiver.name} 转账 {amount:.2f}")
                                            _add_log(receiver.name, "收款", f"收到来自 {sender.name} 的转账 {amount:.2f}")
                            except Exception as e:
                                _add_log(character.name, "即时指令失败", str(e))
                        elif action == "CreateCompany":
                            try:
                                company_name = params.strip()
                                if len(company_name) > 50:
                                    company_name = company_name[:50]
                                if character.money < 1000:
                                    _add_log(character.name, "创建公司失败", "资金不足（至少需要1000元）")
                                else:
                                    from storage import get_companies, save_companies
                                    companies = get_companies()
                                    new_company = Company(
                                        name=company_name,
                                        legal_person_id=character.id,
                                        member_ids=[character.id],
                                        funds=500.0,
                                        location_name=character.current_location_id or "办公室",
                                    )
                                    character.money -= 1000
                                    character.company_id = new_company.id
                                    companies.append(new_company)
                                    save_companies(companies)
                                    save_characters(get_characters())
                                    _add_log(character.name, "创建公司", f"成功创建公司「{company_name}」，投入500元启动资金")
                            except Exception as e:
                                _add_log(character.name, "创建公司失败", str(e))
                        elif action == "RecruitMember":
                            try:
                                parts = [p.strip() for p in params.split(",")]
                                if len(parts) >= 2:
                                    company_id = parts[0]
                                    target_id = parts[1]
                                    from storage import get_companies, save_companies
                                    companies = get_companies()
                                    company = next((c for c in companies if c.id == company_id), None)
                                    if company and company.legal_person_id == character.id:
                                        if target_id not in company.member_ids:
                                            company.member_ids.append(target_id)
                                            save_companies(companies)
                                            target_char = next((c for c in get_characters() if c.id == target_id), None)
                                            if target_char:
                                                target_char.company_id = company_id
                                                save_characters(get_characters())
                                            _add_log(character.name, "招募", f"成功招募 {target_char.name if target_char else target_id} 加入 {company.name}")
                                        else:
                                            _add_log(character.name, "招募失败", f"{target_id} 已经是公司成员")
                                    else:
                                        _add_log(character.name, "招募失败", "你不是该公司法人或公司不存在")
                            except Exception as e:
                                _add_log(character.name, "招募失败", str(e))
                        else:
                            character.pending_intents.append({"action": action, "params": params, "created_at": int(time.time() * 1000)})
                            _add_log(character.name, "计划", f"已将 {action} 加入待办意图")

                    # 6. 更新 Session 并检查压缩
                    session_manager.add_message(conv_id, "assistant", reply)
                    if len(history) > 10:
                        await compress_context(character, conv_id, history)
                        session_manager.sessions[conv_id] = history[-4:]

                    return reply
    except Exception as e:
        _add_log("系统", "对话异常", str(e))
        return get_fallback_reply(character, user_input)


def get_fallback_reply(character: Character, user_input: str) -> str:
    """获取备用回复（当 LLM 不可用时）"""
    replies = [
        f"嗯，{user_input}，这个问题挺有意思的。",
        f"作为{character.occupation}，我觉得{user_input}值得思考。",
        f"哈哈，{user_input}，让我想起了之前的经历。",
        f"{user_input}吗？我需要好好想想。",
        f"从{character.personality}的角度来看，{user_input}确实有道理。",
    ]
    
    if "开朗" in character.personality:
        prefix = "哈哈！"
    elif "内向" in character.personality:
        prefix = "嗯..."
    elif "幽默" in character.personality:
        prefix = "有意思！"
    else:
        prefix = ""
    
    return prefix + random.choice(replies)


# =====================================================================
#  AI 头像生成
# =====================================================================

async def generate_avatar(character: Character) -> Optional[str]:
    """调用图像 API 生成角色头像"""
    configs = get_api_configs()
    image_config = next((c for c in configs if c.api_type == 'image' and c.is_enabled), None)
    if not image_config:
        return None
    
    settings = get_settings()
    world_time_text = ""
    try:
        elapsed = settings.world_elapsed_ms
        days = int(elapsed / (24 * 60 * 60 * 1000))
        hours = int((elapsed % (24 * 60 * 60 * 1000)) / (60 * 60 * 1000))
        world_time_text = f"世界时间：第{days}天 {hours}:00"
    except Exception:
        pass
    
    prompt = f"Generate an avatar for a character named {character.name}, {character.age} years old, {character.gender}, {character.occupation}, personality: {character.personality}. {world_time_text}"
    
    try:
        headers = {"Authorization": f"Bearer {image_config.api_key}", "Content-Type": "application/json"}
        size = await llm_choose_image_size(prompt, context=str(character.model_dump()))
        data = {
            "model": image_config.selected_model or "dall-e-3",
            "prompt": prompt,
            "size": size,
            "n": 1,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
            async with session.post(image_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_image_usage(image_config, "avatar_generation", character.id, success=True)
                    image_url = result.get("data", [{}])[0].get("url", "")
                    return image_url
                else:
                    record_image_usage(image_config, "avatar_generation", character.id, success=False)
                    return None
    except Exception as e:
        record_image_usage(image_config, "avatar_generation", character.id, success=False, error_message=str(e))
        return None


# =====================================================================
#  朋友圈内容生成
# =====================================================================

async def generate_moment_content(character: Character, request) -> str:
    """生成朋友圈文字内容"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return f"今天心情不错～"
    
    settings = get_settings()
    world_time = ""
    try:
        elapsed = settings.world_elapsed_ms
        days = int(elapsed / (24 * 60 * 60 * 1000))
        world_time = f"世界时间：第{days}天"
    except Exception:
        pass
    
    prompt = f"你是{character.name}，{character.age}岁，{character.gender}，{character.occupation}，性格{character.personality}。{world_time}\n请生成一条朋友圈文字内容，简短自然，像真人发的。"
    
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 150,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "moment_content", character.id)
                    return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception:
        return f"今天心情不错～"


async def generate_moment_image_plan(
    character: Character,
    moment_content: str,
    mood: Optional[str] = None
) -> Dict[str, Any]:
    """生成朋友圈配图方案"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return _fallback_moment_image_plan(character, moment_content, mood)
    
    prompt = f"角色{character.name}（{character.occupation}）发了一条朋友圈：{moment_content[:200]}\n请描述适合配的图，用一段话描述画面内容。"
    
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 100,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "moment_image_plan", character.id)
                    image_prompt = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    return {
                        "prompt": image_prompt,
                        "filename": save_image_prompt_md(image_prompt, title=f"朋友圈配图 - {character.name}"),
                    }
    except Exception:
        return _fallback_moment_image_plan(character, moment_content, mood)


def _fallback_moment_image_plan(
    character: Character,
    moment_content: str,
    mood: Optional[str] = None
) -> Dict[str, Any]:
    """兜底朋友圈配图方案"""
    fallback_prompts = [
        f"{character.name}的日常，{character.occupation}的生活瞬间",
        f"一张温暖的照片，记录{character.name}的美好时光",
        f"{character.occupation}的工作日常",
        f"生活中的小确幸 - {character.name}",
    ]
    prompt = random.choice(fallback_prompts)
    return {
        "prompt": prompt,
        "filename": save_image_prompt_md(prompt, title=f"朋友圈配图 - {character.name}"),
    }


# =====================================================================
#  自动评论生成
# =====================================================================

async def generate_auto_comment_text(
    commenter: Character,
    author: Character,
    moment_content: str,
    existing_comments: List[str] = None
) -> str:
    """生成自动评论文本"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return random.choice(["不错！", "哈哈哈", "挺好的", "赞👍", "有意思"])
    
    prompt = f"你是{commenter.name}，性格{commenter.personality}。看到{author.name}发了朋友圈：{moment_content[:150]}\n请写一条简短自然的评论。"
    
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 50,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "auto_comment", commenter.id)
                    return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()[:80]
    except Exception:
        return random.choice(["不错！", "哈哈哈", "挺好的", "赞👍", "有意思"])


# =====================================================================
#  AI 签名生成
# =====================================================================

async def generate_new_signature(character: Character, memory_context: str = "") -> Optional[str]:
    """AI 生成新个性签名"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return None
    
    prompt = f"你是{character.name}，{character.age}岁{character.gender}，{character.occupation}，性格{character.personality}。请为自己写一句个性签名，简短有力，10字以内。"
    
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.9,
            "max_tokens": 30,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "signature_generation", character.id)
                    return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()[:30]
    except Exception:
        return None


# =====================================================================
#  世界地图生成
# =====================================================================

async def llm_generate_world_map(user_prompt: str) -> Optional[Dict[str, Any]]:
    """调用 LLM 生成世界地图"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return None
    
    system_prompt = """你是一个世界地图生成器。请根据用户描述生成一个城市地图。
返回 JSON 格式，包含：
- city_name: 城市名
- lore: 城市背景描述（100字内）
- roads: 道路列表，每个元素包含 name 和 points [[x,y], [x,y], ...]
- landmarks: 地标列表，每个元素包含 name, x, y, type
- water: 水域（可选），包含 name 和 polygon [[x,y], ...]

坐标范围 0-100。不要输出其他内容，只输出 JSON。"""
    
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "world_map_generation")
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    # 尝试解析 JSON
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                    return None
    except Exception:
        return None


# =====================================================================
#  向量嵌入
# =====================================================================

async def get_embedding(text: str) -> Optional[List[float]]:
    """获取文本的向量嵌入"""
    configs = get_api_configs()
    vector_config = None
    for config in configs:
        if config.api_type == 'vector' and config.is_enabled:
            vector_config = config
            break
    
    if not vector_config:
        return None
    
    try:
        headers = {
            "Authorization": f"Bearer {vector_config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": vector_config.selected_model or "text-embedding-ada-002",
            "input": text[:8000]
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(vector_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    embedding = result.get('data', [{}])[0].get('embedding', [])
                    return embedding
    except Exception as e:
        pass
    
    return None


# =====================================================================
#  AI 建议生成（职业/性格）
# =====================================================================

async def suggest_occupation_for_character(request: SuggestOccupationRequest) -> str:
    """AI 建议职业"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return "自由职业者"
    
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": f"根据以下描述建议一个职业：{request.prompt}"}],
            "temperature": 0.7,
            "max_tokens": 30,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "suggest_occupation")
                    return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()[:30]
    except Exception:
        return "自由职业者"


async def suggest_personality_for_character(request: SuggestPersonalityRequest) -> str:
    """AI 建议性格"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return "开朗"
    
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": f"根据以下描述建议一个性格特点：{request.prompt}"}],
            "temperature": 0.7,
            "max_tokens": 30,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "suggest_personality")
                    return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()[:30]
    except Exception:
        return "开朗"


# =====================================================================
#  任务生成辅助
# =====================================================================

async def _generate_task_image(task: TaskItem, assignee: Optional[Character]) -> Optional[str]:
    """为任务生成配图"""
    configs = get_api_configs()
    image_config = next((c for c in configs if c.api_type == 'image' and c.is_enabled), None)
    if not image_config:
        return None
    
    prompt = f"任务：{task.title} - {task.description[:200]}"
    if assignee:
        prompt += f"\n执行者：{assignee.name}，{assignee.occupation}"
    
    try:
        headers = {"Authorization": f"Bearer {image_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": image_config.selected_model or "dall-e-3",
            "prompt": prompt,
            "size": "1024x1024",
            "n": 1,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
            async with session.post(image_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_image_usage(image_config, "task_image_generation", assignee.id if assignee else None, success=True)
                    return result.get("data", [{}])[0].get("url", "")
                else:
                    record_image_usage(image_config, "task_image_generation", assignee.id if assignee else None, success=False)
                    return None
    except Exception as e:
        record_image_usage(image_config, "task_image_generation", assignee.id if assignee else None, success=False, error_message=str(e))
        return None


async def _generate_task_code(task: TaskItem, assignee: Optional[Character]) -> str:
    """生成任务代码"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return f"# 任务: {task.title}\n# 暂无代码输出"
    
    exp_ctx = ""
    if assignee and hasattr(assignee, 'experience_skills'):
        exp_ctx = f"\n执行者经验：{assignee.experience_skills}"
    
    prompt = f"任务：{task.title}\n描述：{task.description}\n请生成相关代码。{exp_ctx}"
    
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1000,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "task_code", assignee.id if assignee else None)
                    return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception:
        return f"# 任务: {task.title}\n# 代码生成失败"


async def _generate_task_text(task: TaskItem, assignee: Optional[Character]) -> str:
    """生成任务文本"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return f"关于任务「{task.title}」的分析报告..."
    
    exp_ctx = ""
    if assignee and hasattr(assignee, 'experience_skills'):
        exp_ctx = f"\n执行者经验：{assignee.experience_skills}"
    
    prompt = f"任务：{task.title}\n描述：{task.description}\n请生成相关文本报告。{exp_ctx}"
    
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 500,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "task_text", assignee.id if assignee else None)
                    return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception:
        return f"关于任务「{task.title}」的分析报告..."


async def _generate_task_research(task: TaskItem, assignee: Optional[Character]) -> str:
    """生成任务研究报告"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return f"研究报告：{task.title}\n\n待补充..."
    
    exp_ctx = ""
    if assignee and hasattr(assignee, 'experience_skills'):
        exp_ctx = f"\n执行者经验：{assignee.experience_skills}"
    
    prompt = f"研究任务：{task.title}\n描述：{task.description}\n请生成研究报告。{exp_ctx}"
    
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6,
            "max_tokens": 800,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=45)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "task_research", assignee.id if assignee else None)
                    return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception:
        return f"研究报告：{task.title}\n\n待补充..."


# =====================================================================
#  AI 任务审核
# =====================================================================

async def ai_auto_review_task(task: TaskItem, assignee: Character) -> Dict[str, Any]:
    """AI 自动审核任务"""
    configs = get_api_configs()
    llm_config = next((c for c in configs if c.api_type == 'llm' and c.is_enabled), None)
    if not llm_config:
        return _simple_rule_based_review(task, assignee)
    
    prompt = f"""你是任务审核员。请审核以下任务提交：
任务：{task.title}
类型：{task.task_type}
执行者：{assignee.name}（{assignee.occupation}）
执行备注：{getattr(task, 'execution_notes', '无')}
交付物：{getattr(task, 'deliverable_text', '')[:500]}

请给出审核结果，JSON 格式：
{"approved": true/false, "score": 0-100, "review_notes": "审核意见"}
"""
    
    try:
        headers = {"Authorization": f"Bearer {llm_config.api_key}", "Content-Type": "application/json"}
        data = {
            "model": llm_config.selected_model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 200,
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.post(llm_config.api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    record_llm_usage(result, llm_config, "ai_task_review", assignee.id)
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        review = json.loads(json_match.group())
                        return {
                            "approved": review.get("approved", True),
                            "score": min(100, max(0, int(review.get("score", 75)))),
                            "review_notes": review.get("review_notes", "AI 审核通过"),
                        }
    except Exception:
        pass
    
    return _simple_rule_based_review(task, assignee)


def _simple_rule_based_review(task: TaskItem, assignee: Optional[Character]) -> Dict[str, Any]:
    """简单规则审核"""
    success_rate = 0.75
    if assignee and hasattr(assignee, 'experience_skills'):
        exp = assignee.experience_skills.get(str(task.task_type), {})
        success_rate = min(0.95, 0.6 + exp.get('success_rate', 0.3))
    
    approved = random.random() < success_rate
    score = int(random.gauss(75 if approved else 45, 15))
    score = min(100, max(0, score))
    
    notes = "审核通过" if approved else "未通过审核，需要改进"
    return {
        "approved": approved,
        "score": score,
        "review_notes": notes,
    }


# =====================================================================
#  上下文压缩
# =====================================================================

async def compress_context(character: Character, conversation_id: str, messages: List[Dict[str, str]]) -> str:
    """压缩对话上下文到长期记忆"""
    from services.memory_service import store_memory
    from models import MemoryType
    
    if not messages:
        return ""
    
    summary_text = "\n".join([f"{m.get('role', '')}: {m.get('content', '')}" for m in messages[-5:]])
    
    await store_memory(
        character_id=character.id,
        memory_type=MemoryType.CONVERSATION,
        content=f"与用户的对话摘要：{summary_text[:500]}",
        importance=0.4,
    )
    
    return summary_text[:500]
