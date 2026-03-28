package com.ai.wechat.network

import retrofit2.Response
import retrofit2.http.*

/**
 * AI API 服务接口
 * 支持多种 AI 服务商
 */
interface AiApiService {

    /**
     * 语言模型聊天接口
     */
    @POST
    suspend fun chat(
        @Url url: String,
        @Header("Authorization") authorization: String,
        @Header("Content-Type") contentType: String = "application/json",
        @Body request: ChatRequest
    ): Response<ChatResponse>

    /**
     * 图像生成接口
     */
    @POST
    suspend fun generateImage(
        @Url url: String,
        @Header("Authorization") authorization: String,
        @Header("Content-Type") contentType: String = "application/json",
        @Body request: ImageRequest
    ): Response<ImageResponse>

    /**
     * 向量嵌入接口
     */
    @POST
    suspend fun embed(
        @Url url: String,
        @Header("Authorization") authorization: String,
        @Header("Content-Type") contentType: String = "application/json",
        @Body request: EmbedRequest
    ): Response<EmbedResponse>

    /**
     * 重排序接口
     */
    @POST
    suspend fun rerank(
        @Url url: String,
        @Header("Authorization") authorization: String,
        @Header("Content-Type") contentType: String = "application/json",
        @Body request: RerankRequest
    ): Response<RerankResponse>
}

/**
 * 聊天请求
 */
data class ChatRequest(
    val model: String,
    val messages: List<Message>,
    val temperature: Double = 0.7,
    val maxTokens: Int = 2048,
    val stream: Boolean = false
)

data class Message(
    val role: String,
    val content: String
)

/**
 * 聊天响应
 */
data class ChatResponse(
    val id: String?,
    val choices: List<Choice>?,
    val error: Error?
)

data class Choice(
    val message: Message,
    val finishReason: String?
)

/**
 * 图像生成请求
 */
data class ImageRequest(
    val prompt: String,
    val negativePrompt: String? = null,
    val width: Int = 1024,
    val height: Int = 1024,
    val steps: Int = 30,
    val cfgScale: Double = 7.0,
    val seed: Long? = null
)

/**
 * 图像生成响应
 */
data class ImageResponse(
    val images: List<String>?,
    val error: Error?
)

/**
 * 向量嵌入请求
 */
data class EmbedRequest(
    val model: String,
    val input: List<String>
)

/**
 * 向量嵌入响应
 */
data class EmbedResponse(
    val data: List<EmbedData>?,
    val error: Error?
)

data class EmbedData(
    val embedding: List<Float>,
    val index: Int
)

/**
 * 重排序请求
 */
data class RerankRequest(
    val query: String,
    val documents: List<String>,
    val topK: Int = 10
)

/**
 * 重排序响应
 */
data class RerankResponse(
    val results: List<RerankResult>?,
    val error: Error?
)

data class RerankResult(
    val index: Int,
    val score: Double,
    val text: String
)

/**
 * 错误响应
 */
data class Error(
    val message: String,
    val type: String?,
    val code: String?
)
