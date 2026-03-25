package com.ai.socialworld.domain.service

import com.ai.socialworld.data.remote.*
import com.ai.socialworld.domain.repository.ApiConfigRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.sqrt

/**
 * 向量模型服务
 * 支持多模型切换和备用机制
 */
@Singleton
class VectorModelService @Inject constructor(
    private val apiConfigRepository: ApiConfigRepository
) {
    
    private val retrofitBuilder = Retrofit.Builder()
        .addConverterFactory(GsonConverterFactory.create())
    
    // 向量缓存，避免重复计算
    private val embeddingCache = mutableMapOf<String, List<Float>>()
    private val maxCacheSize = 1000
    
    /**
     * 生成文本向量
     */
    suspend fun generateEmbedding(text: String): EmbeddingResult = withContext(Dispatchers.IO) {
        // 检查缓存
        val cacheKey = text.hashCode().toString()
        embeddingCache[cacheKey]?.let {
            return@withContext EmbeddingResult.Success(
                embedding = it,
                dimensions = it.size
            )
        }
        
        // 获取启用的向量模型配置
        val configs = apiConfigRepository.getEnabledApiConfigs(ApiType.VECTOR)
        
        if (configs.isEmpty()) {
            // 降级方案：使用BM25或简单哈希
            return@withContext generateFallbackEmbedding(text)
        }
        
        // 按优先级排序
        val sortedConfigs = configs.sortedBy { it.priority }
        
        // 尝试每个配置
        for (config in sortedConfigs) {
            val result = tryCallWithConfig(config, text)
            
            when (result) {
                is EmbeddingResult.Success -> {
                    // 缓存结果
                    cacheEmbedding(cacheKey, result.embedding)
                    return@withContext result
                }
                is EmbeddingResult.Error -> {
                    if (!result.shouldRetry) {
                        return@withContext result
                    }
                    continue
                }
            }
        }
        
        // 所有配置都失败，使用降级方案
        generateFallbackEmbedding(text)
    }
    
    /**
     * 批量生成向量
     */
    suspend fun generateEmbeddings(texts: List<String>): List<EmbeddingResult> = withContext(Dispatchers.IO) {
        texts.map { text ->
            generateEmbedding(text)
        }
    }
    
    /**
     * 计算余弦相似度
     */
    fun cosineSimilarity(vectorA: List<Float>, vectorB: List<Float>): Float {
        if (vectorA.size != vectorB.size) {
            throw IllegalArgumentException("Vectors must have the same dimension")
        }
        
        var dotProduct = 0.0f
        var normA = 0.0f
        var normB = 0.0f
        
        for (i in vectorA.indices) {
            dotProduct += vectorA[i] * vectorB[i]
            normA += vectorA[i] * vectorA[i]
            normB += vectorB[i] * vectorB[i]
        }
        
        return if (normA > 0 && normB > 0) {
            dotProduct / (sqrt(normA) * sqrt(normB))
        } else {
            0.0f
        }
    }
    
    /**
     * 计算欧几里得距离
     */
    fun euclideanDistance(vectorA: List<Float>, vectorB: List<Float>): Float {
        if (vectorA.size != vectorB.size) {
            throw IllegalArgumentException("Vectors must have the same dimension")
        }
        
        var sum = 0.0f
        for (i in vectorA.indices) {
            val diff = vectorA[i] - vectorB[i]
            sum += diff * diff
        }
        
        return sqrt(sum)
    }
    
    /**
     * 尝试使用指定配置调用
     */
    private suspend fun tryCallWithConfig(
        config: ApiConfig,
        text: String
    ): EmbeddingResult {
        return try {
            val retrofit = retrofitBuilder
                .baseUrl(config.apiUrl)
                .build()
            
            val api = retrofit.create(VectorModelApi::class.java)
            
            when {
                config.modelName.contains("text-embedding", ignoreCase = true) ||
                config.apiUrl.contains("openai", ignoreCase = true) -> {
                    callOpenAIEmbedding(api, config, text)
                }
                else -> {
                    callGenericEmbedding(api, config, text)
                }
            }
        } catch (e: Exception) {
            EmbeddingResult.Error(
                message = "API调用异常: ${e.message}",
                shouldRetry = true
            )
        }
    }
    
    /**
     * 调用OpenAI Embedding API
     */
    private suspend fun callOpenAIEmbedding(
        api: VectorModelApi,
        config: ApiConfig,
        text: String
    ): EmbeddingResult {
        val request = OpenAIEmbeddingRequest(
            model = config.modelName,
            input = text
        )
        
        val response = api.createEmbeddingOpenAI(
            authorization = "Bearer ${config.apiKey}",
            request = request
        )
        
        return if (response.isSuccessful) {
            val embedding = response.body()?.data?.firstOrNull()?.embedding
            if (embedding != null) {
                EmbeddingResult.Success(
                    embedding = embedding,
                    dimensions = embedding.size,
                    tokensUsed = response.body()?.usage?.total_tokens ?: 0
                )
            } else {
                EmbeddingResult.Error("响应内容为空", shouldRetry = false)
            }
        } else {
            EmbeddingResult.Error(
                message = response.errorBody()?.string() ?: "请求失败",
                code = response.code(),
                shouldRetry = response.code() in 500..599 || response.code() == 429
            )
        }
    }
    
    /**
     * 调用通用Embedding API
     */
    private suspend fun callGenericEmbedding(
        api: VectorModelApi,
        config: ApiConfig,
        text: String
    ): EmbeddingResult {
        val requestBody = mapOf(
            "model" to config.modelName,
            "input" to text
        )
        
        val headers = mapOf(
            "Authorization" to "Bearer ${config.apiKey}",
            "Content-Type" to "application/json"
        )
        
        val response = api.createEmbedding(
            url = "/embeddings",
            headers = headers,
            request = requestBody
        )
        
        return if (response.isSuccessful) {
            val embedding = response.body()?.get("data")?.let {
                (it as? List<Map<String, Any>>)?.firstOrNull()
                    ?.get("embedding") as? List<Float>
            }
            
            if (embedding != null) {
                EmbeddingResult.Success(
                    embedding = embedding,
                    dimensions = embedding.size
                )
            } else {
                EmbeddingResult.Error("响应内容为空", shouldRetry = false)
            }
        } else {
            EmbeddingResult.Error(
                message = response.errorBody()?.string() ?: "请求失败",
                code = response.code(),
                shouldRetry = response.code() in 500..599 || response.code() == 429
            )
        }
    }
    
    /**
     * 降级方案：使用简单的特征提取
     * 当所有API都失败时使用
     */
    private fun generateFallbackEmbedding(text: String): EmbeddingResult {
        // 使用简单的TF-IDF风格特征
        // 这是一个简化的降级方案，实际项目中可以使用更复杂的算法
        val dimensions = 128
        val embedding = MutableList(dimensions) { 0.0f }
        
        // 基于字符编码生成伪向量
        text.forEachIndexed { index, char ->
            val featureIndex = (char.code + index) % dimensions
            embedding[featureIndex] += 1.0f
        }
        
        // 归一化
        val norm = sqrt(embedding.sumOf { it * it.toDouble() }).toFloat()
        if (norm > 0) {
            for (i in embedding.indices) {
                embedding[i] /= norm
            }
        }
        
        return EmbeddingResult.Success(
            embedding = embedding,
            dimensions = dimensions
        )
    }
    
    /**
     * 缓存向量
     */
    private fun cacheEmbedding(key: String, embedding: List<Float>) {
        // 限制缓存大小
        if (embeddingCache.size >= maxCacheSize) {
            // 移除最旧的条目（简化策略：随机移除）
            embeddingCache.keys.firstOrNull()?.let {
                embeddingCache.remove(it)
            }
        }
        embeddingCache[key] = embedding
    }
    
    /**
     * 清空缓存
     */
    fun clearCache() {
        embeddingCache.clear()
    }
    
    /**
     * 获取缓存大小
     */
    fun getCacheSize(): Int = embeddingCache.size
}
