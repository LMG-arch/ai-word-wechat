package com.ai.wechat.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 聊天消息实体
 */
@Entity(tableName = "chat_messages")
data class ChatMessage(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val conversationId: String,
    val senderId: String,
    val receiverId: String,
    val content: String,
    val messageType: MessageType = MessageType.TEXT,
    val imageUrl: String?,
    val timestamp: Long,
    val isRead: Boolean = false,
    val isFromUser: Boolean = true
)

/**
 * 消息类型
 */
enum class MessageType {
    TEXT,
    IMAGE,
    VOICE,
    SYSTEM
}

/**
 * 会话实体
 */
data class Conversation(
    val id: String,
    val characterId: String,
    val characterName: String,
    val characterAvatar: String?,
    val lastMessage: String?,
    val lastMessageTime: Long?,
    val unreadCount: Int = 0
)
