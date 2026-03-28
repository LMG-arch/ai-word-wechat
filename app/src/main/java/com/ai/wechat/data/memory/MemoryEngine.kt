package com.ai.wechat.data.memory

import java.time.Instant

/**
 * 记忆引擎接口
 * 定义时间感知记忆的存储和检索操作
 */
interface MemoryEngine {
    
    /**
     * 存储记忆（自动带时间戳）
     */
    suspend fun storeMemory(
        characterId: String,
        content: String,
        type: MemoryType,
        importance: Float,
        relatedEntities: List<String> = emptyList(),
        metadata: Map<String, Any> = emptyMap()
    ): Memory

    /**
     * 带时间感知的检索
     */
    suspend fun recallMemories(
        characterId: String,
        query: String,
        timeRange: TimeRange? = null,
        topK: Int = 10
    ): List<Memory>

    /**
     * 向量检索（不带重排）
     */
    suspend fun searchVector(
        characterId: String,
        queryEmbedding: List<Float>,
        topK: Int = 50
    ): List<Memory>

    /**
     * 存储关系（带有效期）
     */
    suspend fun storeRelationship(
        fromId: String,
        toId: String,
        type: RelationshipType,
        properties: Map<String, Any>,
        validFrom: Instant,
        validTo: Instant? = null
    )

    /**
     * 获取当前关系
     */
    suspend fun getCurrentRelationship(
        fromId: String,
        toId: String
    ): RelationshipState?

    /**
     * 查询历史状态
     */
    suspend fun getStateAtTime(
        characterId: String,
        timestamp: Instant
    ): CharacterState?

    /**
     * 获取过期关系（用于每日衰减）
     */
    suspend fun getStaleRelationships(days: Int = 3): List<RelationshipState>

    /**
     * 更新关系失效时间
     */
    suspend fun invalidateRelationship(
        fromId: String,
        toId: String,
        invalidTime: Instant
    )

    /**
     * 获取角色的所有关系
     */
    suspend fun getRelationships(characterId: String): List<RelationshipState>

    /**
     * 存储反思记忆
     */
    suspend fun storeReflection(
        characterId: String,
        taskId: String,
        content: String,
        lessons: List<String>,
        skillDeltas: Map<String, Float>
    ): Memory

    /**
     * 按类型检索记忆
     */
    suspend fun getMemoriesByType(
        characterId: String,
        type: MemoryType,
        limit: Int = 20
    ): List<Memory>

    /**
     * 删除记忆
     */
    suspend fun deleteMemory(memoryId: String)

    /**
     * 清理过期记忆
     */
    suspend fun cleanupExpiredMemories()
}
