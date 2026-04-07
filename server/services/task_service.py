"""
AIWeChat 任务引擎服务模块
任务分配、完成、审核、反思、经验管理。
"""

from __future__ import annotations

import os
import time
import random
from typing import Optional, List, Dict, Any

from config import DATA_DIR


def _get_task_keywords(task_type) -> List[str]:
    """获取任务类型关键词"""
    keyword_map = {
        "text": ["文案", "写作", "编辑", "策划", "营销", "报告"],
        "image": ["设计", "绘画", "插画", "视觉", "美术", "创意"],
        "code": ["编程", "开发", "工程", "算法", "架构", "系统"],
        "research": ["研究", "分析", "调研", "调查", "统计", "数据"],
        "design": ["设计", "规划", "方案", "架构", "产品", "体验"],
    }
    return keyword_map.get(str(task_type).lower(), [])


def choose_task_assignee(task, characters: List, preferred_character_id: Optional[str] = None) -> Optional[Any]:
    """选择任务执行者"""
    if preferred_character_id:
        return next((c for c in characters if c.id == preferred_character_id and c.is_alive), None)
    
    # 按经济压力和职业匹配度选择
    candidates = [c for c in characters if c.is_alive]
    if not candidates:
        return None
    
    scored = []
    for char in candidates:
        score = 0
        # 经济压力
        if char.money < 50:
            score += 3
        elif char.money < 100:
            score += 2
        
        # 职业匹配
        keywords = _get_task_keywords(task.task_type)
        for kw in keywords:
            if kw in (char.occupation or ""):
                score += 2
                break
        
        scored.append((char, score + random.uniform(0, 1)))
    
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0] if scored else None


def apply_auto_take_task_at_index(
    tasks: List,
    index: int,
    preferred_character_id: Optional[str],
    characters: List,
    companies: List,
) -> Any:
    """
    Auto-take: mutate tasks[index] in place. Returns (assignee_name, mode)
    where mode is \"company\" or \"personal\". Raises ValueError on failure.
    """
    from models import TaskAssigneeType, TaskStatus

    task = tasks[index]
    if task.assignee_type == TaskAssigneeType.COMPANY and task.company_id:
        company = next((c for c in companies if c.id == task.company_id), None)
        if not company:
            raise ValueError("Company not found for task")
        alive_ids = [
            mid for mid in company.member_ids
            if any(ch.id == mid and ch.is_alive for ch in characters)
        ]
        if not alive_ids:
            raise ValueError("No alive company member")
        preferred = preferred_character_id
        assignee = None
        if preferred and preferred in alive_ids:
            assignee = next((ch for ch in characters if ch.id == preferred), None)
        if not assignee and company.legal_person_id in alive_ids:
            assignee = next((ch for ch in characters if ch.id == company.legal_person_id), None)
        if not assignee:
            assignee = next((ch for ch in characters if ch.id == alive_ids[0]), None)
        others = [mid for mid in alive_ids if mid != assignee.id]
        random.shuffle(others)
        task.collaborator_ids = others[:2]
        task.assignee_id = assignee.id
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = int(time.time() * 1000)
        tasks[index] = task
        return assignee.name, "company"

    assignee = choose_task_assignee(task, characters, preferred_character_id)
    if not assignee:
        raise ValueError("No alive character available")
    task.collaborator_ids = []
    task.assignee_type = TaskAssigneeType.PERSONAL
    task.assignee_id = assignee.id
    task.status = TaskStatus.IN_PROGRESS
    task.updated_at = int(time.time() * 1000)
    tasks[index] = task
    return assignee.name, "personal"


def try_heartbeat_take_open_task(character, tasks: List, companies: List, characters: List) -> bool:
    """
    Heartbeat: random open non-company task, assign via auto-take with this character preferred.
    Caller must save_tasks. Returns True if a task was claimed.
    """
    from models import TaskAssigneeType, TaskStatus

    open_idx = [
        i for i, t in enumerate(tasks)
        if t.status == TaskStatus.OPEN
        and not (t.assignee_type == TaskAssigneeType.COMPANY and t.company_id)
    ]
    if not open_idx:
        return False
    i = random.choice(open_idx)
    try:
        apply_auto_take_task_at_index(tasks, i, character.id, characters, companies)
    except ValueError:
        return False
    return True


