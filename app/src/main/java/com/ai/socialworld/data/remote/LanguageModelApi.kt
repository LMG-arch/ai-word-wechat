package com.ai.socialworld.data.remote

import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.*

/**
 * 语言模型API接口
 * 支持OpenAI GPT、Claude、国产大模型等
 */
interface LanguageModelApi {
    
    /**
     * OpenAI Chat Completions API
     */
    @POST("v1/chat/completions")
    suspend fun chatOpenAI(
        @Header("Authorization") authorization: String,
        @Header("Content-Type") contentType: String = "application/json",
        @Body request: OpenAIChatRequest
    ): Response<OpenAIChatResponse>
    
    /**
     * Anthropic Claude API
     */
    @POST("v1/messages")
    suspend fun chatClaude(
        @Header("x-api-key") apiKey: String,
        @Header("anthropic-version") version: String = "2023-06-01",
        @Header("Content-Type") contentType: String = "application/json",
        @Body request: ClaudeRequest
    ): Response<ClaudeResponse>
    
    /**
     * 通用聊天接口
     */
    @POST
    suspend fun chatGeneric(
        @Url url: String,
        @HeaderMap headers: Map<String, String>,
        @Body request: Map<String, Any>
    ): Response<Map<String, Any>>
    
    /**
     * 文本生成（非对话）
     */
    @POST
    suspend fun generateText(
        @Url url: String,
        @HeaderMap headers: Map<String, String>,
        @Body request: Map<String, Any>
    ): Response<Map<String, Any>>
}

// ==================== OpenAI Data Classes ====================

data class OpenAIChatRequest(
    val model: String,
    val messages: List<OpenAIMessage>,
    val temperature: Float = 0.7f,
    val max_tokens: Int = 2000,
    val top_p: Float = 1.0f,
    val frequency_penalty: Float = 0.0f,
    val presence_penalty: Float = 0.0f
)

data class OpenAIMessage(
    val role: String,  // system, user, assistant
    val content: String
)

data class OpenAIChatResponse(
    val id: String,
    val object_type: String,
    val created: Long,
    val model: String,
    val choices: List<OpenAIChoice>,
    val usage: OpenAIUsage
)

data class OpenAIChoice(
    val index: Int,
    val message: OpenAIMessage,
    val finish_reason: String
)

data class OpenAIUsage(
    val prompt_tokens: Int,
    val completion_tokens: Int,
    val total_tokens: Int
)

// ==================== Claude Data Classes ====================

data class ClaudeRequest(
    val model: String,
    val max_tokens: Int = 2000,
    val messages: List<ClaudeMessage>,
    val temperature: Float = 0.7f,
    val system: String? = null
)

data class ClaudeMessage(
    val role: String,  // user, assistant
    val content: String
)

data class ClaudeResponse(
    val id: String,
    val type: String,
    val role: String,
    val content: List<ClaudeContent>,
    val model: String,
    val stop_reason: String?,
    val usage: ClaudeUsage
)

data class ClaudeContent(
    val type: String,
    val text: String
)

data class ClaudeUsage(
    val input_tokens: Int,
    val output_tokens: Int
)

// ==================== Generic Response ====================

sealed class ChatResult {
    data class Success(
        val content: String,
        val tokensUsed: Int = 0,
        val model: String = ""
    ) : ChatResult()
    
    data class Error(
        val message: String,
        val code: Int? = null,
        val shouldRetry: Boolean = true
    ) : ChatResult()
}
