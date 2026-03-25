package com.ai.socialworld.data.remote

import retrofit2.Response
import retrofit2.http.*

/**
 * 向量模型API接口
 * 支持OpenAI Embedding、国产向量模型等
 */
interface VectorModelApi {
    
    /**
     * OpenAI Embeddings API
     */
    @POST("v1/embeddings")
    suspend fun createEmbeddingOpenAI(
        @Header("Authorization") authorization: String,
        @Header("Content-Type") contentType: String = "application/json",
        @Body request: OpenAIEmbeddingRequest
    ): Response<OpenAIEmbeddingResponse>
    
    /**
     * 通用向量生成接口
     */
    @POST
    suspend fun createEmbedding(
        @Url url: String,
        @HeaderMap headers: Map<String, String>,
        @Body request: Map<String, Any>
    ): Response<Map<String, Any>>
}

/**
 * OpenAI Embedding请求
 */
data class OpenAIEmbeddingRequest(
    val model: String,
    val input: String,
    val encoding_format: String = "float"
)

/**
 * OpenAI Embedding响应
 */
data class OpenAIEmbeddingResponse(
    val object_type: String,
    val data: List<EmbeddingData>,
    val model: String,
    val usage: EmbeddingUsage
)

data class EmbeddingData(
    val object_type: String,
    val embedding: List<Float>,
    val index: Int
)

data class EmbeddingUsage(
    val prompt_tokens: Int,
    val total_tokens: Int
)

/**
 * 向量生成结果
 */
sealed class EmbeddingResult {
    data class Success(
        val embedding: List<Float>,
        val dimensions: Int,
        val tokensUsed: Int = 0
    ) : EmbeddingResult()
    
    data class Error(
        val message: String,
        val code: Int? = null,
        val shouldRetry: Boolean = true
    ) : EmbeddingResult()
}
