package com.ai.socialworld.data.model

import java.time.Instant

/**
 * 记忆实体（Neo4j 节点）
 */
data class Memory(
    val id: String = java.util.UUID.randomUUID().toString(),
    
    override var businessCreatedAt: Instant = Instant.now(),
    
    override var businessExpiredAt: Instant? = null,
    
    val content: String,
    
    val type: MemoryType = MemoryType.EXPERIENCE,
    
    val importance: Float = 0.5f,
    
    val accessCount: Int = 0,
    
    val lastAccessedAt: Instant? = null,
    
    val metadata: Map<String, String> = emptyMap(),
    
    val characterId: Long? = null
) {
    /**
     * 记忆类型枚举
     */
    enum class MemoryType {
        EXPERIENCE,     // 经历
        KNOWLEDGE,      // 知识
        SKILL,          // 技能
        EMOTION,        // 情感
        BELIEF,         // 信念
        PROCEDURE       // 程序性记忆
    }
}
