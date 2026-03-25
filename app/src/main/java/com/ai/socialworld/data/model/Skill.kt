package com.ai.socialworld.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 技能类型
 */
enum class SkillType {
    REQUIREMENT_UNDERSTANDING,  // 需求理解
    EPIC_SENSE,                 // 史诗感把控
    DETAIL_RICHNESS,            // 细节丰富度
    STYLE_ACCURACY,             // 风格准确性
    REVISION_EFFICIENCY,        // 修改效率
    TEAM_COLLABORATION          // 团队协作
}

/**
 * 技能实体
 */
@Entity(tableName = "skills")
data class Skill(
    @PrimaryKey
    val id: String,
    val characterId: String,           // 角色ID
    val skillType: SkillType,          // 技能类型
    val value: Float = 0f,             // 技能值 (0-100)
    val updatedAt: Long = System.currentTimeMillis()  // 使用Long
)

/**
 * 技能历史记录
 */
@Entity(tableName = "skill_history")
data class SkillHistory(
    @PrimaryKey
    val id: String,
    val characterId: String,
    val skillType: SkillType,
    val oldValue: Float,
    val newValue: Float,
    val taskId: String?,               // 关联的任务
    val changedAt: Long = System.currentTimeMillis()  // 使用Long
)

/**
 * 反思报告
 */
@Entity(tableName = "reflections")
data class Reflection(
    @PrimaryKey
    val id: String,
    val taskId: String,                // 关联的任务ID
    val characterId: String,           // 反思的角色ID
    val success: Boolean,              // 任务是否成功
    val whatWentWell: String = "[]",   // 成功点 JSON数组
    val whatWentWrong: String = "[]",  // 错误点 JSON数组
    val rootCauses: String = "[]",     // 根本原因 JSON数组
    val lessonsLearned: String = "[]", // 经验教训 JSON数组
    val actionItems: String = "[]",    // 改进措施 JSON数组
    val skillDeltas: String = "{}",    // 技能变化 JSON对象
    val importance: Float = 0.7f,      // 重要性 (成功0.7, 失败0.9)
    val createdAt: Long = System.currentTimeMillis()  // 使用Long
)

/**
 * 技能变化
 */
data class SkillDelta(
    val skillType: SkillType,
    val delta: Float
)

/**
 * 反思输入数据
 */
data class ReflectionInput(
    val taskId: String,
    val taskType: String,
    val requirements: String,
    val submissions: List<String>,     // 提交记录
    val feedbacks: List<String>,       // 反馈记录
    val finalResult: String,           // 最终成果
    val success: Boolean,
    val durationMinutes: Long          // 耗时
)
