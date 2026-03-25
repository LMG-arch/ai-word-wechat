package com.ai.socialworld.data.database.dao

import androidx.room.*
import com.ai.socialworld.data.database.entity.*
import kotlinx.coroutines.flow.Flow

/**
 * 社交数据访问对象
 */
@Dao
interface SocialDao {
    // 朋友圈相关
    @Query("SELECT * FROM moments ORDER BY createdAt DESC")
    fun getAllMoments(): Flow<List<MomentEntity>>

    @Query("SELECT * FROM moments WHERE characterId = :characterId ORDER BY createdAt DESC")
    fun getMomentsByCharacter(characterId: String): Flow<List<MomentEntity>>

    @Query("SELECT * FROM moments WHERE id = :momentId")
    suspend fun getMomentById(momentId: String): MomentEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMoment(moment: MomentEntity)

    @Update
    suspend fun updateMoment(moment: MomentEntity)

    @Delete
    suspend fun deleteMoment(moment: MomentEntity)

    @Query("DELETE FROM moments WHERE id = :momentId")
    suspend fun deleteMomentById(momentId: String)

    // 群聊相关
    @Query("SELECT * FROM chat_groups WHERE isActive = 1 ORDER BY createdAt DESC")
    fun getAllChatGroups(): Flow<List<ChatGroupEntity>>

    @Query("SELECT * FROM chat_groups WHERE id = :id")
    suspend fun getChatGroupById(id: String): ChatGroupEntity?

    @Query("SELECT * FROM chat_groups WHERE isActive = 1 AND (memberIds LIKE '%' || :characterId || '%')")
    fun getChatGroupsByMember(characterId: String): Flow<List<ChatGroupEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertChatGroup(group: ChatGroupEntity)

    @Update
    suspend fun updateChatGroup(group: ChatGroupEntity)

    @Query("UPDATE chat_groups SET isActive = 0 WHERE id = :id")
    suspend fun deactivateChatGroup(id: String)

    // 消息相关
    @Query("SELECT * FROM chat_messages WHERE groupId = :groupId ORDER BY timestamp ASC")
    fun getMessagesByGroup(groupId: String): Flow<List<ChatMessageEntity>>

    @Query("SELECT * FROM chat_messages WHERE groupId = :groupId ORDER BY timestamp DESC LIMIT :limit")
    suspend fun getRecentMessages(groupId: String, limit: Int): List<ChatMessageEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMessage(message: ChatMessageEntity)

    @Query("UPDATE chat_messages SET isRead = 1 WHERE id = :id")
    suspend fun markMessageAsRead(id: String)

    @Query("SELECT COUNT(*) FROM chat_messages WHERE groupId = :groupId AND isRead = 0")
    suspend fun getUnreadCount(groupId: String): Int
}