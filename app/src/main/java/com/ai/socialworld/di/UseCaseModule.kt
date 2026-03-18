package com.ai.socialworld.di

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
class UseCaseModule {

    @Provides
    @Singleton
    fun provideSaveMemoryUseCase(
        saveMemoryUseCase: SaveMemoryUseCase
    ): SaveMemoryUseCase {
        return saveMemoryUseCase
    }

    @Provides
    @Singleton
    fun provideRecallMemoriesUseCase(
        recallMemoriesUseCase: RecallMemoriesUseCase
    ): RecallMemoriesUseCase {
        return recallMemoriesUseCase
    }

    @Provides
    @Singleton
    fun provideGetHistoryStateUseCase(
        getHistoryStateUseCase: GetHistoryStateUseCase
    ): GetHistoryStateUseCase {
        return getHistoryStateUseCase
    }
}
