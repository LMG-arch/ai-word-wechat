package com.ai.socialworld.data.repository

import com.ai.socialworld.data.database.Neo4jDatabaseManager
import com.ai.socialworld.data.model.Memory
import com.ai.socialworld.data.model.Neo4jRelationship
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Memory 仓库接口
 */
interface MemoryRepository {
    suspend fun createMemory(memory: Memory): Result<Memory>
    suspend fun getMemoryById(id: String): Result<Memory?>
    suspend fun updateMemory(memory: Memory): Result<Memory>
    suspend fun deleteMemory(id: String): Result<Unit>
    suspend fun linkToCharacter(characterId: Long, memoryId: String, relationship: Neo4jRelationship): Result<Unit>
    fun getAllMemoriesForCharacter(characterId: Long): Flow<List<Memory>>
}

/**
 * Memory 仓库实现
 */
@Singleton
class MemoryRepositoryImpl @Inject constructor(
    private val neo4jManager: Neo4jDatabaseManager
) : MemoryRepository {

    override suspend fun createMemory(memory: Memory): Result<Memory> =
        neo4jManager.createMemory(memory).map { memory }

    override suspend fun getMemoryById(id: String): Result<Memory?> =
        neo4jManager.getMemoryById(id).map { node ->
            node?.let { mapNodeToMemory(it) }
        }

    override suspend fun updateMemory(memory: Memory): Result<Memory> =
        runCatching {
            neo4jManager.execute(
                query = """
                    MATCH (n:Memory {id: $id})
                    SET n.content = $content,
                        n.importance = $importance,
                        n.accessCount = $accessCount,
                        n.lastAccessedAt = $lastAccessedAt
                    RETURN n
                """,
                params = mapOf(
                    "id" to memory.id,
                    "content" to memory.content,
                    "importance" to memory.importance,
                    "accessCount" to memory.accessCount,
                    "lastAccessedAt" to memory.lastAccessedAt?.toString()
                )
            ) { memory }
        }.getOrNull() ?: Result.failure(Exception("Failed to update memory"))

    override suspend fun deleteMemory(id: String): Result<Unit> =
        neo4jManager.execute(
            query = "MATCH (n:Memory {id: $id}) DETACH DELETE n",
            params = mapOf("id" to id)
        ) { }

    override suspend fun linkToCharacter(characterId: Long, memoryId: String, relationship: Neo4jRelationship): Result<Unit> =
        neo4jManager.linkCharacterToMemory(characterId, memoryId, relationship).map { }

    override fun getAllMemoriesForCharacter(characterId: Long): Flow<List<Memory>> = flow {
        val result = neo4jManager.execute(
            query = """
                MATCH (c:Character {id: $characterId})-[r]->(m:Memory)
                RETURN m
            """,
            params = mapOf("characterId" to characterId)
        ) { cursor ->
            cursor.list { record ->
                mapNodeToMemory(record[0].asNode())
            }
        }
        emit(result.getOrNull() ?: emptyList())
    }

    private fun mapNodeToMemory(node: org.neo4j.driver.types.Node): Memory {
        return Memory(
            id = node["id"].asString(),
            content = node["content"].asString(),
            type = Memory.MemoryType.valueOf(node["type"].asString()),
            importance = node["importance"].asFloat(),
            accessCount = node["accessCount"].asInt(),
            characterId = node["characterId"]?.asLong()
        )
    }
}