def apply_exec_submit_task_intent(character, params: str, tasks: List) -> bool:
    """SubmitTask(task_id, notes?) from pending_intents; mutates tasks. Caller saves."""
    from models import TaskStatus

    raw = (params or "").strip()
    parts = [p.strip() for p in raw.split(",")]
    task_id = parts[0] if parts else ""
    notes = parts[1] if len(parts) > 1 else ""
    if not task_id:
        return False
    for i, task in enumerate(tasks):
        if task.id != task_id:
            continue
        if task.assignee_id != character.id:
            return False
        if task.status != TaskStatus.IN_PROGRESS:
            return False
        task.submitter_id = character.id
        task.execution_notes = (notes or "Exec 意图提交").strip()
        task.deliverable_text = f"{character.name} 提交的任务成果"
        task.status = TaskStatus.PENDING_REVIEW
        task.updated_at = int(time.time() * 1000)
        tasks[i] = task
        return True
    return False


def create_reflection_from_task(task, approved: bool, review_notes: str) -> Any:
    """从任务创建反思报告"""
    from models import ReflectionReport
    
    reflection = ReflectionReport(
        task_id=task.id,
        task_name=task.title,
        success=approved,
    )
    
    if approved:
        reflection.what_went_well = ["按时完成任务", "质量达标"]
        reflection.lessons_learned = ["保持当前工作方式"]
    else:
        reflection.what_went_wrong = ["任务未通过审核"]
        reflection.root_causes = ["可能需要更多时间或资源"]
        reflection.action_items = ["改进工作方法", "寻求反馈"]
    
    reflection.review_notes = review_notes
    return reflection


def update_character_experience(character, task_type, reflection, success: bool):
    """更新角色经验"""
    if not hasattr(character, 'experience_skills') or not character.experience_skills:
        character.experience_skills = {}
    
    task_type_str = str(task_type)
    if task_type_str not in character.experience_skills:
        character.experience_skills[task_type_str] = {
            "count": 0,
            "success_count": 0,
            "lessons": [],
            "success_rate": 0.0,
            "last_used": 0,
        }
    
    exp = character.experience_skills[task_type_str]
    exp["count"] += 1
    if success:
        exp["success_count"] += 1
    
    exp["success_rate"] = exp["success_count"] / exp["count"]
    exp["last_used"] = int(time.time() * 1000)
    
    # 添加经验教训
    for lesson in reflection.lessons_learned[:3]:
        if lesson not in exp["lessons"]:
            exp["lessons"].append(lesson)
    
    # 限制教训数量
    if len(exp["lessons"]) > 10:
        exp["lessons"] = exp["lessons"][-10:]


def get_experience_context(character, task_type) -> str:
    """获取角色经验上下文"""
    if not hasattr(character, 'experience_skills') or not character.experience_skills:
        return ""
    
    task_type_str = str(task_type)
    exp = character.experience_skills.get(task_type_str)
    if not exp or exp.get("count", 0) == 0:
        return ""
    
    ctx = f"\n[个人经验] 你已完成 {exp['count']} 个同类任务，成功率 {exp['success_rate']:.0%}"
    if exp.get("lessons"):
        ctx += "。经验教训：" + "; ".join(exp["lessons"][:3])
    return ctx


def get_company_experience_context(company, task_type) -> str:
    """获取公司经验上下文"""
    if not hasattr(company, 'knowledge_base') or not company.knowledge_base:
        return ""
    
    task_type_str = str(task_type)
    company_tasks_done = [
        t for t in company.knowledge_base 
        if t.get("task_type") == task_type_str
    ]
    
    if not company_tasks_done:
        return ""
    
    ctx = f"\n[公司经验] {company.name} 知识库中有 {len(company_tasks_done)} 个相关任务的经验：\n"
    for i, t in enumerate(company_tasks_done[:5], 1):
        reflection = t.get("reflection", {})
        lessons = reflection.get("lessons_learned", [])
        if lessons:
            ctx += f"  {i}. 《{t.get('title', '未知')}》经验：\n"
            for lesson in lessons[:3]:
                ctx += f"     - {lesson}\n"
    ctx += "请参考公司前辈的经验，站在巨人的肩膀上完成任务。"
    return ctx


