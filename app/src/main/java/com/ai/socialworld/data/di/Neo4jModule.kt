package com.ai.socialworld.data.di

import com.ai.socialworld.data.database.Neo4jDatabaseManager
import com.ai.socialworld.data.model.Neo4jConfig
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object Neo4jModule {

    @Provides
    @Singleton
    fun provideNeo4jConfig(): Neo4jConfig {
        return Neo4jConfig(
            uri = "neo4j://localhost:7687",
            username = "neo4j",
            password = "password",
            database = "neo4j"
        )
    }

    @Provides
    @Singleton
    fun provideNeo4jDatabaseManager(config: Neo4jConfig): Neo4jDatabaseManager {
        return Neo4jDatabaseManager(config)
    }
}
