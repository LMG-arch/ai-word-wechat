package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.Character
import com.ai.socialworld.data.model.Memory
import com.ai.socialworld.data.model.MemoryType
import com.ai.socialworld.data.repository.MemoryRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.exp

/**
 * 记忆服务
 * 整合向量检索、时间衰减、重排模型
 */
@Singleton
class MemoryService @Inject constructor(
    private val memoryRepository: MemoryRepository,
    private val vectorModelService: VectorModelService,
    private val rerankModelService: RerankModelService
) {
    
    // 时间衰减半衰期（小时）- 2.5天
    private val HALF_LIFE_HOURS = 60.0
    
    // 反思记忆半衰期（小时）- 7天
    private val REFLECTION_HALF_LIFE_HOURS = 168.0
    
    /**
     * 存储记忆
     */
    suspend fun storeMemory(
        characterId: String,
        content: String,
        type: MemoryType,
        importance: Float = 0.5f,
        emotion: String? = null,
        relatedEntities: List<String> = emptyList(),
        metadata: Map<String, String> = emptyMap()
    ): Result<Memory> = withContext(Dispatchers.IO) {
        try {
            // 生成向量
            val embeddingResult = vectorModelService.generateEmbedding(content)
            
            val embedding = when (embeddingResult) {
                is EmbeddingResult.Success -> embeddingResult.embedding
                is EmbeddingResult.Error -> emptyList()
            }
            
            val memory = Memory(
                id = java.util.UUID.randomUUID().toString(),
                characterId = characterId,
                content = content,
                type = type,
                timestamp = System.currentTimeMillis(),
                importance = importance,
                emotion = emotion,
                relatedEntities = relatedEntities,
                metadata = metadata,
                embedding = embedding
            )
            
            memoryRepository.insertMemory(memory)
            Result.success(memory)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 记忆召回流程
     * 1. 向量检索Top 50
     * 2. 时间衰减加权
     * 3. 重排模型排序
     * 4. 返回Top 10
     */
    suspend fun retrieveMemories(
        characterId: String,
        query: String,
        topK: Int = 10,
        memoryTypes: List<MemoryType>? = null,
        timeRange: Long? = null  // 时间范围（毫秒）
    ): List<ScoredMemory> = withContext(Dispatchers.IO) {
        
        // 1. 生成查询向量
        val queryEmbedding = when (val result = vectorModelService.generateEmbedding(query)) {
            is EmbeddingResult.Success -> result.embedding
            is EmbeddingResult.Error -> return@withContext emptyList()
        }
        
        // 2. 检索候选记忆（Top 50）
        val candidateMemories = memoryRepository.getMemoriesForRetrieval(
            characterId = characterId,
            limit = 50,
            types = memoryTypes,
            since = timeRange?.let { System.currentTimeMillis() - it }
        )
        
        if (candidateMemories.isEmpty()) {
            return@withContext emptyList()
        }
        
        // 3. 计算向量相似度 + 时间衰减
        val scoredMemories = candidateMemories.mapNotNull { memory ->
            if (memory.embedding.isEmpty()) return@mapNotNull null
            
            // 向量相似度
            val vectorScore = vectorModelService.cosineSimilarity(
                queryEmbedding,
                memory.embedding
            )
            
            // 时间衰减权重
            val timeWeight = calculateTimeDecay(memory.timestamp, memory.type)
            
            // 重要性加权
            val importanceWeight = memory.importance
            
            // 反思记忆额外加权
            val reflectionBonus = if (memory.type == MemoryType.REFLECTION) 1.3f else 1.0f
            
            // 综合得分
            val finalScore = vectorScore * timeWeight * importanceWeight * reflectionBonus
            
            ScoredMemory(memory, finalScore, vectorScore, timeWeight)
        }.sortedByDescending { it.finalScore }
        
        // 4. 使用重排模型优化（如果配置了）
        val topCandidates = scoredMemories.take(20)
        
        val rerankedIndices = if (topCandidates.size >= 5) {
            val memoriesContent = topCandidates.map { it.memory.content }
            when (val rerankResult = rerankModelService.rerankMemories(query, memoriesContent, topK)) {
                is RerankResult2.Success -> rerankResult.rankedIndices
                is RerankResult2.Error -> (0 until minOf(topK, topCandidates.size)).toList()
            }
        } else {
            (0 until minOf(topK, topCandidates.size)).toList()
        }
        
        // 5. 返回Top K
        rerankedIndices.mapNotNull { index ->
            topCandidates.getOrNull(index)
        }.take(topK)
    }
    
    /**
     * 计算时间衰减权重
     * 指数衰减：weight = exp(-hours_since / half_life)
     */
    private fun calculateTimeDecay(timestamp: Long, type: MemoryType): Float {
        val hoursSince = (System.currentTimeMillis() - timestamp) / (1000.0 * 60 * 60)
        val halfLife = when (type) {
            MemoryType.REFLECTION -> REFLECTION_HALF_LIFE_HOURS
            else -> HALF_LIFE_HOURS
        }
        
        // 反思记忆衰减慢
        val decay = exp(-hoursSince / halfLife)
        return decay.toFloat().coerceIn(0.1f, 1.0f)
    }
    
    /**
     * 获取反思记忆
     */
    suspend fun getReflectionMemories(
        characterId: String,
        taskType: String? = null,
        topK: Int = 5
    ): List<Memory> = withContext(Dispatchers.IO) {
        val reflections = memoryRepository.getMemoriesByType(characterId, MemoryType.REFLECTION)
            .let { 
                var result = emptyList<Memory>()
                it.collect { list -> result = list }
                result
            }
        
        // 如果指定了任务类型，优先返回相关类型的反思
        if (taskType != null) {
            reflections.filter { 
                it.metadata["task_type"] == taskType 
            }.take(topK)
        } else {
            reflections.take(topK)
        }
    }
    
    /**
     * 获取最近记忆
     */
    suspend fun getRecentMemories(
        characterId: String,
        limit: Int = 10
    ): List<Memory> = withContext(Dispatchers.IO) {
        memoryRepository.getMemoriesByCharacter(characterId)
            .let { 
                var result = emptyList<Memory>()
                it.collect { list -> result = list }
                result
            }
            .take(limit)
    }
    
    /**
     * 删除记忆
     */
    suspend fun deleteMemory(memoryId: String) {
        memoryRepository.deleteMemoryById(memoryId)
    }
    
    /**
     * 更新记忆重要性
     */
    suspend fun updateMemoryImportance(memoryId: String, newImportance: Float) {
        memoryRepository.updateMemoryImportance(memoryId, newImportance)
    }
    
    /**
     * 构建对话上下文
     */
    suspend fun buildConversationContext(
        character: Character,
        userMessage: String,
        chatHistory: List<Pair<String, String>>
    ): ConversationContext = withContext(Dispatchers.IO) {
        
        // 1. 召回相关记忆
        val query = buildString {
            append("角色：${character.name}，")
            append("职业：${character.occupation}，")
            append("用户说：$userMessage")
        }
        
        val retrievedMemories = retrieveMemories(
            characterId = character.id.toString(),
            query = query,
            topK = 10
        )
        
        // 2. 获取最近记忆
        val recentMemories = getRecentMemories(character.id.toString(), 5)
        
        // 3. 获取相关反思
        val reflectionMemories = getReflectionMemories(character.id.toString(), topK = 3)
        
        ConversationContext(
            retrievedMemories = retrievedMemories.map { it.memory },
            recentMemories = recentMemories,
            reflectionMemories = reflectionMemories,
            chatHistory = chatHistory.takeLast(10)
        )
    }
}

/**
 * 带分数的记忆
 */
data class ScoredMemory(
    val memory: Memory,
    val finalScore: Float,
    val vectorScore: Float,
    val timeWeight: Float
)

/**
 * 对话上下文
 */
data class ConversationContext(
    val retrievedMemories: List<Memory>,
    val recentMemories: List<Memory>,
    val reflectionMemories: List<Memory>,
    val chatHistory: List<Pair<String, String>>
)
