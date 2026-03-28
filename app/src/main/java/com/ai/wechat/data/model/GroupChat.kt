package com.ai.wechat.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 群聊实体
 */
@Entity(tableName = "group_chats")
data class GroupChat(
    @PrimaryKey
    val id: String,
    val name: String,
    val type: GroupChatType,
    val avatarUrl: String?,
    val creatorId: String,
    val createdAt: Long,
    val memberCount: Int = 2,
    val lastMessage: String?,
    val lastMessageTime: Long?,
    val isActive: Boolean = true
)

/**
 * 群聊成员
 */
@Entity(tableName = "group_chat_members")
data class GroupChatMember(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val groupChatId: String,
    val characterId: String,
    val joinedAt: Long,
    val isOwner: Boolean = false
)

/**
 * 群聊类型
 */
enum class GroupChatType {
    PRIVATE,    // 私人群聊（两人）
    COMPANY     // 公司群聊
}
