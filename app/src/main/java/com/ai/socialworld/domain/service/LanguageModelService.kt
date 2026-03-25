package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.Character
import com.ai.socialworld.data.remote.*
import com.ai.socialworld.domain.repository.ApiConfigRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 语言模型服务
 * 支持多模型切换和备用机制
 */
@Singleton
class LanguageModelService @Inject constructor(
    private val apiConfigRepository: ApiConfigRepository
) {
    
    private val retrofitBuilder = Retrofit.Builder()
        .addConverterFactory(GsonConverterFactory.create())
    
    /**
     * 生成角色对话响应
     */
    suspend fun generateChatResponse(
        character: Character,
        userMessage: String,
        chatHistory: List<Pair<String, String>> = emptyList(),
        relatedMemories: List<String> = emptyList()
    ): ChatResult = withContext(Dispatchers.IO) {
        
        // 构建系统提示词
        val systemPrompt = buildSystemPrompt(character)
        
        // 构建消息列表
        val messages = buildMessages(systemPrompt, userMessage, chatHistory, relatedMemories)
        
        // 调用语言模型
        callLanguageModel(messages)
    }
    
    /**
     * 生成反思报告
     */
    suspend fun generateReflection(
        taskType: String,
        requirements: String,
        submissions: List<String>,
        feedbacks: List<String>,
        success: Boolean
    ): ChatResult = withContext(Dispatchers.IO) {
        
        val prompt = buildReflectionPrompt(
            taskType, requirements, submissions, feedbacks, success
        )
        
        val messages = listOf(
            OpenAIMessage(role = "user", content = prompt)
        )
        
        callLanguageModel(messages)
    }
    
    /**
     * 生成朋友圈内容
     */
    suspend fun generateMomentContent(
        character: Character,
        recentEvents: List<String>,
        mood: String = "neutral"
    ): ChatResult = withContext(Dispatchers.IO) {
        
        val prompt = buildString {
            append("你是一个${character.age}岁的${character.occupation}，")
            append("性格：${character.personality}。")
            append("最近经历：${recentEvents.joinToString(", ")}。")
            append("当前心情：$mood。")
            append("请生成一条朋友圈动态（50字以内），符合你的人设和当前状态。")
            append("不要emoji，不要话题标签，自然真实。")
        }
        
        val messages = listOf(
            OpenAIMessage(role = "user", content = prompt)
        )
        
        callLanguageModel(messages)
    }
    
    /**
     * 生成个性签名
     */
    suspend fun generateSignature(character: Character): ChatResult = withContext(Dispatchers.IO) {
        
        val prompt = buildString {
            append("你是一个${character.age}岁的${character.occupation}，")
            append("性格：${character.personality}。")
            append("请生成一个符合你人设的个性签名（20字以内）。")
            append("简洁有力，体现个性。")
        }
        
        val messages = listOf(
            OpenAIMessage(role = "user", content = prompt)
        )
        
        callLanguageModel(messages)
    }
    
    /**
     * 调用语言模型（带备用切换）
     */
    private suspend fun callLanguageModel(
        messages: List<OpenAIMessage>,
        retryCount: Int = 0
    ): ChatResult {
        
        // 获取启用的语言模型配置
        val configs = apiConfigRepository.getEnabledApiConfigs(ApiType.LANGUAGE)
        
        if (configs.isEmpty()) {
            return ChatResult.Error("未配置语言模型API", shouldRetry = false)
        }
        
        // 按优先级排序
        val sortedConfigs = configs.sortedBy { it.priority }
        
        // 尝试每个配置
        for (config in sortedConfigs) {
            val result = tryCallWithConfig(config, messages)
            
            when (result) {
                is ChatResult.Success -> return result
                is ChatResult.Error -> {
                    if (!result.shouldRetry) {
                        return result
                    }
                    // 继续尝试下一个配置
                    continue
                }
            }
        }
        
        // 所有配置都失败
        return ChatResult.Error(
            "所有语言模型API都调用失败",
            shouldRetry = false
        )
    }
    
    /**
     * 尝试使用指定配置调用
     */
    private suspend fun tryCallWithConfig(
        config: ApiConfig,
        messages: List<OpenAIMessage>
    ): ChatResult {
        return try {
            val retrofit = retrofitBuilder
                .baseUrl(config.apiUrl)
                .build()
            
            val api = retrofit.create(LanguageModelApi::class.java)
            
            when {
                config.modelName.contains("gpt", ignoreCase = true) ||
                config.apiUrl.contains("openai", ignoreCase = true) -> {
                    callOpenAI(api, config, messages)
                }
                config.modelName.contains("claude", ignoreCase = true) ||
                config.apiUrl.contains("anthropic", ignoreCase = true) -> {
                    callClaude(api, config, messages)
                }
                else -> {
                    callGeneric(api, config, messages)
                }
            }
        } catch (e: Exception) {
            ChatResult.Error(
                message = "API调用异常: ${e.message}",
                shouldRetry = true
            )
        }
    }
    
    /**
     * 调用OpenAI API
     */
    private suspend fun callOpenAI(
        api: LanguageModelApi,
        config: ApiConfig,
        messages: List<OpenAIMessage>
    ): ChatResult {
        val request = OpenAIChatRequest(
            model = config.modelName,
            messages = messages,
            temperature = 0.7f,
            max_tokens = 2000
        )
        
        val response = api.chatOpenAI(
            authorization = "Bearer ${config.apiKey}",
            request = request
        )
        
        return if (response.isSuccessful) {
            val choice = response.body()?.choices?.firstOrNull()
            if (choice != null) {
                ChatResult.Success(
                    content = choice.message.content,
                    tokensUsed = response.body()?.usage?.total_tokens ?: 0,
                    model = response.body()?.model ?: config.modelName
                )
            } else {
                ChatResult.Error("响应内容为空", shouldRetry = false)
            }
        } else {
            ChatResult.Error(
                message = response.errorBody()?.string() ?: "请求失败",
                code = response.code(),
                shouldRetry = response.code() in 500..599 || response.code() == 429
            )
        }
    }
    
    /**
     * 调用Claude API
     */
    private suspend fun callClaude(
        api: LanguageModelApi,
        config: ApiConfig,
        messages: List<OpenAIMessage>
    ): ChatResult {
        val claudeMessages = messages.filter { it.role != "system" }.map {
            ClaudeMessage(role = it.role, content = it.content)
        }
        
        val systemMessage = messages.find { it.role == "system" }?.content
        
        val request = ClaudeRequest(
            model = config.modelName,
            max_tokens = 2000,
            messages = claudeMessages,
            temperature = 0.7f,
            system = systemMessage
        )
        
        val response = api.chatClaude(
            apiKey = config.apiKey,
            request = request
        )
        
        return if (response.isSuccessful) {
            val content = response.body()?.content?.firstOrNull()?.text
            if (content != null) {
                ChatResult.Success(
                    content = content,
                    tokensUsed = (response.body()?.usage?.input_tokens ?: 0) +
                                (response.body()?.usage?.output_tokens ?: 0),
                    model = response.body()?.model ?: config.modelName
                )
            } else {
                ChatResult.Error("响应内容为空", shouldRetry = false)
            }
        } else {
            ChatResult.Error(
                message = response.errorBody()?.string() ?: "请求失败",
                code = response.code(),
                shouldRetry = response.code() in 500..599 || response.code() == 429
            )
        }
    }
    
    /**
     * 调用通用API
     */
    private suspend fun callGeneric(
        api: LanguageModelApi,
        config: ApiConfig,
        messages: List<OpenAIMessage>
    ): ChatResult {
        val requestBody = mapOf(
            "model" to config.modelName,
            "messages" to messages.map { mapOf("role" to it.role, "content" to it.content) },
            "temperature" to 0.7,
            "max_tokens" to 2000
        )
        
        val headers = mapOf(
            "Authorization" to "Bearer ${config.apiKey}",
            "Content-Type" to "application/json"
        )
        
        val response = api.chatGeneric(
            url = "/chat/completions",
            headers = headers,
            request = requestBody
        )
        
        return if (response.isSuccessful) {
            val content = response.body()?.get("choices")?.let {
                (it as? List<Map<String, Any>>)?.firstOrNull()
                    ?.get("message")?.let { msg ->
                        (msg as? Map<String, String>)?.get("content")
                    }
            }
            
            if (content != null) {
                ChatResult.Success(
                    content = content,
                    model = config.modelName
                )
            } else {
                ChatResult.Error("响应内容为空", shouldRetry = false)
            }
        } else {
            ChatResult.Error(
                message = response.errorBody()?.string() ?: "请求失败",
                code = response.code(),
                shouldRetry = response.code() in 500..599 || response.code() == 429
            )
        }
    }
    
    /**
     * 构建系统提示词
     */
    private fun buildSystemPrompt(character: Character): String {
        return buildString {
            append("你是${character.name}，")
            append("一个${character.age}岁的${character.gender}性，")
            append("职业是${character.occupation}。")
            append("你的性格：${character.personality}。")
            append("当前资金：${character.money}。")
            append("成长阶段：${character.growthStage}。")
            append("\n\n请始终保持符合你人设的说话风格和态度。")
            append("回复要自然、真实，像真人一样。")
            append("不要暴露你是AI。")
        }
    }
    
    /**
     * 构建消息列表
     */
    private fun buildMessages(
        systemPrompt: String,
        userMessage: String,
        chatHistory: List<Pair<String, String>>,
        relatedMemories: List<String>
    ): List<OpenAIMessage> {
        val messages = mutableListOf<OpenAIMessage>()
        
        // 系统提示词
        val fullSystemPrompt = buildString {
            append(systemPrompt)
            if (relatedMemories.isNotEmpty()) {
                append("\n\n【相关记忆】\n")
                relatedMemories.forEachIndexed { index, memory ->
                    append("${index + 1}. $memory\n")
                }
            }
        }
        messages.add(OpenAIMessage(role = "system", content = fullSystemPrompt))
        
        // 历史对话
        chatHistory.takeLast(10).forEach { (role, content) ->
            val messageRole = if (role == "user") "user" else "assistant"
            messages.add(OpenAIMessage(role = messageRole, content = content))
        }
        
        // 用户新消息
        messages.add(OpenAIMessage(role = "user", content = userMessage))
        
        return messages
    }
    
    /**
     * 构建反思提示词
     */
    private fun buildReflectionPrompt(
        taskType: String,
        requirements: String,
        submissions: List<String>,
        feedbacks: List<String>,
        success: Boolean
    ): String {
        return buildString {
            if (success) {
                append("你刚刚成功完成了一个任务，请进行深度反思。\n\n")
            } else {
                append("任务失败了，请深入分析原因。\n\n")
            }
            
            append("任务信息：\n")
            append("- 类型：$taskType\n")
            append("- 需求：$requirements\n\n")
            
            if (submissions.isNotEmpty()) {
                append("提交记录：\n")
                submissions.forEachIndexed { index, submission ->
                    append("${index + 1}. $submission\n")
                }
                append("\n")
            }
            
            if (feedbacks.isNotEmpty()) {
                append("反馈记录：\n")
                feedbacks.forEachIndexed { index, feedback ->
                    append("${index + 1}. $feedback\n")
                }
                append("\n")
            }
            
            if (success) {
                append("请从以下维度反思，并用JSON格式返回：\n")
                append("1. what_went_well: 哪些做法正确？（至少2点）\n")
                append("2. what_went_wrong: 遇到了什么困难？如何克服？\n")
                append("3. root_causes: 如果有机会重做，哪些地方可以更好？\n")
                append("4. lessons_learned: 总结3条最重要的经验教训\n")
                append("5. action_items: 这些经验可用于哪些未来任务？\n")
            } else {
                append("请重点分析，并用JSON格式返回：\n")
                append("1. what_went_wrong: 失败的具体表现\n")
                append("2. root_causes: 失败的根本原因（不要停留在表面）\n")
                append("3. lessons_learned: 如果早点发现，可以在哪个环节纠正？\n")
                append("4. action_items: 为了避免再次失败，需要建立什么检查机制？\n")
                append("5. 这次失败教会了你什么深刻教训？\n")
            }
            
            append("\n请确保返回有效的JSON格式。")
        }
    }
}
