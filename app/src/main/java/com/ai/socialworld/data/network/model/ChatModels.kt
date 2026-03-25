package com.ai.socialworld.data.network.model

import com.google.gson.annotations.SerializedName

/**
 * 语言模型API请求体
 */
data class ChatCompletionRequest(
    @SerializedName("model")
    val model: String,
    
    @SerializedName("messages")
    val messages: List<ChatMessage>,
    
    @SerializedName("temperature")
    val temperature: Double = 0.7,
    
    @SerializedName("max_tokens")
    val maxTokens: Int = 2000,
    
    @SerializedName("stream")
    val stream: Boolean = false
)

/**
 * 聊天消息
 */
data class ChatMessage(
    @SerializedName("role")
    val role: String, // system, user, assistant
    
    @SerializedName("content")
    val content: String
)

/**
 * 语言模型API响应
 */
data class ChatCompletionResponse(
    @SerializedName("id")
    val id: String,
    
    @SerializedName("object")
    val objectType: String,
    
    @SerializedName("created")
    val created: Long,
    
    @SerializedName("model")
    val model: String,
    
    @SerializedName("choices")
    val choices: List<Choice>,
    
    @SerializedName("usage")
    val usage: Usage?
)

/**
 * 选项
 */
data class Choice(
    @SerializedName("index")
    val index: Int,
    
    @SerializedName("message")
    val message: ChatMessage,
    
    @SerializedName("finish_reason")
    val finishReason: String?
)

/**
 * 使用量统计
 */
data class Usage(
    @SerializedName("prompt_tokens")
    val promptTokens: Int,
    
    @SerializedName("completion_tokens")
    val completionTokens: Int,
    
    @SerializedName("total_tokens")
    val totalTokens: Int
)

/**
 * 嵌入请求
 */
data class EmbeddingRequest(
    @SerializedName("model")
    val model: String,
    
    @SerializedName("input")
    val input: String
)

/**
 * 嵌入响应
 */
data class EmbeddingResponse(
    @SerializedName("object")
    val objectType: String,
    
    @SerializedName("data")
    val data: List<Embedding>,
    
    @SerializedName("model")
    val model: String,
    
    @SerializedName("usage")
    val usage: Usage
)

/**
 * 嵌入向量
 */
data class Embedding(
    @SerializedName("object")
    val objectType: String,
    
    @SerializedName("embedding")
    val embedding: List<Float>,
    
    @SerializedName("index")
    val index: Int
)
