package com.ai.socialworld.data.database.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 朋友圈动态实体
 */
@Entity(tableName = "moments")
data class MomentEntity(
    @PrimaryKey
    val id: String,
    val characterId: String,
    val content: String,
    val imageUrl: String? = null,
    val createdAt: Long = System.currentTimeMillis(),
    val likesJson: String = "[]", // JSON序列化的点赞列表
    val commentsJson: String = "[]" // JSON序列化的评论列表
)

/**
 * 群聊实体
 */
@Entity(tableName = "chat_groups")
data class ChatGroupEntity(
    @PrimaryKey
    val id: String,
    val name: String,
    val type: String, // PRIVATE or COMPANY
    val memberIds: String = "", // 逗号分隔的ID列表
    val createdAt: Long = System.currentTimeMillis(),
    val createdBy: String,
    val isActive: Boolean = true,
    val relatedRelationshipId: String? = null
)

/**
 * 聊天消息实体
 */
@Entity(tableName = "chat_messages")
data class ChatMessageEntity(
    @PrimaryKey
    val id: String,
    val groupId: String,
    val characterId: String,
    val content: String,
    val type: String = "TEXT", // TEXT, IMAGE, VOICE
    val timestamp: Long = System.currentTimeMillis(),
    val isRead: Boolean = false
)
