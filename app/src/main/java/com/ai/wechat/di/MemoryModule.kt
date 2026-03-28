package com.ai.wechat.di

import com.ai.wechat.data.memory.MemoryEngine
import com.ai.wechat.data.memory.impl.GraphitiMemoryEngine
import com.google.gson.Gson
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import org.neo4j.driver.AuthTokens
import org.neo4j.driver.Driver
import org.neo4j.driver.GraphDatabase
import javax.inject.Singleton

/**
 * 记忆引擎模块
 */
@Module
@InstallIn(SingletonComponent::class)
object MemoryModule {

    @Provides
    @Singleton
    fun provideGson(): Gson {
        return Gson()
    }

    @Provides
    @Singleton
    fun provideNeo4jDriver(): Driver {
        // 默认配置，实际使用时可通过配置修改
        val uri = System.getenv("NEO4J_URI") ?: "bolt://localhost:7687"
        val username = System.getenv("NEO4J_USERNAME") ?: "neo4j"
        val password = System.getenv("NEO4J_PASSWORD") ?: "password"
        
        return GraphDatabase.driver(uri, AuthTokens.basic(username, password))
    }

    @Provides
    @Singleton
    fun provideMemoryEngine(
        neo4jDriver: Driver,
        memoryCacheDao: com.ai.wechat.db.dao.MemoryCacheDao,
        aiService: com.ai.wechat.network.AiService,
        gson: Gson
    ): MemoryEngine {
        return GraphitiMemoryEngine(neo4jDriver, memoryCacheDao, aiService, gson)
    }
}
