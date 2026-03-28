package com.ai.wechat.db.dao

import androidx.room.*
import com.ai.wechat.data.model.ChatMessage
import kotlinx.coroutines.flow.Flow

/**
 * 聊天消息数据访问对象
 */
@Dao
interface ChatMessageDao {

    @Query("SELECT * FROM chat_messages WHERE conversationId = :conversationId ORDER BY timestamp ASC")
    fun getMessagesByConversation(conversationId: String): Flow<List<ChatMessage>>

    @Query("SELECT * FROM chat_messages WHERE conversationId = :conversationId ORDER BY timestamp DESC LIMIT 1")
    suspend fun getLastMessage(conversationId: String): ChatMessage?

    @Query("SELECT DISTINCT conversationId FROM chat_messages ORDER BY timestamp DESC")
    fun getAllConversationIds(): Flow<List<String>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMessage(message: ChatMessage)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMessages(messages: List<ChatMessage>)

    @Query("UPDATE chat_messages SET isRead = 1 WHERE conversationId = :conversationId AND receiverId = :receiverId")
    suspend fun markAsRead(conversationId: String, receiverId: String)

    @Query("SELECT COUNT(*) FROM chat_messages WHERE conversationId = :conversationId AND isRead = 0 AND receiverId = :receiverId")
    suspend fun getUnreadCount(conversationId: String, receiverId: String): Int

    @Query("DELETE FROM chat_messages WHERE conversationId = :conversationId")
    suspend fun deleteConversation(conversationId: String)
}
