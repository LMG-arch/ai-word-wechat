package com.ai.socialworld.data.repository

import com.ai.socialworld.data.database.dao.SocialDao
import com.ai.socialworld.data.database.entity.ChatGroupEntity
import com.ai.socialworld.data.database.entity.ChatMessageEntity
import com.ai.socialworld.data.model.ChatGroup
import com.ai.socialworld.data.model.ChatGroupType
import com.ai.socialworld.data.model.ChatMessage
import com.ai.socialworld.data.model.MessageType
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.time.Instant

interface SocialRepository {
    fun getAllChatGroups(): Flow<List<ChatGroupEntity>>
    fun getChatGroupsByMember(characterId: String): Flow<List<ChatGroupEntity>>
    suspend fun getChatGroupById(groupId: String): ChatGroupEntity?
    suspend fun createChatGroup(name: String, creatorId: String, description: String): String
    suspend fun sendMessage(groupId: String, characterId: String, content: String): String
    fun getMessagesByGroup(groupId: String): Flow<List<ChatMessageEntity>>
    suspend fun markMessageAsRead(messageId: String)
    suspend fun getUnreadCount(groupId: String): Int
}

class SocialRepositoryImpl(
    private val socialDao: SocialDao
) : SocialRepository {

    override fun getAllChatGroups(): Flow<List<ChatGroupEntity>> {
        return socialDao.getAllChatGroups()
    }

    override fun getChatGroupsByMember(characterId: String): Flow<List<ChatGroupEntity>> {
        return socialDao.getChatGroupsByMember(characterId)
    }

    override suspend fun getChatGroupById(groupId: String): ChatGroupEntity? {
        return socialDao.getChatGroupById(groupId)
    }

    override suspend fun createChatGroup(name: String, creatorId: String, description: String): String {
        val id = System.currentTimeMillis().toString()
        val entity = ChatGroupEntity(
            id = id,
            name = name,
            type = ChatGroupType.PRIVATE.name,
            memberIds = creatorId,
            createdBy = creatorId,
            isActive = true,
            relatedRelationshipId = null
        )
        socialDao.insertChatGroup(entity)
        return id
    }

    override suspend fun sendMessage(groupId: String, characterId: String, content: String): String {
        val id = System.currentTimeMillis().toString()
        val entity = ChatMessageEntity(
            id = id,
            groupId = groupId,
            characterId = characterId,
            content = content,
            type = MessageType.TEXT.name,
            timestamp = System.currentTimeMillis(),
            isRead = false
        )
        socialDao.insertMessage(entity)
        return id
    }

    override fun getMessagesByGroup(groupId: String): Flow<List<ChatMessageEntity>> {
        return socialDao.getMessagesByGroup(groupId)
    }

    override suspend fun markMessageAsRead(messageId: String) {
        socialDao.markMessageAsRead(messageId)
    }

    override suspend fun getUnreadCount(groupId: String): Int {
        return socialDao.getUnreadCount(groupId)
    }
}