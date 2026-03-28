package com.ai.wechat.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 记忆缓存实体
 * 用于本地缓存从 Graphiti/Neo4j 检索的记忆
 */
@Entity(tableName = "memory_cache")
data class MemoryCache(
    @PrimaryKey
    val id: String,
    val characterId: String,
    val content: String,
    val type: MemoryType,
    val importance: Float,
    val emotion: String?,
    val timestamp: Long,
    val validFrom: Long,
    val validTo: Long?,
    val relatedEntities: String, // JSON 数组
    val embedding: String?, // Base64 编码
    val metadata: String?, // JSON 对象
    val cachedAt: Long = System.currentTimeMillis()
)

/**
 * 记忆类型
 */
enum class MemoryType {
    CONVERSATION, // 对话
    EVENT,        // 事件
    TASK,         // 任务
    RELATIONSHIP, // 关系变化
    REFLECTION,   // 反思
    SCHEDULE      // 日程
}
