package com.ai.socialworld.data.model

import java.time.Instant

/**
 * 朋友圈动态数据模型
 */
data class Moment(
    val id: String,
    val characterId: String,
    val content: String,
    val imageUrl: String? = null,
    val createdAt: Instant = Instant.now(),
    val likes: List<Like> = emptyList(),
    val comments: List<Comment> = emptyList()
)

/**
 * 点赞
 */
data class Like(
    val characterId: String,
    val timestamp: Instant = Instant.now()
)

/**
 * 评论
 */
data class Comment(
    val id: String,
    val characterId: String,
    val content: String,
    val timestamp: Instant = Instant.now(),
    val replyTo: String? = null // 回复评论ID
)

/**
 * 群聊数据模型
 */
data class ChatGroup(
    val id: String,
    val name: String,
    val type: ChatGroupType,
    val memberIds: List<String>,
    val createdAt: Instant = Instant.now(),
    val createdBy: String,
    val isActive: Boolean = true,
    val relatedRelationshipId: String? = null // 关联的关系ID（私人群聊）
)

/**
 * 群聊类型
 */
enum class ChatGroupType {
    PRIVATE,    // 私人群聊（两人关系）
    COMPANY     // 公司群聊
}

/**
 * 聊天消息
 */
data class ChatMessage(
    val id: String,
    val groupId: String,
    val characterId: String,
    val content: String,
    val type: MessageType = MessageType.TEXT,
    val timestamp: Instant = Instant.now(),
    val isRead: Boolean = false
)

/**
 * 消息类型
 */
enum class MessageType {
    TEXT,   // 文字
    IMAGE,  // 图片
    VOICE   // 语音
}
