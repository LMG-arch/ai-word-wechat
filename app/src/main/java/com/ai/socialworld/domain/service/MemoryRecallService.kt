package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.Memory
import com.ai.socialworld.data.model.MemoryType
import com.ai.socialworld.data.repository.MemoryRepository
import com.ai.socialworld.domain.repository.ApiConfigRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.exp
import kotlin.math.ln
import kotlin.math.sqrt

/**
 * 记忆召回服务
 * 实现向量检索 + 时间衰减 + 重排优化
 */
@Singleton
class MemoryRecallService @Inject constructor(
    private val memoryRepository: MemoryRepository,
    private val vectorService: VectorModelService,
    private val apiConfigRepository: ApiConfigRepository
) {
    
    // 时间衰减参数
    private val halfLifeHours = 72.0 // 半衰期72小时（3天）
    private val reflectionHalfLifeHours = 168.0 // 反思记忆半衰期7天
    
    /**
     * 召回相关记忆
     * @param query 查询文本
     * @param characterId 角色ID
     * @param topK 返回数量（默认10）
     * @param maxCandidates 最大候选数量（默认50）
     */
    suspend fun recallMemories(
        query: String,
        characterId: String,
        topK: Int = 10,
        maxCandidates: Int = 50
    ): List<Memory> = withContext(Dispatchers.IO) {
        
        // 1. 生成查询向量
        val queryEmbedding = when (val result = vectorService.generateEmbedding(query)) {
            is EmbeddingResult.Success -> result.embedding
            is EmbeddingResult.Error -> {
                // 向量生成失败，使用文本匹配降级
                return@withContext recallByText(query, characterId, topK)
            }
        }
        
        // 2. 获取候选记忆
        val candidates = memoryRepository.getMemoriesByCharacterSync(characterId)
        
        if (candidates.isEmpty()) {
            return@withContext emptyList()
        }
        
        // 3. 计算相似度并过滤
        val scoredMemories = candidates.mapNotNull { memory ->
            val embedding = memory.embedding ?: return@mapNotNull null
            
            try {
                // 解码embedding（假设存储为Base64或JSON字符串）
                val memoryEmbedding = parseEmbedding(embedding)
                
                // 计算向量相似度
                val similarity = vectorService.cosineSimilarity(queryEmbedding, memoryEmbedding)
                
                // 时间衰减加权
                val timeWeight = calculateTimeDecay(
                    memory.timestamp,
                    memory.type == MemoryType.REFLECTION
                )
                
                // 综合分数
                val score = similarity * timeWeight
                
                ScoredMemory(memory, score, similarity, timeWeight)
            } catch (e: Exception) {
                null
            }
        }.sortedByDescending { it.score }
        
        // 4. 重排优化（如果有重排模型）
        val reranked = rerankMemories(query, scoredMemories.take(maxCandidates))
        
        // 5. 返回Top K
        reranked.take(topK).map { it.memory }
    }
    
    /**
     * 召回相关反思记忆
     */
    suspend fun recallReflections(
        query: String,
        characterId: String,
        taskType: String? = null,
        topK: Int = 5
    ): List<Memory> = withContext(Dispatchers.IO) {
        
        val allReflections = memoryRepository.getMemoriesByTypeSync(characterId, MemoryType.REFLECTION)
        
        val filtered = if (taskType != null) {
            allReflections.filter { 
                it.metadata?.contains(taskType) == true 
            }
        } else {
            allReflections
        }
        
        if (filtered.isEmpty()) {
            return@withContext emptyList()
        }
        
        // 使用更严格的相似度计算
        recallMemories(query, characterId, topK, maxCandidates = 20)
    }
    
    /**
     * 计算时间衰减权重
     * 公式: weight = exp(-hours_since / half_life)
     */
    private fun calculateTimeDecay(
        timestamp: Long,
        isReflection: Boolean = false
    ): Float {
        val now = System.currentTimeMillis()
        val hoursSince = TimeUnit.MILLISECONDS.toHours(now - timestamp)
        
        val halfLife = if (isReflection) reflectionHalfLifeHours else halfLifeHours
        
        return exp(-hoursSince.toDouble() / halfLife).toFloat()
    }
    
    /**
     * 文本匹配降级方案（BM25风格）
     */
    private suspend fun recallByText(
        query: String,
        characterId: String,
        topK: Int
    ): List<Memory> {
        val candidates = memoryRepository.getMemoriesByCharacterSync(characterId)
        
        val queryTerms = query.lowercase().split(Regex("\\s+"))
        
        val scored = candidates.map { memory ->
            val content = memory.content.lowercase()
            val matchedTerms = queryTerms.count { term -> content.contains(term) }
            val timeWeight = calculateTimeDecay(memory.timestamp)
            
            val score = (matchedTerms.toFloat() / queryTerms.size.coerceAtLeast(1)) * timeWeight
            ScoredMemory(memory, score)
        }.sortedByDescending { it.score }
        
        return scored.take(topK).map { it.memory }
    }
    
    /**
     * 重排记忆（使用重排模型优化）
     */
    private suspend fun rerankMemories(
        query: String,
        candidates: List<ScoredMemory>
    ): List<ScoredMemory> {
        // 检查是否有重排模型配置
        val rerankConfigs = apiConfigRepository.getEnabledApiConfigs(ApiType.RERANK)
        
        if (rerankConfigs.isEmpty()) {
            // 没有重排模型，直接返回按分数排序的结果
            return candidates.sortedByDescending { it.score }
        }
        
        // TODO: 实现重排模型调用
        // 目前使用简单的启发式重排
        return heuristicRerank(query, candidates)
    }
    
    /**
     * 启发式重排
     */
    private fun heuristicRerank(
        query: String,
        candidates: List<ScoredMemory>
    ): List<ScoredMemory> {
        val queryLower = query.lowercase()
        
        return candidates.map { scored ->
            var boost = 0.0f
            
            // 关键词精确匹配加分
            if (scored.memory.content.lowercase().contains(queryLower)) {
                boost += 0.2f
            }
            
            // 反思记忆重要度提升
            if (scored.memory.type == MemoryType.REFLECTION) {
                boost += 0.15f
            }
            
            // 高重要性记忆加分
            if (scored.memory.importance >= 0.8f) {
                boost += 0.1f
            }
            
            // 应用提升
            scored.copy(score = scored.score + boost)
        }.sortedByDescending { it.score }
    }
    
    /**
     * 解析存储的向量
     */
    private fun parseEmbedding(embeddingStr: String): List<Float> {
        return try {
            // 尝试解析JSON数组格式
            if (embeddingStr.startsWith("[")) {
                embeddingStr.trim('[', ']')
                    .split(",")
                    .map { it.trim().toFloat() }
            } else {
                // 尝试解析Base64格式
                parseBase64Embedding(embeddingStr)
            }
        } catch (e: Exception) {
            emptyList()
        }
    }
    
    /**
     * 解析Base64编码的向量
     */
    private fun parseBase64Embedding(base64: String): List<Float> {
        // TODO: 实现Base64解码
        return emptyList()
    }
    
    /**
     * 存储记忆（带向量生成）
     */
    suspend fun storeMemory(
        characterId: String,
        content: String,
        type: MemoryType,
        importance: Float = 0.5f,
        relatedEntities: List<String> = emptyList(),
        metadata: Map<String, String>? = null
    ): Long = withContext(Dispatchers.IO) {
        
        // 生成向量
        val embedding = when (val result = vectorService.generateEmbedding(content)) {
            is EmbeddingResult.Success -> result.embedding
            is EmbeddingResult.Error -> null
        }
        
        // 序列化向量为JSON字符串
        val embeddingStr = embedding?.let {
            it.joinToString(",", "[", "]")
        }
        
        // 创建记忆对象
        val memory = Memory(
            characterId = characterId,
            content = content,
            type = type,
            importance = importance,
            embedding = embeddingStr,
            relatedEntities = relatedEntities.joinToString(","),
            metadata = metadata?.entries?.joinToString(",") { "${it.key}:${it.value}" },
            timestamp = System.currentTimeMillis()
        )
        
        // 存储
        memoryRepository.insertMemory(memory)
    }
    
    /**
     * 内部数据类：带分数的记忆
     */
    private data class ScoredMemory(
        val memory: Memory,
        val score: Float,
        val similarity: Float = 0.0f,
        val timeWeight: Float = 0.0f
    )
}
