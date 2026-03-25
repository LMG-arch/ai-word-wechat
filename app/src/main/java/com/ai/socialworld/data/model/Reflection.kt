package com.ai.socialworld.data.model

import java.time.Instant

/**
 * 反思报告数据模型
 * 根据开发文档定义完整的反思结构
 */
data class Reflection(
    val id: String,
    val taskId: String,
    val characterId: String,
    val taskName: String,
    val completionTime: Instant = Instant.now(),
    val success: Boolean,
    val whatWentWell: List<String> = emptyList(),
    val whatWentWrong: List<String> = emptyList(),
    val rootCauses: List<String> = emptyList(),
    val lessonsLearned: List<String> = emptyList(),
    val actionItems: List<String> = emptyList(),
    val skillImprovements: Map<String, Int> = emptyMap(),
    val summary: String = ""
)

/**
 * 技能维度
 */
enum class SkillDimension(val displayName: String) {
    REQUIREMENT_UNDERSTANDING("需求理解"),
    EPIC_SENSIBILITY("史诗感把控"),
    DETAIL_RICHNESS("细节丰富度"),
    STYLE_ACCURACY("风格准确性"),
    MODIFICATION_EFFICIENCY("修改效率"),
    TEAM_COLLABORATION("团队协作");
}

/**
 * 技能数据
 */
data class Skill(
    val characterId: String,
    val dimension: SkillDimension,
    val level: Int = 0, // 0-100
    val updatedAt: Instant = Instant.now()
)
