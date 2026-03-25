package com.ai.socialworld.domain.engine

import com.ai.socialworld.data.model.*
import com.ai.socialworld.domain.repository.MemoryRepository
import com.ai.socialworld.domain.service.TimeDecayService
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import java.time.Instant
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 记忆引擎
 * 处理记忆存储、召回、检索等
 */
@Singleton
class MemoryEngine @Inject constructor(
    private val memoryRepository: MemoryRepository,
    private val timeDecayService: TimeDecayService
) {
    /**
     * 存储记忆
     */
    suspend fun storeMemory(
        characterId: String,
        content: String,
        type: MemoryType,
        importance: Float = 0.5f,
        relatedEntities: List<String> = emptyList(),
        metadata: Map<String, Any> = emptyMap()
    ): Result<String> {
        val memory = Memory(
            id = generateMemoryId(),
            characterId = characterId,
            content = content,
            timestamp = System.currentTimeMillis(),
            type = type,
            importance = importance,
            relatedEntities = relatedEntities
        )
        return memoryRepository.storeMemory(memory)
    }
    
    /**
     * 召回记忆
     */
    suspend fun recallMemories(
        characterId: String,
        query: String,
        timeRange: TimeRange? = null,
        topK: Int = 10
    ): List<MemoryRecallResult> {
        // 1. 向量检索Top 50
        val candidates = memoryRepository.searchMemories(characterId, query, 50)
        
        // 2. 时间加权
        val timeWeighted = candidates.map { memory ->
            val decayWeight = timeDecayService.calculateDecayWeight(memory.timestamp)
            val weightedScore = memory.importance * decayWeight.toFloat()
            memory to weightedScore
        }.sortedByDescending { it.second }
        
        // 3. 取Top K
        return timeWeighted.take(topK).map { (memory, score) ->
            MemoryRecallResult(
                memory = memory,
                similarity = score,
                timeWeightedScore = score.toDouble()
            )
        }
    }
    
    /**
     * 获取历史状态
     */
    suspend fun getStateAtTime(
        characterId: String,
        timestamp: Instant
    ): CharacterState? {
        return memoryRepository.getCharacterStateAtTime(characterId, timestamp)
    }
    
    /**
     * 生成记忆ID
     */
    private fun generateMemoryId(): String {
        return "mem_${System.currentTimeMillis()}_${(0..9999).random()}"
    }
}

/**
 * 角色状态
 */
data class CharacterState(
    val characterId: String,
    val timestamp: Instant,
    val location: String? = null,
    val activity: String? = null,
    val mood: String? = null
)
