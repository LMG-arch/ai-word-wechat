package com.ai.socialworld.domain.service

import com.ai.socialworld.data.model.Character
import com.ai.socialworld.data.model.LogType
import com.ai.socialworld.data.model.Memory
import com.ai.socialworld.data.model.MemoryType
import com.ai.socialworld.domain.repository.ApiConfigRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 聊天服务
 * 处理角色与用户的对话，集成记忆召回
 */
@Singleton
class ChatService @Inject constructor(
    private val languageModelService: LanguageModelService,
    private val memoryRecallService: MemoryRecallService,
    private val memoryService: MemoryService,
    private val apiConfigRepository: ApiConfigRepository
) {

    /**
     * 生成角色回复
     */
    suspend fun generateResponse(
        character: Character,
        userMessage: String,
        chatHistory: List<Pair<String, String>> = emptyList()
    ): ChatResult = withContext(Dispatchers.IO) {

        val query = buildString {
            append("角色：${character.name}，")
            append("职业：${character.occupation}，")
            append("性格：${character.personality}，")
            append("用户说：$userMessage")
        }

        val retrievedMemories = memoryRecallService.recallMemories(
            query = query,
            characterId = character.id.toString(),
            topK = 10
        )

        val memoryContexts = retrievedMemories.map { it.content }

        val result = languageModelService.generateChatResponse(
            character = character,
            userMessage = userMessage,
            chatHistory = chatHistory,
            relatedMemories = memoryContexts
        )

        if (result is ChatResult.Success) {
            storeConversationMemory(character, userMessage, result.content, retrievedMemories)
        }

        result
    }

    /**
     * 存储对话记忆
     */
    private suspend fun storeConversationMemory(
        character: Character,
        userMessage: String,
        aiResponse: String,
        relatedMemories: List<Memory>
    ) {
        val content = buildString {
            append("与用户对话：\n")
            append("用户：$userMessage\n")
            append("${character.name}：$aiResponse")
        }

        val relatedEntities = relatedMemories.mapNotNull { it.id }

        memoryService.storeMemory(
            characterId = character.id.toString(),
            content = content,
            type = MemoryType.CONVERSATION,
            importance = 0.5f,
            relatedEntities = relatedEntities.take(5)
        )
    }

    /**
     * 生成AI角色间的对话
     */
    suspend fun generateCharacterToCharacterResponse(
        speaker: Character,
        listener: Character,
        message: String,
        topic: String
    ): ChatResult = withContext(Dispatchers.IO) {

        val systemPrompt = buildString {
            append("你是${speaker.name}。\n")
            append("你的性格：${speaker.personality}。\n")
            append("你正在和${listener.name}对话。\n")
            append("话题是：$topic\n")
            append("请以符合你人设的方式回复。")
        }

        val query = "$topic - $message"

        val retrievedMemories = memoryRecallService.recallMemories(
            query = query,
            characterId = speaker.id.toString(),
            topK = 5
        )

        val memoryContexts = retrievedMemories.map { it.content }

        val messages = mutableListOf<Pair<String, String>>()

        if (memoryContexts.isNotEmpty()) {
            messages.add("user" to "【相关记忆】\n${memoryContexts.joinToString("\n")}")
        }

        messages.add("user" to message)

        languageModelService.generateChatResponse(
            character = speaker,
            userMessage = message,
            chatHistory = messages,
            relatedMemories = memoryContexts
        )
    }
}