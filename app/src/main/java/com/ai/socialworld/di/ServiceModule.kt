package com.ai.socialworld.di

import com.ai.socialworld.domain.service.MemoryService
import com.ai.socialworld.domain.service.MemoryServiceImpl
import com.ai.socialworld.domain.service.TimeDecayService
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
class ServiceModule {

    @Provides
    @Singleton
    fun provideTimeDecayService(): TimeDecayService {
        return TimeDecayService()
    }

    @Provides
    @Singleton
    fun provideMemoryService(
        timeDecayService: TimeDecayService
    ): MemoryService {
        return MemoryServiceImpl(timeDecayService)
    }
}
