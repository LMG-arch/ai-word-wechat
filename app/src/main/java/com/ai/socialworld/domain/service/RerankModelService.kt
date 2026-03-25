package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.ApiType
import com.ai.socialworld.domain.repository.ApiConfigRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 重排模型API接口
 * 用于对检索到的记忆进行重新排序
 */
interface RerankModelApi {
    
    /**
     * Cohere Rerank API
     */
    @POST("v1/rerank")
    suspend fun rerankCohere(
        @Header("Authorization") authorization: String,
        @Header("Content-Type") contentType: String = "application/json",
        @Body request: CohereRerankRequest
    ): retrofit2.Response<CohereRerankResponse>
    
    /**
     * 通用重排接口
     */
    @POST
    suspend fun rerank(
        @Url url: String,
        @HeaderMap headers: Map<String, String>,
        @Body request: Map<String, Any>
    ): retrofit2.Response<Map<String, Any>>
}

/**
 * Cohere重排请求
 */
data class CohereRerankRequest(
    val model: String = "rerank-multilingual-v2.0",
    val query: String,
    val documents: List<String>,
    val top_n: Int = 10,
    val return_documents: Boolean = true
)

/**
 * Cohere重排响应
 */
data class CohereRerankResponse(
    val id: String,
    val results: List<RerankResult>,
    val meta: MetaInfo
)

data class RerankResult(
    val document: RerankDocument?,
    val index: Int,
    val relevance_score: Float
)

data class RerankDocument(
    val text: String
)

data class MetaInfo(
    val api_version: ApiVersion,
    val billed_units: BilledUnits
)

data class ApiVersion(
    val version: String
)

data class BilledUnits(
    val search_units: Int
)

/**
 * 重排结果
 */
sealed class RerankResult2 {
    data class Success(
        val rankedIndices: List<Int>,
        val scores: List<Float>
    ) : RerankResult2()
    
    data class Error(
        val message: String,
        val shouldRetry: Boolean = true
    ) : RerankResult2()
}

/**
 * 重排模型服务
 * 用于对检索到的记忆进行重新排序
 */
