package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.ApiConfig
import com.ai.socialworld.data.network.LanguageModelApi
import com.ai.socialworld.data.network.model.ChatCompletionRequest
import com.ai.socialworld.data.network.model.ChatMessage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import javax.inject.Inject
import javax.inject.Singleton

/**
 * AI服务
 * 统一管理所有AI模型调用
 */
@Singleton
class AIService @Inject constructor(
    private val apiConfigRepository: com.ai.socialworld.domain.repository.ApiConfigRepository
) {
    private val retrofitCache = mutableMapOf<String, Retrofit>()
    
    /**
     * 生成对话回复
     */
    suspend fun generateChatResponse(
        messages: List<Pair<String, String>>, // role to content
        systemPrompt: String? = null
    ): Result<String> = withContext(Dispatchers.IO) {
        try {
            val config = apiConfigRepository.getCurrentConfig(com.ai.socialworld.data.model.ApiType.LANGUAGE_MODEL)
                ?: return@withContext Result.failure(Exception("未配置语言模型"))
            
            val api = getLanguageModelApi(config)
            val chatMessages = mutableListOf<ChatMessage>()
            
            systemPrompt?.let {
                chatMessages.add(ChatMessage("system", it))
            }
            
            messages.forEach { (role, content) ->
                chatMessages.add(ChatMessage(role, content))
            }
            
            val request = ChatCompletionRequest(
                model = config.modelName,
                messages = chatMessages
            )
            
            val response = api.createChatCompletion("Bearer ${config.apiKey}", request)
            
            if (response.isSuccessful) {
                val content = response.body()?.choices?.firstOrNull()?.message?.content
                if (content != null) {
                    Result.success(content)
                } else {
                    Result.failure(Exception("响应内容为空"))
                }
            } else {
                Result.failure(Exception("API调用失败: ${response.errorBody()?.string()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 生成角色回复
     */
    suspend fun generateCharacterResponse(
        characterName: String,
        characterPersonality: String,
        userMessage: String,
        conversationHistory: List<Pair<String, String>> = emptyList()
    ): Result<String> {
        val systemPrompt = buildString {
            append("你是$characterName。")
            append("你的性格是：$characterPersonality。")
            append("请以第一人称回复，保持角色人设的一致性。")
            append("回复要自然、有情感，符合你的性格特点。")
        }
        
        val messages = conversationHistory + listOf("user" to userMessage)
        return generateChatResponse(messages, systemPrompt)
    }
    
    /**
     * 生成头像描述
     */
    suspend fun generateAvatarPrompt(
        characterName: String,
        age: Int,
        gender: String,
        occupation: String,
        personality: String
    ): Result<String> {
        val systemPrompt = "你是一位专业的角色设计师，擅长根据描述生成详细的图像提示词。"
        
        val userMessage = buildString {
            append("请为以下角色生成一个详细的头像描述，用于AI图像生成：\n")
            append("姓名: $characterName\n")
            append("年龄: $age\n")
            append("性别: $gender\n")
            append("职业: $occupation\n")
            append("性格: $personality\n")
            append("\n要求：")
            append("1. 描述要详细，包含面部特征、发型、服装、表情等")
            append("2. 风格要写实，不要卡通或二次元")
            append("3. 直接返回描述文本，不要添加任何解释")
        }
        
        return generateChatResponse(listOf("user" to userMessage), systemPrompt)
    }
    
    /**
     * 获取或创建Retrofit实例
     */
    private fun getLanguageModelApi(config: ApiConfig): LanguageModelApi {
        return retrofitCache.getOrPut(config.baseUrl) {
            Retrofit.Builder()
                .baseUrl(config.baseUrl)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
        }.create(LanguageModelApi::class.java)
    }
}
