package com.ai.socialworld.data.di

import com.ai.socialworld.data.model.Neo4jConfig
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import org.neo4j.driver.Driver
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
    fun provideNeo4jDriver(config: Neo4jConfig): Driver {
        return org.neo4j.driver.GraphDatabase.driver(
            config.uri,
            org.neo4j.driver.AuthTokens.basic(config.username, config.password)
        )
    }
}
