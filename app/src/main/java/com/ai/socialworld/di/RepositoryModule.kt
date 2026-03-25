package com.ai.socialworld.di

import com.ai.socialworld.data.database.dao.SocialDao
import com.ai.socialworld.data.repository.*
import com.ai.socialworld.domain.repository.*
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object RepositoryModule {

    @Provides
    @Singleton
    fun provideCharacterRepository(characterDao: CharacterDao): CharacterRepository {
        return CharacterRepositoryImpl(characterDao)
    }

    @Provides
    @Singleton
    fun provideTaskRepository(
        taskDao: TaskDao,
        companyDao: CompanyDao
    ): TaskRepository {
        return TaskRepositoryImpl(taskDao, companyDao)
    }

    @Provides
    @Singleton
    fun provideMemoryRepository(
        memoryDao: MemoryDao,
        reflectionDao: ReflectionDao
    ): MemoryRepository {
        return MemoryRepositoryImpl(memoryDao, reflectionDao)
    }

    @Provides
    @Singleton
    fun provideRelationshipRepository(relationshipDao: RelationshipDao): RelationshipRepository {
        return RelationshipRepositoryImpl(relationshipDao)
    }

    @Provides
    @Singleton
    fun provideSkillRepository(skillDao: SkillDao): SkillRepository {
        return SkillRepositoryImpl(skillDao)
    }

    @Provides
    @Singleton
    fun provideReflectionRepository(reflectionDao: ReflectionDao): ReflectionRepository {
        return ReflectionRepositoryImpl(reflectionDao)
    }

    @Provides
    @Singleton
    fun provideCompanyRepository(companyDao: CompanyDao): CompanyRepository {
        return CompanyRepositoryImpl(companyDao)
    }

    @Provides
    @Singleton
    fun provideScheduleRepository(scheduleDao: ScheduleDao): ScheduleRepository {
        return ScheduleRepositoryImpl(scheduleDao)
    }

    @Provides
    @Singleton
    fun provideApiConfigRepository(apiConfigDao: ApiConfigDao): ApiConfigRepository {
        return ApiConfigRepositoryImpl(apiConfigDao)
    }

    @Provides
    @Singleton
    fun provideMomentRepository(socialDao: SocialDao): MomentRepository {
        return MomentRepositoryImpl(socialDao)
    }

    @Provides
    @Singleton
    fun provideSocialRepository(socialDao: SocialDao): SocialRepository {
        return SocialRepositoryImpl(socialDao)
    }
}