async def store_task_reflection_memory(character, task, reflection, success: bool):
    """存储任务反思记忆"""
    from services.memory_service import store_memory
    from models import MemoryType
    
    lessons_text = "; ".join(reflection.lessons_learned) if reflection.lessons_learned else "无"
    memory_content = f"任务《{task.title}》反思：{lessons_text}"
    
    if reflection.what_went_wrong:
        memory_content += f"。不足：{'; '.join(reflection.what_went_wrong)}"
    if reflection.action_items:
        memory_content += f"。改进：{'; '.join(reflection.action_items)}"
    
    await store_memory(
        character_id=character.id,
        memory_type=MemoryType.REFLECTION,
        content=memory_content,
        importance=0.9 if not success else 0.7,
        related_entities=[task.id],
    )


def add_reflection_to_company_knowledge(company, task, reflection):
    """添加反思到公司知识库"""
    if not hasattr(company, 'knowledge_base'):
        company.knowledge_base = []
    
    company.knowledge_base.insert(0, {
        "task_id": task.id,
        "task_type": str(task.task_type),
        "title": task.title,
        "reflection": reflection.model_dump() if hasattr(reflection, 'model_dump') else reflection,
        "timestamp": int(time.time() * 1000),
    })
    
    if len(company.knowledge_base) > 50:
        company.knowledge_base = company.knowledge_base[:50]


async def apply_reflection_after_task(task, approved: bool, review_notes: str):
    """任务审核后的反思应用"""
    from storage import get_characters, save_characters, get_companies, save_companies, get_tasks, save_tasks
    
    characters = get_characters()
    companies = get_companies()
    tasks = get_tasks()
    
    reflection = create_reflection_from_task(task, approved, review_notes)
    
    # 更新任务对象
    for i, t in enumerate(tasks):
        if t.id == task.id:
            t.reflection = reflection
            tasks[i] = t
    save_tasks(tasks)
    
    # 更新角色经验
    if task.assignee_id:
        assignee = next((c for c in characters if c.id == task.assignee_id), None)
        if assignee:
            update_character_experience(assignee, task.task_type, reflection, approved)
            await store_task_reflection_memory(assignee, task, reflection, approved)
            
            for i, c in enumerate(characters):
                if c.id == assignee.id:
                    characters[i] = assignee
                    break
            save_characters(characters)
            
            # 公司知识共享
            if assignee.company_id:
                company = next((comp for comp in companies if comp.id == assignee.company_id), None)
                if company:
                    add_reflection_to_company_knowledge(company, task, reflection)
                    for i, c in enumerate(companies):
                        if c.id == company.id:
                            companies[i] = company
                            break
                    save_companies(companies)


async def auto_review_pending_tasks(max_tasks: int = 3) -> Dict[str, Any]:
    """自动审核待审核任务"""
    from storage import get_tasks, save_tasks
    from services.ai_service import ai_auto_review_task
    
    tasks = get_tasks()
    pending = [t for t in tasks if t.status.value == "pending_review" or str(t.status) == "TaskStatus.PENDING_REVIEW"]
    
    reviewed = 0
    for task in pending[:max_tasks]:
        assignee = None
        if task.assignee_id:
            from storage import get_characters
            characters = get_characters()
            assignee = next((c for c in characters if c.id == task.assignee_id), None)
        
        review_result = await ai_auto_review_task(task, assignee)
        
        # 更新任务状态
        for i, t in enumerate(tasks):
            if t.id == task.id:
                if review_result.get("approved"):
                    t.status = "completed"
                else:
                    t.status = "failed"
                t.review_notes = review_result.get("review_notes", "")
                t.score = review_result.get("score", 50)
                tasks[i] = t
                break
        
        reviewed += 1
        
        # 应用反思
        await apply_reflection_after_task(task, review_result.get("approved", False), review_result.get("review_notes", ""))
    
    if reviewed > 0:
        save_tasks(tasks)
    
    return {"reviewed": reviewed}


