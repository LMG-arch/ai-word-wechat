package com.ai.socialworld.data.database

import com.ai.socialworld.data.model.Memory
import com.ai.socialworld.data.model.Neo4jNode
import com.ai.socialworld.data.model.Neo4jRelationship
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.neo4j.driver.*
import org.neo4j.driver.types.Node
import org.neo4j.driver.types.Relationship
import java.time.Instant
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Neo4j 数据库管理器
 */
@Singleton
class Neo4jDatabaseManager @Inject constructor(
    private val config: Neo4jConfig
) {
    private var driver: Driver? = null

    fun connect() {
        if (driver == null) {
            driver = GraphDatabase.driver(
                config.uri,
                AuthTokens.basic(config.username, config.password)
            )
        }
    }

    fun disconnect() {
        driver?.close()
        driver = null
    }

    suspend fun <T> execute(query: String, params: Map<String, Any> = emptyMap(), block: (ResultCursor) -> T): Result<T> = withContext(Dispatchers.IO) {
        try {
            driver?.session()?.use { session ->
                val result = session.run(query, Values.parameters(*params.flatMap { it.toPair() }.toTypedArray()))
                Result.success(block(result))
            } ?: Result.failure(IllegalStateException("Neo4j driver not initialized"))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun createMemory(memory: Memory): Result<Node> = execute(
        query = """
            CREATE (n:Memory {
                id: $id,
                content: $content,
                type: $type,
                importance: $importance,
                accessCount: $accessCount,
                businessCreatedAt: $businessCreatedAt,
                businessExpiredAt: $businessExpiredAt
            })
            RETURN n
        """,
        params = mapOf(
            "id" to memory.id,
            "content" to memory.content,
            "type" to memory.type.name,
            "importance" to memory.importance,
            "accessCount" to memory.accessCount,
            "businessCreatedAt" to memory.businessCreatedAt.toString(),
            "businessExpiredAt" to memory.businessExpiredAt?.toString()
        )
    ) { cursor ->
        cursor.single()[0].asNode()
    }

    suspend fun getMemoryById(id: String): Result<Node?> = execute(
        query = "MATCH (n:Memory {id: $id}) RETURN n",
        params = mapOf("id" to id)
    ) { cursor ->
        if (cursor.hasNext()) cursor.single()[0].asNode() else null
    }

    suspend fun linkCharacterToMemory(characterId: Long, memoryId: String, relationshipType: Neo4jRelationship): Result<Relationship> = execute(
        query = """
            MATCH (c:Character {id: $characterId})
            MATCH (m:Memory {id: $memoryId})
            MERGE (c)-[r:${relationshipType.name}]->(m)
            RETURN r
        """,
        params = mapOf(
            "characterId" to characterId,
            "memoryId" to memoryId
        )
    ) { cursor ->
        cursor.single()[0].asRelationship()
    }

    data class Neo4jConfig(
        val uri: String = "bolt://localhost:7687",
        val username: String = "neo4j",
        val password: String = "password"
    )
}
