package com.ai.wechat.service

import com.ai.wechat.data.memory.MemoryEngine
import com.ai.wechat.data.memory.MemoryType
import com.ai.wechat.data.model.Task
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 反思引擎
 * 负责生成反思报告、提取经验教训、更新技能
 */
@Singleton
class ReflectionEngine @Inject constructor(
    private val memoryEngine: MemoryEngine,
    private val aiWeChatService: AiWeChatService
) {

    /**
     * 任务完成后触发反思
     */
    suspend fun reflectOnTask(
        characterId: String,
        task: Task,
        executionLog: String
    ): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val isSuccess = task.status == com.ai.wechat.data.model.TaskStatus.COMPLETED

            // 生成反思报告
            val reflectionResult = aiWeChatService.generateReflection(task, executionLog, isSuccess)
            
            reflectionResult.onSuccess { report ->
                // 提取经验教训和技能提升
                val lessons = extractLessons(report.content)
                val skillDeltas = extractSkillDeltas(report.content)

                // 存储反思记忆
                memoryEngine.storeReflection(
                    characterId = characterId,
                    taskId = task.id,
                    content = report.content,
                    lessons = lessons,
                    skillDeltas = skillDeltas
                )
            }

            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 从反思内容中提取经验教训
     */
    private fun extractLessons(content: String): List<String> {
        // 简单实现：按行分割，提取包含"教训"、"经验"的行
        return content.lines()
            .filter { line ->
                line.contains("教训") || line.contains("经验") || 
                line.contains("注意") || line.contains("要")
            }
            .take(5)
            .map { it.trim() }
    }

    /**
     * 从反思内容中提取技能提升
     */
    private fun extractSkillDeltas(content: String): Map<String, Float> {
        // 简单实现：返回默认技能提升
        return mapOf(
            "需求理解" to 5f,
            "执行效率" to 3f
        )
    }

    /**
     * 审核不通过时的反思
     */
    suspend fun reflectOnRejection(
        characterId: String,
        task: Task,
        rejectionReason: String
    ): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val prompt = """
            任务"${task.title}"未通过审核，原因如下：
            $rejectionReason
            
            请分析：
            1. 问题出在哪里？
            2. 如何改进？
            3. 下次应该注意什么？
            """.trimIndent()

            val reflection = aiWeChatService.generateText(prompt)
            reflection.onSuccess { content ->
                memoryEngine.storeMemory(
                    characterId = characterId,
                    content = "任务审核不通过反思：$content",
                    type = MemoryType.REFLECTION,
                    importance = 0.8f,
                    relatedEntities = listOf(task.id)
                )
            }

            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
