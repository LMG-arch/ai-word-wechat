package com.ai.socialworld.domain.engine

import com.ai.socialworld.data.model.*
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 任务系统引擎
 * 处理任务创建、执行、审核等
 */
@Singleton
class TaskEngine @Inject constructor() {
    
    companion object {
        const val MIN_TASK_REWARD = 100
        const val MAX_TASK_REWARD = 10000
        const val AUTO_GENERATED_MIN_REWARD = 100
        const val AUTO_GENERATED_MAX_REWARD = 1000
        const val COMPANY_VOTE_THRESHOLD = 0.5 // 50%参与
        const val COMPANY_APPROVAL_THRESHOLD = 0.6 // 60%赞成
        const val MAX_REVISION_ROUNDS = 3
    }
    
    /**
     * 生成AI自动任务
     */
    fun generateAutoTasks(count: Int = 3): List<Task> {
        val taskTypes = TaskType.values()
        return (1..count).map { index ->
            Task(
                id = "task_auto_${System.currentTimeMillis()}_$index",
                title = generateTaskTitle(taskTypes.random()),
                description = "系统自动生成的任务",
                type = taskTypes.random(),
                reward = (AUTO_GENERATED_MIN_REWARD..AUTO_GENERATED_MAX_REWARD).random()
            )
        }
    }
    
    /**
     * 生成任务标题
     */
    private fun generateTaskTitle(type: TaskType): String {
        return when (type) {
            TaskType.TEXT -> listOf("写一篇短文", "创作一个故事", "撰写报告").random()
            TaskType.IMAGE -> listOf("绘制风景图", "创作人物肖像", "设计海报").random()
            TaskType.CODE -> listOf("编写脚本", "开发小程序", "修复Bug").random()
            TaskType.RESEARCH -> listOf("市场调研", "竞品分析", "用户研究").random()
            TaskType.DESIGN -> listOf("设计Logo", "UI设计", "品牌设计").random()
        }
    }
    
    /**
     * 检查公司投票是否通过
     */
    fun isCompanyVotePassed(
        totalMembers: Int,
        votedMembers: Int,
        approvedMembers: Int
    ): Boolean {
        val participationRate = votedMembers.toDouble() / totalMembers
        if (participationRate < COMPANY_VOTE_THRESHOLD) return false
        
        val approvalRate = approvedMembers.toDouble() / votedMembers
        return approvalRate >= COMPANY_APPROVAL_THRESHOLD
    }
    
    /**
     * 计算任务技能提升
     */
    fun calculateSkillImprovement(
        taskType: TaskType,
        success: Boolean,
        revisionCount: Int
    ): Map<SkillDimension, Int> {
        val improvements = mutableMapOf<SkillDimension, Int>()
        
        // 基础提升
        val baseImprovement = if (success) (1..5).random() else (2..8).random()
        
        when (taskType) {
            TaskType.IMAGE -> {
                improvements[SkillDimension.EPIC_SENSIBILITY] = baseImprovement
                improvements[SkillDimension.DETAIL_RICHNESS] = baseImprovement / 2
            }
            TaskType.TEXT -> {
                improvements[SkillDimension.REQUIREMENT_UNDERSTANDING] = baseImprovement
                improvements[SkillDimension.STYLE_ACCURACY] = baseImprovement / 2
            }
            TaskType.CODE -> {
                improvements[SkillDimension.MODIFICATION_EFFICIENCY] = baseImprovement
            }
            else -> {
                improvements[SkillDimension.REQUIREMENT_UNDERSTANDING] = baseImprovement
            }
        }
        
        // 修改次数影响
        if (revisionCount > 0) {
            improvements[SkillDimension.MODIFICATION_EFFICIENCY] = 
                (improvements[SkillDimension.MODIFICATION_EFFICIENCY] ?: 0) + revisionCount
        }
        
        return improvements
    }
    
    /**
     * 生成图像生成提示词
     */
    fun generateImagePrompt(description: String): String {
        val positivePrompt = "史诗感,宏大构图,电影质感,8K分辨率,光影追踪,细节丰富"
        val negativePrompt = "卡通,二次元,动漫,Q版,简笔画,低分辨率,模糊"
        
        return """
            描述: $description
            正面提示词: $positivePrompt
            负面提示词: $negativePrompt
        """.trimIndent()
    }
}
