package com.ai.socialworld.domain.engine

import com.ai.socialworld.data.model.*
import java.time.Instant
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 反思引擎
 * 处理任务完成后的反思报告生成
 */
@Singleton
class ReflectionEngine @Inject constructor() {
    
    /**
     * 生成反思报告（成功）
     */
    fun generateSuccessReflection(
        task: Task,
        executionLog: ExecutionLog
    ): Reflection {
        return Reflection(
            id = generateReflectionId(),
            taskId = task.id,
            characterId = executionLog.characterId,
            taskName = task.title,
            success = true,
            whatWentWell = listOf(
                "成功完成了${task.type.displayName}任务",
                "获得了${task.reward}资金奖励"
            ),
            lessonsLearned = listOf(
                "每次提交前要对照需求清单检查",
                "注意任务类型的特殊要求"
            ),
            skillImprovements = mapOf(
                SkillDimension.REQUIREMENT_UNDERSTANDING.name to (1..5).random(),
                SkillDimension.STYLE_ACCURACY.name to (1..3).random()
            ),
            summary = "成功完成任务：${task.title}"
        )
    }
    
    /**
     * 生成反思报告（失败）
     */
    fun generateFailureReflection(
        task: Task,
        executionLog: ExecutionLog,
        failureReason: String
    ): Reflection {
        return Reflection(
            id = generateReflectionId(),
            taskId = task.id,
            characterId = executionLog.characterId,
            taskName = task.title,
            success = false,
            whatWentWrong = listOf(failureReason),
            rootCauses = listOf("对任务需求理解不够深入"),
            lessonsLearned = listOf(
                "失败是成功之母，吸取教训",
                "下次任务前仔细分析需求",
                "建立检查清单避免重复错误"
            ),
            skillImprovements = mapOf(
                SkillDimension.REQUIREMENT_UNDERSTANDING.name to (3..8).random(),
                SkillDimension.MODIFICATION_EFFICIENCY.name to (2..5).random()
            ),
            summary = "任务失败：${task.title} - $failureReason"
        )
    }
    
    /**
     * 生成反思提示词（成功）
     */
    fun generateSuccessReflectionPrompt(task: Task): String {
        return """
            你刚刚成功完成了${task.type.displayName}任务"${task.title}"。
            
            请反思：
            1. 哪些做法正确？（至少2点）
            2. 遇到什么困难？如何克服？
            3. 总结3条最重要的经验教训
            4. 这些经验可用于哪些未来任务？
            
            任务描述：${task.description}
            奖励：${task.reward}资金
        """.trimIndent()
    }
    
    /**
     * 生成反思提示词（失败）
     */
    fun generateFailureReflectionPrompt(task: Task, failureReason: String): String {
        return """
            任务"${task.title}"失败了。
            
            失败原因：$failureReason
            
            请分析：
            1. 失败的根本原因是什么？
            2. 哪个环节可以纠正？
            3. 建立什么检查机制避免再犯？
            4. 至少3条深刻教训
            
            任务描述：${task.description}
        """.trimIndent()
    }
    
    /**
     * 生成反思ID
     */
    private fun generateReflectionId(): String {
        return "refl_${System.currentTimeMillis()}_${(0..9999).random()}"
    }
    
    /**
     * 检查反思是否重要（用于知识库共享）
     */
    fun isImportantReflection(reflection: Reflection): Boolean {
        // 失败反思总是重要的
        if (!reflection.success) return true
        
        // 技能提升较大的反思
        val totalImprovement = reflection.skillImprovements.values.sum()
        return totalImprovement >= 10
    }
}
