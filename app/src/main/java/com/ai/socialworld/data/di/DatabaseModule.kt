package com.ai.socialworld.data.di

import android.content.Context
import androidx.room.Room
import com.ai.socialworld.data.database.CharacterDatabase
import com.ai.socialworld.data.database.dao.*
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideCharacterDatabase(
        @ApplicationContext context: Context
    ): CharacterDatabase {
        return Room.databaseBuilder(
            context,
            CharacterDatabase::class.java,
            "character_database"
        ).build()
    }

    @Provides
    @Singleton
    fun provideCharacterDao(
        database: CharacterDatabase
    ): CharacterDao {
        return database.characterDao()
    }
    
    @Provides
    @Singleton
    fun provideTaskDao(
        database: CharacterDatabase
    ): TaskDao {
        return database.taskDao()
    }
    
    @Provides
    @Singleton
    fun provideCompanyDao(
        database: CharacterDatabase
    ): CompanyDao {
        return database.companyDao()
    }
    
    @Provides
    @Singleton
    fun provideScheduleDao(
        database: CharacterDatabase
    ): ScheduleDao {
        return database.scheduleDao()
    }
    
    @Provides
    @Singleton
    fun provideSocialDao(
        database: CharacterDatabase
    ): SocialDao {
        return database.socialDao()
    }
}
