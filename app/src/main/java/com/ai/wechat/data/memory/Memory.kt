package com.ai.wechat.data.memory

import java.time.Instant

/**
 * 记忆实体（时间感知型）
 */
data class Memory(
    val id: String,
    val characterId: String,
    val content: String,
    val type: MemoryType,
    val importance: Float,
    val emotion: String?,
    val timestamp: Long,
    val validFrom: Instant,
    val validTo: Instant?,
    val relatedEntities: List<String>,
    val embedding: List<Float>?,
    val metadata: Map<String, Any> = emptyMap()
)

/**
 * 时间范围查询
 */
data class TimeRange(
    val startTime: Instant,
    val endTime: Instant
) {
    companion object {
        fun last24Hours(): TimeRange {
            val now = Instant.now()
            return TimeRange(now.minusSeconds(86400), now)
        }

        fun last7Days(): TimeRange {
            val now = Instant.now()
            return TimeRange(now.minusSeconds(604800), now)
        }

        fun last30Days(): TimeRange {
            val now = Instant.now()
            return TimeRange(now.minusSeconds(2592000), now)
        }
    }
}

/**
 * 关系类型
 */
enum class RelationshipType {
    FRIEND_WITH,      // 好友关系
    WORK_AT,          // 工作关系
    POSTED,           // 任务提交
    LOCATED_AT,       // 位置关系
    HAS_MEMORY,       // 记忆关系
    PARTICIPATED_IN,  // 任务参与
    MEMBER_OF,        // 公司成员
    CREATED           // 创建关系
}

/**
 * 角色状态快照
 */
data class CharacterState(
    val id: String,
    val name: String,
    val age: Int,
    val money: Double,
    val location: String?,
    val companyId: String?,
    val relationships: List<RelationshipState>,
    val timestamp: Instant
)

/**
 * 关系状态
 */
data class RelationshipState(
    val targetId: String,
    val targetName: String,
    val type: RelationshipType,
    val intimacy: Double,
    val validFrom: Instant,
    val validTo: Instant?
)