async def run_task_engine(max_tasks_per_tick: int = 5):
    """
    任务引擎 - 后台定期运行，驱动角色/公司自动接取和完成任务。
    """
    from storage import get_tasks, save_tasks, get_characters, save_characters, get_companies
    from models import TaskStatus, TaskAssigneeType, TaskType
    
    try:
        tasks = get_tasks()
        characters = get_characters()
        companies = get_companies()
        alive_chars = [c for c in characters if c.is_alive]
        
        if not alive_chars:
            return
            
        open_tasks = [t for t in tasks if str(t.status) in ["open", "TaskStatus.OPEN"]]
        in_progress_tasks = [t for t in tasks if str(t.status) in ["in_progress", "TaskStatus.IN_PROGRESS"]]
        tasks_changed = False
        action_count = 0
        
        # 阶段 1: 公司自动接取公司任务
        company_tasks_open = [t for t in open_tasks if str(t.assignee_type) in ["company", "TaskAssigneeType.COMPANY"] and t.company_id]
        for task in company_tasks_open[:max_tasks_per_tick]:
            company = next((c for c in companies if c.id == task.company_id), None)
            if not company:
                continue
            alive_members = [mid for mid in company.member_ids if any(ch.id == mid and ch.is_alive for ch in alive_chars)]
            if not alive_members:
                continue
            
            task.assignee_id = company.legal_person_id if company.legal_person_id in alive_members else alive_members[0]
            task.status = "in_progress"
            task.updated_at = int(time.time() * 1000)
            
            t_idx = tasks.index(task)
            tasks[t_idx] = task
            tasks_changed = True
            action_count += 1
        
        # 阶段 2: 个人角色自动接取任务
        char_needs = []
        for char in alive_chars:
            busy = any(t.assignee_id == char.id and str(t.status) in ["in_progress", "pending_review", "TaskStatus.IN_PROGRESS", "TaskStatus.PENDING_REVIEW"] for t in tasks)
            if busy:
                continue
            
            pressure_score = 0
            if char.money < 50:
                pressure_score += 3
            elif char.money < 100:
                pressure_score += 2
            
            total_score = pressure_score + random.uniform(0, 1)
            char_needs.append((char, total_score))
        
        char_needs.sort(key=lambda x: x[1], reverse=True)
        
        for char, score in char_needs[:max_tasks_per_tick]:
            if score < 0.5:
                continue
            if not open_tasks:
                break
                
            personal_tasks = [t for t in open_tasks if str(t.assignee_type) not in ["company", "TaskAssigneeType.COMPANY"]]
            if not personal_tasks:
                continue
            
            chosen_task = personal_tasks[0]
            task_idx = tasks.index(chosen_task)
            chosen_task.assignee_id = char.id
            chosen_task.assignee_type = "personal"
            chosen_task.status = "in_progress"
            chosen_task.updated_at = int(time.time() * 1000)
            tasks[task_idx] = chosen_task
            tasks_changed = True
            action_count += 1
            
            open_tasks.remove(chosen_task)
        
        # 阶段 3: 自动完成任务
        for task in in_progress_tasks[:max_tasks_per_tick]:
            assignee = next((c for c in alive_chars if c.id == task.assignee_id), None)
            if not assignee:
                continue
            
            complete_prob = 0.15
            if assignee.money < 50:
                complete_prob += 0.15
            if assignee.debt_balance > 0:
                complete_prob += 0.1
            
            if random.random() < complete_prob:
                task_idx = tasks.index(task)
                task.status = "pending_review"
                task.updated_at = int(time.time() * 1000)
                task.execution_notes = f"{assignee.name} 完成任务并提交审核"
                tasks[task_idx] = task
                tasks_changed = True
                action_count += 1
        
        if tasks_changed:
            save_tasks(tasks)
        
        # 阶段 4: 自动审核
        await auto_review_pending_tasks(max_tasks=3)
        
    except Exception as e:
        pass
