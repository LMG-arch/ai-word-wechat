package com.ai.socialworld.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 记忆类型
 */
enum class MemoryType {
    CONVERSATION,    // 对话记忆
    EVENT,           // 事件记忆
    TASK,            // 任务记忆
    RELATIONSHIP,    // 关系变化
    REFLECTION,      // 反思记忆
    SCHEDULE         // 日程记忆
}

/**
 * 记忆实体
 */
@Entity(tableName = "memories")
data class Memory(
    @PrimaryKey
    val id: String,
    val characterId: String,           // 所属角色ID
    val type: MemoryType,              // 记忆类型
    val content: String,               // 记忆内容
    val timestamp: Long = System.currentTimeMillis(), // 时间戳 (Long)
    val importance: Float = 0.5f,      // 重要性 (0-1)
    val emotion: String? = null,       // 情绪
    val embedding: String? = null,     // 向量数据 (Base64)
    val relatedEntities: String = "[]", // 相关实体JSON数组
    val isReflection: Boolean = false, // 是否为反思记忆
    val reflectionOf: String? = null,  // 关联的任务ID
    val lessonsLearned: String? = null, // 学到的教训JSON
    val validFrom: Long = System.currentTimeMillis(), // 有效开始时间 (Long)
    val validTo: Long? = null          // 有效结束时间 (Long)
)

/**
 * 记忆检索结果
 */
data class MemoryRetrievalResult(
    val memory: Memory,
    val similarity: Float,      // 相似度分数
    val timeWeight: Float       // 时间权重
)

/**
 * 记忆查询请求
 */
data class MemoryQueryRequest(
    val query: String,
    val characterId: String? = null,
    val types: List<MemoryType>? = null,
    val timeRange: TimeRange? = null,
    val topK: Int = 10
)

/**
 * 时间范围
 */
data class TimeRange(
    val from: Long,
    val to: Long
)
