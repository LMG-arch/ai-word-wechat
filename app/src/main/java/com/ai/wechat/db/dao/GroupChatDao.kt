package com.ai.wechat.db.dao

import androidx.room.*
import com.ai.wechat.data.model.GroupChat
import com.ai.wechat.data.model.GroupChatMember
import kotlinx.coroutines.flow.Flow

/**
 * 群聊数据访问对象
 */
@Dao
interface GroupChatDao {

    @Query("SELECT * FROM group_chats WHERE isActive = 1 ORDER BY lastMessageTime DESC")
    fun getAllGroupChats(): Flow<List<GroupChat>>

    @Query("SELECT * FROM group_chats WHERE id = :id")
    suspend fun getGroupChatById(id: String): GroupChat?

    @Query("SELECT * FROM group_chats WHERE id = :id")
    fun getGroupChatByIdFlow(id: String): Flow<GroupChat?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertGroupChat(groupChat: GroupChat)

    @Update
    suspend fun updateGroupChat(groupChat: GroupChat)

    @Delete
    suspend fun deleteGroupChat(groupChat: GroupChat)

    @Query("UPDATE group_chats SET lastMessage = :message, lastMessageTime = :time WHERE id = :id")
    suspend fun updateLastMessage(id: String, message: String?, time: Long)

    @Query("UPDATE group_chats SET isActive = 0 WHERE id = :id")
    suspend fun deactivateGroupChat(id: String)

    // Group Chat Members
    @Query("SELECT * FROM group_chat_members WHERE groupChatId = :groupChatId ORDER BY joinedAt")
    fun getMembersByGroupId(groupChatId: String): Flow<List<GroupChatMember>>

    @Query("SELECT * FROM group_chat_members WHERE characterId = :characterId")
    fun getGroupsByCharacterId(characterId: String): Flow<List<GroupChatMember>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMember(member: GroupChatMember)

    @Delete
    suspend fun deleteMember(member: GroupChatMember)

    @Query("SELECT * FROM group_chat_members WHERE groupChatId = :groupId AND characterId = :characterId")
    suspend fun getMember(groupId: String, characterId: String): GroupChatMember?
}