@Singleton
class RerankModelService @Inject constructor(
    private val apiConfigRepository: ApiConfigRepository
) {
    
    private val retrofitBuilder = Retrofit.Builder()
        .addConverterFactory(GsonConverterFactory.create())
    
    /**
     * 重排记忆列表
     * @param query 查询文本
     * @param memories 候选记忆列表
     * @param topN 返回前N个
     * @return 重排后的记忆索引列表
     */
    suspend fun rerankMemories(
        query: String,
        memories: List<String>,
        topN: Int = 10
    ): RerankResult2 = withContext(Dispatchers.IO) {
        
        if (memories.isEmpty()) {
            return@withContext RerankResult2.Success(emptyList(), emptyList())
        }
        
        // 获取启用的重排模型配置
        val configs = apiConfigRepository.getEnabledApiConfigs(ApiType.RERANK)
        
        if (configs.isEmpty()) {
            // 降级方案：直接返回前N个
            return@withContext RerankResult2.Success(
                rankedIndices = memories.indices.take(topN).toList(),
                scores = List(minOf(topN, memories.size)) { 1.0f }
            )
        }
        
        // 按优先级排序
        val sortedConfigs = configs.sortedBy { it.priority }
        
        // 尝试每个配置
        for (config in sortedConfigs) {
            val result = tryCallWithConfig(config, query, memories, topN)
            
            when (result) {
                is RerankResult2.Success -> return@withContext result
                is RerankResult2.Error -> {
                    if (!result.shouldRetry) {
                        return@withContext result
                    }
                    continue
                }
            }
        }
        
        // 所有配置都失败，使用降级方案
        RerankResult2.Success(
            rankedIndices = memories.indices.take(topN).toList(),
            scores = List(minOf(topN, memories.size)) { 1.0f }
        )
    }
    
    /**
     * 尝试使用指定配置调用
     */
    private suspend fun tryCallWithConfig(
        config: com.ai.socialworld.data.model.ApiConfig,
        query: String,
        memories: List<String>,
        topN: Int
    ): RerankResult2 {
        return try {
            val retrofit = retrofitBuilder
                .baseUrl(config.apiUrl)
                .build()
            
            val api = retrofit.create(RerankModelApi::class.java)
            
            when {
                config.apiUrl.contains("cohere", ignoreCase = true) -> {
                    callCohereRerank(api, config, query, memories, topN)
                }
                else -> {
                    callGenericRerank(api, config, query, memories, topN)
                }
            }
        } catch (e: Exception) {
            RerankResult2.Error(
                message = "API调用异常: ${e.message}",
                shouldRetry = true
            )
        }
    }
    
    /**
     * 调用Cohere Rerank API
     */
    private suspend fun callCohereRerank(
        api: RerankModelApi,
        config: com.ai.socialworld.data.model.ApiConfig,
        query: String,
        memories: List<String>,
        topN: Int
    ): RerankResult2 {
        val request = CohereRerankRequest(
            model = config.modelName,
            query = query,
            documents = memories,
            top_n = topN,
            return_documents = true
        )
        
        val response = api.rerankCohere(
            authorization = "Bearer ${config.apiKey}",
            request = request
        )
        
        return if (response.isSuccessful) {
            val results = response.body()?.results
            if (results != null) {
                val indices = results.map { it.index }
                val scores = results.map { it.relevance_score }
                RerankResult2.Success(indices, scores)
            } else {
                RerankResult2.Error("响应内容为空", shouldRetry = false)
            }
        } else {
            RerankResult2.Error(
                message = response.errorBody()?.string() ?: "请求失败",
                shouldRetry = response.code() in 500..599 || response.code() == 429
            )
        }
    }
    
    /**
     * 调用通用重排API
     */
    private suspend fun callGenericRerank(
        api: RerankModelApi,
        config: com.ai.socialworld.data.model.ApiConfig,
        query: String,
        memories: List<String>,
        topN: Int
    ): RerankResult2 {
        val requestBody = mapOf(
            "model" to config.modelName,
            "query" to query,
            "documents" to memories,
            "top_n" to topN
        )
        
        val headers = mapOf(
            "Authorization" to "Bearer ${config.apiKey}",
            "Content-Type" to "application/json"
        )
        
        val response = api.rerank(
            url = "/rerank",
            headers = headers,
            request = requestBody
        )
        
        return if (response.isSuccessful) {
            val results = response.body()?.get("results") as? List<Map<String, Any>>
            if (results != null) {
                val indices = results.map { (it["index"] as? Number)?.toInt() ?: 0 }
                val scores = results.map { (it["score"] as? Number)?.toFloat() ?: 0f }
                RerankResult2.Success(indices, scores)
            } else {
                RerankResult2.Error("响应内容为空", shouldRetry = false)
            }
        } else {
            RerankResult2.Error(
                message = response.errorBody()?.string() ?: "请求失败",
                shouldRetry = response.code() in 500..599 || response.code() == 429
            )
        }
    }
    
    /**
     * 简单重排（基于向量相似度）
     * 当没有重排模型时使用
     */
    suspend fun rerankBySimilarity(
        queryEmbedding: List<Float>,
        memoryEmbeddings: List<Pair<Int, List<Float>>>,
        topN: Int = 10
    ): List<Pair<Int, Float>> = withContext(Dispatchers.Default) {
        
        // 计算相似度
        val similarities = memoryEmbeddings.map { (index, embedding) ->
            val similarity = cosineSimilarity(queryEmbedding, embedding)
            index to similarity
        }
        
        // 按相似度排序
        similarities.sortedByDescending { it.second }.take(topN)
    }
    
    /**
     * 计算余弦相似度
     */
    private fun cosineSimilarity(vectorA: List<Float>, vectorB: List<Float>): Float {
        if (vectorA.size != vectorB.size) return 0f
        
        var dotProduct = 0.0f
        var normA = 0.0f
        var normB = 0.0f
        
        for (i in vectorA.indices) {
            dotProduct += vectorA[i] * vectorB[i]
            normA += vectorA[i] * vectorA[i]
            normB += vectorB[i] * vectorB[i]
        }
        
        return if (normA > 0 && normB > 0) {
            dotProduct / (kotlin.math.sqrt(normA) * kotlin.math.sqrt(normB))
        } else {
            0.0f
        }
    }
}
