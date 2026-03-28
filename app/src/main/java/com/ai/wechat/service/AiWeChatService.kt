package com.ai.wechat.service

import com.ai.wechat.data.memory.MemoryEngine
import com.ai.wechat.data.memory.MemoryType
import com.ai.wechat.data.memory.TimeRange
import com.ai.wechat.data.model.*
import com.ai.wechat.db.dao.*
import com.ai.wechat.network.AiService
import com.ai.wechat.network.ChatRequest
import com.ai.wechat.network.ImageRequest
import com.ai.wechat.network.Message
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import java.time.Instant
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * AI 服务层
 * 封装所有 AI 相关的调用逻辑
 */
@Singleton
class AiWeChatService @Inject constructor(
    private val aiService: AiService,
    private val memoryEngine: MemoryEngine,
    private val characterDao: CharacterDao,
    private val chatMessageDao: ChatMessageDao,
    private val apiConfigDao: ApiConfigDao
) {

    /**
     * 生成对话响应
     */
    suspend fun generateResponse(
        characterId: String,
        userInput: String,
        conversationHistory: List<Pair<String, String>> = emptyList()
    ): Result<String> = withContext(Dispatchers.IO) {
        try {
            // 获取角色信息
            val character = characterDao.getCharacterById(characterId)
                ?: return@withContext Result.failure(Exception("角色不存在"))

            // 检索相关记忆
            val memories = memoryEngine.recallMemories(
                characterId = characterId,
                query = userInput,
                timeRange = TimeRange.last7Days(),
                topK = 10
            )

            // 构建上下文
            val context = buildContext(character, memories, conversationHistory)

            // 调用语言模型
            val request = ChatRequest(
                model = "", // 将在 AiService 中填充
                messages = context,
                temperature = 0.7,
                maxTokens = 1024
            )

            val response = aiService.chat(com.ai.wechat.data.model.ApiType.LLM, request)

            response.onSuccess { resp ->
                // 存储对话记忆
                memoryEngine.storeMemory(
                    characterId = characterId,
                    content = "用户：$userInput\n角色：${resp.choices?.firstOrNull()?.message?.content ?: ""}",
                    type = MemoryType.CONVERSATION,
                    importance = 0.6f,
                    relatedEntities = emptyList()
                )
            }

            response.map { it.choices?.firstOrNull()?.message?.content ?: "响应为空" }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 生成角色头像
     */
    suspend fun generateAvatar(
        character: Character
    ): Result<String> = withContext(Dispatchers.IO) {
        try {
            val prompt = buildAvatarPrompt(character)
            val request = ImageRequest(
                prompt = prompt,
                negativePrompt = "卡通，二次元，动漫，Q 版，简笔画，低分辨率，模糊",
                width = 512,
                height = 512,
                steps = 30
            )

            val response = aiService.generateImage(request)
            response.map { resp ->
                resp.images?.firstOrNull()
                    ?: throw Exception("图像生成结果为空")
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 生成文本内容（任务用）
     */
    suspend fun generateText(
        prompt: String,
        systemPrompt: String = "你是一个专业的 AI 助手"
    ): Result<String> = withContext(Dispatchers.IO) {
        try {
            val request = ChatRequest(
                model = "",
                messages = listOf(
                    Message(role = "system", content = systemPrompt),
                    Message(role = "user", content = prompt)
                ),
                temperature = 0.7,
                maxTokens = 2048
            )

            val response = aiService.chat(com.ai.wechat.data.model.ApiType.LLM, request)
            response.map { it.choices?.firstOrNull()?.message?.content ?: "生成失败" }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 生成图像（任务用）
     */
    suspend fun generateImage(
        prompt: String,
        negativePrompt: String = "卡通，二次元，动漫，Q 版，简笔画，低分辨率，模糊",
        width: Int = 1024,
        height: Int = 1024
    ): Result<String> = withContext(Dispatchers.IO) {
        try {
            val request = ImageRequest(
                prompt = prompt,
                negativePrompt = negativePrompt,
                width = width,
                height = height,
                steps = 30,
                cfgScale = 7.0
            )

            val response = aiService.generateImage(request)
            response.map { resp ->
                resp.images?.firstOrNull()
                    ?: throw Exception("图像生成结果为空")
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 生成反思报告
     */
    suspend fun generateReflection(
        task: Task,
        executionLog: String,
        isSuccess: Boolean
    ): Result<ReflectionReport> = withContext(Dispatchers.IO) {
        try {
            val prompt = if (isSuccess) {
                """
                你刚刚成功完成任务：${task.title}
                任务类型：${task.type}
                执行过程：$executionLog
                
                请反思：
                1. 哪些做法正确？（至少 2 点）
                2. 遇到什么困难？如何克服？
                3. 总结 3 条最重要的经验教训
                4. 这些经验可用于哪些未来任务？
                """.trimIndent()
            } else {
                """
                任务失败：${task.title}
                任务类型：${task.type}
                执行过程：$executionLog
                
                请分析原因：
                1. 失败的根本原因是什么？
                2. 哪个环节可以纠正？
                3. 建立什么检查机制避免再犯？
                4. 至少 3 条深刻教训
                """.trimIndent()
            }

            val response = generateText(prompt, "你是一个善于反思和总结的 AI 助手")
            
            response.map { content ->
                ReflectionReport(
                    taskId = task.id,
                    taskName = task.title,
                    success = isSuccess,
                    content = content,
                    completionTime = System.currentTimeMillis()
                )
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 生成日程
     */
    suspend fun generateDailySchedule(
        character: Character
    ): Result<String> = withContext(Dispatchers.IO) {
        try {
            val prompt = """
            为以下角色生成一天的日程安排：
            姓名：${character.name}
            年龄：${character.age}
            职业：${character.occupation}
            性格：${character.personality}
            当前心情：${character.mood}
            
            日程格式：
            09:00-12:00 地点 活动
            12:00-13:00 地点 午餐
            18:00-20:00 地点 活动
            
            请根据职业和性格生成合理的日程。
            """.trimIndent()

            generateText(prompt, "你是一个日程规划助手")
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    // 辅助方法

    private suspend fun buildContext(
        character: Character,
        memories: List<com.ai.wechat.data.memory.Memory>,
        conversationHistory: List<Pair<String, String>>
    ): List<Message> {
        val memoryContext = memories.joinToString("\n") { "[记忆] ${it.content}" }
        val historyContext = conversationHistory.joinToString("\n") { "用户：${it.first}\n角色：${it.second}" }

        val systemPrompt = """
        【角色人设】
        姓名：${character.name}
        年龄：${character.age}岁
        性别：${character.gender}
        职业：${character.occupation}
        性格：${character.personality}
        当前心情：${character.mood}
        资金：${character.money}

        【相关记忆】
        $memoryContext

        【对话历史】
        $historyContext

        请以上述人设与用户对话，保持性格一致。
        """.trimIndent()

        return listOf(
            Message(role = "system", content = systemPrompt),
            Message(role = "user", content = "你好")
        )
    }

    private fun buildAvatarPrompt(character: Character): String {
        val ageDesc = when (character.getAgeStage()) {
            AgeStage.CHILD -> "儿童"
            AgeStage.TEENAGER -> "青少年"
            AgeStage.YOUTH -> "年轻人"
            AgeStage.MIDDLE_AGE -> "中年人"
            AgeStage.SENIOR -> "老年人"
        }

        return """
        生成一个${character.gender}性${ageDesc}的肖像头像，
        职业是${character.occupation}，
        性格特征：${character.personality}。
        
        要求：
        - 写实风格，照片质感
        - 史诗感，电影质感
        - 8K 分辨率，细节丰富
        - 光影效果自然
        - 表情符合性格特征
        
        负面提示词：卡通，二次元，动漫，Q 版，简笔画，低分辨率，模糊
        """.trimIndent()
    }
}

/**
 * 反思报告数据结构
 */
data class ReflectionReport(
    val taskId: String,
    val taskName: String,
    val success: Boolean,
    val content: String,
    val completionTime: Long
)
