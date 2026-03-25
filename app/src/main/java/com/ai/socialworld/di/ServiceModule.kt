package com.ai.socialworld.di

import com.ai.socialworld.domain.engine.*
import com.ai.socialworld.domain.service.*
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object ServiceModule {

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
    
    // 引擎提供
    
    @Provides
    @Singleton
    fun provideWorldTimeManager(): WorldTimeManager {
        return WorldTimeManager()
    }
    
    @Provides
    @Singleton
    fun provideEconomyEngine(): EconomyEngine {
        return EconomyEngine()
    }
    
    @Provides
    @Singleton
    fun provideTaskEngine(): TaskEngine {
        return TaskEngine()
    }
    
    @Provides
    @Singleton
    fun provideReflectionEngine(): ReflectionEngine {
        return ReflectionEngine()
    }
    
    @Provides
    @Singleton
    fun provideScheduleEngine(): ScheduleEngine {
        return ScheduleEngine()
    }
}
