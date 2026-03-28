package com.ai.wechat.db

import androidx.room.Database
import androidx.room.RoomDatabase
import com.ai.wechat.data.model.*
import com.ai.wechat.db.dao.*

/**
 * 应用主数据库
 * 包含所有本地数据表
 */
@Database(
    entities = [
        Character::class,
        ApiConfig::class,
        ChatMessage::class,
        Company::class,
        CompanyMember::class,
        GroupChat::class,
        GroupChatMember::class,
        Task::class,
        MemoryCache::class
    ],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    
    abstract fun characterDao(): CharacterDao
    abstract fun apiConfigDao(): ApiConfigDao
    abstract fun chatMessageDao(): ChatMessageDao
    abstract fun companyDao(): CompanyDao
    abstract fun groupChatDao(): GroupChatDao
    abstract fun taskDao(): TaskDao
    abstract fun memoryCacheDao(): MemoryCacheDao
}
