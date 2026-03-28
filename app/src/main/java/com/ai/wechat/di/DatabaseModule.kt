package com.ai.wechat.di

import android.content.Context
import androidx.room.Room
import com.ai.wechat.db.AppDatabase
import com.ai.wechat.db.dao.ApiConfigDao
import com.ai.wechat.db.dao.CharacterDao
import com.ai.wechat.db.dao.ChatMessageDao
import com.ai.wechat.db.dao.CompanyDao
import com.ai.wechat.db.dao.GroupChatDao
import com.ai.wechat.db.dao.TaskDao
import com.ai.wechat.db.dao.MemoryCacheDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * Database 模块
 * 提供 Room 数据库实例
 */
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideAppDatabase(
        @ApplicationContext context: Context
    ): AppDatabase {
        return Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "ai_wechat_db"
        )
            .fallbackToDestructiveMigration()
            .build()
    }

    @Provides
    @Singleton
    fun provideCharacterDao(database: AppDatabase): CharacterDao {
        return database.characterDao()
    }

    @Provides
    @Singleton
    fun provideApiConfigDao(database: AppDatabase): ApiConfigDao {
        return database.apiConfigDao()
    }

    @Provides
    @Singleton
    fun provideChatMessageDao(database: AppDatabase): ChatMessageDao {
        return database.chatMessageDao()
    }

    @Provides
    @Singleton
    fun provideCompanyDao(database: AppDatabase): CompanyDao {
        return database.companyDao()
    }

    @Provides
    @Singleton
    fun provideGroupChatDao(database: AppDatabase): GroupChatDao {
        return database.groupChatDao()
    }

    @Provides
    @Singleton
    fun provideTaskDao(database: AppDatabase): TaskDao {
        return database.taskDao()
    }

    @Provides
    @Singleton
    fun provideMemoryCacheDao(database: AppDatabase): MemoryCacheDao {
        return database.memoryCacheDao()
    }
}
