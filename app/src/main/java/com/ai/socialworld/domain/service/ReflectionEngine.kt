package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.*
import com.ai.socialworld.data.repository.MemoryRepository
import com.ai.socialworld.data.repository.SkillRepository
import com.ai.socialworld.domain.repository.TaskRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 反思引擎
 * 任务完成后自动触发反思，提取经验教训
 */
@Singleton
class ReflectionEngine @Inject constructor(
    private val languageModelService: LanguageModelService,
    private val memoryRecallService: MemoryRecallService,
    private val memoryRepository: MemoryRepository,
    private val skillRepository: SkillRepository,
    private val taskRepository: TaskRepository
) {
    
    /**
     * 触发反思
     * 任务完成或失败时调用
     */
    suspend fun triggerReflection(
        taskId: String,
        characterId: String,
        success: Boolean
    ): Reflection? = withContext(Dispatchers.IO) {
        
        // 1. 获取任务信息
        val task = taskRepository.getTaskById(taskId) ?: return@withContext null
        
        // 2. 收集过程数据
        val processData = collectProcessData(task)
        
        // 3. 调用LLM生成反思报告
        val reflectionContent = when (val result = languageModelService.generateReflection(
            taskType = task.type.name,
            requirements = task.description,
            submissions = processData.submissions,
            feedbacks = processData.feedbacks,
            success = success
        )) {
            is ChatResult.Success -> result.content
            is ChatResult.Error -> {
                // 反思生成失败，使用简单模板
                generateSimpleReflection(task, success)
            }
        }
        
        // 4. 解析反思内容
        val parsedReflection = parseReflection(reflectionContent, success)
        
        // 5. 创建反思对象
        val reflection = Reflection(
            taskId = taskId,
            characterId = characterId,
            content = reflectionContent,
            success = success,
            whatWentWell = parsedReflection.whatWentWell,
            whatWentWrong = parsedReflection.whatWentWrong,
            rootCauses = parsedReflection.rootCauses,
            lessonsLearned = parsedReflection.lessonsLearned,
            actionItems = parsedReflection.actionItems,
            importance = if (success) 0.7f else 0.9f, // 失败反思更重要
            timestamp = System.currentTimeMillis()
        )
        
        // 6. 保存反思
        memoryRepository.insertReflection(reflection)
        
        // 7. 更新技能
        updateSkills(characterId, parsedReflection.skillImprovements)
        
        // 8. 存储为反思记忆
        storeReflectionMemory(characterId, reflection)
        
        reflection
    }
    
    /**
     * 收集任务过程数据
     */
    private suspend fun collectProcessData(task: Task): ProcessData {
        // TODO: 从任务提交记录中获取
        return ProcessData(
            submissions = emptyList(),
            feedbacks = emptyList(),
            votes = emptyList()
        )
    }
    
    /**
     * 生成简单反思（降级方案）
     */
    private fun generateSimpleReflection(task: Task, success: Boolean): String {
        return if (success) {
            """
            {
                "what_went_well": ["成功完成了${task.type}任务"],
                "what_went_wrong": [],
                "root_causes": [],
                "lessons_learned": ["继续努力，保持专注"],
                "action_items": ["总结经验，提升技能"],
                "skill_improvements": {}
            }
            """.trimIndent()
        } else {
            """
            {
                "what_went_well": [],
                "what_went_wrong": ["任务未能成功完成"],
                "root_causes": ["需要进一步分析原因"],
                "lessons_learned": ["失败是成功之母，下次改进"],
                "action_items": ["加强相关技能学习"],
                "skill_improvements": {}
            }
            """.trimIndent()
        }
    }
    
    /**
     * 解析反思内容
     */
    private fun parseReflection(content: String, success: Boolean): ParsedReflection {
        return try {
            val json = JSONObject(content)
            
            ParsedReflection(
                whatWentWell = parseJsonArray(json, "what_went_well"),
                whatWentWrong = parseJsonArray(json, "what_went_wrong"),
                rootCauses = parseJsonArray(json, "root_causes"),
                lessonsLearned = parseJsonArray(json, "lessons_learned"),
                actionItems = parseJsonArray(json, "action_items"),
                skillImprovements = parseSkillImprovements(json)
            )
        } catch (e: Exception) {
            // JSON解析失败，返回空解析结果
            ParsedReflection()
        }
    }
    
    /**
     * 解析JSON数组
     */
    private fun parseJsonArray(json: JSONObject, key: String): List<String> {
        return try {
            val array = json.getJSONArray(key)
            (0 until array.length()).map { array.getString(it) }
        } catch (e: Exception) {
            emptyList()
        }
    }
    
    /**
     * 解析技能提升
     */
    private fun parseSkillImprovements(json: JSONObject): Map<SkillType, Float> {
        return try {
            val improvements = json.getJSONObject("skill_improvements")
            val result = mutableMapOf<SkillType, Float>()
            
            improvements.keys().forEach { key ->
                val value = improvements.getString(key)
                    .replace("%", "")
                    .replace("+", "")
                    .toFloatOrNull() ?: 0f
                
                val skillType = when (key) {
                    "需求理解", "requirement_understanding" -> SkillType.REQUIREMENT_UNDERSTANDING
                    "史诗感把控", "epic_sense" -> SkillType.EPIC_SENSE
                    "细节丰富度", "detail_richness" -> SkillType.DETAIL_RICHNESS
                    "风格准确性", "style_accuracy" -> SkillType.STYLE_ACCURACY
                    "修改效率", "revision_efficiency" -> SkillType.REVISION_EFFICIENCY
                    "团队协作", "team_collaboration" -> SkillType.TEAM_COLLABORATION
                    else -> null
                }
                
                if (skillType != null && value > 0) {
                    result[skillType] = value / 100f // 转换为0-1范围
                }
            }
            
            result
        } catch (e: Exception) {
            emptyMap()
        }
    }
    
    /**
     * 更新技能
     */
    private suspend fun updateSkills(
        characterId: String,
        improvements: Map<SkillType, Float>
    ) {
        improvements.forEach { (skillType, delta) ->
            val currentSkill = skillRepository.getSkillSync(characterId, skillType)
            
            if (currentSkill != null) {
                // 更新现有技能
                val newValue = (currentSkill.value + delta).coerceIn(0f, 100f)
                
                val updated = currentSkill.copy(
                    value = newValue,
                    updatedAt = System.currentTimeMillis()
                )
                
                skillRepository.updateSkill(updated)
                
                // 记录技能历史
                val history = SkillHistory(
                    characterId = characterId,
                    skillType = skillType,
                    oldValue = currentSkill.value,
                    newValue = newValue,
                    taskId = null,
                    changedAt = System.currentTimeMillis()
                )
                
                skillRepository.insertSkillHistory(history)
            } else {
                // 创建新技能
                val newSkill = Skill(
                    characterId = characterId,
                    skillType = skillType,
                    value = delta.coerceIn(0f, 100f),
                    updatedAt = System.currentTimeMillis()
                )
                
                skillRepository.insertSkill(newSkill)
            }
        }
    }
    
    /**
     * 存储反思记忆
     */
    private suspend fun storeReflectionMemory(
        characterId: String,
        reflection: Reflection
    ) {
        val memoryContent = buildString {
            append("【反思】")
            if (reflection.success) {
                append("任务成功：")
            } else {
                append("任务失败：")
            }
            
            if (reflection.lessonsLearned.isNotEmpty()) {
                append("\n经验教训：")
                reflection.lessonsLearned.forEach { lesson ->
                    append("\n- $lesson")
                }
            }
        }
        
        memoryRecallService.storeMemory(
            characterId = characterId,
            content = memoryContent,
            type = MemoryType.REFLECTION,
            importance = reflection.importance,
            relatedEntities = listOf(reflection.taskId),
            metadata = mapOf(
                "success" to reflection.success.toString(),
                "reflection_id" to reflection.id
            )
        )
    }
    
    /**
     * 计算技能变化
     */
    fun calculateSkillDeltas(
        task: Task,
        reflection: Reflection,
        success: Boolean
    ): Map<SkillType, Float> {
        val deltas = mutableMapOf<SkillType, Float>()
        
        // 基础技能映射
        val relevantSkills = when (task.type) {
            TaskType.IMAGE -> listOf(
                SkillType.EPIC_SENSE,
                SkillType.DETAIL_RICHNESS,
                SkillType.STYLE_ACCURACY
            )
            TaskType.TEXT -> listOf(
                SkillType.REQUIREMENT_UNDERSTANDING,
                SkillType.DETAIL_RICHNESS
            )
            TaskType.CODE -> listOf(
                SkillType.REQUIREMENT_UNDERSTANDING,
                SkillType.DETAIL_RICHNESS,
                SkillType.REVISION_EFFICIENCY
            )
            TaskType.RESEARCH -> listOf(
                SkillType.REQUIREMENT_UNDERSTANDING,
                SkillType.DETAIL_RICHNESS
            )
            TaskType.DESIGN -> listOf(
                SkillType.EPIC_SENSE,
                SkillType.STYLE_ACCURACY,
                SkillType.DETAIL_RICHNESS
            )
        }
        
        // 计算变化值
        relevantSkills.forEach { skill ->
            val baseDelta = if (success) {
                (1..5).random() // 成功：+1~5
            } else {
                (2..8).random() // 失败：+2~8
            }
            
            // 同类任务收益递减（简化实现）
            deltas[skill] = baseDelta.toFloat()
        }
        
        return deltas
    }
    
    /**
     * 获取反思提示（用于任务执行前）
     */
    suspend fun getReflectionHints(
        characterId: String,
        taskType: TaskType
    ): List<String> = withContext(Dispatchers.IO) {
        
        val reflections = memoryRecallService.recallReflections(
            query = taskType.name,
            characterId = characterId,
            taskType = taskType.name,
            topK = 3
        )
        
        reflections.mapNotNull { reflection ->
            val lessons = reflection.metadata?.split(",")?.find { 
                it.startsWith("lessons:") 
            }?.removePrefix("lessons:")
            
            lessons
        }
    }
    
    // 数据类
    private data class ProcessData(
        val submissions: List<String>,
        val feedbacks: List<String>,
        val votes: List<String>
    )
    
    private data class ParsedReflection(
        val whatWentWell: List<String> = emptyList(),
        val whatWentWrong: List<String> = emptyList(),
        val rootCauses: List<String> = emptyList(),
        val lessonsLearned: List<String> = emptyList(),
        val actionItems: List<String> = emptyList(),
        val skillImprovements: Map<SkillType, Float> = emptyMap()
    )
}
