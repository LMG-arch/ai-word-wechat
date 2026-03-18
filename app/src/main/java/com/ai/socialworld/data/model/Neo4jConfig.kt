package com.ai.socialworld.data.model

data class Neo4jConfig(
    val uri: String,
    val username: String,
    val password: String,
    val database: String = "neo4j"
)
