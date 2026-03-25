package com.ai.socialworld.di

import com.ai.socialworld.domain.engine.MemoryEngine
import com.ai.socialworld.domain.usecase.memory.GetHistoryStateUseCase
import com.ai.socialworld.domain.usecase.memory.RecallMemoriesUseCase
import com.ai.socialworld.domain.usecase.memory.SaveMemoryUseCase
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object UseCaseModule {

    @Provides
    @Singleton
    fun provideSaveMemoryUseCase(
        memoryEngine: MemoryEngine
    ): SaveMemoryUseCase {
        return SaveMemoryUseCase(memoryEngine)
    }

    @Provides
    @Singleton
    fun provideRecallMemoriesUseCase(
        memoryEngine: MemoryEngine
    ): RecallMemoriesUseCase {
        return RecallMemoriesUseCase(memoryEngine)
    }

    @Provides
    @Singleton
    fun provideGetHistoryStateUseCase(
        memoryEngine: MemoryEngine
    ): GetHistoryStateUseCase {
        return GetHistoryStateUseCase(memoryEngine)
    }
}
